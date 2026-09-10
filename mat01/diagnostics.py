"""诊断对象：携带源码位置的错误信息。

位置约定：``offset`` 为从 0 开始的字符偏移，``line`` / ``column`` 从 1 开始。
详见 docs/expression-language-v1.md 的"诊断对象"一节。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourcePosition:
    """源码中的一个位置。"""

    offset: int
    line: int
    column: int


@dataclass(frozen=True)
class Diagnostic:
    """一条可定位的诊断信息。"""

    message: str
    position: SourcePosition
    source_name: str = "<expression>"

    def __str__(self) -> str:
        return (
            f"{self.source_name}:{self.position.line}:{self.position.column}: "
            f"{self.message}"
        )
