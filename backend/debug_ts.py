import tree_sitter
import tree_sitter_python

lang = tree_sitter.Language(tree_sitter_python.language())
parser = tree_sitter.Parser(lang)
tree = parser.parse(b"@app.get('/health')\ndef health(): pass")
query = tree_sitter.Query(lang, "(decorator) @d")
cursor = tree_sitter.QueryCursor(query)
caps = cursor.captures(tree.root_node)

for k, v in caps.items():
    for node in v:
        print(f"Node: {node.type}, Text: {node.text.decode('utf8')}")
        print(f"Parent: {node.parent.type}")
        print(f"Parent children types: {[c.type for c in node.parent.children]}")
