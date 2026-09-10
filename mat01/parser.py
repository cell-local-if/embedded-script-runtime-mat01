"""语法分析：把记号流解析为抽象语法树。

优先级与语法范围见 docs/expression-language-v1.md 的"语法"一节。
比较运算不结合；`a < b < c` 之类的链式比较在这里报语法错误。
"""

from __future__ import annotations

from .diagnostics import Diagnostic
from .errors import CompileError
from .lexer import Token, tokenize
from . import nodes

_COMPARISON_OPS = ("<", "<=", ">", ">=", "==", "!=")


class _Parser:
    def __init__(self, tokens: list[Token], source_name: str) -> None:
        self._tokens = tokens
        self._source_name = source_name
        self._index = 0

    def parse(self) -> nodes.Node:
        expression = self._parse_or()
        token = self._peek()
        if token.kind != "eof":
            self._fail(f"unexpected {self._describe(token)} after expression", token)
        return expression

    # or := and ( "or" and )*
    def _parse_or(self) -> nodes.Node:
        left = self._parse_and()
        while self._at_keyword("or"):
            op = self._advance()
            right = self._parse_and()
            left = nodes.LogicalOp("or", left, right, op.position)
        return left

    # and := not ( "and" not )*
    def _parse_and(self) -> nodes.Node:
        left = self._parse_not()
        while self._at_keyword("and"):
            op = self._advance()
            right = self._parse_not()
            left = nodes.LogicalOp("and", left, right, op.position)
        return left

    # not := "not" not | comparison
    def _parse_not(self) -> nodes.Node:
        if self._at_keyword("not"):
            op = self._advance()
            operand = self._parse_not()
            return nodes.UnaryOp("not", operand, op.position)
        return self._parse_comparison()

    # comparison := additive ( COMPARE additive )?   —— 不结合
    def _parse_comparison(self) -> nodes.Node:
        left = self._parse_additive()
        token = self._peek()
        if token.kind == "op" and token.text in _COMPARISON_OPS:
            self._advance()
            right = self._parse_additive()
            following = self._peek()
            if following.kind == "op" and following.text in _COMPARISON_OPS:
                self._fail(
                    "chained comparisons are not supported; "
                    "combine comparisons with 'and' / 'or'",
                    following,
                )
            return nodes.BinaryOp(token.text, left, right, token.position)
        return left

    # additive := multiplicative ( ("+"|"-") multiplicative )*
    def _parse_additive(self) -> nodes.Node:
        left = self._parse_multiplicative()
        while self._at_op("+", "-"):
            op = self._advance()
            right = self._parse_multiplicative()
            left = nodes.BinaryOp(op.text, left, right, op.position)
        return left

    # multiplicative := unary ( ("*"|"/"|"%") unary )*
    def _parse_multiplicative(self) -> nodes.Node:
        left = self._parse_unary()
        while self._at_op("*", "/", "%"):
            op = self._advance()
            right = self._parse_unary()
            left = nodes.BinaryOp(op.text, left, right, op.position)
        return left

    # unary := "-" unary | primary
    def _parse_unary(self) -> nodes.Node:
        if self._at_op("-"):
            op = self._advance()
            operand = self._parse_unary()
            return nodes.UnaryOp("-", operand, op.position)
        return self._parse_primary()

    # primary := INT | "true" | "false" | "null" | NAME | NAME "(" args ")" | "(" or ")"
    def _parse_primary(self) -> nodes.Node:
        token = self._peek()
        if token.kind == "int":
            self._advance()
            return nodes.IntLiteral(token.value, token.position)
        if token.kind == "keyword":
            if token.text == "true":
                self._advance()
                return nodes.BoolLiteral(True, token.position)
            if token.text == "false":
                self._advance()
                return nodes.BoolLiteral(False, token.position)
            if token.text == "null":
                self._advance()
                return nodes.NullLiteral(token.position)
            self._fail(f"unexpected keyword {token.text!r}", token)
        if token.kind == "name":
            self._advance()
            if self._at_op("("):
                return self._parse_call(token)
            return nodes.Name(token.text, token.position)
        if self._at_op("("):
            self._advance()
            expression = self._parse_or()
            self._expect_op(")", "expected ')' to close parenthesized expression")
            return expression
        self._fail(f"expected an expression but found {self._describe(token)}", token)

    def _parse_call(self, name_token: Token) -> nodes.Call:
        self._expect_op("(", "expected '('")
        args: list[nodes.Node] = []
        if not self._at_op(")"):
            args.append(self._parse_or())
            while self._at_op(","):
                self._advance()
                args.append(self._parse_or())
        self._expect_op(")", "expected ')' after function arguments")
        return nodes.Call(name_token.text, tuple(args), name_token.position)

    # ---- 记号工具 ----

    def _peek(self) -> Token:
        return self._tokens[self._index]

    def _advance(self) -> Token:
        token = self._tokens[self._index]
        if token.kind != "eof":
            self._index += 1
        return token

    def _at_keyword(self, text: str) -> bool:
        token = self._peek()
        return token.kind == "keyword" and token.text == text

    def _at_op(self, *texts: str) -> bool:
        token = self._peek()
        return token.kind == "op" and token.text in texts

    def _expect_op(self, text: str, message: str) -> Token:
        if not self._at_op(text):
            self._fail(message, self._peek())
        return self._advance()

    def _describe(self, token: Token) -> str:
        if token.kind == "eof":
            return "end of input"
        return repr(token.text)

    def _fail(self, message: str, token: Token) -> None:
        raise CompileError(Diagnostic(message, token.position, self._source_name))


def parse(source: str, source_name: str = "<expression>") -> nodes.Node:
    """把源码解析为一个表达式节点；失败时抛出 CompileError。"""
    return _Parser(tokenize(source, source_name), source_name).parse()
