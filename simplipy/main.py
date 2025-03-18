from simplipy.parse.parse import Visitor
from simplipy.semantics.state import State
import ast
from rich import print


filename = "tests/test_files/a.py"
with open(filename, "r", encoding="utf-8") as f:
    tree = ast.parse(f.read(), filename=filename)

visitor = Visitor()
pgm = visitor.parse_pgm(tree)

state = State(pgm)

print(state.ctfs)

while True:
    print(state.e, state.k)
    state.step()
