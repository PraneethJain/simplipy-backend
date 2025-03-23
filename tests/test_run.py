from simplipy.parse.parse import Visitor
from simplipy.semantics.state import State, GLOBAL_ENV_ID
from simplipy.semantics.types import Closure
import ast


def test_run_simple():
    filename = "tests/test_files/a.py"
    with open(filename, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filename)

    visitor = Visitor()
    pgm = visitor.parse_pgm(tree)

    state = State(pgm)

    while not state.is_final():
        state.step()

    assert state.e.envs[GLOBAL_ENV_ID] == {
        "i": 11,
        "y": 742,
        "z": 752,
        "f": Closure(2, ["x", "y"]),
    }
