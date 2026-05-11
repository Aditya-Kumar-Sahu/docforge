import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor
from typing import Any, List, Dict
import structlog

logger = structlog.get_logger()

PY_LANGUAGE = Language(tspython.language())

class FastAPIParser:
    def __init__(self):
        self.parser = Parser(PY_LANGUAGE)
        self.models: Dict[str, Dict[str, Any]] = {}
        self.prefixes: Dict[str, str] = {}

    def parse_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Parses a Python file and extracts FastAPI route information, Pydantic models, and router prefixes.
        """
        tree = self.parser.parse(bytes(content, "utf8"))
        
        # Pass 1: Collect Metadata
        self._collect_models(tree.root_node)
        self._collect_prefixes(tree.root_node)
        
        # Pass 2: Extract Routes
        query = Query(PY_LANGUAGE, "(decorator) @decorator")
        cursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)
        
        routes = []
        decorator_nodes = captures.get("decorator", [])
        
        for node in decorator_nodes:
            try:
                call_node = next((c for c in node.children if c.type == "call"), None)
                if not call_node:
                    continue
                
                func_node = call_node.child_by_field_name("function")
                if not func_node or func_node.type != "attribute":
                    continue
                
                method_node = func_node.child_by_field_name("attribute")
                obj_node = func_node.child_by_field_name("object")
                
                method = method_node.text.decode("utf8").upper()
                obj_name = obj_node.text.decode("utf8") if obj_node else ""
                
                if method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue
                
                # Extract path
                arg_list = call_node.child_by_field_name("arguments")
                path = ""
                if arg_list and arg_list.named_child_count > 0:
                    path_node = arg_list.named_children[0]
                    if path_node.type == "string":
                        path = path_node.text.decode("utf8").strip("\"'")
                
                # Apply router prefix if applicable
                if obj_name in self.prefixes:
                    prefix = self.prefixes[obj_name]
                    path = "/" + prefix.strip("/") + "/" + path.lstrip("/")
                    path = path.replace("//", "/")
                
                # Find the function definition
                parent = node.parent
                func_def = None
                if parent and parent.type == "decorated_definition":
                    func_def = next((c for c in parent.children if c.type == "function_definition"), None)
                
                if not func_def:
                    continue
                
                # Extract docstring
                docstring = ""
                body_node = func_def.child_by_field_name("body")
                if body_node and body_node.named_child_count > 0:
                    first_stmt = body_node.named_children[0]
                    if first_stmt.type == "expression_statement":
                        expr = first_stmt.named_children[0]
                        if expr.type == "string":
                            docstring = expr.text.decode("utf8").strip("\"' \n\r")

                # Extract handler name
                handler_name = ""
                name_node = func_def.child_by_field_name("name")
                if name_node:
                    handler_name = name_node.text.decode("utf8")
                
                if not handler_name:
                    continue
                
                # Extract parameters
                params = []
                parameters_node = func_def.child_by_field_name("parameters")
                if parameters_node:
                    for param in parameters_node.named_children:
                        p_name = ""
                        p_type = "Any"
                        p_schema = None
                        
                        if param.type == "typed_parameter":
                            p_name = param.named_children[0].text.decode("utf8")
                            type_node = param.child_by_field_name("type")
                            if type_node:
                                p_type = type_node.text.decode("utf8")
                        elif param.type == "identifier":
                            p_name = param.text.decode("utf8")
                        elif param.type == "default_parameter":
                            # default_parameter has child 'name' which could be a typed_parameter
                            name_child = param.child_by_field_name("name")
                            if name_child:
                                if name_child.type == "typed_parameter":
                                    p_name = name_child.named_children[0].text.decode("utf8")
                                    type_node = name_child.child_by_field_name("type")
                                    if type_node:
                                        p_type = type_node.text.decode("utf8")
                                else:
                                    p_name = name_child.text.decode("utf8")
                        
                        if p_name and p_name != "self":
                            if p_type in self.models:
                                p_schema = self.models[p_type]
                                
                            params.append({
                                "name": p_name,
                                "type": p_type,
                                "schema": p_schema
                            })
                
                routes.append({
                    "method": method,
                    "path": path,
                    "handler_name": handler_name,
                    "file_path": file_path,
                    "line_number": func_def.start_point[0] + 1,
                    "params": params,
                    "docstring": docstring
                })
                
            except Exception as e:
                logger.error("parse_error", error=str(e))
                continue
        
        logger.info("parsed_file", file_path=file_path, routes_found=len(routes))
        return routes

    def _collect_models(self, root_node: Any):
        """
        Scans the AST for class definitions and extracts their structure.
        """
        query = Query(PY_LANGUAGE, "(class_definition name: (identifier) @name body: (block) @body) @class")
        cursor = QueryCursor(query)
        captures = cursor.captures(root_node)
        
        class_nodes = captures.get("class", [])
        name_nodes = captures.get("name", [])
        body_nodes = captures.get("body", [])
        
        for i in range(len(class_nodes)):
            name = name_nodes[i].text.decode("utf8")
            body = body_nodes[i]
            
            fields = {}
            for child in body.children:
                if child.type == "expression_statement":
                    expr = child.children[0]
                    if expr.type == "assignment":
                        left = expr.child_by_field_name("left")
                        type_node = expr.child_by_field_name("type")
                        if left and type_node:
                            f_name = left.text.decode("utf8")
                            f_type = type_node.text.decode("utf8")
                            fields[f_name] = {"type": f_type}
            
            self.models[name] = {"fields": fields}

    def _collect_prefixes(self, root_node: Any):
        """
        Scans for router = APIRouter(prefix="/...") patterns.
        """
        query = Query(PY_LANGUAGE, """
        (assignment
          left: (identifier) @var_name
          right: (call
            function: (identifier) @class_name
            arguments: (argument_list
              (keyword_argument
                name: (identifier) @arg_name
                value: (string) @prefix
              )
            )
          )
        )
        """)
        cursor = QueryCursor(query)
        captures = cursor.captures(root_node)
        
        var_names = captures.get("var_name", [])
        class_names = captures.get("class_name", [])
        arg_names = captures.get("arg_name", [])
        prefixes = captures.get("prefix", [])
        
        for i in range(min(len(var_names), len(class_names), len(arg_names), len(prefixes))):
            if class_names[i].text.decode("utf8") == "APIRouter":
                if arg_names[i].text.decode("utf8") == "prefix":
                    self.prefixes[var_names[i].text.decode("utf8")] = prefixes[i].text.decode("utf8").strip("\"'")
