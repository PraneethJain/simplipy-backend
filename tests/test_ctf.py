from simplipy.ctf.ctf import get_ctfs
from simplipy.parse.parse import Visitor
import ast


def test_ctf_simple():
    filename = "tests/test_files/a.py"
    with open(filename, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filename)

    visitor = Visitor()
    pgm = visitor.parse_pgm(tree)

    ctf_table = get_ctfs(pgm)

    assert ctf_table == {
        "next": {
            2: 3,
            3: 4,
            7: 8,
            9: 10,
            10: 11,
            11: 12,
            13: 14,
            14: 8,
            16: 18,
            19: 24,
            21: 22,
            22: 8,
        },
        "true": {8: 9, 12: 13, 18: 19},
        "false": {8: 24, 12: 16, 18: 21},
    }


test_ctf_simple()
