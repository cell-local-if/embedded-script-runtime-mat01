"""宿主应用集成示例：注册函数、传入变量、求值并处理结构化错误。

从仓库根目录运行：

    python examples/host_integration.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# 允许直接从源码树运行本示例（未安装包时把仓库根目录加入导入路径）。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mat01


def build_environment() -> mat01.Environment:
    """宿主把自己的能力显式注册给表达式；未注册的能力表达式不可见。"""
    env = mat01.Environment()
    env.register_function("clamp", lambda value, lo, hi: max(lo, min(value, hi)))
    env.register_function("is_even", lambda n: n % 2 == 0)
    env.register_function("version", lambda: 3)  # 零参数函数
    return env


def show(env: mat01.Environment, source: str, variables: dict | None = None) -> None:
    print(f"source:    {source}")
    try:
        program = mat01.compile_source(source, source_name="example")
        result = program.evaluate(env, variables=variables)
    except mat01.CompileError as error:
        print(f"compile error:    {error}")
    except mat01.EvaluationError as error:
        print(f"evaluation error ({type(error).__name__}): {error}")
    else:
        print(f"result:    {result!r}")
    print()


def main() -> None:
    env = build_environment()

    # 成功求值：变量、函数调用、短路逻辑、空值。
    show(env, "clamp(score, 0, 100)", {"score": 137})
    show(env, "is_even(count) and count > 0", {"count": 4})
    show(env, "missing == null", {"missing": None})
    show(env, "false and clamp(1, 2, 3)")  # 短路：clamp 不会被调用

    # 结构化错误：编译错误与执行错误都携带行列位置。
    show(env, "1 + true")              # 类型错误，指向 '+'
    show(env, "unknown_fn(1)")         # 未注册函数
    show(env, "clamp(1, 2)")           # 参数数量错误
    show(env, "1 +")                   # 语法错误，指向输入末尾
    show(env, "'hello'")               # 不支持的语法（字符串字面量）


if __name__ == "__main__":
    main()
