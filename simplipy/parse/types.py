from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterator
from collections.abc import Sequence


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

    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "idx": getattr(self, "idx", -1),
            "first_line": self.first(),
            "last_line": self.last(),
        }


class Block(Sequence):
    def __init__(self, stmts: list[Statement], lexical: bool = False) -> None:
        self.stmts = stmts
        self.lexical = lexical
        if lexical:
            self.locals: set[str] = set()
            self.nonlocals: set[str] = set()
            self.globals: set[str] = set()

    def first(self) -> int:
        return self[0].first()

    def last(self) -> int:
        return self[-1].last()

    def to_dict(self) -> dict:
        data = {
            "type": "Block",
            "first_line": self.first(),
            "last_line": self.last(),
            "statements": [stmt.to_dict() for stmt in self.stmts],
            "lexical": self.lexical,
        }

        if self.lexical:
            data["locals"] = sorted(list(getattr(self, "locals", set())))
            data["nonlocals"] = sorted(list(getattr(self, "nonlocals", set())))
            data["globals"] = sorted(list(getattr(self, "globals", set())))

        return data

    def _add_stmt(self, stmt: Statement) -> None:
        self.stmts.append(stmt)

    def set_parent(self, stmt: Statement) -> None:
        self.parent = stmt

    def __getitem__(self, i) -> Statement:
        return self.stmts[i]

    def __iter__(self) -> Iterator[Statement]:
        return iter(self.stmts)

    def __len__(self) -> int:
        return len(self.stmts)


class Program:
    def __init__(self, block: Block) -> None:
        self.block = block

    def to_dict(self) -> dict:
        return {"type": "Program", "block": self.block.to_dict()}
