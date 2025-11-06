from simplipy.parse.types import Instruction, Block, Program
from simplipy.parse.statement import IfStmt, DefStmt, WhileStmt
from simplipy.parse.instruction import (
    IfInstr,
    DefInstr,
    RetInstr,
    PassInstr,
    BreakInstr,
    WhileInstr,
    GlobalInstr,
    ContinueInstr,
    NonlocalInstr,
    CallAssignInstr,
    ExprAssignInstr,
)
from simplipy.ctf.ctf import get_ctfs
from simplipy.semantics.types import Bottom, Closure, Context
import ast

GLOBAL_ENV_ID = 0


class LexicalMap:
    def __init__(self) -> None:
        self.envs: dict[int, dict] = {GLOBAL_ENV_ID: {}}

    def create_new_env(self) -> int:
        new_env_id = max(self.envs.keys()) + 1
        self.envs[new_env_id] = {}
        return new_env_id

    def as_dict(self) -> dict:
        res = {}
        for env_id, env in self.envs.items():
            res[env_id] = {}
            for k, v in env.items():
                if isinstance(v, Closure):
                    res[env_id][k] = {
                        "lineno": v.lineno,
                        "formals": v.formals,
                        "par_env_id": v.par_env_id,
                    }
                elif isinstance(v, Bottom):
                    res[env_id][k] = "💀"
                else:
                    res[env_id][k] = v
        return res

    def __str__(self) -> str:
        return str(self.envs)


class ParentChain:
    def __init__(self) -> None:
        self.edges: dict[int, int] = {}

    def add_edge(self, child: int, parent: int) -> None:
        self.edges[child] = parent


class Continuation:
    def __init__(self, pgm: Program) -> None:
        self.stack: list[Context] = [Context(pgm.block.first(), GLOBAL_ENV_ID)]

    def as_dict(self) -> list:
        return [{"lineno": ctx.lineno, "env_id": ctx.env_id} for ctx in self.stack]

    def top(self) -> Context:
        return self.stack[-1]

    def pop(self) -> Context:
        return self.stack.pop()

    def push(self, ctx: Context) -> None:
        self.stack.append(ctx)

    def __str__(self) -> str:
        return str(self.stack)


