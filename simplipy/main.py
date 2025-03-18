from simplipy.parse.parse import Visitor
import ast


filename = "tests/test_files/a.py"
with open(filename, "r", encoding="utf-8") as f:
    tree = ast.parse(f.read(), filename=filename)

visitor = Visitor()
pgm = visitor.parse_pgm(tree)
