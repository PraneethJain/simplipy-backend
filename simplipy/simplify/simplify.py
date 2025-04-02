import ast
import black


class UnsupportedConstructError(ValueError):
    """Custom error for Python constructs not supported by the simplifier."""

    def __init__(self, node: ast.AST, message: str = "Unsupported construct"):
        self.node = node
        self.message = (
            f"{message}: {type(node).__name__} at line {getattr(node, 'lineno', '?')}"
        )
        super().__init__(self.message)


class ExpressionTransformer(ast.NodeTransformer):
    """
    Transforms expressions containing function calls.

    Extracts function calls into preceding assignment statements
    and replaces the call site with a temporary variable.
    """

    def __init__(self):
        super().__init__()
        self.temp_var_count = 0
        self.preceding_assignments: list[ast.Assign] = []

    def _generate_temp_var(self) -> str:
        name = f"_simplipy_temp_{self.temp_var_count}"
        self.temp_var_count += 1
        return name

    def visit_Call(self, node: ast.Call) -> ast.Name:
        # Recursively transform arguments first, as they might contain calls
        node.args = [self.visit(arg) for arg in node.args]
        # Keyword arguments are not supported in simplipy CallAssignInstr
        if node.keywords:
            raise UnsupportedConstructError(
                node, "Keyword arguments in calls not supported"
            )

        # Generate a temporary variable name
        temp_name = self._generate_temp_var()

        # Create the assignment statement: _simplipy_temp_N = original_call(...)
        assign_node = ast.Assign(
            targets=[ast.Name(id=temp_name, ctx=ast.Store())],
            value=node,  # The original call node (with potentially transformed args)
            lineno=node.lineno,
            col_offset=node.col_offset,
        )
        # Store this assignment to be inserted *before* the statement using the expression
        self.preceding_assignments.append(assign_node)

        # Return a Name node representing the temporary variable
        return ast.Name(
            id=temp_name, ctx=ast.Load(), lineno=node.lineno, col_offset=node.col_offset
        )


