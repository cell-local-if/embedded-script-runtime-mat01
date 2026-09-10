# 嵌入式脚本执行引擎

为宿主应用提供可嵌入的脚本语言运行时：通过库接口加载源码、绑定输入数据与显式注册的宿主函数，得到结果或可定位的错误。

## 当前状态

仓库已包含首个可运行的表达式语言内核（`mat01` 包）：整数字面量、布尔与空值、括号、一元运算、基本二元算术/比较/相等运算、`and`/`or`/`not` 短路逻辑、显式输入变量，以及宿主显式注册后才能调用的函数。本版本语义契约见 [表达式语言语义规范 v1](docs/expression-language-v1.md)；长期产品范围见 [产品需求](docs/product.md)，其中的能力地图是演进方向，不代表已有功能。

## 使用方式

库无需安装即可从仓库根目录导入：

```python
import mat01

env = mat01.Environment()
env.register_function("double", lambda x: x * 2)

program = mat01.compile_source("double(x) + 1")
result = program.evaluate(env, variables={"x": 3})  # 7
```

编译错误（`CompileError`）与执行错误（`EvaluationError` 及其子类）都携带含行列与偏移的 `Diagnostic` 诊断对象；不支持的语法、未绑定名称、参数数量错误、宿主函数异常和类型不匹配都会给出明确错误。

## 验证命令

在仓库根目录执行（Python 3.12，仅依赖标准库）：

```sh
# 运行测试套件
python3 -m unittest discover -s tests -t . -v

# 运行宿主集成示例
python3 examples/host_integration.py
```

## 仓库结构

- `mat01/`：表达式语言内核（词法、语法、求值、环境、诊断）。
- `docs/expression-language-v1.md`：本版本已实现的语义契约。
- `docs/product.md`：长期产品需求与演进边界。
- `examples/host_integration.py`：宿主集成示例。
- `tests/`：标准库 `unittest` 测试套件。

## 首期工程约定

- Python 3.12，优先使用标准库；运行和核心验证不依赖外部服务或真实设备。
- 主要交付是可导入的软件库及可运行的宿主集成示例，不建设通用命令行产品或业务管理界面。
- 首个实现固定有限语言语义和公开调用方式，明确支持与不支持的范围，不默认兼容 Python 或 JavaScript。
- 验证优先使用标准库 `unittest`。实现交付时提供真实可用的运行和测试命令。
- 不默认开放文件、网络或进程访问；宿主能力由应用显式注册。执行预算不等同于操作系统级安全隔离。
- 未实现的能力不写成已支持；示例输入不冒充生产数据，性能结论注明实测环境与范围。

## 开发环境

本地准备环境为 Linux、Python 3.12 和 Git。首次克隆后的代码实现及验证方式，由对应功能提交补充。产品需求中的未来能力按依赖逐步建设。
