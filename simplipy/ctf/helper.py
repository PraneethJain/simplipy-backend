from simplipy.parse.types import Statement
from simplipy.parse.statement import WhileStmt
from functools import partial
from typing import Type


def encl(stmt_type: Type[Statement], stmt: Statement) -> Statement:
    parent_block = stmt.parent
    if parent_block.parent is None:
        raise SyntaxError("Hit top level without finding enclosing statement")
    else:
        parent_stmt = parent_block.parent
        if isinstance(parent_stmt, stmt_type):
            return parent_stmt
        else:
            return encl(stmt_type, parent_stmt)


encl_while = partial(encl, WhileStmt)
