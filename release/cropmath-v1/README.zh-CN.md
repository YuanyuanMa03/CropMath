# CropMath

[English](README.md) | **简体中文**

CropMath 是一个农业机理公式数值评测数据集，包含数值参考答案与受控知识条件。
`cropmath-v1` 快照公开发布于
[myy555/CropMath](https://huggingface.co/datasets/myy555/CropMath)；
配套的提示构建器、评分器与校验脚本位于代码仓库
[YuanyuanMa03/CropMath](https://github.com/YuanyuanMa03/CropMath)。

## 内容与 split 关系

| 配置 | dev | test | gold | hidden_public |
|---|---:|---:|---:|---:|
| default | 252 | 751 | 95 | — |
| eval_prompts | 1,512 | 4,506 | 570 | — |
| hidden_public | — | — | — | 160 |

95 道 gold 题取自 test 用于审计；不要把它们叠加进 test 计数，也不要当作独立 split。
开发/测试共有 1,003 道不重复题目。六条件展开是对同一批题目附加不同知识块，
不产生独立新题。公式目录包含 62 个公开标识符 CMF001–CMF062。

公开过程类别为 `growth_yield`、`carbon_nitrogen_cycle`、`methane_emission` 与
`environmental_response`；推理模式为 `direct`、`sensitivity`、`branch` 与 `chain_2`。

## 从 Hub 加载

```python
from datasets import load_dataset

questions = load_dataset("myy555/CropMath", "default")
prompts = load_dataset("myy555/CropMath", "eval_prompts")
auxiliary = load_dataset("myy555/CropMath", "hidden_public")
assert len(questions["test"]) == 751
assert len(prompts["test"]) == 4506
assert len(auxiliary["hidden_public"]) == 160
```

请在实验记录中固定所使用的数据集修订版本。不要把访问令牌写进代码或预测文件。

如需离线使用或运行内置校验器，可下载本仓库后以本地路径加载。独立数据集目录还包含
`pyproject.toml`、`uv.lock`、校验脚本与数据集测试。在其根目录执行：

```bash
uv sync --locked
uv run --locked pytest -q tests
uv run --locked python scripts/validate_cropmath_release.py --release-dir . --no-scan-repo-root
uv run --locked python scripts/validate_formula_catalog.py --path metadata/formula_catalog.csv
```

GitHub 仓库内的副本请使用该仓库根目录 README 中的命令。校验通过仅表示所列本地检查
通过，不确立科学有效性，也不代表在线 Viewer 行为。

## 字段与使用方式

`default` 行包含 `id`、`problem`、`formula`、`parameters`、推理模式、知识块、
各条件提示、`answer` 与 `solution`。`eval_prompts` 行包含条件专属 `id`、原
`sample_id`、`condition`、`prompt`、`answer_float`、`precision` 与分组元数据。
只把所选 `prompt` 发给模型；不要把答案、解答、其他条件的知识块或评分元数据
放进模型输入。

六个条件为：C（公式与输入）、K_name（名称）、K_formula（参数语义）、
K_domain（领域背景）、K_distractor（干扰项）、K_wrong（错误公式）。
即使 K_wrong 提供了错误公式，目标仍是原题的参考答案。

数值评分规则：

```text
abs(prediction - answer) <= max(0.5 * 10**(-precision), abs(answer) * 0.01)
```

无法解析的预测计为错误。跨条件请保持样本配对，统计推断需考虑公式级聚类。
序列化协议见 `eval.yaml`，辅助集政策见 `HIDDEN_POLICY.md`。

## 来源与局限

本快照包含标准化表达式、参考答案标签、公开公式目录与审计元数据，不分发私有计算器
实现、生成代码或逐公式的完整文献映射。因此本包支持题目复用与基于存储标签的数值
预测校验，不能独立复现公式获取与参考答案生成的全过程。

审计 CSV 与协议是随包提供的记录，不是由包校验器新执行的独立人工审计。自动化解析器
测试检查序列化的解答，不证明人工审计的来源。题目输入为合成数据；本基准不确立模型
在田间观测、完整作物模拟或真实农业决策上的可靠性。

160 道辅助题公开题目而保留答案，不提供在线评分服务。ID 不重叠与答案保留不构成
"无训练数据污染"的证明。见 `HIDDEN_POLICY.md`。

## 许可与署名

数据集内容采用 CC BY 4.0 提供，见 `LICENSE`；本数据集仓库内置校验代码采用
`CODE_LICENSE` 中的 MIT 条款。GitHub 仓库对其代码另附 MIT 许可。署名元数据见
`CITATION.cff`（含代码仓库链接）。不声明论文 DOI；既有声明保持原样。
这些产物支持的范围见[可复现性说明](REPRODUCIBILITY.md)。
