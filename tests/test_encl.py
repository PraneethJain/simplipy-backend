from simplipy.ctf.helper import encl_while
from simplipy.parse.parse import Visitor
from simplipy.parse.statement import IfStmt
import ast


def test_encl_while_simple():
    filename = "tests/test_files/a.py"
    with open(filename, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filename)

    visitor = Visitor()
    pgm = visitor.parse_pgm(tree)
    while_stmt = pgm.block.stmts[-2]

    for stmt in while_stmt.block.stmts:
        assert encl_while(stmt) == while_stmt

        if isinstance(stmt, IfStmt):
            for inner_stmt in stmt.if_block.stmts + stmt.else_block.stmts:
                assert encl_while(inner_stmt) == while_stmt
