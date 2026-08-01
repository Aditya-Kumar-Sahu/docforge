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

        self.router_query = Query(self.language, """
        (assignment
            left: (identifier) @router_var
            right: (call
                function: (identifier) @class_name
                (#eq? @class_name "APIRouter")
                arguments: (argument_list
                    (keyword_argument
                        name: (identifier) @arg_name
                        (#eq? @arg_name "prefix")
                        value: (string) @prefix
                    )?
                )
            )
        )
        """)

        # Detects: app.include_router(some_router, prefix="/v2")
        # Captures: @include_app, @include_router_var, @include_prefix (optional)
        self.include_router_query = Query(self.language, """
        (expression_statement
            (call
                function: (attribute
                    object: (identifier) @include_app
                    attribute: (identifier) @include_method
                    (#eq? @include_method "include_router")
                )
                arguments: (argument_list
                    (identifier) @include_router_var
                    (keyword_argument
                        name: (identifier) @kw
                        (#eq? @kw "prefix")
                        value: (string) @include_prefix
                    )?
                )
            )
        )
        """)

    def parse_file(self, file_path: str) -> List[ParsedRoute]:
        if not os.path.exists(file_path):
            return []
            
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
            
        return self.parse_code(source_code, file_path)

    def _resolve_model_type(self, type_hint: str) -> str:
        """Helper to extract the core model name from Optional[Model], List[Model], etc."""
        if not type_hint:
            return "Any"
        # Handle List[Model], Optional[Model], Union[Model, None]
        match = re.search(r'(?:List|Optional|Union|dict)\[([^,\]]+)', type_hint)
        if match:
            return match.group(1).strip()
        return type_hint

    def parse_code(self, source_code: str, file_path: str = "unknown") -> List[ParsedRoute]:
        tree = self.parser.parse(bytes(source_code, "utf8"))

        # 1. Detect APIRouter definitions and their own prefixes
        router_prefixes: dict[str, str] = {}
        router_cursor = QueryCursor(self.router_query)
        for _, captures in router_cursor.matches(tree.root_node):
            var_node = captures.get('router_var', [None])[0]
            prefix_node = captures.get('prefix', [None])[0]
            if var_node and var_node.text:
                var_name = var_node.text.decode('utf8')
                prefix = ""
                if prefix_node and prefix_node.text:
                    prefix = prefix_node.text.decode('utf8').strip('\'"')
                router_prefixes[var_name] = prefix

        # 2. Detect include_router() calls and merge additional prefixes
        #    e.g. app.include_router(users_router, prefix="/api/v1")
        #    → users_router's effective prefix = its own prefix + "/api/v1"
        include_cursor = QueryCursor(self.include_router_query)
        for _, captures in include_cursor.matches(tree.root_node):
            router_var_node = captures.get('include_router_var', [None])[0]
            extra_prefix_node = captures.get('include_prefix', [None])[0]
            if router_var_node and router_var_node.text:
                router_var = router_var_node.text.decode('utf8')
                extra_prefix = ""
                if extra_prefix_node and extra_prefix_node.text:
                    extra_prefix = extra_prefix_node.text.decode('utf8').strip('\'"')
                if router_var in router_prefixes:
                    existing = router_prefixes[router_var]
                    # Merge: include_router prefix comes first (outer), own prefix second
                    merged = (extra_prefix.rstrip('/') + '/' + existing.lstrip('/')).rstrip('/')
                    if not merged.startswith('/'):
                        merged = '/' + merged
                    router_prefixes[router_var] = merged

        # 3. Parse Routes
        cursor = QueryCursor(self.route_query)
        matches = cursor.matches(tree.root_node)

        routes = []
        
        for _, captures in matches:
            if 'method' in captures and 'path' in captures and 'handler_name' in captures:
                app_obj_node = captures['app_obj'][0] if isinstance(captures['app_obj'], list) else captures['app_obj']
                method_node = captures['method'][0] if isinstance(captures['method'], list) else captures['method']
                path_node = captures['path'][0] if isinstance(captures['path'], list) else captures['path']
                handler_node = captures['handler_name'][0] if isinstance(captures['handler_name'], list) else captures['handler_name']
                
                if not (method_node and method_node.text and path_node and path_node.text and handler_node and handler_node.text):
                    continue

                app_obj = app_obj_node.text.decode('utf8') if app_obj_node and app_obj_node.text else "app"
                method = method_node.text.decode('utf8').upper()
                path = path_node.text.decode('utf8').strip('\'"')
                
                # Prepend router prefix if applicable
                if app_obj in router_prefixes:
                    prefix = router_prefixes[app_obj]
                    path = (prefix.rstrip('/') + '/' + path.lstrip('/')).rstrip('/')
                    if not path.startswith('/'):
                        path = '/' + path
                
                handler_name = handler_node.text.decode('utf8')
                line_number = handler_node.start_point.row + 1
                
                docstring = None
                if 'body' in captures:
                    body_node = captures['body'][0] if isinstance(captures['body'], list) else captures['body']
                    if body_node and body_node.named_child_count > 0:
                        first_stmt = body_node.named_child(0)
                        if first_stmt and first_stmt.type == 'expression_statement':
                            expr = first_stmt.named_child(0)
                            if expr and expr.type == 'string' and expr.text:
                                docstring = expr.text.decode('utf8').strip('\'"')

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
                            if child.type == 'identifier' and child.text:
                                name = child.text.decode('utf8')
                            elif child.type == 'type' and child.text:
                                type_hint = child.text.decode('utf8')
                    elif param.type == 'identifier' and param.text:
                        name = param.text.decode('utf8')
                        type_hint = "Any"
                        
                    if not name:
                        continue
                        
                    param_info = {"name": name, "type": type_hint}
                    
                    if name in path_param_names:
                        path_parameters.append(param_info)
                    else:
                        core_type = self._resolve_model_type(type_hint or "")
                        if core_type and core_type[0].isupper() and core_type not in ("Any", "List", "Dict", "Optional", "Union", "Set", "Tuple"):
                            request_model = {"name": name, "type": type_hint}
                        else:
                            query_parameters.append(param_info)

                response_model = None
                if 'return_type' in captures:
                    node = captures['return_type'][0]
                    if node and node.text:
                        response_model = {"type": node.text.decode('utf8')}
                elif 'response_model_arg' in captures:
                    node = captures['response_model_arg'][0]
                    if node and node.text:
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