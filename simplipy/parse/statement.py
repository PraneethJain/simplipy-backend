from simplipy.parse.types import Instruction, Statement, Block
from simplipy.parse.instruction import (
    DoneInstr,
    PassInstr,
    ExprAssignInstr,
    CallAssignInstr,
    IfInstr,
    WhileInstr,
    DefInstr,
    RetInstr,
    BreakInstr,
    ContinueInstr,
    GlobalInstr,
    NonlocalInstr,
)


class DoneStatement(Statement):
    def __init__(self, instr: DoneInstr) -> None:
        self.instr = instr
        self.instr.set_parent(self)

    def first(self) -> int:
        return self.instr.lineno

    def last(self) -> int:
        return self.instr.lineno

    def first_instr(self) -> Instruction:
        return self.instr


class GlobalStmt(Statement):
    def __init__(self, instr: GlobalInstr) -> None:
        self.instr = instr
        self.instr.set_parent(self)

    def first(self) -> int:
        return self.instr.lineno

    def last(self) -> int:
        return self.instr.lineno

    def first_instr(self) -> Instruction:
        return self.instr


class NonlocalStmt(Statement):
    def __init__(self, instr: NonlocalInstr) -> None:
        self.instr = instr
        self.instr.set_parent(self)

    def first(self) -> int:
        return self.instr.lineno

    def last(self) -> int:
        return self.instr.lineno

    def first_instr(self) -> Instruction:
        return self.instr


class PassStmt(Statement):
    def __init__(self, instr: PassInstr) -> None:
        self.instr = instr
        self.instr.set_parent(self)

    def first(self) -> int:
        return self.instr.lineno

    def last(self) -> int:
        return self.instr.lineno

    def first_instr(self) -> Instruction:
        return self.instr


class ExpAssignStmt(Statement):
    def __init__(self, instr: ExprAssignInstr) -> None:
        self.instr = instr
        self.instr.set_parent(self)

    def first(self) -> int:
        return self.instr.lineno

    def last(self) -> int:
        return self.instr.lineno

    def first_instr(self) -> Instruction:
        return self.instr


class CallAssignStmt(Statement):
    def __init__(self, instr: CallAssignInstr) -> None:
        self.instr = instr
        self.instr.set_parent(self)

    def first(self) -> int:
        return self.instr.lineno

    def last(self) -> int:
        return self.instr.lineno

    def first_instr(self) -> Instruction:
        return self.instr


class IfStmt(Statement):
    def __init__(
        self,
        if_instr: IfInstr,
        if_block: Block,
        else_block: Block,
    ) -> None:
        self.if_instr = if_instr
        self.if_block = if_block
        self.else_block = else_block

        self.if_instr.set_parent(self)
        self.if_block.set_parent(self)
        self.else_block.set_parent(self)

    def first(self) -> int:
        return self.if_instr.lineno

    def last(self) -> int:
        return self.else_block.last()

    def first_instr(self) -> Instruction:
        return self.if_instr

    def to_dict(self) -> dict:
        data = super().to_dict()

        data["if_block"] = self.if_block.to_dict()
        data["else_block"] = self.else_block.to_dict()

        return data


class WhileStmt(Statement):
    def __init__(self, while_instr: WhileInstr, block: Block) -> None:
        self.while_instr = while_instr
        self.block = block

        self.while_instr.set_parent(self)
        self.block.set_parent(self)

    def first(self) -> int:
        return self.while_instr.lineno

    def last(self) -> int:
        return self.block.last()

    def first_instr(self) -> Instruction:
        return self.while_instr

    def to_dict(self) -> dict:
        data = super().to_dict()

        data["block"] = self.block.to_dict()

        return data


class BreakStmt(Statement):
    def __init__(self, instr: BreakInstr) -> None:
        self.instr = instr
        self.instr.set_parent(self)

    def first(self) -> int:
        return self.instr.lineno

    def last(self) -> int:
        return self.instr.lineno

    def first_instr(self) -> Instruction:
        return self.instr


class ContinueStmt(Statement):
    def __init__(self, instr: ContinueInstr) -> None:
        self.instr = instr
        self.instr.set_parent(self)

    def first(self) -> int:
        return self.instr.lineno

    def last(self) -> int:
        return self.instr.lineno

    def first_instr(self) -> Instruction:
        return self.instr


class DefStmt(Statement):
    def __init__(self, def_instr: DefInstr, block: Block) -> None:
        self.def_instr = def_instr
        self.block = block

        self.def_instr.set_parent(self)
        self.block.set_parent(self)

    def first(self) -> int:
        return self.def_instr.lineno

    def last(self) -> int:
        return self.block.last()

    def first_instr(self) -> Instruction:
        # Think about this later
        return self.def_instr

    def to_dict(self) -> dict:
        data = super().to_dict()

        data["name"] = self.def_instr.func_var
        data["block"] = self.block.to_dict()

        return data


class RetStmt(Statement):
    def __init__(self, instr: RetInstr) -> None:
        self.instr = instr
        self.instr.set_parent(self)

    def first(self) -> int:
        return self.instr.lineno

    def last(self) -> int:
        return self.instr.lineno

    def first_instr(self) -> Instruction:
        return self.instr