class SimplipyConverter(ast.NodeTransformer):
    """
    Transforms a Python AST into the subset supported by SimpliPy.
    """

    def __init__(self):
        super().__init__()
        # Track temp variables globally for simplicity, assuming no complex scoping issues
        # for temps across functions after transformation. A more robust implementation
        # might manage scope.
        self.global_temp_var_count = 0

    def _generate_temp_var(self) -> str:
        name = f"_simplipy_temp_{self.global_temp_var_count}"
        self.global_temp_var_count += 1
        return name

    def _transform_expression(
        self, node: ast.expr
    ) -> tuple[ast.expr, list[ast.Assign]]:
        """Transforms an expression node, extracting calls."""
        transformer = ExpressionTransformer()
        # Share the global temp counter logic if needed, or keep it separate
        # transformer.temp_var_count = self.global_temp_var_count # Example sharing
        new_expr = transformer.visit(node)
        # self.global_temp_var_count = transformer.temp_var_count # Update global counter
        return new_expr, transformer.preceding_assignments

    def visit_Assign(self, node: ast.Assign) -> list[ast.stmt]:
        """
        Handles assignments. Extracts calls from the right-hand side expression
        if it's not a direct Call node (which SimpliPy handles).
        Checks for unsupported assignment targets.
        """
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            raise UnsupportedConstructError(
                node, "Assignment target must be a single variable name"
            )

        # SimpliPy handles direct calls like `x = func()` via CallAssignInstr.
        # We only need to transform calls *within* more complex expressions.
        if isinstance(node.value, ast.Call):
            # Check arguments within the call for nested calls
            new_args = []
            preceding_assignments = []
            for arg in node.value.args:
                new_arg, assignments = self._transform_expression(arg)
                preceding_assignments.extend(assignments)
                new_args.append(new_arg)

            if node.value.keywords:
                raise UnsupportedConstructError(
                    node.value, "Keyword arguments not supported"
                )

            # Rebuild the call node with transformed args
            new_call = ast.Call(
                func=node.value.func,  # Assume func is simple Name for SimpliPy
                args=new_args,
                keywords=[],
                lineno=node.value.lineno,
                col_offset=node.value.col_offset,
            )
            ast.copy_location(new_call, node.value)

            # Create the final assignment using the (potentially) modified call
            final_assign = ast.Assign(
                targets=node.targets,
                value=new_call,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
            ast.copy_location(final_assign, node)

            # Return preceding assignments + the final assignment
            return preceding_assignments + [final_assign]
        else:
            # Transform the expression on the right-hand side
            new_value, preceding_assignments = self._transform_expression(node.value)

            # Create the potentially modified assignment statement
            final_assign = ast.Assign(
                targets=node.targets,
                value=new_value,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
            ast.copy_location(final_assign, node)

            # Return the preceding assignments followed by the final assignment
            return preceding_assignments + [final_assign]

    def visit_Expr(self, node: ast.Expr) -> list[ast.stmt]:
        """
        Handles expressions used as statements (e.g., just calling a function).
        Transforms the expression, potentially creating temp assignments.
        Note: SimpliPy doesn't directly support expression statements other than Pass.
              A standalone call `func()` needs to be `_ = func()` in SimpliPy.
              Let's transform `func()` into `_simplipy_temp_N = func()`.
        """
        if isinstance(node.value, ast.Call):
            # This is like an assignment `_ = func()`, transform it
            # Transform arguments first
            new_args = []
            preceding_assignments = []
            for arg in node.value.args:
                new_arg, assignments = self._transform_expression(arg)
                preceding_assignments.extend(assignments)
                new_args.append(new_arg)

            if node.value.keywords:
                raise UnsupportedConstructError(
                    node.value, "Keyword arguments not supported"
                )

            # Rebuild the call node
            new_call = ast.Call(
                func=node.value.func,
                args=new_args,
                keywords=[],
                lineno=node.value.lineno,
                col_offset=node.value.col_offset,
            )
            ast.copy_location(new_call, node.value)

            # Assign the result to a temporary variable
            temp_name = self._generate_temp_var()
            assign_node = ast.Assign(
                targets=[ast.Name(id=temp_name, ctx=ast.Store())],
                value=new_call,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
            ast.copy_location(assign_node, node)
            return preceding_assignments + [assign_node]
        else:
            # Other expression statements (like bare constants) are often useless
            # or invalid Python anyway. SimpliPy parser likely ignores them or
            # errors. We can perhaps convert them to Pass or error.
            # Let's convert to Pass for simplicity.
            pass_node = ast.Pass(lineno=node.lineno, col_offset=node.col_offset)
            ast.copy_location(pass_node, node)
            return [pass_node]  # Return as a list for consistency

    def visit_If(self, node: ast.If) -> ast.If | list[ast.stmt]:
        """
        Ensures 'else' block exists. Transforms test expression.
        Recursively visits bodies.
        """
        new_test, preceding_assignments = self._transform_expression(node.test)
        node.test = new_test

        # Recursively visit the body and orelse, handling list returns from visits
        node.body = self.visit_statements(node.body)
        if node.orelse:
            node.orelse = self.visit_statements(node.orelse)
        else:
            # Add 'else: pass' if no else block exists
            node.orelse = [
                ast.Pass(lineno=node.lineno, col_offset=node.col_offset)
            ]  # Estimate location
            ast.fix_missing_locations(node.orelse[0])

        ast.copy_location(node, node)  # Ensure node itself has location
        return preceding_assignments + [node]

    def visit_While(self, node: ast.While) -> ast.While | list[ast.stmt]:
        """
        Transforms test expression. Ensures loop body ends with 'continue'.
        Recursively visits body. Forbids 'else' on while.
        """
        if node.orelse:
            raise UnsupportedConstructError(
                node, "While loop 'else' clause not supported"
            )

        new_test, preceding_assignments = self._transform_expression(node.test)
        node.test = new_test

        # Recursively visit the body
        node.body = self.visit_statements(node.body)

        # Add 'continue' if not already the last statement
        if not node.body or not isinstance(node.body[-1], ast.Continue):
            continue_node = ast.Continue(
                lineno=node.lineno, col_offset=node.col_offset
            )  # Estimate location
            ast.fix_missing_locations(continue_node)
            node.body.append(continue_node)

        ast.copy_location(node, node)
        return preceding_assignments + [node]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Ensures function body ends with 'return'.
        Recursively visits body. Checks for unsupported features.
        """
        # Check for unsupported function features
        if (
            node.args.defaults
            or node.args.kwonlyargs
            or node.args.kw_defaults
            or node.args.posonlyargs
            or node.args.vararg
            or node.args.kwarg
        ):
            raise UnsupportedConstructError(
                node,
                "Function signature features like defaults, *args, **kwargs not supported",
            )
        if node.decorator_list:
            raise UnsupportedConstructError(node, "Function decorators not supported")
        if isinstance(node, ast.AsyncFunctionDef):
            raise UnsupportedConstructError(
                node, "Async functions (async def) not supported"
            )

        # Recursively visit the body
        node.body = self.visit_statements(node.body)

        # Add 'return None' if not present
        if not node.body or not isinstance(node.body[-1], ast.Return):
            return_node = ast.Return(
                value=ast.Constant(value=None),
                lineno=node.lineno,
                col_offset=node.col_offset,
            )  # Estimate location
            ast.fix_missing_locations(return_node)
            node.body.append(return_node)

        ast.copy_location(node, node)
        return node  # Return single node, not list

    def visit_Return(self, node: ast.Return) -> ast.Return | list[ast.stmt]:
        """Transforms the return expression."""
        if node.value:
            new_value, preceding_assignments = self._transform_expression(node.value)
            node.value = new_value
            ast.copy_location(node, node)
            return preceding_assignments + [node]
        else:
            # SimpliPy requires Return to have a value, convert `return` to `return None`
            node.value = ast.Constant(value=None)
            ast.fix_missing_locations(node)
            return [node]  # Return as list

    def visit_statements(self, stmts: list[ast.stmt]) -> list[ast.stmt]:
        """Helper to visit a list of statements and flatten the results."""
        new_stmts = []
        for stmt in stmts:
            result = self.visit(stmt)
            if isinstance(result, list):
                new_stmts.extend(result)
            elif isinstance(result, ast.AST):  # Should be ast.stmt, but check AST
                new_stmts.append(result)
            # Can ignore None results if visit methods might return None
        return new_stmts

    def visit(self, node):
        """Override visit to handle statement lists returned by children."""
        # Handle specific list-returning visits first
        if isinstance(node, (ast.Assign, ast.Expr, ast.If, ast.While, ast.Return)):
            method = "visit_" + node.__class__.__name__
            visitor = getattr(self, method, self.generic_visit)
            # These visitors return lists or single nodes that become lists
            result = visitor(node)
            # Ensure fix_missing_locations runs on newly created nodes within the list
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, ast.AST):
                        ast.fix_missing_locations(item)
            elif isinstance(result, ast.AST):
                ast.fix_missing_locations(result)

            return result

        # For nodes that manage bodies (Module, FunctionDef), handle recursion manually
        elif isinstance(
            node, (ast.Module, ast.FunctionDef)
        ):  # Add ClassDef etc. if needed
            # Let the specific visitor handle body recursion via visit_statements
            method = "visit_" + node.__class__.__name__
            visitor = getattr(self, method, self.generic_visit)
            new_node = visitor(node)
            if isinstance(new_node, ast.AST):
                ast.fix_missing_locations(new_node)
            return new_node
        else:
            # Default behavior for other nodes (like Pass, Break, Continue, Name, Constant etc.)
            new_node = super().visit(node)
            if isinstance(new_node, ast.AST):
                ast.fix_missing_locations(new_node)
            return new_node

    # --- Generic Visit and Unsupported Nodes ---

    def generic_visit(self, node: ast.AST):
        """
        Called if no explicit visitor method exists.
        Raise error for explicitly unsupported constructs.
        Otherwise, continue traversal.
        """
        unsupported_types = (
            ast.For,
            ast.AsyncFor,
            ast.With,
            ast.AsyncWith,
            ast.Raise,
            ast.Try,
            ast.Assert,
            ast.Import,
            ast.ImportFrom,
            ast.ClassDef,
            ast.Delete,
            ast.AugAssign,
            ast.AnnAssign,
            ast.FormattedValue,
            ast.JoinedStr,  # f-strings
            ast.ListComp,
            ast.SetComp,
            ast.DictComp,
            ast.GeneratorExp,
            ast.Await,
            ast.Yield,
            ast.YieldFrom,
            ast.Starred,  # e.g., *args in calls or assignments
            ast.Lambda,
        )
        # Also check for tuple/list/subscript targets in assignment covered in visit_Assign

        if isinstance(node, unsupported_types):
            raise UnsupportedConstructError(node)

        # If not explicitly unsupported, continue descent
        return super().generic_visit(node)

    def transform(self, code: str) -> str:
        """Parse, transform, and unparse the code."""
        try:
            tree = ast.parse(code)
            # Perform transformations. Need to handle the top-level list of statements.
            new_body = self.visit_statements(tree.body)
            tree.body = new_body
            # Fix locations for the whole modified tree
            ast.fix_missing_locations(tree)
            simplified_code = ast.unparse(tree)

            try:
                formatted_code = black.format_str(
                    simplified_code, mode=black.FileMode()
                )
                return formatted_code
            except Exception as format_error:
                print(format_error)
                return simplified_code
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}") from e


def simplify_python_code(code: str) -> str:
    """
    Takes a string containing Python code and attempts to simplify it
    to the subset supported by SimpliPy.

    Args:
        code: The Python code string.

    Returns:
        The simplified Python code string.

    Raises:
        ValueError: If the code contains syntax errors or unsupported constructs
                    that cannot be automatically simplified.
    """
    converter = SimplipyConverter()
    try:
        simplified_code = converter.transform(code)
        return simplified_code
    except UnsupportedConstructError as e:
        # Re-raise as ValueError for the API to catch nicely
        raise ValueError(f"Simplification failed: {e}") from e
    except Exception as e:
        raise ValueError(f"An unexpected error occurred: {e}") from e


# --- Example Usage ---
if __name__ == "__main__":
    test_code_simple = """
x = 1
y = x + 2
if y > 2:
    z = y * 3
else:
    z = 0
pass
    """

    test_code_calls = """
def greet(name):
    print("Hello", name) # print is often a builtin, needs handling if simplipy requires user-def funcs

def add(a, b):
    res = a + b
    return res

x = add(1, 2)
y = add(x, add(3, 4)) + 5
# greet("World") # Standalone call

if y > 10:
    z = y - 1
# Missing else

while x < 5:
    x = add(x, 1)
    if x == 3:
        break
    # Missing continue

def factorial(n):
    if n <= 1:
        return 1
    else:
        # Recursive call inside expression
        return n * factorial(n-1)
    # Missing return at end of definition (implicitly None)

result = factorial(3)
# print(result)
"""
    # Note: print() needs special handling or needs to be defined if not builtin in simplipy
    # Assuming print is not available, we comment it out for now.

    print("--- Original Code ---")
    print(test_code_calls)
    print("\n--- Simplified Code ---")
    try:
        simplified = simplify_python_code(test_code_calls)
        print(simplified)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Code with unsupported feature ---")
    test_code_unsupported = """
for i in range(5):
    print(i)
    """
    print(test_code_unsupported)
    try:
        simplify_python_code(test_code_unsupported)
    except ValueError as e:
        print(f"Error: {e}")
