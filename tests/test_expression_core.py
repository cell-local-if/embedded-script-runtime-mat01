"""表达式语言内核的 unittest 测试套件。

从仓库根目录运行：

    python -m unittest discover -s tests -t . -v
"""

from __future__ import annotations

import unittest

import mat01
from mat01 import (
    ArityError,
    CompileError,
    DivisionByZeroError,
    Environment,
    HostFunctionError,
    TypeMismatchError,
    UnboundNameError,
    compile_source,
)


def evaluate(source: str, env: Environment | None = None, variables=None):
    return compile_source(source).evaluate(env, variables)


class ArithmeticTests(unittest.TestCase):
    def test_integer_literals_and_arithmetic(self):
        self.assertEqual(evaluate("1 + 2 * 3"), 7)
        self.assertEqual(evaluate("(1 + 2) * 3"), 9)
        self.assertEqual(evaluate("10 - 4 - 3"), 3)  # 左结合
        self.assertEqual(evaluate("17 % 5"), 2)

    def test_unary_minus(self):
        self.assertEqual(evaluate("-3 + 1"), -2)
        self.assertEqual(evaluate("- -5"), 5)
        self.assertEqual(evaluate("-(2 + 3)"), -5)

    def test_division_is_floor_division(self):
        self.assertEqual(evaluate("7 / 2"), 3)
        self.assertEqual(evaluate("-7 / 2"), -4)

    def test_division_by_zero(self):
        with self.assertRaises(DivisionByZeroError):
            evaluate("1 / 0")
        with self.assertRaises(DivisionByZeroError):
            evaluate("1 % 0")

    def test_arbitrary_precision(self):
        self.assertEqual(evaluate("1000000000000 * 1000000000000"), 10**24)


class ComparisonAndEqualityTests(unittest.TestCase):
    def test_ordering_comparisons(self):
        self.assertIs(evaluate("1 < 2"), True)
        self.assertIs(evaluate("2 <= 2"), True)
        self.assertIs(evaluate("3 > 2"), True)
        self.assertIs(evaluate("3 >= 4"), False)

    def test_equality_across_types(self):
        self.assertIs(evaluate("1 == 1"), True)
        self.assertIs(evaluate("1 != 2"), True)
        self.assertIs(evaluate("1 == true"), False)  # bool 与 int 是不同类型
        self.assertIs(evaluate("true == true"), True)
        self.assertIs(evaluate("null == null"), True)
        self.assertIs(evaluate("null == 0"), False)
        self.assertIs(evaluate("null != null"), False)


class LogicTests(unittest.TestCase):
    def test_and_or_not(self):
        self.assertIs(evaluate("true and false"), False)
        self.assertIs(evaluate("true or false"), True)
        self.assertIs(evaluate("not false"), True)
        self.assertIs(evaluate("not 1 < 2"), False)  # not 优先级低于比较

    def test_precedence(self):
        self.assertIs(evaluate("true or false and false"), True)
        self.assertIs(evaluate("(true or false) and false"), False)

    def test_short_circuit_and_does_not_call_right_side(self):
        calls = []
        env = Environment()
        env.register_function("mark", lambda: calls.append("called") or True)
        self.assertIs(evaluate("false and mark()", env), False)
        self.assertEqual(calls, [])

    def test_short_circuit_or_does_not_call_right_side(self):
        calls = []
        env = Environment()
        env.register_function("mark", lambda: calls.append("called") or True)
        self.assertIs(evaluate("true or mark()", env), True)
        self.assertEqual(calls, [])

    def test_short_circuit_right_side_evaluated_when_needed(self):
        calls = []
        env = Environment()
        env.register_function("mark", lambda: calls.append("called") or True)
        self.assertIs(evaluate("true and mark()", env), True)
        self.assertEqual(calls, ["called"])


class VariableAndFunctionTests(unittest.TestCase):
    def test_variables(self):
        self.assertEqual(evaluate("x * 2 + y", variables={"x": 3, "y": 1}), 7)

    def test_null_variable(self):
        self.assertIs(evaluate("maybe == null", variables={"maybe": None}), True)

    def test_unbound_variable(self):
        with self.assertRaises(UnboundNameError) as caught:
            evaluate("x + 1")
        self.assertIn("'x'", str(caught.exception))

    def test_function_call(self):
        env = Environment()
        env.register_function("double", lambda x: x * 2)
        env.register_function("add3", lambda a, b, c: a + b + c)
        self.assertEqual(evaluate("double(21)", env), 42)
        self.assertEqual(evaluate("add3(1, 2, 3)", env), 6)

    def test_function_call_with_variables(self):
        env = Environment()
        env.register_function("clamp", lambda v, lo, hi: max(lo, min(v, hi)))
        self.assertEqual(evaluate("clamp(score, 0, 100)", env, {"score": 137}), 100)

    def test_arity_inferred_from_signature(self):
        env = Environment()
        env.register_function("f", lambda a, b=10: a + b)  # arity 1..2
        self.assertEqual(evaluate("f(1)", env), 11)
        self.assertEqual(evaluate("f(1, 2)", env), 3)

    def test_unregistered_function(self):
        with self.assertRaises(UnboundNameError):
            evaluate("nope(1)", Environment())

    def test_wrong_argument_count(self):
        env = Environment()
        env.register_function("double", lambda x: x * 2)
        with self.assertRaises(ArityError):
            evaluate("double(1, 2)", env)
        with self.assertRaises(ArityError):
            evaluate("double()", env)

    def test_host_function_exception_is_wrapped(self):
        def boom():
            raise RuntimeError("host blew up")

        env = Environment()
        env.register_function("boom", boom)
        with self.assertRaises(HostFunctionError) as caught:
            evaluate("boom()", env)
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.assertIn("host blew up", str(caught.exception))

    def test_host_function_returning_unsupported_type(self):
        env = Environment()
        env.register_function("bad", lambda: "text")
        with self.assertRaises(TypeMismatchError):
            evaluate("bad()", env)

    def test_variable_and_function_namespaces_are_independent(self):
        env = Environment()
        env.register_function("f", lambda: 1)
        self.assertEqual(evaluate("f + f()", env, {"f": 10}), 11)


