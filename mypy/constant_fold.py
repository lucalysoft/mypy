"""Constant folding of expressions.

For example, 3 + 5 can be constant folded into 8.
"""

from __future__ import annotations

from typing import Union
from typing_extensions import Final

from mypy.nodes import Expression, FloatExpr, IntExpr, NameExpr, OpExpr, StrExpr, UnaryExpr, Var

# All possible result types of constant folding
ConstantValue = Union[int, bool, float, str]
CONST_TYPES: Final = (int, bool, float, str)


def constant_fold_expr(expr: Expression, cur_mod_id: str) -> ConstantValue | None:
    """Return the constant value of an expression for supported operations.

    Among other things, support int arithmetic and string
    concatenation. For example, the expression 3 + 5 has the constant
    value 8.

    Also bind simple references to final constants defined in the
    current module (cur_mod_id). Binding to references is best effort
    -- we don't bind references to other modules. Mypyc trusts these
    to be correct in compiled modules, so that it can replace a
    constant expression (or a reference to one) with the statically
    computed value. We don't want to infer constant values based on
    stubs, in particular, as these might not match the implementation
    (due to version skew, for example).

    Return None if unsuccessful.
    """
    if isinstance(expr, IntExpr):
        return expr.value
    if isinstance(expr, StrExpr):
        return expr.value
    if isinstance(expr, FloatExpr):
        return expr.value
    elif isinstance(expr, NameExpr):
        if expr.name == "True":
            return True
        elif expr.name == "False":
            return False
        node = expr.node
        if (
            isinstance(node, Var)
            and node.is_final
            and node.fullname.rsplit(".", 1)[0] == cur_mod_id
        ):
            value = node.final_value
            if isinstance(value, (CONST_TYPES)):
                return value
    elif isinstance(expr, OpExpr):
        left = constant_fold_expr(expr.left, cur_mod_id)
        right = constant_fold_expr(expr.right, cur_mod_id)
        if isinstance(left, int) and isinstance(right, int):
            return constant_fold_binary_int_op(expr.op, left, right)
        elif isinstance(left, str) and isinstance(right, str):
            return constant_fold_binary_str_op(expr.op, left, right)
    elif isinstance(expr, UnaryExpr):
        value = constant_fold_expr(expr.expr, cur_mod_id)
        if isinstance(value, int):
            return constant_fold_unary_int_op(expr.op, value)
    return None


def constant_fold_binary_int_op(op: str, left: int, right: int) -> int | None:
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    elif op == "*":
        return left * right
    elif op == "//":
        if right != 0:
            return left // right
    elif op == "%":
        if right != 0:
            return left % right
    elif op == "&":
        return left & right
    elif op == "|":
        return left | right
    elif op == "^":
        return left ^ right
    elif op == "<<":
        if right >= 0:
            return left << right
    elif op == ">>":
        if right >= 0:
            return left >> right
    elif op == "**":
        if right >= 0:
            ret = left**right
            assert isinstance(ret, int)
            return ret
    return None


def constant_fold_unary_int_op(op: str, value: int) -> int | None:
    if op == "-":
        return -value
    elif op == "~":
        return ~value
    elif op == "+":
        return value
    return None


def constant_fold_binary_str_op(op: str, left: str, right: str) -> str | None:
    if op == "+":
        return left + right
    return None
