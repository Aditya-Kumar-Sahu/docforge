import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor

language = Language(tspython.language())
parser = Parser(language)
query = Query(language, "(function_definition name: (identifier) @name) @func")

code = "def foo(): pass"
tree = parser.parse(bytes(code, "utf8"))
cursor = QueryCursor(query)
matches = cursor.matches(tree.root_node)

for match in matches:
    print(f"Match: {type(match)} - {match}")
    if isinstance(match, tuple):
        for i, item in enumerate(match):
            print(f"  Item {i}: {type(item)} - {item}")
