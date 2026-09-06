# CropMath

[English](README.md) | **简体中文**

CropMath 在六种受控知识条件下评测模型对农业机理公式的数值执行能力。本仓库包含数据集、
提示构建器、数值答案解析器、批量评分器与验证测试。数据集同步发布于
[Hugging Face Hub](https://huggingface.co/datasets/myy555/CropMath)，两个平台承载
相同的 `cropmath-v1` 数据载荷。

这些产物与论文的关系见[可复现性范围](release/cropmath-v1/REPRODUCIBILITY.md)。

## 本地快速开始

使用 Python 3.12 与 uv。在本目录执行：

```bash
uv sync --locked
uv run --locked pytest -q -ra tests
uv run --locked python examples/quickstart.py
uv run --locked python scripts/validate_cropmath_release.py
uv run --locked python scripts/validate_formula_catalog.py
```

quickstart 加载公开数据并用给定金标解答演练提示构建与答案解析，不发起任何模型请求，
也不报告模型性能。发布检查会运行 Hugging Face 数据加载与所选的公开来源扫描；
被跳过的检查不会被报告为通过。

## 包含内容

| 路径 | 用途 |
|---|---|
| `src/cropmath/` | 提示构建器与数值抽取/容差判分 |
| `release/cropmath-v1/` | 与 Hugging Face 独立数据集相同的载荷 |
| `scripts/` | 批量评分器及数据、公式目录、结果记录校验脚本 |
| `tests/` | 公开解析器、校验器与真实数据加载测试 |
| `examples/quickstart.py` | 本地数据与公开 API 冒烟示例 |
| `pyproject.toml`、`uv.lock` | 可复现的本地测试与数据加载环境 |

数据集包含 252 道开发题与 751 道测试题；gold 为取自测试集的 95 道审计子集。
六种知识条件将同一批测试题展开为 4,506 条提示。共有 62 个公式标识符和 160 道
答案保留的附加题。模式（schema）、许可、split 之间关系与科学局限性见
[数据集卡片](release/cropmath-v1/README.md)。

## 评测你自己的模型输出

每个模型/每次运行准备一个 JSONL 文件。每行必须包含 `id`（从所选 `eval_prompts`
行原样复制）和 `response`（模型的输出文本）。只把 prompt 内容发给模型，
不要发送参考答案等字段。生成失败用空字符串表示，使其保留在分母中。

```bash
uv run --locked python scripts/score_predictions.py --predictions predictions.jsonl --split test --output scores.json
```

默认对 test 的全部六个条件评分（共 4,506 条响应）。只评 C 条件时加 `--conditions C`
并提供其 751 条响应；也可用 `--split dev` 或 `--split gold` 选择其他公开 split。
重复、未知与缺失的 ID 会被拒绝；无法解析的输出计为错误；已存在的报告文件不会被覆盖。
每个条件报告 0–1 区间的准确率。输入契约、提示格式与报告要求见
[评测说明](docs/EVALUATION.md)。

`validate_eval_results.py` 校验本项目的详细结果记录 schema。其 `--formal-config`
模式检查的是历史确定性本地推理配置，不适用于任意 API 响应；它只对输入中出现的模型
检查条件完整性，调用方须自行核对预期模型名单、样本 ID 与单元数量。记录 schema
校验既不给预测打分，也不确立其科学有效性。

本包不含推理运行器、模型权重、原始模型响应、论文级分析结果或私有公式/生成实现。
因此它支持公开数据复用与数值评分，不支持一键重跑论文全流程，也不提供在线榜单或
隐藏答案评分服务。

## 答案保留题

公开的开发/测试/gold 答案随数据提供。160 道 `hidden_public` 题公开公式、参数与提示，
但不包含参考答案或解答。这一安排不构成"无训练数据污染"的证明。见
[共享政策](release/cropmath-v1/HIDDEN_POLICY.md)。隐藏答案测试另行维护，
不属于本公开包。

## 许可、引用与维护

代码采用 `LICENSE` 中的 MIT 声明；数据采用数据集 `LICENSE` 指定的 CC BY 4.0。
`CITATION.cff` 提供数据集署名与仓库链接；此处不指定论文 DOI，请通过 `CITATION.cff`
引用，并在论文信息可用后更新。环境元数据版本 `0.0.0` 标识本测试环境，
不是版本化软件发布。

请保持公开公式 ID、split 名称与条件名称稳定。变更后请运行上述测试与两个发布校验器。
数据加载测试不证明公式来源或人工审计已完成。