class TypeErrorTests(unittest.TestCase):
    def test_arithmetic_on_bool(self):
        with self.assertRaises(TypeMismatchError):
            evaluate("1 + true")

    def test_arithmetic_on_null(self):
        with self.assertRaises(TypeMismatchError):
            evaluate("null * 2")

    def test_ordering_on_null(self):
        with self.assertRaises(TypeMismatchError):
            evaluate("null < 1")

    def test_not_requires_bool(self):
        with self.assertRaises(TypeMismatchError):
            evaluate("not 1")

    def test_and_requires_bool(self):
        with self.assertRaises(TypeMismatchError):
            evaluate("1 and true")

    def test_or_requires_bool_on_right(self):
        with self.assertRaises(TypeMismatchError):
            evaluate("false or 0")

    def test_type_error_position_points_at_operator(self):
        with self.assertRaises(TypeMismatchError) as caught:
            evaluate("1 + true")
        diagnostic = caught.exception.diagnostic
        self.assertEqual((diagnostic.position.line, diagnostic.position.column), (1, 3))
        self.assertEqual(diagnostic.position.offset, 2)


class CompileErrorTests(unittest.TestCase):
    def test_syntax_error_position(self):
        with self.assertRaises(CompileError) as caught:
            compile_source("1 +")
        diagnostic = caught.exception.diagnostic
        self.assertEqual((diagnostic.position.line, diagnostic.position.column), (1, 4))
        self.assertEqual(diagnostic.position.offset, 3)

    def test_multiline_position(self):
        with self.assertRaises(CompileError) as caught:
            compile_source("1 +\n  * 2")
        position = caught.exception.diagnostic.position
        self.assertEqual((position.line, position.column), (2, 3))

    def test_unclosed_parenthesis(self):
        with self.assertRaises(CompileError):
            compile_source("(1 + 2")

    def test_trailing_content(self):
        with self.assertRaises(CompileError):
            compile_source("1 2")

    def test_string_literal_not_supported(self):
        with self.assertRaises(CompileError) as caught:
            compile_source("'hello'")
        self.assertIn("string literals are not supported", str(caught.exception))

    def test_float_literal_not_supported(self):
        with self.assertRaises(CompileError) as caught:
            compile_source("1.5")
        self.assertIn("floating-point literals are not supported", str(caught.exception))

    def test_assignment_not_supported(self):
        with self.assertRaises(CompileError) as caught:
            compile_source("x = 1")
        self.assertIn("assignment is not supported", str(caught.exception))

    def test_chained_comparison_not_supported(self):
        with self.assertRaises(CompileError) as caught:
            compile_source("1 < 2 < 3")
        self.assertIn("chained comparisons are not supported", str(caught.exception))

    def test_keyword_as_expression(self):
        with self.assertRaises(CompileError):
            compile_source("and")

    def test_diagnostic_str_includes_source_name_and_position(self):
        with self.assertRaises(CompileError) as caught:
            compile_source("1 +", source_name="rule-7")
        self.assertEqual(str(caught.exception).split(": ", 1)[0], "rule-7:1:4")


class HostApiTests(unittest.TestCase):
    def test_comments_and_whitespace(self):
        self.assertEqual(evaluate("1 + # comment\n 2"), 3)

    def test_invalid_variable_value_rejected(self):
        with self.assertRaises(TypeError):
            evaluate("x", variables={"x": "text"})

    def test_invalid_variable_name_rejected(self):
        with self.assertRaises(ValueError):
            evaluate("true", variables={"and": 1})

    def test_invalid_function_registration(self):
        env = Environment()
        with self.assertRaises(ValueError):
            env.register_function("and", lambda: 1)
        with self.assertRaises(TypeError):
            env.register_function("f", 42)

    def test_program_is_reusable(self):
        program = compile_source("x + 1")
        self.assertEqual(program.evaluate(variables={"x": 1}), 2)
        self.assertEqual(program.evaluate(variables={"x": 41}), 42)


if __name__ == "__main__":
    unittest.main()
