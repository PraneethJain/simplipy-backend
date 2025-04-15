class Bottom:
    def __repr__(self) -> str:
        return "⊥"


class Closure:
    def __init__(self, lineno: int, formals: list[str], par_env_id: int) -> None:
        self.lineno = lineno
        self.formals = formals
        self.par_env_id = par_env_id

    def __repr__(self) -> str:
        return f"({self.lineno}, {self.formals}, {self.par_env_id})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Closure):
            return NotImplemented
        return (
            self.lineno == other.lineno
            and self.formals == other.formals
            and self.par_env_id == other.par_env_id
        )


class Context:
    def __init__(self, lineno: int, env_id: int) -> None:
        self.lineno = lineno
        self.env_id = env_id

    def __repr__(self) -> str:
        return f"({self.lineno},{self.env_id})"
