"""mat01：可嵌入宿主应用的有限表达式语言内核。

本版本只支持表达式：整数、布尔、空值、括号、一元运算、基本二元
算术/比较/相等运算、and/or/not 短路逻辑、显式输入变量，以及宿主
显式注册后才能调用的函数。完整语义契约见
docs/expression-language-v1.md。

公共接口：

- ``compile_source(source, source_name=...)``：编译源码为 ``Program``。
- ``Program.evaluate(environment=None, variables=None)``：求值并返回结果。
- ``Environment``：宿主函数注册表（``register_function``）。
- 错误：``CompileError``（编译期）、``EvaluationError`` 及其子类
  （执行期），均携带 ``Diagnostic`` 诊断对象（含行列与偏移）。
"""

from .api import Program, compile_source
from .diagnostics import Diagnostic, SourcePosition
from .environment import Environment, HostFunction
from .errors import (
    ArityError,
    CompileError,
    DivisionByZeroError,
    EvaluationError,
    HostFunctionError,
    MatError,
    TypeMismatchError,
    UnboundNameError,
)

__version__ = "0.1.0"

__all__ = [
    "ArityError",
    "CompileError",
    "Diagnostic",
    "DivisionByZeroError",
    "Environment",
    "EvaluationError",
    "HostFunction",
    "HostFunctionError",
    "MatError",
    "Program",
    "SourcePosition",
    "TypeMismatchError",
    "UnboundNameError",
    "compile_source",
]
