from simplipy.parse.types import Statement
from simplipy.parse.statement import (
    IfStmt,
    RetStmt,
    BreakStmt,
    WhileStmt,
    ContinueStmt,
)
from simplipy.ctf.helper import encl_while


def next(stmt: Statement) -> Statement:
    if isinstance(stmt, ContinueStmt):
        return encl_while(stmt)
    if isinstance(stmt, BreakStmt):
        return next(encl_while(stmt))
    if isinstance(stmt, RetStmt):
        raise ValueError("next control transfer function not defined for return")

    block, stmt_num = stmt.parent, stmt.idx

    if stmt_num == len(block) - 1:
        if block.parent is None:  # Top level block
            return stmt  # Fixed point
        else:
            return next(block.parent)
    else:
        return block[stmt_num + 1]


def true(stmt: Statement) -> Statement:
    if isinstance(stmt, WhileStmt):
        return stmt.block[0]

    if isinstance(stmt, IfStmt):
        return stmt.if_block[0]

    raise ValueError(f"true control transfer function not defined for {stmt}")


def false(stmt: Statement) -> Statement:
    if isinstance(stmt, WhileStmt):
        return next(stmt)

    if isinstance(stmt, IfStmt):
        return stmt.else_block[0]

    raise ValueError(f"true control transfer function not defined for {stmt}")
