from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterator


class Instruction(ABC):
    def __init__(self, lineno: int) -> None:
        self.lineno = lineno

    def set_parent(self, stmt: Statement) -> None:
        self.parent = stmt


class Statement(ABC):
    @abstractmethod
    def first(self) -> int:
        pass

    @abstractmethod
    def last(self) -> int:
        pass

    @abstractmethod
    def first_instr(self) -> Instruction:
        pass

    def set_idx(self, idx: int) -> None:
        self.idx = idx

    def set_parent(self, block: Block) -> None:
        self.parent = block


class Block:
    def __init__(self, stmts: list[Statement]) -> None:
        self.stmts = stmts

    def first(self) -> int:
        return self.stmts[0].first()

    def last(self) -> int:
        return self.stmts[-1].last()

    def _add_stmt(self, stmt: Statement) -> None:
        self.stmts.append(stmt)

    def set_parent(self, stmt: Statement) -> None:
        self.parent = stmt

    def __iter__(self) -> Iterator[Statement]:
        return iter(self.stmts)

    def __len__(self) -> int:
        return len(self.stmts)


class Program:
    def __init__(self, block: Block) -> None:
        self.block = block
