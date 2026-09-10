"""抽象语法树节点定义。

每个节点都携带 ``position``（SourcePosition），供执行错误定位。
"""

from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import SourcePosition


@dataclass(frozen=True)
class IntLiteral:
    value: int
    position: SourcePosition


@dataclass(frozen=True)
class BoolLiteral:
    value: bool
    position: SourcePosition


@dataclass(frozen=True)
class NullLiteral:
    position: SourcePosition


@dataclass(frozen=True)
class Name:
    name: str
    position: SourcePosition


@dataclass(frozen=True)
class UnaryOp:
    op: str  # "-" | "not"
    operand: Node
    position: SourcePosition


@dataclass(frozen=True)
class BinaryOp:
    op: str  # 算术、比较或相等运算符
    left: Node
    right: Node
    position: SourcePosition  # 运算符位置


@dataclass(frozen=True)
class LogicalOp:
    op: str  # "and" | "or"
    left: Node
    right: Node
    position: SourcePosition  # 运算符位置


@dataclass(frozen=True)
class Call:
    name: str
    args: tuple[Node, ...]
    position: SourcePosition  # 函数名位置


Node = IntLiteral | BoolLiteral | NullLiteral | Name | UnaryOp | BinaryOp | LogicalOp | Call
