import ast


class Expression:
    def __init__(self, node: ast.expr) -> None:
        self.node = node
        self._validate()

    def _validate(self) -> None:
        for n in ast.walk(self.node):
            if isinstance(n, ast.Call):
                raise AssertionError("Function calls are not allowed in expressions")
