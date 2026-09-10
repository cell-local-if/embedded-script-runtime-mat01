"""公共调用接口：编译源码、求值程序。

典型用法::

    import mat01

    env = mat01.Environment()
    env.register_function("double", lambda x: x * 2)
    program = mat01.compile_source("double(x) + 1")
    result = program.evaluate(env, variables={"x": 3})  # 7
"""

from __future__ import annotations

from collections.abc import Mapping

from . import interpreter, parser
from .environment import Environment
from .interpreter import Value, is_valid_value
from .lexer import KEYWORDS


class Program:
    """一次编译得到的表达式程序，可在不同环境与变量下重复求值。"""

    def __init__(self, source: str, source_name: str) -> None:
        self._source = source
        self._source_name = source_name
        self._root = parser.parse(source, source_name)

    @property
    def source(self) -> str:
        return self._source

    @property
    def source_name(self) -> str:
        return self._source_name

    def evaluate(
        self,
        environment: Environment | None = None,
        variables: Mapping[str, Value] | None = None,
    ) -> Value:
        """求值本程序。

        ``environment`` 提供已注册的宿主函数，缺省为空环境（任何函数
        调用都会报 UnboundNameError）。``variables`` 提供表达式可见的
        输入变量；键必须是合法标识符，值必须是 int（非 bool）、bool
        或 None，否则抛出 ValueError / TypeError（宿主调用错误）。
        """
        if environment is None:
            environment = Environment()
        checked = self._check_variables(variables)
        return interpreter.evaluate(
            self._root, environment, checked, self._source_name
        )

    @staticmethod
    def _check_variables(
        variables: Mapping[str, Value] | None,
    ) -> Mapping[str, Value]:
        if variables is None:
            return {}
        for key, value in variables.items():
            if (
                not isinstance(key, str)
                or not key.isidentifier()
                or key in KEYWORDS
            ):
                raise ValueError(
                    f"invalid variable name {key!r}: must be an identifier "
                    "and not a reserved keyword"
                )
            if not is_valid_value(value):
                raise TypeError(
                    f"invalid value for variable {key!r}: expected int, bool "
                    f"or None, got {type(value).__name__}"
                )
        return variables


def compile_source(source: str, source_name: str = "<expression>") -> Program:
    """编译一段表达式源码。词法/语法问题抛出 CompileError。"""
    if not isinstance(source, str):
        raise TypeError(f"source must be a str, got {type(source).__name__}")
    return Program(source, source_name)
