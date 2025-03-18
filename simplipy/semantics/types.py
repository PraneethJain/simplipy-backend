class Bottom:
    def __repr__(self) -> str:
        return "⊥"


class Closure:
    def __init__(self, lineno: int, formals: list[str]) -> None:
        self.lineno = lineno
        self.formals = formals

    def __repr__(self) -> str:
        return f"({self.lineno}, {self.formals})"


class Context:
    def __init__(self, lineno: int, env_id: int) -> None:
        self.lineno = lineno
        self.env_id = env_id

    def __repr__(self) -> str:
        return f"({self.lineno},{self.env_id})"
