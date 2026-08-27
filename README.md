# 实习工作详述

> **仓库定位**：维护答辩 PPT 文稿 `manuscript.md`（21 页，含 mermaid 图）。`render_mermaid.py` 把图中 mermaid 渲染成 `images/mmd_XX.png`。文稿生成 pptx 由 [ppt-pipeline-swarm](../Agent/ppt-pipeline-swarm) skill 的 stage 4 负责，不在本仓库。

> 2026.07—2026.08 两个月实习工作详尽记录，按项目与主题组织，保留具体技术细节、问题与方案、量化数据。
>
> 实习人：田沛康　部门：SAIE业务域　导师：向云武　直接主管：李兆星

## 整体总结

这两个月我在华为 SAIE 业务域 Omni 生态实习，主要做了两个项目，前后衔接。前半段在 OmniStream，这是一个把 Flink 算子用 C++ 重写来加速流处理的项目，我负责 SQL 表达式的原生化开发——让 Flink SQL 里的函数和操作符走 Native 向量化执行路径，替代原生 Java 执行。期间开发了 IFNULL、LEFT/RIGHT、BETWEEN、SIMILAR TO 等 7 个表达式，每个都独立分支提 PR，走通了从设计、实现、审计到修复补测试的完整链路。其中 BETWEEN 的崩溃排查是个典型案例：用原生 Flink 做对照组二分法，区分上游缺陷和本侧 bug，这套方法论后来沉淀下来反复用。

后半段切到 AgentOS，基于九问 Agent 平台做一体机办公 Agent，具体是 PPT 制作这条线。我把一个 4 角色流水线（attachment-reader → planner → researcher → designer）在平台上落地，设计了一套 .trace/ 可观察性体系让每个阶段的 agent 调用都可检查，还参考了学术 SOTA DeepPresenter 的内容风格。最难的一块是公式原生插入：中文办公场景公式必须可编辑，WPS 兼容是硬约束，但 Python PPT 库不支持原生公式，WPS 渲染又有各种兼容陷阱。方案迭代了四轮，从转图片到转换库到重型工具，最后手写了一个递归下降解析器直接生成 OMML，26 个公式全部注入成功，WPS 验证可见，零新增依赖。

除了项目本身的代码和设计文档，我还写了 21 篇 Wiki 约 34 万字，分基础学习、知识拓展、工作指南、工程实践四类，把过程中的根因、原则、验证都记下来，每条改动可追溯到提交。方法论上沉淀了 15 条，核心是 vanilla 二分法做 bug 归因、只读旁路做可观察性、纯净原则做文档质量保障。认知上比较大的升级是：工具是行为约束而不只是声明能力，隐式交互是脆弱的需要显式强约束，看起来完整不等于真的能用。

不足主要在个人能力提升方向：工程编码能力、底层原理理解、多项目时间管理与优先级调度都还需要继续练。下一步计划围绕工程编码、底层原理、多项目管理三个通用方向提升，与具体业务无关，是可持续迁移的底层能力。

## 文档结构

| 文件 | 内容 | 行数 |
|---|---|---|
| [01-实习概述.md](01-实习概述.md) | 基本信息、五条实习目标、两个项目定位、主线时间线 | 47 |
| [02-OmniStream项目.md](02-OmniStream项目.md) | 项目背景、三仓库双层架构、编译流程、表达式开发（5阶段/Type ABCD/双后端/12表达式）、3 个深度案例、9 个问题与方案、开发工具链、文件清单、知识库 | 845 |
| [03-AgentOS项目-架构与公式.md](03-AgentOS项目-架构与公式.md) | 项目背景、九问平台 8 核心仓、4 角色流水线、研究员开发、.trace/ 可观察性、PPTv2agent 参考与源码、27 PPT 方案分级、框架比较、公式原生插入（4 轮迭代/inject_omml 函数级/8 项目对比/banana-slides 源码/样式与文字约束调研） | 699 |
| [04-AgentOS项目-调优与质量.md](04-AgentOS项目-调优与质量.md) | 调优与大重构（workbuddy-align/designer-opt/feat-native-preserve-v2/refactor 各分支完整 commit 清单）、纯净原则审计、校验脚本体系（inspect_slide/verify_deck/build_deck/preflight）、tencent-pptx 三处调优、PresentBench 30 条 + 三 agent 产物原则 | 295 |
| [05-Wiki产出与方法论.md](05-Wiki产出与方法论.md) | 21 篇 Wiki 文稿四类清单（基础学习/知识拓展/工作指南/工程实践）+ 统计、15 条方法论沉淀 | 79 |
| [06-时间线与每日纪要.md](06-时间线与每日纪要.md) | 30+ 关键节点时间线、9 周每日工作纪要（保留日记级细节） | 227 |

## 两个项目

| 项目 | 周期 | 角色 | 核心工作 |
|---|---|---|---|
| OmniStream | 7月上中旬 | 表达式开发 | SQL 表达式原生加速、bug 修复、编译流程、工具链 |
| AgentOS / PPT-Agentskill | 7月下旬—8月 | 研究员部分开发与调优 | 4 角色流水线落地、可观察性、公式原生插入、大重构 |

## 素材来源

- 每日日志记录（D:\Myknows\日志，25 篇每日 + 6 篇周记）
- 两个项目本地资料（D:\Project\Work、D:\Project\Agent）
- Wiki 粗文稿（D:\Project\Agent\docs，21 篇）
- 九问平台研究（D:\Myknows\项目\一体机办公agent\openjiuwen，8 核心仓）
- 27 PPT 方案调研（D:\Myknows\项目\一体机办公agent\PPT工作流）
- 网上调研（OmniStream/openEuler、OMML 技术、PPT-agent 竞品框架）
