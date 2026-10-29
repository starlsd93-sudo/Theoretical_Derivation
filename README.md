**简体中文** | [English](README.en-US.md)

# theoretical-derivation

一个让 Claude 做**理论推导与建模**时"推得对、验得实"的 Claude Skill。

大模型做推导的典型问题不是解不出来，而是：替你补了一个你没说过的对称假设；跳过"预判为零"的中间项；给出一个数却不说为什么；解出闭式结果就默认模型成立；形式自洽的推导里藏着一个反号。这个 skill 把这些失误变成每个阶段的强制动作，并用**多方验证**兜底：

- **建模严谨性**：结构假设由人钉死（P1）、完整通解次序（P2）、前提显式化（P3）、有效域三问（P4），收尾过四问闸门。
- **多方验证**：双路独立推导对比 → 五类数值判据（含强制的**独立外部锚点**与**标准库实跑**）→ 严格模式下跨会话/跨模型独立复算。

---

## 安装

1. 下载 **[`theoretical-derivation_v1.0_20261029.skill`](theoretical-derivation_v1.0_20261029.skill)**
2. 在 Claude 客户端技能设置里上传（**Settings → Capabilities → Skills**）

`.skill` 本质是 ZIP。客户端不支持上传时，把 `theoretical-derivation/` 文件夹复制到 `~/.claude/skills/` 后重启 Claude Code。

R4 验证脚本需要 Python 3 + `numpy`、`scipy`（按任务另装 `sympy` 等）。

---

## 工作流

```
R0 问题数学化 ─N0─► R1 独立推导 ──┐
                                  ├─► R3 对比选定 ─N3─► R3.5 参数冻结 ─► R4 全程数值验证 ─N4─► R5 交付包
                   R2 文献借鉴推导 ┘
```

| 阶段 | 做什么 | 关键约束 |
|:--|:--|:--|
| R0 | 把问题归约为数学问题，锁定约定，列出分解计划与验证判据 | 结构假设缺项必问，不默认补全 |
| R1 | 不看文献独立推导 | 完整通解、每个计数说依据、四项自查 |
| R2 | 对照教材/文献推导，补强 R1 | 文献可溯源，禁止编造 |
| R3 | 两路对比，选定推导 | 有效域三问：前提 / 失效条件 / 推广路径 |
| R3.5 | 冻结所有数值参数 | 多端共用同一份 |
| R4 | 全程数值验证 | 五类判据 + 四问闸门 |
| R5 | 封装为结构化交付包 | 只封装，不新增推导 |

N0、N3、N4 是必经的人工审阅节点。

### R4 五类判据

1. 解析 vs 数值一致性
2. 结构性质（对称、正定、齐次律、守恒、量纲）
3. ★ **独立外部锚点**：经典闭式解 / 独立第二推导 / 可解析特例退化，三选一，强制
4. ★ **标准库实跑**：numpy/scipy/sympy/OpenCV 等独立复算，强制
5. 随机采样（蒙特卡洛或参数空间扫描）

`templates/verify_harness.py` 带一个可直接运行的示例（悬臂梁端部挠度，以单位载荷法作独立锚点）。

---

## 工作模式

| 模式 | 流程 | 适用 |
|:--|:--|:--|
| **轻量** | R0 → R1 → R4 精简（判据 1–3）| 探索性、短推导 |
| **标准**（默认）| 完整 R0→R5 | 正式建模 |
| **严格** | 标准 + 跨会话/跨模型独立复算 | 核心结论、将发表或用于设计决策 |
| **审校** | 对已有推导跑规则与判据，输出问题清单 | 审他人或自己的推导 |

执行环境与模式正交：**A** 有本地 Python 的环境（Claude Code，主推 + 终裁）、**B** 网页对话（文献对标）、**C** 外部 AI（skill 生成一份自包含委派提示词，作独立第二意见）。

---

## 快速开始

在 Claude Code 中：

```
调用 theoretical-derivation skill，对以下问题做理论推导。
工作根目录：D:\my-project
问题：求偏置布置的 n 根平行弹性杆连接两刚性板时的轴向等效刚度。
```

Claude 会先完成 R0，把你没给定的结构要素列出来问你，再推荐工作模式。

审校已有推导：

```
调用 theoretical-derivation skill 的审校模式，审 D:\my-project\inputs\derivation.md
```

更多提示词见 `references/prompts.md`。

---

## 目录

```
theoretical-derivation/
├─ SKILL.md                      入口：骨架、模式、导航
├─ references/
│  ├─ modeling.md                R0 + P1–P4 + 四问闸门
│  ├─ verification.md            五类判据、误差分层、验证 harness
│  ├─ cross-validation.md        双路与跨端多方验证
│  ├─ workflow.md                R1–R5 详规、失败回退、检查表
│  └─ prompts.md                 粘贴即用提示词
└─ templates/
   ├─ derivation-package.md      R5 交付包 schema
   ├─ verify_harness.py          R4 验证脚本骨架（含可运行示例）
   └─ pyrightconfig.json         可选静态检查配置
```

## 许可

[Apache-2.0](LICENSE)
