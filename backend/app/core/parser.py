import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor
from typing import Any, List, Dict
import structlog

logger = structlog.get_logger()

PY_LANGUAGE = Language(tspython.language())

class FastAPIParser:
    def __init__(self):
        self.parser = Parser(PY_LANGUAGE)

    def parse_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Parses a Python file and extracts FastAPI route information.
        """
        tree = self.parser.parse(bytes(content, "utf8"))
        
        # Query to find decorators
        # Pattern: @app.get("/path") or @router.post("/path")
        query_text = """
        (decorator
          (call
            function: (attribute
              object: (identifier) @obj
              attribute: (identifier) @method
            )
            arguments: (argument_list
              (string) @path
            )
          )
        ) @decorator
        """
        query = Query(PY_LANGUAGE, query_text)
        cursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)
        
        routes = []
        # 'captures' is a dict mapping capture names to lists of nodes in tree-sitter 0.25+
        decorator_nodes = captures.get("decorator", [])
        
        for node in decorator_nodes:
            # In Python grammar, decorators and the function they decorate are wrapped in a decorated_definition
            parent = node.parent
            if parent and parent.type == "decorated_definition":
                # Find the function_definition sibling/child
                func_def = None
                for child in parent.children:
                    if child.type == "function_definition":
                        func_def = child
                        break
                
                if func_def:
                    # Extract handler name
                    handler_name = ""
                    for child in func_def.children:
                        if child.type == "identifier" and child.prev_sibling and child.prev_sibling.type == "def":
                            handler_name = child.text.decode("utf8")
                            break
                    
                    # Extract method and path from the decorator node
                    try:
                        # decorator -> call
                        call_node = node.named_children[0]
                        attr_node = call_node.child_by_field_name("function")
                        method_node = attr_node.child_by_field_name("attribute")
                        method = method_node.text.decode("utf8").upper()
                        
                        arg_list = call_node.child_by_field_name("arguments")
                        path = ""
                        if arg_list and arg_list.named_child_count > 0:
                            path_node = arg_list.named_children[0]
                            path = path_node.text.decode("utf8").strip("\"'")
                        
                        if method in ["GET", "POST", "PUT", "DELETE", "PATCH"] and handler_name:
                            routes.append({
                                "method": method,
                                "path": path,
                                "handler_name": handler_name,
                                "file_path": file_path,
                                "line_number": func_def.start_point[0] + 1
                            })
                    except (IndexError, AttributeError):
                        continue
        
        logger.info("parsed_file", file_path=file_path, routes_found=len(routes))
        return routes
