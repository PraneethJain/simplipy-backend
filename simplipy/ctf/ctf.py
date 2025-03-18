from simplipy.ctf import stf
from simplipy.parse.types import Instruction, Statement, Block, Program
from simplipy.parse.statement import IfStmt, WhileStmt, DefStmt, RetStmt
from typing import Callable


def construct_ctf(
    stf: Callable[[Statement], Statement]
) -> Callable[[Instruction], Instruction]:
    def ctf(instr: Instruction) -> Instruction:
        stmt = stf(instr.parent)
        return stmt.first_instr()

    return ctf


next = construct_ctf(stf.next)
true = construct_ctf(stf.true)
false = construct_ctf(stf.false)


def get_ctfs(pgm: Program) -> dict[str, dict[int, int]]:
    ctf_table: dict[str, dict[int, int]] = {"next": {}, "true": {}, "false": {}}

    def visit_all_instrs(blk: Block):
        for stmt in blk:
            if isinstance(stmt, IfStmt):
                ctf_table["true"][stmt.first()] = true(stmt.if_instr).lineno
                ctf_table["false"][stmt.first()] = false(stmt.if_instr).lineno
                visit_all_instrs(stmt.if_block)
                visit_all_instrs(stmt.else_block)
            elif isinstance(stmt, WhileStmt):
                ctf_table["true"][stmt.first()] = true(stmt.while_instr).lineno
                ctf_table["false"][stmt.first()] = false(stmt.while_instr).lineno
                visit_all_instrs(stmt.block)
            elif isinstance(stmt, DefStmt):
                visit_all_instrs(stmt.block)
            elif isinstance(stmt, RetStmt):
                pass
            elif blk.parent is None and stmt.idx == len(blk) - 1:
                pass
            else:
                ctf_table["next"][stmt.first()] = next(stmt.first_instr()).lineno

    visit_all_instrs(pgm.block)

    return ctf_table