class State:
    def __init__(self, pgm: Program) -> None:
        self.pgm = pgm
        self.ctfs = get_ctfs(pgm)

        self.e = LexicalMap()
        self.p = ParentChain()
        self.k = Continuation(pgm)

        self.instr_map: dict[int, Instruction] = {}
        self._populate_instr_map(pgm.block)
        self.last_ctf_used: str | None = None

    def is_final(self) -> bool:
        lineno = self.k.top().lineno
        return lineno in self.ctfs["next"] and self.ctfs["next"][lineno] == lineno

    def as_dict(self) -> dict:
        return {
            "e": self.e.as_dict(),
            "p": self.p.edges,
            "k": self.k.as_dict(),
            "ctfs": self.ctfs,
        }

    def step(self) -> None:
        instr = self.instr_map[self.k.top().lineno]

        ctf_to_use = None

        if isinstance(
            instr, (PassInstr, BreakInstr, ContinueInstr, GlobalInstr, NonlocalInstr)
        ):
            ctf_to_use = "next"
        elif isinstance(instr, ExprAssignInstr):
            env = self.lookup_env(instr.var)
            val = self.eval_expr(instr.expr.node)
            env[instr.var] = val
            ctf_to_use = "next"
        elif isinstance(instr, (IfInstr, WhileInstr)):
            if self.eval_expr(instr.expr.node):
                ctf_to_use = "true"
            else:
                ctf_to_use = "false"
        elif isinstance(instr, DefInstr):
            func_stmt: DefStmt = instr.parent
            closure = Closure(
                func_stmt.block.first(), instr.formals, self.k.top().env_id
            )
            env = self.lookup_env(instr.func_var)
            env[instr.func_var] = closure
            ctf_to_use = "next"
        elif isinstance(instr, CallAssignInstr):
            closure = self.lookup_val(instr.func_var)
            if not isinstance(closure, Closure):
                raise ValueError(f"Variable {instr.func_var} is not callable")
            if len(instr.func_args) != len(closure.formals):
                raise TypeError(
                    f"{instr.func_var}() takes {len(closure.formals)} argument(s) but {len(instr.func_args)} were given`"
                )

            env_id = self.e.create_new_env()
            env = self.e.envs[env_id]
            for var, val in zip(
                closure.formals,
                map(self.eval_expr, [expr.node for expr in instr.func_args]),
            ):
                env[var] = val
            blk = self.instr_map[closure.lineno].parent.parent
            blk_locals = blk.locals - blk.nonlocals - blk.globals
            for var in blk_locals:
                env[var] = Bottom()

            self.p.add_edge(env_id, closure.par_env_id)
            self.k.push(Context(closure.lineno, env_id))

        elif isinstance(instr, RetInstr):
            val = self.eval_expr(instr.expr.node)
            self.k.pop()
            call_instr: CallAssignInstr = self.instr_map[self.k.top().lineno]
            env = self.lookup_env(call_instr.var)
            env[call_instr.var] = val
            self.k.top().lineno = self.ctfs["next"][self.k.top().lineno]
        else:
            NotImplementedError(f"Unsupported instruction type: {type(instr).__name__}")

        if ctf_to_use is not None:
            self.k.top().lineno = self.ctfs[ctf_to_use][self.k.top().lineno]
            self.last_ctf_used = ctf_to_use

    def get_parent_chain(self) -> list[int]:
        current = self.k.top().env_id
        result = [current]

        while current in self.p.edges:
            parent = self.p.edges[current]
            result.append(parent)
            current = parent

        return result

    def lookup_env(self, var: str) -> dict:
        blk = self.instr_map[self.k.top().lineno].parent.parent
        while not blk.lexical:
            blk = blk.parent.parent

        envs = [self.e.envs[env_id] for env_id in self.get_parent_chain()]

        if var in blk.globals and var in blk.nonlocals:
            raise ValueError(f"Variable {var} cannot be both nonlocal and global")
        elif blk.parent is None or var in blk.globals:
            return self.e.envs[GLOBAL_ENV_ID]
        elif var in blk.nonlocals:
            for env in envs[1:-1]:
                if var in env:
                    return env
        else:
            for env in envs:
                if var in env:
                    return env

        raise LookupError(f"Failed to lookup {var}")

    def lookup_val(self, var: str):
        return self.lookup_env(var)[var]

    def eval_expr(self, expr: ast.expr):
        if isinstance(expr, ast.Constant):
            return expr.value
        elif isinstance(expr, ast.Name):
            return self.lookup_val(expr.id)
        elif isinstance(expr, ast.UnaryOp):
            val = self.eval_expr(expr.operand)
            if isinstance(expr.op, ast.USub):
                return -val
            elif isinstance(expr.op, ast.UAdd):
                return +val
            elif isinstance(expr.op, ast.Not):
                return not val
            elif isinstance(expr.op, ast.Invert):
                return ~val
            else:
                raise ValueError(
                    f"Unsupported unary operator: {type(expr.op).__name__}"
                )
        elif isinstance(expr, ast.BinOp):
            left = self.eval_expr(expr.left)
            right = self.eval_expr(expr.right)
            if isinstance(expr.op, ast.Add):
                return left + right
            elif isinstance(expr.op, ast.Sub):
                return left - right
            elif isinstance(expr.op, ast.Mult):
                return left * right
            elif isinstance(expr.op, ast.Div):
                return left / right
            elif isinstance(expr.op, ast.FloorDiv):
                return left // right
            elif isinstance(expr.op, ast.Mod):
                return left % right
            elif isinstance(expr.op, ast.Pow):
                return left**right
            elif isinstance(expr.op, ast.LShift):
                return left << right
            elif isinstance(expr.op, ast.RShift):
                return left >> right
            elif isinstance(expr.op, ast.BitOr):
                return left | right
            elif isinstance(expr.op, ast.BitXor):
                return left ^ right
            elif isinstance(expr.op, ast.BitAnd):
                return left & right
            elif isinstance(expr.op, ast.MatMult):
                return left @ right
            else:
                raise ValueError(
                    f"Unsupported binary operator: {type(expr.op).__name__}"
                )
        elif isinstance(expr, ast.Compare):
            left = self.eval_expr(expr.left)
            for op, comparator in zip(expr.ops, expr.comparators):
                right = self.eval_expr(comparator)
                if isinstance(op, ast.Eq):
                    result = left == right
                elif isinstance(op, ast.NotEq):
                    result = left != right
                elif isinstance(op, ast.Lt):
                    result = left < right
                elif isinstance(op, ast.LtE):
                    result = left <= right
                elif isinstance(op, ast.Gt):
                    result = left > right
                elif isinstance(op, ast.GtE):
                    result = left >= right
                elif isinstance(op, ast.Is):
                    result = left is right
                elif isinstance(op, ast.IsNot):
                    result = left is not right
                elif isinstance(op, ast.In):
                    result = left in right
                elif isinstance(op, ast.NotIn):
                    result = left not in right
                else:
                    raise ValueError(
                        f"Unsupported comparison operator: {type(op).__name__}"
                    )
                if not result:
                    return False
                left = right
            return True
        else:
            raise TypeError(f"Unsupported expression type: {type(expr).__name__}")

    def _populate_instr_map(self, blk: Block):
        for stmt in blk:
            self.instr_map[stmt.first_instr().lineno] = stmt.first_instr()
            if isinstance(stmt, IfStmt):
                self._populate_instr_map(stmt.if_block)
                self._populate_instr_map(stmt.else_block)
            elif isinstance(stmt, WhileStmt):
                self._populate_instr_map(stmt.block)
            elif isinstance(stmt, DefStmt):
                self._populate_instr_map(stmt.block)
