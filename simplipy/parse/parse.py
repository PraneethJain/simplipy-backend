import ast
from simplipy.parse.statement import (
    Block,
    Statement,
    IfStmt,
    DefStmt,
    RetStmt,
    PassStmt,
    BreakStmt,
    WhileStmt,
    ContinueStmt,
    CallAssignStmt,
    ExpAssignStmt,
    GlobalStmt,
    NonlocalStmt,
)
from simplipy.parse.expression import Expression
from simplipy.parse.instruction import (
    IfInstr,
    DefInstr,
    RetInstr,
    PassInstr,
    BreakInstr,
    WhileInstr,
    ContinueInstr,
    CallAssignInstr,
    ExprAssignInstr,
    GlobalInstr,
    NonlocalInstr,
)
from simplipy.parse.types import Program


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.block_stack = [Block([], lexical=True)]
        self.block_stack[-1].set_parent(None)

    def _add_stmt(self, stmt: Statement) -> None:
        stmt.set_idx(len(self.block_stack[-1]))
        stmt.set_parent(self.block_stack[-1])
        self.block_stack[-1]._add_stmt(stmt)

    def _encl_lexical_block(self) -> Block:
        for blk in reversed(self.block_stack):
            if blk.lexical:
                return blk
        raise LookupError("No enclosing lexical block found")

    def _update_locals(self, var: str) -> None:
        encl_lexical_block = self._encl_lexical_block()
        if self.block_stack.index(encl_lexical_block) != 0:  # Not the top level block
            encl_lexical_block.locals.add(var)

    def parse_pgm(self, tree: ast.AST) -> Program:
        self.visit(tree)
        return Program(self.block_stack[0])

    def visit_Module(self, node: ast.Module) -> None:
        for stmt_node in node.body:
            self.visit(stmt_node)

    def visit_Pass(self, node: ast.Pass) -> None:
        instr = PassInstr(node.lineno)
        stmt = PassStmt(instr)
        self._add_stmt(stmt)

    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) != 1:
            raise NotImplementedError("Multiple Assignment targets not supported")
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise NotImplementedError("Only assignments to variables are supported")
        var = target.id
        self._update_locals(var)
        value = node.value
        if isinstance(value, ast.Call):
            if not isinstance(value.func, ast.Name):
                raise NotImplementedError("Only simple function calls are supported")
            func_var = value.func.id
            func_args = [Expression(arg) for arg in value.args]
            instr = CallAssignInstr(node.lineno, var, func_var, func_args)
            stmt = CallAssignStmt(instr)
        else:
            expr = Expression(value)
            instr = ExprAssignInstr(node.lineno, var, expr)
            stmt = ExpAssignStmt(instr)
        self._add_stmt(stmt)

    def visit_If(self, node: ast.If) -> None:
        test_expr = Expression(node.test)
        if_instr = IfInstr(node.lineno, test_expr)
        self.block_stack.append(Block([]))
        for stmt_node in node.body:
            self.visit(stmt_node)
        if_block = self.block_stack.pop()
        if not node.orelse:
            raise ValueError("If must have an else block")
        self.block_stack.append(Block([]))
        for stmt_node in node.orelse:
            self.visit(stmt_node)
        else_block = self.block_stack.pop()

        if_stmt = IfStmt(if_instr, if_block, else_block)
        self._add_stmt(if_stmt)

    def visit_While(self, node: ast.While) -> None:
        test_expr = Expression(node.test)
        while_instr = WhileInstr(node.lineno, test_expr)
        self.block_stack.append(Block([]))
        for stmt_node in node.body:
            self.visit(stmt_node)
        loop_block = self.block_stack.pop()
        while_stmt = WhileStmt(while_instr, loop_block)
        self._add_stmt(while_stmt)

    def visit_Break(self, node: ast.Break) -> None:
        instr = BreakInstr(node.lineno)
        stmt = BreakStmt(instr)
        self._add_stmt(stmt)

    def visit_Continue(self, node: ast.Continue) -> None:
        instr = ContinueInstr(node.lineno)
        stmt = ContinueStmt(instr)
        self._add_stmt(stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        formals = [arg.arg for arg in node.args.args]
        self._update_locals(node.name)
        def_instr = DefInstr(node.lineno, node.name, formals)
        self.block_stack.append(Block([], lexical=True))
        for stmt_node in node.body:
            self.visit(stmt_node)
        func_block = self.block_stack.pop()
        def_stmt = DefStmt(def_instr, func_block)
        self._add_stmt(def_stmt)

    def visit_Return(self, node: ast.Return) -> None:
        if node.value is None:
            raise NotImplementedError("Return without value is not supported")
        expr = Expression(node.value)
        instr = RetInstr(node.lineno, expr)
        stmt = RetStmt(instr)
        self._add_stmt(stmt)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self._encl_lexical_block().nonlocals.update(node.names)
        instr = NonlocalInstr(node.lineno, node.names)
        stmt = NonlocalStmt(instr)
        self._add_stmt(stmt)

    def visit_Global(self, node: ast.Global) -> None:
        self._encl_lexical_block().globals.update(node.names)
        instr = GlobalInstr(node.lineno, node.names)
        stmt = GlobalStmt(instr)
        self._add_stmt(stmt)

    def generic_visit(self, node: ast.AST) -> None:
        raise NotImplementedError(f"Unsupported node type: {type(node).__name__}")
