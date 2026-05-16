import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor
from typing import List
from app.models.route import ParsedRoute
import os
import re

class FastAPIParser:
    def __init__(self) -> None:
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)
        
        self.route_query = Query(self.language, """
        (decorated_definition
            (decorator
                (call
                    function: (attribute
                        object: (identifier) @app_obj
                        attribute: (identifier) @method
                        (#match? @method "^(get|post|put|patch|delete)$")
                    )
                    arguments: (argument_list
                        (string) @path
                        (keyword_argument
                            name: (identifier) @kw_name
                            value: (_) @response_model_arg
                            (#eq? @kw_name "response_model")
                        )?
                    )
                )
            ) @decorator
            (function_definition
                name: (identifier) @handler_name
                parameters: (parameters) @params
                return_type: (type)? @return_type
                body: (block)? @body
            ) @function
        ) @route_def
        """)

    def parse_file(self, file_path: str) -> List[ParsedRoute]:
        if not os.path.exists(file_path):
            return []
            
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
            
        return self.parse_code(source_code, file_path)

    def parse_code(self, source_code: str, file_path: str = "unknown") -> List[ParsedRoute]:
        tree = self.parser.parse(bytes(source_code, "utf8"))
        cursor = QueryCursor(self.route_query)
        matches = cursor.matches(tree.root_node)
        
        routes = []
        
        for _, captures in matches:
            # In tree_sitter 0.22+, matches returns (pattern_index, captures_dict)
            # captures_dict is { "capture_name": [nodes] }
            
            if 'method' in captures and 'path' in captures and 'handler_name' in captures:
                # Get the first node for each capture
                method_node = captures['method'][0] if isinstance(captures['method'], list) else captures['method']
                path_node = captures['path'][0] if isinstance(captures['path'], list) else captures['path']
                handler_node = captures['handler_name'][0] if isinstance(captures['handler_name'], list) else captures['handler_name']
                
                if not (method_node and path_node and handler_node):
                    continue

                method = method_node.text.decode('utf8').upper() if method_node.text is not None else ""
                path = path_node.text.decode('utf8').strip('\'"') if path_node.text is not None else ""
                
                handler_name = handler_node.text.decode('utf8') if handler_node.text is not None else ""
                line_number = handler_node.start_point.row + 1
                
                docstring = None
                if 'body' in captures:
                    body_node = captures['body'][0] if isinstance(captures['body'], list) else captures['body']
                    if body_node and body_node.named_child_count > 0:
                        first_stmt = body_node.named_child(0)
                        if first_stmt and first_stmt.type == 'expression_statement':
                            expr = first_stmt.named_child(0)
                            if expr and expr.type == 'string' and expr.text is not None:
                                docstring = expr.text.decode('utf8').strip('\'"')

                # Extract Path Parameters from path string
                path_param_names = re.findall(r'\{([a-zA-Z0-9_]+)\}', path)
                
                path_parameters = []
                query_parameters = []
                request_model = None
                
                params_node = captures['params'][0] if isinstance(captures['params'], list) else captures['params']
                for param in params_node.named_children:
                    name = None
                    type_hint = None
                    
                    if param.type in ('typed_parameter', 'typed_default_parameter'):
                        for child in param.named_children:
                            if child.type == 'identifier':
                                name = child.text.decode('utf8') if child.text is not None else ""
                            elif child.type == 'type':
                                type_hint = child.text.decode('utf8') if child.text is not None else ""
                    elif param.type == 'identifier':
                        name = param.text.decode('utf8') if param.text is not None else ""
                        type_hint = "Any"
                        
                    if not name:
                        continue
                        
                    param_info = {"name": name, "type": type_hint}
                    
                    # Heuristic for request_model vs path/query param
                    if name in path_param_names:
                        path_parameters.append(param_info)
                    else:
                        # In FastAPI, usually capitalized types denote a request body Pydantic model
                        if type_hint and type_hint[0].isupper() and type_hint not in ("Any", "List", "Dict", "Optional", "Union"):
                            request_model = {"name": name, "type": type_hint}
                        else:
                            query_parameters.append(param_info)

                response_model = None
                if 'return_type' in captures:
                    node = captures['return_type'][0] if isinstance(captures['return_type'], list) else captures['return_type']
                    if node and node.text is not None:
                        response_model = {"type": node.text.decode('utf8')}
                elif 'response_model_arg' in captures:
                    node = captures['response_model_arg'][0] if isinstance(captures['response_model_arg'], list) else captures['response_model_arg']
                    if node and node.text is not None:
                        response_model = {"type": node.text.decode('utf8')}

                route = ParsedRoute(
                    method=method,
                    path=path,
                    handler_name=handler_name,
                    file_path=file_path,
                    line_number=line_number,
                    docstring=docstring,
                    path_parameters=path_parameters,
                    query_parameters=query_parameters,
                    request_model=request_model,
                    response_model=response_model
                )
                routes.append(route)
                
        return routes