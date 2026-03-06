"""
tools/calculator.py
===================
Safe arithmetic evaluator.

Accepts a plain-text mathematical expression and returns the result
as a string.  Uses Python's ast module to avoid arbitrary code
execution – only numeric literals and safe operators are permitted.
"""

import ast
import logging
import operator

log = logging.getLogger(__name__)

# Whitelist of allowed AST node types
_ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div,
    ast.FloorDiv, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd,
)

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Non-numeric constant: {node.value!r}")
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op_fn = _OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_fn(left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op_fn = _OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_fn(operand)
    raise ValueError(f"Disallowed AST node: {type(node).__name__}")


def calculate(expression: str) -> str:
    """
    Evaluate a mathematical *expression* and return the result.

    Examples
    --------
    >>> calculate("2 + 2")
    '4'
    >>> calculate("(3 ** 2) / 4.5")
    '2.0'
    """
    expr = expression.strip()
    log.info("Calculator input: %s", expr)
    try:
        tree = ast.parse(expr, mode="eval")
        # Validate all nodes are in the whitelist
        for node in ast.walk(tree):
            if not isinstance(node, _ALLOWED_NODES):
                raise ValueError(f"Disallowed node type: {type(node).__name__}")
        result = _eval_node(tree.body)
        # Return int if result is a whole number
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(round(result, 10))
    except ZeroDivisionError:
        return "Error: division by zero"
    except Exception as exc:
        log.warning("Calculator error for %r: %s", expr, exc)
        return f"Error: {exc}"
