"""求值器：对抽象语法树做树遍历求值。

求值顺序、类型规则与错误分类见 docs/expression-language-v1.md。
值在 Python 侧的表示：int（严格 int，bool 不算）、bool、None。
"""

from __future__ import annotations

from collections.abc import Mapping

from .diagnostics import Diagnostic, SourcePosition
from .environment import Environment
from .errors import (
    ArityError,
    DivisionByZeroError,
    EvaluationError,
    HostFunctionError,
    TypeMismatchError,
    UnboundNameError,
)
from . import nodes

Value = int | bool | None

_ARITHMETIC = ("+", "-", "*", "/", "%")
_ORDERING = ("<", "<=", ">", ">=")


def type_name(value: Value) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "bool"
    return "int"


def is_valid_value(value: object) -> bool:
    """判断一个 Python 值是否属于本语言的值类型。"""
    return value is None or type(value) is bool or type(value) is int


class _Evaluator:
    def __init__(
        self,
        environment: Environment,
        variables: Mapping[str, Value],
        source_name: str,
    ) -> None:
        self._environment = environment
        self._variables = variables
        self._source_name = source_name

    def evaluate(self, node: nodes.Node) -> Value:
        if isinstance(node, nodes.IntLiteral):
            return node.value
        if isinstance(node, nodes.BoolLiteral):
            return node.value
        if isinstance(node, nodes.NullLiteral):
            return None
        if isinstance(node, nodes.Name):
            return self._eval_name(node)
        if isinstance(node, nodes.UnaryOp):
            return self._eval_unary(node)
        if isinstance(node, nodes.BinaryOp):
            return self._eval_binary(node)
        if isinstance(node, nodes.LogicalOp):
            return self._eval_logical(node)
        if isinstance(node, nodes.Call):
            return self._eval_call(node)
        raise AssertionError(f"unknown node: {node!r}")  # pragma: no cover

    def _eval_name(self, node: nodes.Name) -> Value:
        if node.name in self._variables:
            return self._variables[node.name]
        self._fail(
            UnboundNameError,
            f"name {node.name!r} is not bound: pass it via evaluate(variables=...)",
            node.position,
        )

    def _eval_unary(self, node: nodes.UnaryOp) -> Value:
        operand = self.evaluate(node.operand)
        if node.op == "-":
            self._require_int(operand, "unary '-'", node.position)
            return -operand
        # "not"
        if type(operand) is not bool:
            self._fail(
                TypeMismatchError,
                f"operator 'not' requires a bool operand, got {type_name(operand)}",
                node.position,
            )
        return not operand

    def _eval_binary(self, node: nodes.BinaryOp) -> Value:
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        op = node.op
        if op in _ARITHMETIC:
            self._require_int(left, f"operator '{op}'", node.position)
            self._require_int(right, f"operator '{op}'", node.position)
            return self._apply_arithmetic(op, left, right, node.position)
        if op in _ORDERING:
            self._require_int(left, f"operator '{op}'", node.position)
            self._require_int(right, f"operator '{op}'", node.position)
            return self._apply_ordering(op, left, right)
        # == / !=：任意类型；类型不同则不相等
        equal = type(left) is type(right) and left == right
        return equal if op == "==" else not equal

    def _eval_logical(self, node: nodes.LogicalOp) -> Value:
        left = self.evaluate(node.left)
        self._require_bool(left, f"operator '{node.op}'", node.position)
        # 短路：左侧已决定结果时右侧不求值，其中的函数调用不会执行。
        if node.op == "and":
            if not left:
                return False
            right = self.evaluate(node.right)
            self._require_bool(right, "operator 'and'", node.position)
            return right
        if left:
            return True
        right = self.evaluate(node.right)
        self._require_bool(right, "operator 'or'", node.position)
        return right

    def _eval_call(self, node: nodes.Call) -> Value:
        function = self._environment.get_function(node.name)
        if function is None:
            self._fail(
                UnboundNameError,
                f"function {node.name!r} is not registered in the environment",
                node.position,
            )
        if not function.accepts(len(node.args)):
            self._fail(
                ArityError,
                f"function {node.name!r} expects {function.describe_arity()} "
                f"argument(s), got {len(node.args)}",
                node.position,
            )
        args = [self.evaluate(arg) for arg in node.args]
        try:
            result = function.func(*args)
        except Exception as exc:
            error = HostFunctionError(
                Diagnostic(
                    f"host function {node.name!r} raised {type(exc).__name__}: {exc}",
                    node.position,
                    self._source_name,
                )
            )
            raise error from exc
        if not is_valid_value(result):
            self._fail(
                TypeMismatchError,
                f"host function {node.name!r} returned unsupported type "
                f"{type(result).__name__}; expected int, bool or None",
                node.position,
            )
        return result

    # ---- 类型检查与运算 ----

    def _require_int(self, value: Value, what: str, position: SourcePosition) -> None:
        if type(value) is not int:
            self._fail(
                TypeMismatchError,
                f"{what} requires int operands, got {type_name(value)}",
                position,
            )

    def _require_bool(self, value: Value, what: str, position: SourcePosition) -> None:
        if type(value) is not bool:
            self._fail(
                TypeMismatchError,
                f"{what} requires bool operands, got {type_name(value)}",
                position,
            )

    def _apply_arithmetic(
        self, op: str, left: int, right: int, position: SourcePosition
    ) -> int:
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if right == 0:
            self._fail(
                DivisionByZeroError,
                f"division by zero in operator '{op}'",
                position,
            )
        if op == "/":
            return left // right  # 向下取整除法
        return left % right

    @staticmethod
    def _apply_ordering(op: str, left: int, right: int) -> bool:
        if op == "<":
            return left < right
        if op == "<=":
            return left <= right
        if op == ">":
            return left > right
        return left >= right

    def _fail(
        self,
        error_type: type[EvaluationError],
        message: str,
        position: SourcePosition,
    ) -> None:
        raise error_type(Diagnostic(message, position, self._source_name))


def evaluate(
    node: nodes.Node,
    environment: Environment,
    variables: Mapping[str, Value],
    source_name: str = "<expression>",
) -> Value:
    """在给定环境与变量下求值一个表达式节点。"""
    return _Evaluator(environment, variables, source_name).evaluate(node)
