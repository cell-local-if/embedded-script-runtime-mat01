"""词法分析：把源码切成记号流。

词法范围见 docs/expression-language-v1.md 的"词法"一节。不支持的
字符（字符串引号、小数点、赋值号等）在这里报出带位置的编译错误。
"""

from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import Diagnostic, SourcePosition
from .errors import CompileError

KEYWORDS = frozenset({"and", "or", "not", "true", "false", "null"})

# 双字符运算符必须先于单字符匹配。
_DOUBLE_OPS = ("<=", ">=", "==", "!=")
_SINGLE_OPS = frozenset("+-*/%(),<>")

# 常见误用的针对性提示；其余非法字符走通用报错。
_CHAR_HINTS = {
    "'": "string literals are not supported in this version",
    '"': "string literals are not supported in this version",
    "=": "assignment is not supported; use '==' for equality",
    "!": "unexpected '!'; use 'not' for negation or '!=' for inequality",
    "&": "unexpected '&'; use 'and' for logical conjunction",
    "|": "unexpected '|'; use 'or' for logical disjunction",
}


@dataclass(frozen=True)
class Token:
    kind: str  # "int" | "name" | "keyword" | "op" | "eof"
    text: str
    position: SourcePosition
    value: int | None = None  # 仅 kind == "int" 时有值


class _Lexer:
    def __init__(self, source: str, source_name: str) -> None:
        self._source = source
        self._source_name = source_name
        self._index = 0
        self._line = 1
        self._column = 1

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while True:
            self._skip_trivia()
            position = self._position()
            char = self._peek()
            if char == "":
                tokens.append(Token("eof", "", position))
                return tokens
            if char.isdigit():
                tokens.append(self._read_integer(position))
            elif char.isalpha() or char == "_":
                tokens.append(self._read_name(position))
            elif any(self._source.startswith(op, self._index) for op in _DOUBLE_OPS):
                text = self._source[self._index : self._index + 2]
                self._advance()
                self._advance()
                tokens.append(Token("op", text, position))
            elif char in _SINGLE_OPS:
                self._advance()
                tokens.append(Token("op", char, position))
            else:
                self._fail(self._describe_unexpected(char), position)

    def _describe_unexpected(self, char: str) -> str:
        hint = _CHAR_HINTS.get(char)
        if hint is not None:
            return hint
        return f"unexpected character {char!r}"

    def _read_integer(self, position: SourcePosition) -> Token:
        start = self._index
        while self._peek().isdigit():
            self._advance()
        text = self._source[start : self._index]
        if self._peek() == ".":
            self._fail(
                "floating-point literals are not supported in this version",
                self._position(),
            )
        return Token("int", text, position, value=int(text))

    def _read_name(self, position: SourcePosition) -> Token:
        start = self._index
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self._source[start : self._index]
        kind = "keyword" if text in KEYWORDS else "name"
        return Token(kind, text, position)

    def _skip_trivia(self) -> None:
        while True:
            char = self._peek()
            if char != "" and char in " \t\r\n":
                self._advance()
            elif char == "#":
                while self._peek() not in ("", "\n"):
                    self._advance()
            else:
                return

    def _peek(self) -> str:
        if self._index >= len(self._source):
            return ""
        return self._source[self._index]

    def _advance(self) -> None:
        if self._source[self._index] == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        self._index += 1

    def _position(self) -> SourcePosition:
        return SourcePosition(offset=self._index, line=self._line, column=self._column)

    def _fail(self, message: str, position: SourcePosition) -> None:
        raise CompileError(Diagnostic(message, position, self._source_name))


def tokenize(source: str, source_name: str = "<expression>") -> list[Token]:
    """把源码切成记号序列，末尾附带一个 eof 记号。"""
    return _Lexer(source, source_name).tokenize()
