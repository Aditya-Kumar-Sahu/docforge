import tree_sitter
import tree_sitter_python

lang = tree_sitter.Language(tree_sitter_python.language())
parser = tree_sitter.Parser(lang)
tree = parser.parse(b"""
class User(BaseModel):
    id: int
    username: str = "guest"
    active: bool = True
""")

query = tree_sitter.Query(lang, "(class_definition body: (block) @body) @class")
cursor = tree_sitter.QueryCursor(query)
caps = cursor.captures(tree.root_node)

body = caps["body"][0]
for child in body.children:
    print(f"Child type: {child.type}, Text: {child.text.decode('utf8')}")
    if child.type == "expression_statement":
        expr = child.children[0]
        print(f"  Expr type: {expr.type}")
        print(f"    Children types: {[c.type for c in expr.children]}")
        for i in range(expr.child_count):
            field = expr.field_name_for_child(i)
            if field:
                print(f"      Field {i}: {field}")
