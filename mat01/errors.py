"""错误类型：编译错误与执行错误的区分。

``CompileError`` 在编译（词法/语法分析）阶段抛出；``EvaluationError``
及其子类在求值阶段抛出。两者都携带 ``Diagnostic``。宿主 API 误用
（非法函数名、非法变量值等）抛出普通的 ``ValueError`` / ``TypeError``，
不属于脚本错误。
"""

from __future__ import annotations

from .diagnostics import Diagnostic


class MatError(Exception):
    """所有脚本错误的基类，携带诊断对象。"""

    def __init__(self, diagnostic: Diagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(str(diagnostic))


class CompileError(MatError):
    """词法或语法错误，求值不会发生。"""


class EvaluationError(MatError):
    """求值阶段错误的基类。"""


class TypeMismatchError(EvaluationError):
    """运算符或函数收到类型不符的值。"""


class UnboundNameError(EvaluationError):
    """引用了未传入的变量或未注册的函数。"""


class ArityError(EvaluationError):
    """函数调用的参数数量不在注册时声明的范围内。"""


class HostFunctionError(EvaluationError):
    """宿主函数抛出异常；原异常通过 ``__cause__`` 保留。"""


class DivisionByZeroError(EvaluationError):
    """除法或取模的除数为零。"""
