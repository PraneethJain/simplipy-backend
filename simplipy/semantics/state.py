from simplipy.parse.types import Instruction, Block, Program
from simplipy.parse.statement import IfStmt, DefStmt, WhileStmt, RetStmt

GLOBAL_ENV_ID = 0


class LexicalMap:
    def __init__(self) -> None:
        self.envs: dict[id, dict] = {GLOBAL_ENV_ID: {}}

    def create_new_env(self) -> int:
        new_env_id = max(self.envs.keys()) + 1
        self.envs[new_env_id] = {}
        return new_env_id


class ParentChain:
    def __init__(self) -> None:
        self.edges: set[tuple[int, int]] = set()

    def add_edge(self, child: int, parent: int) -> None:
        self.edges.add((child, parent))


class Context:
    def __init__(self, lineno: int, env_id: int) -> None:
        self.lineno = lineno
        self.env_id = env_id


class Continuation:
    def __init__(self, pgm: Program) -> None:
        self.stack: list[Context] = [(pgm.block.first(), GLOBAL_ENV_ID)]

    def top(self) -> Context:
        return self.stack[-1]

    def pop(self) -> Context:
        return self.stack.pop()

    def push(self, ctx: Context) -> None:
        self.stack.append(ctx)


class State:
    def __init__(self, pgm: Program) -> None:
        self.pgm = pgm

        self.e = LexicalMap()
        self.p = ParentChain()
        self.k = Continuation(pgm)

        self._instr_map: dict[int, Instruction] = {}
        self._populate_instr_map(pgm.block)

    def step(self) -> None:
        pass

    def _populate_instr_map(self, blk: Block):
        for stmt in blk:
            self._instr_map[stmt.first_instr().lineno] = stmt.first_instr()
            if isinstance(stmt, IfStmt):
                self._populate_instr_map(stmt.if_block)
                self._populate_instr_map(stmt.else_block)
            elif isinstance(stmt, WhileStmt):
                self._populate_instr_map(stmt.block)
            elif isinstance(stmt, DefStmt):
                self._populate_instr_map(stmt.block)
