"""求值环境：宿主显式注册函数的容器。

语言没有内置函数和隐式环境；表达式能调用的函数全部来自宿主的
显式注册。注册接口本身的误用（非法名称、不可调用对象、无法推断
的参数个数）抛出 ValueError / TypeError，属于宿主调用错误。
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass

from .lexer import KEYWORDS


@dataclass(frozen=True)
class HostFunction:
    """一个已注册的宿主函数及其参数个数约束（min_arity, max_arity）。"""

    name: str
    func: Callable
    min_arity: int
    max_arity: int  # 本版本不支持可变参数，min == max 或由 (min, max) 指定

    def accepts(self, count: int) -> bool:
        return self.min_arity <= count <= self.max_arity

    def describe_arity(self) -> str:
        if self.min_arity == self.max_arity:
            return str(self.min_arity)
        return f"{self.min_arity}..{self.max_arity}"


def _is_valid_name(name: str) -> bool:
    return name.isidentifier() and name not in KEYWORDS


def _infer_arity(name: str, func: Callable) -> tuple[int, int]:
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        raise ValueError(
            f"cannot infer arity of {name!r}; pass arity= explicitly"
        ) from None
    minimum = 0
    maximum = 0
    for parameter in signature.parameters.values():
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            raise ValueError(
                f"cannot infer arity of {name!r}: variadic parameters are not "
                "supported; pass arity= explicitly"
            )
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY:
            if parameter.default is inspect.Parameter.empty:
                raise ValueError(
                    f"cannot infer arity of {name!r}: required keyword-only "
                    "parameters cannot be bound from an expression call"
                )
            continue
        maximum += 1
        if parameter.default is inspect.Parameter.empty:
            minimum += 1
    return minimum, maximum


class Environment:
    """宿主函数注册表。变量不属于环境，在每次求值时传入。"""

    def __init__(self) -> None:
        self._functions: dict[str, HostFunction] = {}

    def register_function(
        self,
        name: str,
        func: Callable,
        arity: int | tuple[int, int] | None = None,
    ) -> None:
        """注册一个宿主函数。

        ``arity`` 为整数（精确个数）或 ``(min, max)`` 元组；省略时从
        函数签名推断。重复注册同名函数会覆盖旧定义。
        """
        if not isinstance(name, str) or not _is_valid_name(name):
            raise ValueError(
                f"invalid function name {name!r}: must be an identifier and "
                "not a reserved keyword"
            )
        if not callable(func):
            raise TypeError(f"registered object for {name!r} is not callable")
        if arity is None:
            min_arity, max_arity = _infer_arity(name, func)
        elif isinstance(arity, int):
            min_arity = max_arity = arity
        else:
            min_arity, max_arity = arity
        if not (0 <= min_arity <= max_arity):
            raise ValueError(f"invalid arity range for {name!r}: {arity!r}")
        self._functions[name] = HostFunction(name, func, min_arity, max_arity)

    def get_function(self, name: str) -> HostFunction | None:
        return self._functions.get(name)
