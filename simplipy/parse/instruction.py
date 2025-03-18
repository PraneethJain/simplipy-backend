from simplipy.parse.expression import Expression
from simplipy.parse.types import Instruction


class PassInstr(Instruction):
    pass


class GlobalInstr(Instruction):
    def __init__(self, lineno: int, vars: list[str]) -> None:
        super().__init__(lineno)
        self.vars = vars


class NonlocalInstr(Instruction):
    def __init__(self, lineno: int, vars: list[str]) -> None:
        super().__init__(lineno)
        self.vars = vars


class ExprAssignInstr(Instruction):
    def __init__(self, lineno: int, var: str, expr: Expression) -> None:
        super().__init__(lineno)
        self.var = var
        self.expr = expr


class CallAssignInstr(Instruction):
    def __init__(
        self, lineno: int, var: str, func_var: str, func_args: list[Expression]
    ) -> None:
        super().__init__(lineno)
        self.var = var
        self.func_var = func_var
        self.func_args = func_args


class IfInstr(Instruction):
    def __init__(self, lineno: int, expr: Expression) -> None:
        super().__init__(lineno)
        self.expr = expr


class ElseInstr(Instruction):
    pass


class WhileInstr(Instruction):
    def __init__(self, lineno: int, expr: Expression) -> None:
        super().__init__(lineno)
        self.expr = expr


class BreakInstr(Instruction):
    pass


class ContinueInstr(Instruction):
    pass


class DefInstr(Instruction):
    def __init__(self, lineno: int, func_var: str, formals: list[str]) -> None:
        super().__init__(lineno)
        self.func_var = func_var
        self.formals = formals


class RetInstr(Instruction):
    def __init__(self, lineno: int, expr: Expression) -> None:
        super().__init__(lineno)
        self.expr = expr
