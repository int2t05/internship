# 实习工作详述 · AgentOS 项目（架构与公式）

## 三、AgentOS / PPT-Agentskill 项目

## 三、AgentOS / PPT-Agentskill 项目

### 3.1 项目背景

**AgentOS = openJiuwen（九问）Agent 平台**：开源 Agent 平台，提供 AI Agent 的"开发 + 运行 + 部署 + 运维"全生命周期能力。

**五层架构**（自底向上）：

| 层 | 子系统                          | 职责                                                                                          |
| -- | ------------------------------- | --------------------------------------------------------------------------------------------- |
| 5  | Agent System Service（AgentOS） | 安全隔离沙箱 / 统一记忆持久化 / 原生 CLI / 标准化 Agent 文件系统 / 跨 Agent 通信总线          |
| 4  | Agent Distributed Runtime       | 分布式运行时底座（一键发布部署 + 全生命周期管控），subprocess/docker/k8s 部署策略             |
| 3  | Agent Framework（agent-core）   | 核心 SDK 与执行引擎，Spec/Manifest/Harness/Rail/Provider 抽象 + ReAct/Workflow/DeepAgent 执行 |
| 2  | Agent Studio + SkillHub         | 一站式可视化开发平台 + Skill 托管与分发                                                       |
| 1  | DeepAgents                      | jiuwenswarm（多智能体协同旗舰）/ deepsearch / jiuwensymbiosis（具身）                         |

**核心抽象**：ReActAgent（Reasoning + Action 循环）、WorkflowAgent、DeepAgent（双层：外层规划 + 内层 ReAct）；Skill 经 SkillUseRail 挂到 Agent；Rail 护栏；Provider（OpenAI 兼容模型接入，一体机本地化降本）。

**一体机办公 agent 定位**：基于九问 agent-core/swarm 平台开发"一体机办公 Agent"产品——把大模型能力经多渠道通信 App 直达用户指尖的本地化、可编辑交付的办公智能体。

**关键技术约束**（决定后续所有选型）：

- 产物必须可编辑（中文办公刚需）→ python-pptx 主路线；Slidev/Marp/reveal.js 三家 Markdown 框架导出的 PPTX 均为图片型不可编辑
- 本地化部署 → Provider 走 OpenAI 兼容接一体机模型（GLM/Qwen/9B 等可本地化降本）
- 中文场景 + WPS 兼容 → 现有 benchmark 偏英文学术，需自建中文企业场景补充集；WPS 渲染兼容性是硬约束

**PPT 专家 Agent 选型建议**（来自 27 方案调研）：S 层首选参考 DeepPresenter（ACL2026 SOTA，Avg 4.44 超商业系统 Gamma 4.36）、ppt-master（41.5k★，MIT，SVG→DrawingML）、SLIDEGEN/Paper2Slide（6 智能体分工）。推荐架构：以 DeepPresenter 双 agent + 环境接地反思为骨架，以 ppt-master SVG→DrawingML 为可编辑导出主路径，借 SlideGen 6 智能体分工与 LandPPT 角色路由做编排，用 PresentBench + SlidesGen-Bench 做评测。

### 3.2 九问平台调研

**切入点**：以"skill 如何驱动 agent 干活"作为贯穿全流程的切入点，详细解析到源码层面，用代码验证文档描述。

#### 3.2.1 平台五层架构

openJiuwen 是开源 Agent 平台，GitHub 组织 openJiuwen-ai 共 20 个仓库，官方归纳为 5 层 12 核心仓：

```
DeepAgents（开箱即用复杂智能体）：jiuwenswarm · jiuwensymbiosis · deepsearch
Agent Studio + SkillHub：可视化开发平台 + Skill 托管分发
Agent Framework：agent-core · agent-core-java · agent-memory · agent-gateway
Agent Distributed Runtime：agent-runtime · agent-runtime-java · agent-protocol
Agent System Service（AgentOS）：安全沙箱 / 记忆持久化 / 原生 CLI / 文件系统 / 通信总线
```

一句话分层：openjiuwen（通用框架）→ jiuwenswarm/deepsearch/jiuwensymbiosis（应用实现）→ jiuwenclaw（产品打包）。

#### 3.2.2 8 核心仓研究

| 仓 | 语言 | ★ | 定位 |
|---|---|---|---|
| agent-core | Python | 356 | 用 Spec 描述 Agent 该长什么样，框架把它装配（Manifest/Harness）起来并跑（Runner）——声明、装配、运行三步分离 |
| jiuwenswarm | Python | 1789 | 外部渠道把请求送进 Gateway，规范化后交 AgentServer 调度 Agent 执行，复杂任务经 Symphony 技能编排——接入、运行、编排三层分离 |
| agent-studio | Java | 106 | Angular 前端画 Agent/工作流，Java 后端编译成 IR 契约，远程交 Python 九问引擎执行——画→编译→执行 |
| deepsearch | Python | 90 | 给问题像研究员一样规划任务、检索知识、推理分析、生成带引用报告——每条结论可追到原始片段 |
| agent-memory | Python | 18 | 自遗传记忆系统（AutoGenetic Memory）——会记事、会巩固、会遗忘的大脑 |
| agent-runtime | Python | 5 | 把 Agent 从开发态稳定带到生产态，发布/运行/管理标准可控 |
| agent-protocol | C++ | 55 | 三 SDK 各管一层——A2A 管 Agent↔Agent 协作，MCP 管 Agent↔工具，A2X 管注册发现 |
| skillhub | Python | 6 | 把 Skill 当可版本化、可评审、可检索、可审计的制品管理——marketplace 控制面 + skill-runner 执行面 |

**agent-core**（核心 SDK，pip 包名 openjiuwen v0.1.16）：双层 API——core 积木层（ReActAgent/Model/Tool/Memory/WorkflowAgent）+ harness 装配层（Spec/BuildContext/Manifest/Harness）。五大核心概念：Spec（声明式规格）/ Manifest（装配后的元素清单）/ Harness（运行时装配成可执行 Agent）/ Rail（护栏，生命周期钩子式校验拦截）/ Provider（模型注册统一 LLM 接入）。Agent 类型体系：ReActAgent（推理执行循环）/ DeepAgent（双层：外层规划+内层 ReAct）/ WorkflowAgent（图编排多步骤流程）。执行引擎 Runner + resource_mgr 资源管理 + 状态管理与中断恢复。

**jiuwenswarm**（旗舰应用）：三大组件——Gateway 网关（多渠道接入 9 IM 渠道 + ACP/A2A/SSH 协议、请求路由、E2A 信封规范化）/ AgentServer 服务核心（Agent 生命周期管理、会话与事件流、沙箱执行）/ Symphony 技能编排（技能检索树、技能编排图、技能进化）。多智能体协同：Swarm 声明式装配、Leader/Teammate 团队、分布式协同（pyzmq）。运行时双进程：Gateway（端口 19001）+ AgentServer（端口 18092），由 app.py 一体化拉起，0.25s 轮询任一退出全终止。Agent 三层并发：reload 全局锁 / per-key 创建锁（WeakValueDict）/ borrower+pin 在用计数。harness 三模式：claw（默认 DeepAgent）/ code（LSP+worktree+subagent）/ team（Leader-Teammate）。

**agent-studio**（可视化平台，Java 17 / Spring Boot / Angular 20）：三 App 分面——Manager（管理面：资源 CRUD、版本发布、IR 编译）/ Runtime（执行面：IR 缓存、在线调试、SSE 桥接）/ Space（门户：chat 式 builder、NL2Agent）。IR 契约体系：visual DSL 画布 → IrAdapterService 编译 → IR JSON 落 OBS → 九问引擎消费。关键边界：Java 后端是薄编排/SSE 桥接层，不碰 agent-core 执行逻辑，真正干活的是 Python openjiuwen。

**deepsearch**（深度检索引擎，包名 openjiuwen-deepsearch v0.2.0）：三种工作模式——research（深度研究）/ search（探索搜索）/ react（推理反应）。分层架构：agent-core 底座 → framework 编排层 → algorithm 算法层（84 文件）+ server REST 服务。chunk 级引文机制（片段级溯源、引用校验、可信度）+ 可追溯推理链（意图识别→大纲编辑团队→报告合成；推理链可视化、观点溯源）。

**agent-memory**（记忆系统，包名 JiuwenMemory v0.1.1）：自遗传记忆系统。L0-L3 分层记忆（L0 原始信息/L1 摘要记忆/L2 结构化记忆/L3 用户画像）。五类记忆类型（user_profile/semantic_memory/episodic_memory/variable/summary）。Dreaming 睡时巩固（浅睡筛选→REM 提取归类→深睡去重消解）。MemoryTurbo 加速（写入即更新、后台异步提取、小模型按话题合并）。检索与遗忘（语义向量检索、冲突检测 MemUpdateChecker、Ebbinghaus 软遗忘）。双维度扩展（Plugin 平台钩子 + Provider 引擎接口，Mem0/openViking/AgentArts 可互操作）。

**agent-runtime**（分布式运行时）：双平面架构——管理面（server FastAPI 管理 REST + management DeploymentManager SDK）/ 数据面（applications AgentApp 进程 + service 服务壳框架）/ foundation 共享基座（DB/config/log/security）。部署管理 DeploymentManager 策略三选一：subprocess（进程）/ docker（容器）/ k8s（集群）。AgentApp 服务壳：BaseApp FastAPI 封装，对话端点 /query（SSE 流式）/health/reset_conversation。IR 编译桥接：消费 agent-studio IR JSON → AgentCompiler 编译 → ConfigAdapter 适配 → LLMAgent/WorkflowAgent 执行。

**agent-protocol**（互操作协议 SDK，Apache-2.0）：三 SDK 各管一层——A2A（Agent-to-Agent v1.0：HTTP+JSON-RPC+SSE，AgentCard/Message/Task，AgentExecutor+TaskUpdater）/ MCP（Model Context Protocol：Streamable HTTP+stdio，Tool/Resource/Prompt，ToolFunc 注册式服务端）/ A2X（Registry：AgentCard 发现机制，well-known 抓取，注册中心 LLM 分类法搜索）。三层互操作栈：垂直能力 MCP → 水平协作 A2A → 发现路由 A2X。关系单向：agent-core 消费本仓发布的三个 SDK，本仓不引用 openjiuwen。

**skillhub**（Skill 托管分发，Apache-2.0）：双组件——marketplace 控制面（托管与版本、评审 skill_review v3、索引 Capability Tree、检索 hybrid、下载 presigned S3、审计与 ClawHub 兼容）/ skill-runner 执行面（SandboxExecutor 沙箱 / LocalExecutor 进程内 / K8sExecutor 每会话一 Pod；SkillBundle 制品装载）。Skill 生命周期：publish → review → version → index → retrieve → download → run。Skill 制品模型：ZIP + SKILL.md + plugin.yaml + artifact_sha256 + plugin_type。LLM 代理与预算：per-session token、llm_proxy 兑换真实 key、UserBudgetStore 日预算，真实 LLM key 永不离开控制面。skill-runner 是唯一 import openjiuwen 的组件，把 Skill 跑成 DeepAgent/TeamAgent。

#### 3.2.3 skill → workflow.md → workflow.py 执行链路

- skill 里定义 workflow.md：声明各种子 agent，每个子 agent 带自己的上下文、可用 skill、可用工具
- 框架在条件满足时根据 workflow.md 生成可执行的 workflow.py 并执行
- workflow.py 里可有自定义机制（各类自定义流程和反馈处理）

**Swarm Skill 生命周期两阶段**：

- 生成（jiuwenswarm 的 swarmskill-creator 模板生成五件套）：SKILL.md（入口）+ roles/*.md（角色定义）+ workflow.md（人读流程）+ bind.md（规则约束）+ dependencies.yaml（依赖清单）+ scripts/workflow.py（可执行脚本）
- 执行（agent-core 的 swarmflow 引擎加载 workflow.py）：ast 提取 META → importlib 导入取 run 函数；contextvar 注入 Runtime

**Skill 生命周期全景**：① 装进来（4 来源）→ ② 落到 skills/ 文件夹 → ③ 系统发现（扫描 SKILL.md）→ ④ 挂到 Agent 上（SkillUseRail）→ ⑤ 被调用（直接调/编排/自己找）→ ⑥ 执行（沙箱或本地）→ ⑦ 越用越准（进化调权重）。

**Skill 调用路径**（7 种）：Symphony 编排（系统自动从关系网规划链）/ Agent 自己逛技能树（agentic retrieval 不调 LLM）/ 直接调 skill_tool（skill_mode=all 每个技能注册成工具）/ list_skill 查（skill_mode=auto_list）/ search_skill 外部找（去云端搜→安装→刷新→重试）/ 多智能体各自调（Swarm 团队协作每成员按角色认领）/ 子 agent 调 skill（独立 SkillUseRail，enabled_skills 限定可见技能）。

**worker 派生机制**：每个 agent() 临时造一个 worker（从 teammate spec 派生），跑完销毁不进名册；skills 完全照搬、tools 只加不减。节点级 skill 加载是路线图缺口（_ENGINE_OPTIONS 无 skills/tools/work_dir）。

#### 3.2.4 swarmflow 原语底层实现

核心结论是原语完全复用 agent-core 框架——agent() 造的 worker 就是 DeepAgent，跑 ReActAgent 迭代循环（思考→工具→观察→再思考），能迭代、能循环、能规划 todo。

**Swarmflow DSL 原语**（engine/primitives.py）：

| 原语 | 作用 | 语义 |
|---|---|---|
| agent(prompt, *, label, phase, schema, options) | 单 agent 节点跑一次 | 节点=临时铸一个 worker |
| agent_session / human_session | 有状态多轮会话 | 保活多轮，跨轮保留上下文 |
| human | agent + 真人输入 | avatar 把真人输入格式化 |
| parallel(thunks) | fork-join 并行屏障 | 等全部完成才返回 |
| pipeline(items, *stages) | 无屏障流式 | item 间不阻塞 |
| map_parallel / pmap | 并行映射 | — |
| phase / log | 阶段标记 / 日志 | 进度事件 |
| workflow(name_or_path, args) | 内联子工作流 | 深度限 1 |
| budget / compact / flatten_filter | 预算 / 结果整理 | — |

**并发治理（三层 L1/L2/L3）**：L1 max_workflows=16（同时 run 数，超限立即拒绝）/ L2 agents_per_run=None→min(16,cpu-2)（单 run 内并发，超限阻塞，每 run 独立 Semaphore）/ L3 max_agents_total=64（全局 agent 并发，超限阻塞，共享 global sem）。RunAgentAdmission.acquire() 先 L2 后 L3，退出逆序释放。

**Token 预算（F_66）**：BudgetLedger 取代旧不可变 int；SwarmflowBudgetRail 挂每个 worker/avatar；after_model_call 记真实 token（来自 usage_metadata 不估算）；超预算 force_finish 就地停，before_model_call 挡付不起的调用；账本是 leader 级（非 run 级），跨主循环+所有工作流共享；真实数字不猜：provider 不报就记 0。

**Journal 断点续传**：落盘路径 {team_home}/sessions/{session_id}/workflows/{workflow_name}/journal.jsonl；resume 命中前缀续跑，不重跑已完成的 agent()；WorkflowAborted 是 BaseException，穿透 parallel/pipeline 的 except Exception；pause 三步停（engine abort_event → TeamWorkerBackend.abort_sessions → AvatarSessionManager.abort_all → 顶层 task cancel，WAL 保留）；resume 经 _relaunch(inputs, session_id) + set_session_id(原 session) + launch_async_tool。

能力支柱：编排表达力（串行/并行/流水线）+ agent 内部智能（ReAct+todo）+ 工程治理（journal 续跑+budget 预算+并发控制+错误隔离）。

**核心结论**：三套工作流互不相通（core 工作流组件图 PregelGraph / Swarmflow 命令式 Python DSL / Studio 可视化画布 JSON）；两种 workflow.py 都不能由单 agent 自动跑；workflow.md → workflow.py 不是自动转换（运行时只认 .py）。

#### 3.2.5 jiuwenswarm 运行时双进程

```
app.py (split layout) — 0.25s 轮询，任一子进程退出即全终止
├── Gateway 进程 (接入, 端口 19001)
│   ├── GatewayServer (WS 服务端): RouteConfig 路由 / X-User-Id 握手 / SESSION_IN_USE 守卫
│   ├── AgentServerClient: request_id 多路复用 / per-rid 队列 / send_lock 串行发送
│   ├── MessageHandler (双队列): _user_messages 入 / _robot_messages 出 / E2A 双向规范化
│   ├── ChannelManager: 9 IM 渠道 + ACP/A2A/SSH / fan_out 多目标分发
│   └── RoutingKey 5 维: (user_id, channel_id, app_id, agent_ref, session_id)
│       ├── SessionSharingRegistry (1:N 订阅, 纯内存)
│       └── SessionMap (1:1 映射, 落盘)
└── AgentServer 进程 (运行, 端口 18092)
    ├── AgentWebSocketServer: 三层降级解析 / send_lock 串行化
    ├── AgentManager (三层并发): reload 全局锁 / per-key 创建锁 / borrower+pin
    ├── SessionManager (PriorityQueue): 同 session 串行 / 一次性 session 哨兵回收 / ContextVar 快照
    ├── JiuWenSwarm facade: create_instance / process_message_stream 漏斗路由
    └── harness 三模式: claw / code / team
```

端到端调用链（19 步，IM 群聊数字分身为例）：IM 平台发消息 → ChannelManager → MessageHandler → _forward_loop（7 步固定顺序）→ AgentServerClient.send_request → E2A over WebSocket → AgentWebSocketServer → req_method 路由 → _handle_stream → AgentManager.get_agent（cache key 四元组）→ JiuWenSwarm.process_message_stream（漏斗路由）→ adapter.process_message_stream_impl → 权限拦截 → 流式 chunk 生产 → send_wire_payload 有界发送 → 响应回推 → MessageHandler → ChannelManager → IMOutboundPipeline → IM 平台。

关键设计决策（10 条）：split layout、request_id 多路复用、Agent 三层并发、同 session 串行+新任务优先、漏斗式请求路由、E2A 协议中性信封、三模式 leader 去 todo、分布式降级友好、tiered_policy 取更严、有界发送+降级保路由。

### 3.3 4 角色流水线架构

**PPT-Agentskill**（仓库 gitcode.com/hellokitty911/ppt-pipeline-swarm/tree/ppt_agent，fork: gitcode.com/int2t/ppt-pipeline-swarm）：在九问 agent-core/swarm 上实现的"PPT 制作专家 Agent"——4 角色专门化流水线（C-pattern pipeline），把文档或主题转成可编辑 .pptx。

**4 角色 Pipeline**：

| 角色              | kind     | 职责                                                                             | tools                         |
| ----------------- | -------- | -------------------------------------------------------------------------------- | ----------------------------- |
| attachment-reader | ai_agent | MinerU-first 引擎提取结构化内容（PDF/DOCX/PPTX/XLSX/图像），自动 fallback 本地库 | python                        |
| ppt-planner       | ai_agent | 设计大纲结构 + 需求对齐，产出 outline.json（含 alignment + slides）              | python                        |
| ppt-researcher    | ai_agent | 调研信息 / 组织视觉素材 / 写带配图的 Markdown 文稿，语义 alt + 本地图片引用      | python, curl                  |
| ppt-designer      | ai_agent | 把文稿转成视觉平衡的 HTML 幻灯片 + 逐页 QA + 生成最终 .pptx（带 PDF 备份）       | python, node, npm, playwright |

**单一失败模式**：单 agent PPT 生成产出浅、未校验、视觉不一致——一个 agent 无法同时精通文档提取、结构规划、深度研究与视觉设计。Pipeline 强制专门化、校验、用户确认检查点。

**产物链路（路径契约，全链路硬校验）**：

```
{workspace}/
├── attachments/<stem>/<stem>.md      ← attachment-reader
├── attachments/<stem>/overview.json  ← planner parse_document
├── outline.json                      ← planner finalize 校验在 workspace 根
├── manuscript.md                     ← researcher finalize_check 校验在 workspace 根
├── .manuscript.md                    ← researcher 备份
├── images/                           ← researcher 产物
├── slides/                           ← designer finalize 校验
│   ├── global.css
│   ├── slide_XX.html
│   └── .inspect/slide_XX.jpg         ← inspect_slide 留痕
├── output.pptx                       ← designer build_deck
└── output.pdf                        ← PDF 备份
```

**双层质量保证**：

| 角色       | 脚本硬校验（结构）                                                                                                                                                   | LLM 自审（语义）                                               |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| planner    | finalize.py：JSON 结构 / 字段白名单 / index 连续 / visual_role 枚举 / page_count==slides 交叉校验                                                                    | self-check.md：主题清晰、逻辑流、标题质量、无占位页            |
| researcher | inspect_manuscript.py + finalize_check.py：页数 / 外链 / 缺图 / 缺 alt / 未用图 / 表格忠实度                                                                         | self-check.md：内容纯净、语言一致、图表存在性/准确性、数据落点 |
| designer   | inspect_slide.py（逐页）+ finalize.py + build_deck.py + verify_deck.py：字数上限 / 裸 LaTeX / 字体安全 / 栅格化 / 字号下限 / page-type / 公式占位符残留 / shape 重叠 | self-check.md：设计一致性、视觉平衡、字号、公式渲染            |

**C-pattern 隔离规则**：每阶段不得修改上游产物，只增强/标注。

**编排模式**：Markdown-spec swarm-skill——无 scripts/workflow.py，kind: swarm-skill 仅声明结构，手动 build_team 编排。Leader 用三个工具手动编排：build_team → spawn_teammate × 4 → create_task（含 depends_on）。Leader-as-orchestrator only——不执行阶段脚本、不写内容、不替任何阶段干活。

### 3.4 研究员角色开发

**Identity**：内容大脑——调研、写文稿、自审，产出信息美学 Markdown 文档，其中原生表格和公式保持可编辑；图片靠承载信息挣位置，不靠填空。

**五步工作流**：① 研究信息 → ② 组织视觉资产 → ③ 写文稿 → ④ 自审 → ⑤ 收尾

**落地内容**：

- roles/ppt-researcher.md：角色定义（Identity / Success Criteria / Boundary / Output Schema / Inline Persona）
- Content Style 段（v2 看齐）：one core insight per slide + pyramid principle + bold sparingly + credible sources first
- Native Structure Preservation 段：HTML/LaTeX 原样保留，tableN/chartN 不进 images/
- Visual Asset Strategy 段：图片即内容/选择性复用/信息图优先
- inspect_manuscript.py 告警扩展：table_page_with_image（页含 table 又配 img）+ alt_topic_mismatch（alt 与标题零关键词重叠）+ adjacent_duplicate_ref（相邻页同图 high 硬阻断）
- finalize_check.py 硬门禁：12 条 errors（路径契约/无外链/图片存在/images 一致/表格忠实度 4 条）
- table_checks.py：表格忠实度校验 Layer A 占位检测 + Layer B 附件比对
- rewrite_image_links.py：相对→绝对 + alt 追加宽高比（GCD 化简如 1920×1080→16:9）+ 无条件备份
- 数据落点自审：关键数值后必须补判断（含义/业务影响/管理启示三选一），靠提示词 + 步骤④ Self-Refine
- math-recognition.md：LaTeX 公式识别决策表（9 类 + 9 步决策树 + 10 反模式）
- formula_checks.py：公式合规校验（拦截 \text{}/\operatorname{} 等内多字母词违规，high 级硬阻断）

**MUST 规则**：至少 1 轮 web search（即使有上游文档）；读 outline.alignment（source_fidelity/audience/objective/content_scope）；读每页 visual_role/density/anti_pattern；保留原生 HTML table + LaTeX；按 math-recognition.md 决策表包裹公式；每页围绕一个核心洞察，金字塔原则开头；每个关键数字必须落点；数值一致性自审（反算 (a-b)/b 再写"X% higher"）；优先可信源；相邻页不同图。

### 3.5 .trace/ 可观察性体系

**痛点**：多 agent 工作流跑起来后，最大的痛点是看不见里面发生了什么——workflow 卡住时不知道停在哪一步、哪个 agent；子 agent 返回什么、审批是否触发、串行还是并行都只能靠最终产物反推；调试和审计没有抓手。

**核心方案**：在 {workspace}/.trace/ 下按阶段编号落盘每个 agent 的完整返回，附 manifest.json 做最终审计汇总。

```
{workspace}/.trace/
├── 00_init.json                      # Init: tier/viewport/cfg
├── 01_research.json                  # Researcher 完整返回
├── 02_outline_approval.json          # HITL 审批结果(或 skipped)
├── 03_design.json                    # Designer 返回
├── 04_generation/
│   ├── presenter_serial.json         # 串行模式
│   └── presenter_01_04.json          # 并行 chunk(页范围)
├── 05_review.json                    # Review 汇总(verdict)
├── 05_review_critic/
│   ├── slide_01.json ... slide_NN.json   # 每页 Critic
│   └── arbiter.json                  # Arbiter(thorough)
├── 06_revision.json                  # Revision 汇总(final_verdict)
├── 06_revision/
│   ├── round_01_reviser.json
│   ├── round_01_critic_slide_NN.json
│   └── round_01_verdict.json ... round_03_verdict.json
├── 07_export_approval.json           # HITL(或 skipped)
├── 08_export.json                    # Exporter 返回
├── 08_export_finalize/
│   └── finalize_slide_NN.json        # 终检每页
└── manifest.json                     # 最终汇总(完整审计)
```

**实现**：新增 write_trace(workspace, name, data, subdir="") helper（写 JSON，default=str 容错）；在 run() 的 9 个阶段边界 + 各子函数 agent 调用后插入 write_trace。

**关键约束**：只读地旁路写 trace，不改变任何控制流、schemas、原语调用。trace 写在 args.workspace（运行时工作目录），不写 skill 目录——多场景复跑互不污染。

**验证结果**：validator 0 error、4 warning；stubbed 测试全过（write_trace 写文件 ✓、default=str 容错 ✓、原有 helper ✓）。

**9 阶段流水线**：Init → Researcher → Outline Approval(HITL) → Designer → Generation(串行/并行) → Review(每页 Critic + Arbiter) → Revision(多轮 Reviser + 复检) → Export Approval(HITL) → Exporter(终检)。

### 3.6 PPTv2agent 参考

**PPTv2agent = PPTAgent v2 = DeepPresenter**：PPTAgent（EMNLP2025，icip-cas/PPTAgent）的 v2 版本，ACL2026 SOTA。源项目在 D:\Project\Agent\PPTAgent。

**学术地位**：PPTEval Avg 3.67（vs DocPres 2.87），与人类偏好 Pearson 0.71；DeepPresenter Avg 4.44 超 SOTA 商业系统 Gamma(4.36)；9B 版 4.19 逼近 GPT-5(4.22)。架构：Researcher + Presenter 双 agent 共享 observation space + 环境接地反思（渲染成像素图反馈）+ ReAct。

**核心 Content Style Guidelines（5 条，v2 看齐对象）**：

1. Pursue Information Aesthetics：信息加工成半成品而非原材料；图片与文字同等重要作为内容载体；优先信息图呈现结构/流程/对比，成为每页视觉焦点
2. Each slide revolves around one core insight：通过深度分析提炼高价值结论，合理布局与分段组织信息
3. Bold only first occurrences of terminology and key conclusions；金字塔原则，每页以强有力的主题句领起
4. Images as Content：图片基于页面内容的高层抽象和核心隐喻；禁止无意义插图或通用商务占位图
5. Prioritize credible sources（arxiv/wikipedia/官方/权威媒体），优先真实高质量图片资产

**与 PPT-Agentskill 的关系**：PPTAgent v2 是学术参考方法论，PPT-Agentskill 是在九问平台上落地的工程实现。feat-native-preserve-v2 分支把 PPTAgent v2 的 Content Style 看齐进 researcher/designer 提示词层。

**PPTAgent 框架解析要点**（docs/research/PPTAgent框架解析.md）：

- 双代码路径：v1 pptagent/（EMNLP 2025，模板编辑）+ v2 deeppresenter/（ACL 2026，HTML→PPTX），v1 作为 v2 的 MCP 工具服务器保留
- v2 主流程：Planner→Research→Design/PPTAgent 三阶段串行，自定义 ReAct Agent（非 LangChain），OpenAI tool-calling 循环 + compact_history 上下文折叠
- 7 个 MCP server（any2markdown/search/task/deeppresenter/tool_agents/pptagent/sandbox）+ Docker-in-Docker sandbox 隔离
- 本地 ppt-pipeline-swarm 的 designer 脚本源自 PPTAgent v2，提取并重写为独立 CLI

#### 3.6.1 PPTAgent v2 源码深挖

**版本信息**：包名 pptagent，Python ≥3.11，MIT，版本 1.1.37。两个 console scripts：pptagent = deeppresenter.cli:main（v2）/ pptagent-mcp = pptagent.mcp_server:main（v1）。平台 Linux/macOS（不支持 Windows，__init__.py 强制 os.name == "posix"）。

**main.py AgentLoop 串行调度三阶段**：AgentLoop.run(request) 是 async generator，串行调度：

```
InputRequest(指令+附件+页数+aspect+convert_type+enable_planner)
[1] Planner（可选, enable_planner=True）：research_agent 模型 + 全工具 → 生成 outline.json {slides:[{index,title,context}]} → yield outline → CLI _edit_outline 交互修订(.asend)
[2] Research（必跑）：research_agent 模型 + 全工具(除 pptagent/inspect_slide) → 接收 outline_path → 按 --- 分页写 manuscript.md → 深度检索(search_web/fetch_url/convert_to_markdown/image_generation/image_caption) → finalize → task.py 重写图片链接
[3] 分支 convert_type：
    PPTAGENT → PPTAgent agent(模板化,走 pptagent-mcp)→ *.pptx
    DEEPPRESENTER(默认)→ Design agent(design_agent 模型 + sandbox + delegate_subagent/inspect_slide/finalize) → 生成 slides/global.css + slides/slide_XX.html(逐页 inspect_slide 反思) → convert_html_to_pptx → *.pptx（失败 fallback PlaywrightConverter.convert_to_pdf → *.pdf）
```

关键编排细节：AgentEnv 作为 async with 上下文，入口杀同名 sandbox 容器；multiagent_mode 时注册 SubAgent.delegate 为本地工具；每阶段 finally 调 save_history() + save_results()（写 intermediate_output.json）；convert_html_to_pptx 标注 "experimental stage"。

**Agent 基类（自定义 ReAct，非 LangChain）**：加载 roles/{ClassName}.yaml → RoleConfig；按 toolset 从 AgentEnv 装配工具（_setup_toolset）。

- action() — ReAct 一步：渲染 instruction 进 chat_history（Jinja2 Template.render，StrictUndefined）→ 调 llm.run(messages, tools) → max_turns 检查（剩余<2 时插入"Finish the remaining work soon and call finalize immediately"）
- execute(tool_calls) — 并行执行：asyncio.gather 并行执行所有 tool_calls；识别 finalize（outcome 参数）→ 返回 str 终止循环；上下文预算 50%/80% 两级警告（HALF_BUDGET_NOTICE_MSG / URGENT_BUDGET_NOTICE_MSG）；超上下文窗口时调 compact_history()；MAX_TOOLCALL_PER_TURN=7 限制每轮最大工具调用数
- compact_history() — 上下文折叠：保留 head(10 条) + tail(4 条)；中间历史喂 LLM 生成结构化摘要替换；research_iter 计数，最多 max_context_folds（默认 5）次；摘要要求 5 部分（Collected Information / Uncertainties / Generated Artifacts / Next Steps / Lessons Learned）；摘要后追加 CONTINUE_MSG + 最后一次追加 LAST_ITER_MSG
- save_history() — 历史持久化：jsonlines 写 .history/{name}-{iter:02d}-history.jsonl；config JSON 写 .history/{name}-config.json；error_history 写 .history/{name}-errors.jsonl

**5 个 Role 配置**（roles/*.yaml）：

| Role | use_model | toolset | 运行时注入 | 产物 |
|---|---|---|---|---|
| Planner | research_agent | all 除 tool_agents/deeppresenter；除 search_images | 无（无 sandbox，无注入） | outline.json |
| Research | research_agent | all 除 pptagent；除 inspect_slide | + MA_RESEACHER_PROMPT（multiagent 时） | manuscript.md |
| Design | design_agent | sandbox + delegate_subagent/inspect_slide/finalize | + AGENT_PROMPT + MA_RRESENTER_PROMPT | slides/slide_XX.html + global.css |
| PPTAgent | research_agent | pptagent + sandbox + finalize | + AGENT_PROMPT | *.pptx |
| SubAgent | design_agent | all 除 pptagent/delegate_subagent | + AGENT_PROMPT | 文件路径 |

**AgentEnv — 工具环境 + Sandbox**：MCP 客户端读 mcp.json → MCPServer 列表，__aenter__ 并行 connect_server；工具注册进 _tools_dict/_server_tools/_tool_to_server；offline_mode 跳过 network=true 的 server。Docker sandbox：docker.from_env()，同名容器 force remove 后重建，Docker-in-Docker 支持（HOST_WORKSPACE 映射）。tool_execute()：jsonschema 校验参数 → 执行 → 结果截断（TOOL_CUTOFF_LEN=4096，超长写本地文件+CUTOFF_WARNING）→ ChatMessage；记 timing_dict；async_tool_mode 慢工具超 5s 转后台 task 返回 task_id。register_tool() 本地 Python callable 注册为工具（fastmcp 自动生成 JSON Schema）。

**7 个 MCP Server**：

| Server | 工具 | 职责 |
|---|---|---|
| any2markdown | convert_to_markdown | PDF/docx→md；PDF 优先 MinerU，否则 MarkItDown；base64 图片落地 |
| search | search_web/search_images/fetch_url/download_file | SerpAPI 或 Tavily；fetch_url 用 Playwright 渲染+trafilatura 提取；network: true |
| task | finalize | 终止 agent 循环+按 agent 类型校验产物 |
| deeppresenter | inspect_slide/inspect_manuscript | inspect_slide: HTML→pptx 校验，heavy_reflect 返回渲染 jpg；inspect_manuscript: 页数/语言/图片/alt/重复 |
| tool_agents | image_generation/image_caption/document_summary | t2i/vision caption/长文档摘要 |
| pptagent | list_templates/create_presentation 等 | v1 模板化 pptx 生成 |
| sandbox | read_file/write_file/edit_file/execute_command 等 | DesktopCommanderMCP fork；容器隔离；config.json 黑名单命令 |

**config.yaml 配置项**：context_folding（上下文折叠）/ offline_mode（离线禁用 network server）/ async_tool_mode（慢工具异步化 5s 转后台）/ multiagent_mode（多 agent 实验性）/ context_window（默认 200000//5=40000）/ max_context_folds=5 / heavy_reflect（重反思用渲染 slide 图，需多模态 design_agent）/ research_agent（claude-sonnet-4.5 @ openrouter）/ design_agent（gemini-3-pro-preview @ openrouter）/ long_context_model / vision_model / t2i_model / provider（openai/litellm 路由 100+ provider）。

**SubAgent 委派机制**：delegate_subagent(short, task, context_file) — short 短唯一任务 id，task 最小动作指令，context_file 完整委托上下文文件路径。隔离：空上下文（不继承父 agent）、独立 workspace、max_turns=10。防递归：SubAgent toolset 排除 delegate_subagent。

#### 3.6.2 PPTAgent 提示词体系

**提示词体系结构**：

```
最终 system prompt = role.yaml 的 system[zh|en]
                   + (含 execute_command ? AGENT_PROMPT :)
                   + (含 delegate_subagent & Research ? MA_RESEACHER_PROMPT :)
                   + (含 delegate_subagent & Design  ? MA_RRESENTER_PROMPT :)
                   + (offline_mode ? OFFLINE_PROMPT :)
                   + (context_folding ? CONTEXT_MODE_PROMPT :)
```

instruction 字段是 Jinja2 模板，每轮 action() 时用 Template(instruction).render(**context) 渲染后拼进 chat_history。

**5 个 Role system prompt 要点**：

- Planner：专业演示文稿大纲规划专家；理解需求→背景调研→设计大纲（开篇/主体/结尾）→JSON 输出（index/title/context）→写入 JSON 文件→finalize；不生成幻灯片内容本身；8-20 页
- Research：专业幻灯片内容专家，践行信息美学；信息研究→视觉素材组织→Markdown 文稿（--- 分页）→inspect_manuscript 审查→finalize；"由宽到窄""由粗到细"检索策略；严禁虚构；Content Style 5 条
- Design：专业幻灯片视觉设计专家，HTML/CSS 固定版式；理解文稿→制定 global.css→逐页生成 HTML→每页 inspect_slide 质量检查→finalize；固定尺寸 16:9=1280x720，字号≥18px，文本须包裹 p/li/span，行内元素禁 margin/border/shadow，仅跨平台安全字体
- PPTAgent：专业幻灯片制作专家，根据 Markdown 调用工具生成多页忠实还原的幻灯片；markdown 表格不能直接输入要用工具生成表格图片
- SubAgent：通用子智能体，完成主智能体委派的一个独立子任务；不继承主智能体上下文；task 只是最小动作指令；先写入本地文件再 finalize

**运行时注入的 Prompt 常量**（utils/constants.py）：

- AGENT_PROMPT（含 sandbox 的 role 注入）：触发于工具集含 execute_command 的 role（Design/PPTAgent/SubAgent）。含 Environment（时间/工作目录/平台/预装工具）、Task Guidelines（探索原则 10% 剩余预算告警、工具调用输出超 cutoff_len 截断、每轮最多 max_toolcall_per_turn 工具并行、每响应须含推理+工具调用）
- MA_RESEACHER_PROMPT（Research + multiagent_mode 注入）：指导 Research 用子 agent 并行多视角/长文档分片研究。两场景示例（长文档 20000 行分 20 子 agent 各 1000 行；多视角检索一个主体从多方面分析）
- MA_RRESENTER_PROMPT（Design + multiagent_mode 注入）：指导 Design ≥3 页时先定全局视觉系统再并行生成；<3 页逐页生成+inspect_slide 检查
- OFFLINE_PROMPT：离线模式无互联网，network 工具已移除，聚焦可用工具
- CONTEXT_MODE_PROMPT：有限工作上下文，接近限制时被要求压缩历史为本地摘要，尽量保存文件/图片/中间结果，压缩后只留首尾消息+摘要
- 运行时预算通知：HALF_BUDGET_NOTICE_MSG（50% 已用约半，聚焦核心任务）/ URGENT_BUDGET_NOTICE_MSG（80% 预算近尽，必须完成核心任务并立即 finalize）/ HIST_LOST_MSG（历史已压缩）/ CONTINUE_MSG（历史已压缩，参考摘要继续）/ LAST_ITER_MSG（预算近尽，必须 finalize）

**注入规则总表**：

| Role | AGENT_PROMPT | MA_RESEACHER | MA_RRESENTER | OFFLINE | CONTEXT_MODE | 触发条件 |
|---|:---:|:---:|:---:|:---:|:---:|---|
| Planner | — | — | — | ✓ | ✓ | 无 sandbox/delegate |
| Research | — | ✓(MA) | — | ✓ | ✓ | multiagent_mode 时有 delegate_subagent |
| Design | ✓ | — | ✓(MA) | ✓ | ✓ | sandbox + multiagent 时 delegate |
| PPTAgent | ✓ | — | — | ✓ | ✓ | sandbox |
| SubAgent | ✓ | — | — | ✓ | ✓ | sandbox |

> MA_* 两列仅在 multiagent_mode=True 时生效。OFFLINE/CONTEXT_MODE 两列仅在对应 config 开关开启时生效。

### 3.7 框架比较

#### 与标准 swarm-skill 的关键差异

| 维度         | 标准 swarm-skill                                                                   | ppt-pipeline-swarm                                                                                         |
| ------------ | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 编排模式     | swarmflow 工具加载 scripts/workflow.py 跑原语                                      | Markdown-spec：无 workflow.py，手动 build_team 编排                                                        |
| 文件结构     | SKILL.md + roles + workflow.md + bind.md + dependencies.yaml + scripts/workflow.py | 同上但无 workflow.py——swarmflow 工具未注册                                                               |
| Leader 角色  | swarmflow 引擎跑 workflow.py                                                       | Leader 用三个工具手动编排：build_team → spawn_teammate × 4 → create_task                                |
| Task content | workflow.py 原语编排                                                               | 7 要素模板：目标 / Input / Workspace / Swarm skill directory / Action / Quality gate / Forbidden           |
| HITL         | human/human_session 原语                                                           | HITL Relay 协议：teammate send_message(leader) 加 [HITL-RELAY] 前缀 → Leader MUST 调 ask_user → 回传答案 |
| 质量门       | workflow.py 内嵌                                                                   | 脚本硬校验 + LLM 自审双层                                                                                  |

原因：enable_swarmflow:false 门控（Markdown-spec 无 workflow.py）。

#### 与 PPTv2agent 的分工

| 项       | PPTv2agent（学术参考）                                  | PPT-Agentskill（落地实现）                                                     |
| -------- | ------------------------------------------------------- | ------------------------------------------------------------------------------ |
| 形态     | 论文方法（DeepPresenter Researcher+Presenter 双 agent） | 九问平台上的 swarm-skill（4 角色流水线）                                       |
| 编排     | ReAct + 环境接地反思                                    | build_team + 4 角色 spawn + task 依赖链                                        |
| 反思机制 | 渲染像素图反馈                                          | inspect_slide.py + heavy 视觉渲染 + verify_deck 终态校验                       |
| 评测     | 自建多维（Cons/Content/Style）                          | PresentBench material_independent 30 项 + SlidesGen-Bench PEI 编辑性           |
| 导出     | —                                                      | HTML→PPTX（html2pptx.js + Playwright DOM 提取 + PptxGenJS）+ 公式 OMML 后处理 |
| 内容风格 | Content Style 5 条                                      | 看齐 v2 + researcher.md Content Style 段                                       |

#### 4 种流水线组装方式对比（docs/research/PPT流水线组装方式选择.md）

四种方式：单 agent 自包含（最省心）/ swarmflow 编排（可观测+可续跑+可预算）/ 集群团队（成员持久复用）/ 链接原 skill（独立维护）。已实现形态：ppt-pipeline（单 agent 自包含）+ ppt-pipeline-swarm（swarmflow 编排）。推荐按场景选：固定流水线+断点续跑→swarmflow；一个人用+流程灵活→单 agent 自包含。

#### 27 个 PPT 方案调研分级

调研 27 个开源 PPT 生成方案，分 S/A/B/C 四层：

**S 层 · 九问首选参考（直接借鉴架构）**：

| 方案 | 定位 | 可借鉴点 |
|---|---|---|
| DeepPresenter（ACL2026 SOTA） | Researcher + Presenter 双智能体共享 observation space + 环境接地反思（渲染像素图反馈）；Avg 4.44 超 Gamma(4.36)；9B 版 4.19 逼近 GPT-5(4.22)；Diversity 0.79 远超模板基线 0.17-0.35；消融 w/o 环境接地反思 9B 降至 3.82，w/o 双 agent 降至 3.23 | 双 agent + 环境接地反思骨架；inspect 工具暴露渲染后感知状态；extrinsic verification 抑制自验证偏差 |
| ppt-master（41.5k★ MIT） | AI 逐页生成 SVG → 转换器 → 原生 DrawingML .pptx（形状/母版/图表/动画/旁白）；agent skill 形态接入 Claude Code/Cursor/Codex；三承诺（成本透明/数据不出本地/不锁平台） | SVG→DrawingML 管线（1:1 矢量映射）；skill 形态接入 jiuwenswarm；母版/版式继承；音频旁白/视频导出 |
| SLIDEGEN/Paper2Slide（2025-12） | 模块化 visual-in-the-loop 多智能体 paper-to-slide；6 智能体（Outliner/Mapper/Formulizer/Speaker/Arranger/Refiner）；DOCLING+MARKER 预处理；19 布局模板；SlideQA 73.56 vs PPTAgent 55.22；GAD 92.25 vs 56.93 | 6 智能体分工映射 jiuwenswarm 技能编排；19 布局模板 + GAD 自动校验；输出格式合规 Rail |

**A 层 · 强参考 / 可集成组件**：

| 方案 | 定位 | 可借鉴点 |
|---|---|---|
| presenton（9.2k★） | 生产级开源 AI 演示文稿生成器，Gamma/Canva 自托管替代；Next.js + FastAPI + Electron + Docker；16 家 LLM（含 Ollama/LM Studio）；REST API + 内置 MCP Server；HTML+Tailwind 模板；AI Template Generation；Mem0 记忆 | Docker 部署后经 REST/MCP 被 swarm 调用；16 家 LLM 接入范式 |
| PPTAgent（EMNLP2025） | 两阶段 edit-based——先分析参考 PPT 提取功能类型与内容 schema，再起草大纲迭代生成编辑动作改造参考页；5 个编辑 API；PPTEval Content/Design/Coherence 三维 Pearson 0.71 | 适合"有参考 PPT"分支模式；PPTEval 评测框架 |
| AutoPresent（CVPR2025） | 自然语言指令→Python 程序→执行生成 PPTX；SLIDESLIB 7 函数（程序从 170 行压缩到 13 行）；7k 指令-代码对 LoRA 微调 Llama-3.1-8B，8B 逼近 GPT-4o | NL→Code→PPTX 映射 WorkflowAgent"生成→渲染→反思→修订"；SLIDESLIB 高层封装降复杂度 |
| LandPPT（3.5k★） | LLM 智能演示文稿生成平台，HTML 原生形态；四阶段工作流（需求确认→大纲→任务追踪→PPT 生成）；按角色路由模型；MinerU+MarkItDown 解析；Tavily+SearXNG 深度研究；Edge-TTS 讲解视频 | 与九问 WorkflowAgent/Provider 机制高度对齐，最佳架构参考 |
| banana-slides（15.3k★） | nano banana pro 多模态直出图片型 PPT + Vibe PPT 区域口头修改；框选编辑+局部重绘 | 多模态直出参考（AGPL-3.0 传染+模型依赖限制闭源集成） |

**B 层 · 输出后端 / 模板参考**：

| 方案 | 定位 | 可借鉴点 |
|---|---|---|
| python-pptx（3.5k★） | Python 生态生成/读取/更新可编辑 .pptx 事实标准；占位符/形状/图表/表格/母版/备注；不支持动画/SmartArt/3D；_element XML 逃逸口 | 事实标准（低维护，建议内部 fork 补丁层） |
| Marp（12.2k★） | Markdown→幻灯片生态最轻量可移植；导出 PPTX 为图片型不可编辑 | 仅作 PDF/HTML 交付或预览互补 |
| Slidev（47.8k★） | Vue3+Vite，工程化最强；导出 PPTX 为图片型不可编辑 | 仅作 PDF/HTML 交付或预览互补 |
| reveal.js（72k★） | 最流行 HTML 演示框架，不原生导 PPTX | 纯 Web 不涉及 PPTX |
| PPtYoda（32★） | 占位符+组件+容器模板系统；上传 .pptx 作母版；容器机制（max_n-x/direction-l-r/align-c） | 模板引擎设计参考 |
| LRriver-AIPPT（10★） | 可控端到端工作流 + 多模型角色分离（text/vlm/ocr/image/edit，全 OpenAI 兼容）+ 可编辑 PPTX | 多模型角色分离 |
| slide-deck-ai（363★） | LLM→JSON→python-pptx 五步 + LiteLLM 多供应商 + SSRF 校验；工程基础最牢 | LiteLLM 多供应商接入 |
| llm-pptx-deck-builder（4★） | LangGraph 6 节点 RAG + 反重复/思想校验/strict-lenient | 内容质量 Rail 与九问 WorkflowAgent/Rail 最对齐 |

**C 层 · 历史基线 / 轻量参考**：Doc2PPT（AAAI2022 层次化 seq2seq Bi-GRU pre-LLM 基线）/ veasion-AiPPT（GPL-3.0 原生图表/动画/3D 解析 PPT⇄JSON 双向）/ slides_generator（Sber GigaChat+Kandinsky-3 并行）/ Powerpointer（GPT-3.5+Flask 最小原型反面教材）/ odin-slides（Word→PPT 轻量 CLI）/ ai-ppt-slide-generator（FastAPI+Gemini 四端点）/ presentation-ai（ALLWEONE 商业产品开放窗口）。

**Benchmark 专题（5 个）**：

| Benchmark | 来源 | 规模 | 特点 |
|---|---|---|---|
| PresentBench | 清华 2026-03 | 238 例/5 领域/54 项 rubric | 5 维，Spearman 0.532，material_independent 30 条检查项 |
| SlidesGen-Bench | 港中文 2026-01 | PEI L0-L5 编辑性 | Spearman 0.71，九问可编辑 PPTX 差异化卖点 |
| SLIDESBench | Berkeley 2025 | 7k 训练/585 测试 | 单页从零生成，ICC 73.8%-85.3% |
| PPTEval | PPTAgent 论文 | Content/Design/Coherence 三维 | Pearson 0.71，MLLM-as-judge |
| Paper2Slide Benchmark | 2025-12 | GAD/SlideQA/VLM-as-Judge/PPL 四维 | GAD ρ=0.82 |

### 3.8 公式原生插入

#### 3.8.1 问题是什么

如何把 LaTeX 公式以原生可编辑 OMML 形式插入 PPTX，使其在 PowerPoint 双击可编辑 + WPS 可见，而非以图片形式插入（不可编辑）。

#### 3.8.2 为什么难（三大根因）

1. **python-pptx 不支持 OMML** — issue #528 自 2019 年至今 OPEN 无官方进展，无 PR 提交 OMML 注入代码
2. **PowerPoint 特有包装** — PowerPoint 需要 a14:m 包装器（Word 不需要），a14 命名空间 URI 必须是 schemas.microsoft.com/office/drawing/2010/main（之前方案用错成 openxmlformats.org/drawingml/2006/main）
3. **WPS 渲染兼容性陷阱** — WPS 演示：不渲染 m:sty=p（直立体属性，导致 \text{Area} 仍斜体）；不认 m:box 包装；不认缺 m:jc 时的 OOXML 默认 centerGroup（渲染为左对齐）；嵌套 xmlns 声明冗余干扰 WPS 解析；缺 Cambria Math 字体声明导致不显示

#### 3.8.3 方案演进（4 次迭代）

| # | 方案                                       | 结果                                                                            | commit            |
| - | ------------------------------------------ | ------------------------------------------------------------------------------- | ----------------- |
| 1 | KaTeX→PNG 图片（线上原方案）              | 全兼容但不可编辑，96KB（8 公式含 PNG），需 Node + Playwright 启动浏览器截图，慢 | 082821c           |
| 2 | latex2mathml + mathml2omml OMML            | WPS 不渲染（m:box 包装 + a14 命名空间 URI 错 + 嵌套 xmlns + 缺 Cambria Math）   | c6c57ad（已清除） |
| 3 | pandoc / MML2OMML.XSL                      | pandoc 150MB 太重；XSL 许可证不明                                               | 已排除            |
| 4 | banana-slides 手写 parser OMML（最终方案） | WPS 已验证可见，零新依赖，可编辑，32KB（26 公式纯 XML）                         | 本次产出          |

#### 3.8.4 最终方案（inject_omml.py）核心设计

**架构**：手写递归下降 LaTeX parser 直接生成 OMML XML（不经 MathML/XSLT 中间步骤）。

**全链路**（researcher → designer → build_deck）：

```
researcher 写 $...$/$$...$$ in manuscript.md
  ↓ （按 math-recognition.md 决策表判定哪些进 LaTeX、哪些纯文本）
designer 转 HTML data-latex 属性
  ↓ <span class="formula" data-latex="x^2" data-display="inline" data-font-size="28" data-color="#1A2230">
html2pptx.js collectFormulas 检测 data-latex
  ↓ 替换为占位符 FORMULA_PLACEHOLDER_N_M + 写 sidecar .formulas.json
     （记录 slide/placeholder/latex/display/font_size/color/align）
build_deck.py 调 inject_omml.py 后处理
  ↓ python-pptx oxml 层注入 OMML 到 <a:p> 段落
PPTX 公式为原生 OMML（PowerPoint 双击可编辑，WPS 可见）
```

**XML 结构**（WPS 已验证可见）：

```xml
<a:p>
  <a14:m xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main">
    <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      <m:oMath>
        <m:f>
          <m:fPr><m:type m:val="bar"/></m:fPr>
          <m:num><m:r><a:rPr lang="en-US" sz="2400"><a:latin typeface="Cambria Math"/></a:rPr><m:t>a</m:t></m:r></m:num>
          <m:den><m:r><a:rPr lang="en-US" sz="2400"><a:latin typeface="Cambria Math"/></a:rPr><m:t>b</m:t></m:r></m:den>
        </m:f>
      </m:oMath>
    </m:oMathPara>
  </a14:m>
  <a:endParaRPr sz="2400"/>
</a:p>
```

**关键设计决策**：

- a14 命名空间手动注册：_nsmap['a14'] = 'http://schemas.microsoft.com/office/drawing/2010/main'（python-pptx 不认识 a14）
- 不用 mc:AlternateContent——banana-slides 测试明确断言无 Fallback、无 p:pic、无 a:t
- 每个 m:r 加 a:rPr + Cambria Math 字体（DrawingML 命名空间，非 m:rPr）
- 清除 a:endParaRPr 后重建避免样式冲突
- block 公式显式 m:jc + 同步 pPr.algn——解决 WPS 不认默认 centerGroup 的坑
- 清零段落冗余 spcBef/spcAft——html2pptx 把 margin 映射成 paraSpaceBefore/After，但 shape 位置已含 margin 推移，双重计入致间距×2
- 不支持命令降级为友好文本（latex_to_display_text，如 \frac{a}{b}→(a)/(b)、\sqrt{x}→√(x)），非原始 LaTeX 源码（命令名可能泄漏如 \hat{y}→haty，已文档化）

**inject_omml.py 模块构成**（~470 行 Python）：

- _LatexOmmlParser：递归下降 parser（parse_expression/parse_group/parse_atom/parse_command/parse_scripts）
- OMML 构建函数：_fraction/_radical/_subscript/_superscript/_sub_sup/_text_command_run/_math_run/_coalesce_runs
- 注入逻辑：latex_to_omml/_apply_math_run_style/_wrap_powerpoint_math/find_and_replace_placeholders/inject_omml
- 字号/颜色降级链：data-font-size/data-color 显式 > 段内正文 > 同 shape 正文 > 同 slide 正文 > 18pt 兜底
- block 公式对齐：_resolve_block_align（data-align > pPr.algn > center）+ _sync_paragraph_align
- 段落间距清零：_zero_paragraph_spacing（修双重计入 bug）

**inject_omml.py 函数级模块构成**（~738 行，按职责分层）：

常量层：FORMULAS_SIDECAR_SUFFIX（sidecar 路径后缀）、_nsmap['a14']（python-pptx 不认识 a14 命名空间，手动注册）、M_NS/A_NS/A14_NS 三个命名空间 URI、LATEX_SYMBOLS（60+ 希腊字母/运算符/箭头 LaTeX→Unicode 映射，如 \alpha→α、\times→×、\leq→≤、\sum→∑）、LATEX_ESCAPES（转义命令映射，如 \%→%、\left→空、\quad→双空格）、_WRAPPER_PATTERNS（4 种数学分隔符正则 $$...$$/$...$/\[...\]/\(...\)）。

降级文本层：normalize_latex_math(source)（剥离 LaTeX 数学分隔符）、latex_to_display_text(source)（不支持命令的友好文本降级，非原始 LaTeX 源码；先替 \frac{a}{b}→(a)/(b) while 循环处理嵌套，\sqrt[n]{x}→√[n](x)，\arg\max→arg max，文字命令提取 {} 内容，先替 LATEX_ESCAPES 再替 LATEX_SYMBOLS 否则 \le→≤ 会子串腐蚀 \left 为 ≤ft，去剩余反斜杠命令；已知命令名可能泄漏如 \hat{y}→haty）。

递归下降 parser 层（_LatexOmmlParser 类）：_TEXT_COMMANDS（7 个文字命令集合 \text/\mathrm/\mathbf/\mathit/\mathbb/\mathcal/\operatorname，注释 WPS 不支持 m:sty 渲染故 parser 仅解析不降级不设 m:sty）、_FUNCTION_COMMANDS（9 个函数名 \arg→arg/\sin/\cos/\tan/\log/\ln/\lim/\min/\max）、parse()入口调 _parse_expression、_parse_expression(stop_chars)主循环（遍历字符，空格进 text_buffer，{触发 group 解析 + 检查后继 _/^，}/& break，否则 parse_atom + parse_scripts，最后 _coalesce_runs 合并连续 m:r）、_parse_group、_parse_atom（\→parse_command，{→parse_group，否则单字符 m:r）、_parse_command（\frac→_fraction，\sqrt→_radical 带[n]次数检测，文字命令→_text_command_run，\left/\right 透传，函数名→m:r，LATEX_SYMBOLS/ESCAPES→m:r，否则 raise _UnsupportedLatex）、_parse_scripts(base)（向前探查空格后 _/^，消费 subscript/superscript）、_parse_script_argument、_parse_required_group、_read_command、_skip_spaces/_peek/_expect 辅助。

OMML XML 构建函数层：_math_run(text)（创建 m:r + m:t）、_text_command_run(nodes)（text 命令内容合并为单 m:r 平铺，不用 m:e 分组——m:e 直接挂 m:oMath 下 WPS 不渲染；内容含非文字结构时返回空 run 兜底）、_append_children、_coalesce_runs（合并连续 m:r 文本减少碎片）、_wrap_as_group（创建 m:e 包装）、_child_container、_node_as_expression、_fraction(numerator,denominator)（m:f + m:fPr m:type val="bar" + m:num + m:den）、_radical(radicand,degree)（m:rad + m:radPr 无次数时 m:degHide val="1" + m:deg + m:e）、_subscript(base,subscript)（m:sSub + base + m:sub）、_superscript(base,superscript)（m:sSup + base + m:sup）、_sub_sup(base,subscript,superscript)（m:sSubSup + base + m:sub + m:sup）。

PPTX 注入层：latex_to_omml(source)入口（normalize → parser.parse() → 组装 m:oMath；失败返回 None，意外异常打 stderr 供诊断）、_apply_math_run_style(math_element,font_size=1800,color=None)（给每个 m:r 加 a:rPr lang/sz/kumimoji=0 + a:latin typeface="Cambria Math" + 可选 a:solidFill a:srgbClr/a:schemeClr；color 为 ('srgb',val) 或 ('scheme',val) 元组）、_wrap_powerpoint_math(math_element,display='block',align='center')（包装 OMML 为 a14:m > m:oMathPara > m:oMath（block）或 a14:m > m:oMath（inline）；block 公式必须显式写 m:oMathParaPr/m:jc）、_resolve_block_align（data-align > 段落 pPr.algn 推断 > center 默认）、_sync_paragraph_align(p,align)（同步段落 pPr.algn 与 m:jc 一致，PowerPoint 用 pPr.algn WPS 用 m:jc）、_zero_paragraph_spacing(p)（清零段落 a:pPr 的 a:spcBef/a:spcAft，修 html2pptx margin 双重计入）、_px_to_sz（CSS px → PPTX sz，1px=0.75pt，sz=px×75）、_normalize_color（hex→('srgb',val)，3 位简写扩展 6 位）、_read_surrounding_style（从 run 列表读首个有字号/有颜色的非占位符正文 run 样式）、find_and_replace_placeholders(slide,formulas)（在 slide 所有 shape 的 a:p 段落找占位符文本替换为 OMML；字号/颜色优先级 data-font-size/data-color 显式 > 段内正文 > 同 shape 正文 > 同 slide 正文 > 18pt 兜底；block 公式被 html2pptx 提取为独立 shape 时逐级回退；block 公式显式解析对齐 + 同步 pPr.algn + 清零段落冗余间距 + 同步 endParaRPr 字号）、inject_omml(pptx_path,sidecar_path)主入口（读 sidecar JSON 注入 OMML 返回注入数）、main() CLI 入口。

**WPS 兼容性 5 个陷阱各如何解决**：

1. m:box 包装（方案 2 失败原因）：mathml2omml 输出含 m:box 包装 PowerPoint/WPS 不认。解决：方案 3 手写 parser 直射 OMML 无 m:box。
2. a14 命名空间 URI 错误（方案 2 失败原因）：用了 openxmlformats.org/drawingml/2006/main，正确是 microsoft.com/office/drawing/2010/main。解决：方案 3 用正确 URI + _nsmap['a14'] 手动注册。
3. m:e 直接挂 m:oMath 下 WPS 不渲染（commit 6eefb75 修复）：\text{} 内容用 m:e 分组 WPS 不渲染。解决：_text_command_run 内容合并为单 m:r 平铺不用 m:e 分组；后跟上下标时 _parse_scripts → _node_as_expression 自动包 m:e 作 base。
4. WPS 不支持 m:sty 渲染（commit 6eefb75 + math-recognition.md）：\text{}/\operatorname{} 等在 OMML 规范里应让内容直立体 m:sty=p，但 WPS 演示不支持 m:sty 渲染（实测忽略，\text{Area} 的 Area 仍斜体）。解决：parser 仅解析这些命令（不降级、空格保留、不破坏渲染）但不设 m:sty；多字母词直立由 researcher 规范在源头用纯文本保证（math-recognition.md 决策表）；脚本硬阻断 \text{}/\operatorname{} 等内多字母词（finalize_check text_command_multi_letter）。
5. WPS 不认 m:oMathPara 缺 m:jc 时的 OOXML 默认 centerGroup（commit 0dacf7e 修复）：block 公式缺 m:jc 时 WPS 渲染为左对齐。解决：block 公式必须显式写 m:oMathParaPr/m:jc（_wrap_powerpoint_math）；对齐优先级 data-align > 段落 pPr.algn 推断 > center 默认（_resolve_block_align）；同步段落 pPr.algn 与 m:jc 一致（_sync_paragraph_align）；清零段落冗余间距（_zero_paragraph_spacing）。

#### 3.8.5 评估验证（test_omml_native.py 端到端）

| 测试项                                                                 | 结果                       |
| ---------------------------------------------------------------------- | -------------------------- |
| 8 种公式类型（分数/上标/根号/求和/mathcal/希腊字母/质能方程/求根公式） | 8/8 成功                   |
| manuscript.md 26 个公式                                                | 26/26 成功                 |
| PPTX XML 结构（oMath=52, a14:m=26, oMathPara=26, Cambria Math=84）     | 全部正确                   |
| WPS 可见性                                                             | 已确认                     |
| PPTX 文件大小                                                          | 32KB（vs KaTeX→PNG 96KB） |

vs KaTeX→PNG 全面优势：零新依赖 / 矢量（缩放不失真）/ 可编辑（PowerPoint 双击）/ 文件更小（32KB vs 96KB）/ 性能更好（纯内存 XML 构建 vs 启动浏览器截图）/ 纯 Python 无 Node 依赖。

#### 3.8.6 支持的 LaTeX 子集

| 类别                                 | 命令                                                           | OMML 元素                   |
| ------------------------------------ | -------------------------------------------------------------- | --------------------------- |
| 分数                                 | \frac{a}{b}                                                    | m:f (type=bar)              |
| 根号                                 | \sqrt{x}, \sqrt[n]{x}                                          | m:rad (degHide)             |
| 上下标                               | x_1, x^2, x_1^2                                                | m:sSub / m:sSup / m:sSubSup |
| 文字命令                             | \text/\mathrm/\mathbf/\mathit/\mathbb/\mathcal/\operatorname   | m:e（但 WPS 不渲染直立）    |
| 函数名（9 内置）                     | \arg/\sin/\cos/\tan/\log/\ln/\lim/\min/\max                    | m:r (text)                  |
| 大算子                               | \sum/\prod/\int                                                | m:r (Unicode)               |
| 60+ 希腊字母/运算符/箭头/集合/关系符 | 见 LATEX_SYMBOLS 映射表                                        | m:r (Unicode)               |
| 不支持（降级文本）                   | 矩阵 \begin{matrix}/方程组 \begin{aligned}/重音 \hat/\vec/\bar | 纯文本描述                  |

#### 3.8.7 配套产出

- math-recognition.md：LaTeX 公式识别决策表（9 类 + 9 步决策树 + 10 反模式），判定哪些数学性内容用 $...$、哪些纯文本
- formula_checks.py：公式合规校验（拦截 \text{}/\operatorname{} 等内多字母词违规，high 级硬阻断）
- 3 篇评估文档（docs/research/）：公式插入调研（8 项目对比）/ OMML 方案可行性评估 / 依赖组成深度评估（零新依赖证明）

#### 3.8.8 8 项目公式插入实现对比

| 项目 | 实现方式 | PPTX 形态 | LaTeX 支持 | WPS 兼容 | 可编辑 | 关键文件 |
|---|---|---|---|---|---|---|
| banana-slides | 手写 parser→OMML | 原生 OMML | 中等 | 不确定 | 是 | pptx_math.py, pptx_builder.py |
| ppt-master | 编译器 parser→AST→OMML | 原生 OMML | 广 | 承认不完美 | 是 | formula_compiler.py, formula_omml.py |
| SLIDEGEN | matplotlib/PDF 裁剪 | PNG 图片 | 依赖 matplotlib | 高 | 否 | formulas_json_to_ppt.py |
| presenton | KaTeX→SVG foreignObject | SVG 图片 | KaTeX 全集 | 高 | 否 | math.ts |
| tencent-pptx | MathJax→SVG | SVG 图片 | MathJax 全集 | 高 | 否 | component-math.md |
| reveal.js | MathJax/KaTeX CDN | N/A (HTML) | 完整 | N/A | N/A | plugin/math/ |
| marp-core | MathJax SVG/KaTeX | N/A (HTML) | 完整 | N/A | N/A | src/math/ |
| PPTAgent | 不处理 | N/A | N/A | N/A | N/A | — |

**两种路线**：原生 OMML（banana-slides/ppt-master，可编辑但 WPS 不确定）vs 图片（SLIDEGEN/presenton/tencent-pptx，全兼容但不可编辑）。python-pptx issue #528 仍 OPEN（2019 至今无官方进展），PowerPoint 需 a14:m 包装器（Word 不需要）。

**ppt-master 四阶段编译管线**：LaTeX → formula_parser.py（parser→AST）→ formula_ast.py（AST 节点）→ formula_omml.py（AST→OMML emitter）→ formula_compiler.py（编排入口）。支持范围远超 banana-slides：矩阵 m:m、方程组 m:eqArr、定界符 m:d（含 \left/\right/\middle）、重音 m:acc（hat/vec/dot）、上下划线 m:bar、组字符 m:groupChr、极限 m:limLow/limUpp、函数 m:func、幻影 m:phant、边框 m:borderBox、前置上下标 m:sPre、N 元算子 m:nary。PPTX→SVG 逆向导入（formula_import.py 从 a14:m 重建 LaTeX，往返验证）。docs/faq.md 明确承认"原生对象在 PowerPoint/Keynote/LibreOffice/WPS 上可能略有不同"。

#### 3.8.9 banana-slides 参考实现源码分析

**pptx_math.py**（469 行）：模块定位——python-pptx 不暴露公式 API，此模块手写生成 OMML XML 填补空白。import 纯标准库 + python-pptx OxmlElement/qn + 自有 latex_utils 符号映射，零第三方 LaTeX 库。

- latex_to_omml(source)（:150）：入口，预处理（去定界符+OCR 令牌修复）→ parser.parse() → 组装 m:oMath。不支持的命令抛 _UnsupportedLatex 返回 None 让调用方走文本回退
- normalize_latex_math（:50）：去除 $$...$$ / $...$ / \[...\] / \(...\) 四种定界符
- normalize_ocr_math_tokens（:60）：修复 OCR 丢失反斜杠（geq→\geq、leq→\leq、neq→\neq、forall→\forall、exists→\exists）
- latex_to_display_text（:77）：文本回退方案，循环展开 \frac{a}{b}→(a)/(b)、\sqrt{x}→√(x)、\arg\max→arg max，最后调 latex_to_text 转符号，剥离剩余反斜杠命令
- looks_like_latex_math（:93）：启发式判定文本是否像 LaTeX 公式——排除路径/URL，识别定界符包裹、已知命令、反斜杠+结构符号、Unicode 数学字符。关键反例 Area = x^2 返回 False

**_LatexOmmlParser 递归下降 parser**（:181）：

- _LIMIT_COMMANDS = {\sum:∑, \prod:∏, \int:∫}
- _TEXT_COMMANDS = {\text, \mathrm, \mathbf, \mathit, \mathbb, \mathcal}
- _FUNCTION_COMMANDS = {\arg:arg, \sin:sin, \cos:cos, \tan:tan, \log:log, \ln:ln, \lim:lim, \min:min, \max:max}
- parse()（:205）：入口调 _parse_expression(stop_chars=set())
- _parse_expression(stop_chars)（:212）：主循环，处理 { 分组、空格、\\ 命令、普通字符 atom，每个 atom 后尝试 _parse_scripts
- _parse_command()（:266）：分发 \frac→_fraction、\sqrt→_radical（含[n]次方）、文字命令→_wrap_as_group、\left/\right→透传、函数命令→_math_run、极限命令→_math_run(Unicode)、LATEX_SYMBOLS→_math_run、LATEX_ESCAPES→_math_run，否则抛 _UnsupportedLatex
- _parse_scripts(base)（:309）：循环处理 _{...} 和 ^{...}，组合成 _sub_sup / _subscript / _superscript

**OMML 构建函数**（:373-468）：_math_run(text)（创建 m:r + m:t）、_append_children、_coalesce_runs（合并连续 m:r 文本减少 XML 节点）、_wrap_as_group（创建 m:e）、_child_container、_fraction（m:f + m:fPr m:type val="bar" + m:num + m:den）、_radical（m:rad + m:radPr 无次数时 m:degHide val="1" + m:deg + m:e）、_subscript（m:sSub）、_superscript（m:sSup）、_sub_sup（m:sSubSup）。

**pptx_builder.py 数学函数**（:22, :543-632）：

- _nsmap.setdefault('a14', ...) + _nsmap.setdefault('mc', ...)（:22 注册 a14 和 mc，但实际不用 mc:AlternateContent）
- add_math_element（:543）：latex_to_omml 失败返回 False → 创建 textbox → 清除 a:endParaRPr → _wrap_powerpoint_math 包装 → 计算字号（用 display_text 估算）→ _apply_math_run_style → 追加到 paragraph → 重建 endParaRPr
- _wrap_powerpoint_math（:598）：包装 OMML 为 a14:m > m:oMathPara > m:oMath（block）。关键：block 公式必须显式写 m:oMathParaPr/m:jc
- _apply_math_run_style（:608）：给每个 m:r 加 a:rPr（sz/kumimoji=0 + a:latin typeface="Cambria Math" + 可选 a:solidFill a:srgbClr）。关键：样式在 a:rPr（DrawingML 命名空间）而非 m:rPr

**latex_utils.py 符号映射**（7802 字节）：

- LATEX_ESCAPES（:16）：\%/\$/\&/\#/\_/\{/\/\,/\;/\!/\quad/\qquad 共 13 个转义
- LATEX_SYMBOLS（:33）共 60+ 映射：希腊字母小写 24 个（alpha→α ... omega→ω）+ 大写 9 个（Gamma→Γ ... Omega→Ω）+ 运算符 18 个（times→×/leq→≤/neq→≠/infty→∞/sum→∑/int→∫）+ 箭头 6 个 + 其他 12 个（forall→∀/exists→∃/in→∈/cup→∪/cap→∩）
- SUPERSCRIPT_MAP / SUBSCRIPT_MAP（:63/:71）：上下标数字/字母 Unicode 映射，用于 latex_to_text 文本回退
- 备用 MathML 路径（:161-248）：latex_to_mathml（调 latex2mathml.converter.convert）+ mathml_to_omml（lxml 加载 MML2OMML.XSL XSLT 转换）。但 pptx_math.py 的 latex_to_omml 不走这条路——直接手写 parser，这是 banana-slides 的明确设计选择

**测试断言要点**（test_editable_pptx_equations.py，313 行）：

1. test_builder_writes_native_omml_equation_instead_of_raw_tex：\frac{x^2}{y_1} → 断言 a14:m/oMath/oMathPara/m:f/m:sSup/m:sSub 存在，原始 \frac 不出现
2. test_builder_applies_math_color_to_omml_runs：红色 (255,0,0) → m:r>a:rPr 存在，m:rPr>a:rPr 不存在，a:srgbClr val="FF0000" 存在
3. test_game_theory_latex_lines_are_native_omml_not_raw_tex：3 个博弈论公式，断言 a14:m/oMathPara/oMath 各 3 个，原始 \pi/\dots/\arg/\max/\forall/\geq 不出现，Unicode π/…/arg/∀/≥ 出现
4. test_math_element_uses_only_native_formula_shape_without_visible_fallback：关键断言——mc:AlternateContent 不存在、mc:Fallback 不存在、p:pic 不存在、a:t 不存在，证明 banana-slides 不用双轨 Fallback 纯 OMML
5. test_latex_math_detection_uses_content_not_metadata：looks_like_latex_math 正例（\frac{x^2}{y_1}/\begin{matrix}a & b\end{matrix}/$x^2+y^2=z^2$/E=mc^2）反例（Area=x^2/Revenue formula/URL/Windows 路径）

**与本方案关系**：参考实现方式不复制代码。参考其架构决策（手写递归下降 parser 直射 OMML 不经 MathML/XSLT）、命名空间处理（_nsmap['a14'] 注册 + OxmlElement 自动管理）、样式位置（a:rPr 而非 m:rPr，Cambria Math 字体）、测试模式（XML 结构断言 + 无 Fallback 断言）。OMML 映射规则基于 OOXML 公开规范 ECMA-376，非 banana-slides 原创。独立编写 test_omml_native.py，结构借鉴但非逐字复制。

#### 3.8.10 样式模板调研（docs/research/2026-08-17-pptx-style-template.md）

**global.css 不稳定根因**：PPTAgent v2（DeepPresenter）没有任何主题库、调色板、风格配置。生成 global.css 的指令来自 Design.yaml——只给约束不给值（固定尺寸 16:9=1280x720、字号≥18px、仅跨平台安全字体、行内元素禁 margin/border/shadow）。全仓库 grep 商务严谨/slide-inner/--primary 零源码命中——样例 global.css 的 :root 变量集、类名、配色全是 LLM 运行时即兴产物。唯一守门 inspect_slide 只在 heavy_reflect=True 且 design_agent 是多模态时才真渲染 jpg 供视觉反思；否则直接返回字符串 "This slide is valid." 不看图。

**tencent-pptx 30 份设计契约体系（7 层架构）**：

1. 30 份机器可读设计契约（.DESIGN.md，位于 vendor/.../themes/，每份用 pptx-to-design-md skill 从真实 .pptx 反向抽取）。schema 字段：canvas（画布+安全区）/ grid（栅格骨架）/ colors（配色池带出处标注🟢XML出现次数/🟡视觉估计/🔴推断）/ typography（5 级字号含 minProjectedSize）/ spacing/rounded / imagery/iconography / layouts（命名版式 structure+requiredFields+rationale+inheritsFrom）/ patterns.decorations / motion / meta（来源元数据）/ doAndDont（护栏清单）
2. BM25+IDF 检索引擎（slidep.js:29-32）：BM25+IDF over three frontmatter fields，fused with field weights（description 0.55 / audience 0.30 / name 0.15）+ boosts（exact-name/phrase-in-description/IDF coverage/name-intent/top-3-IDF/rare-term）
3. 三层风格选择：程序检索 → 意图路由（垂直分支）→ 人机对齐。完全命中（结构层+常量值层共同生效）/ 软降级命中（结构层生效，常量值层由 query 改写）/ 全表无命中（仅通用 design-principle.md + AI 生成 DESIGN.md）
4. 通用设计法则 + 垂直分支硬闸门：A/B/C 三区母版（标题块 0-120px / 内容区 120-660px / 页脚条 660-720px）/ 色彩面积分配（主色≤60%/辅色≤30%/强调色≤10%，Hero 页强调色可到 15-20%）/ 字号层级表 / 信息密度门禁（容器填充率≥85%，常规页留白≤35%）/ L1/L2/L3 配图分级 / 页面映射表
5. 4 卡 2×2 风格预览（human-alignment.md §2.3）：每张卡含编号+风格名/5 色板条带 HEX/16:9 封面缩略图（用户真实主题文字渲染）/气质胶囊标签。4 卡须版式结构性不同
6. 声明式 DSL + OOXML 编译：LLM 写 .slide（受限 JSX）→ @tencent/slidex 编译成 OOXML，Yoga(flexbox) 排版
7. 程序校验：slidep validate 跑 SlideX.validate() 查语法/溢出/图片占位符；success:false 触发修复循环

**5 开源项目模板体系横向对比**：

| 项目 | 模板格式 | 参数化机制 | 选择机制 |
|---|---|---|---|
| marp-core | 单 .scss/.css 文件 | CSS 变量在 section 上，light-dark() 翻转 | Marpit 指令 theme: gaia + class: lead invert |
| slidev-themes | npm 包（package.json + styles/layouts.css + 6 个 layouts/*.vue SFC） | --slidev-theme-* 变量，themeConfig:{primary:...} 注入 | theme: seriph (headmatter) + layout: cover (每页) |
| SlideCraft | 双轨（HTML :root CSS 块 + STYLE_PRESETS.md；PPTX ThemeSpec dataclass） | HTML:CSS 变量；PPTX:dataclass 字段 | Phase2 mood→preset 表；PptxGenerator(theme="neon-cyber") |
| Office-PowerPoint-MCP | 单体 slide_layout_templates.json（color_schemes 8 + typography_styles 5 + templates 21） | color_role 字符串引用（"primary"→color_schemes[name].primary 的 [r,g,b]） | MCP 工具 apply_slide_template |
| presenton | templates/<name>/template.json（~448KB）+ 8 内置主题 | GeneratedColorPalette（OKLCH 算法生成）+ 用户 .pptx 经 LiteParse 导入 | API template 字段 |

**color_role 间接层**（Office-MCP）：元素不写死 hex 而写 color_role:"primary"；渲染时由 color_schemes[scheme].primary 解析。同一模板换 color_scheme 参数即换全套配色——结构不动、皮可换。slidev 的 --slidev-theme-* 是同一思想的 CSS 变量版。

**PPTEval 5 分制 vs tencent 生成期硬闸门**：PPTEval（PPTAgent v1 论文 arXiv 2501.03936v3）Design 维度 5 分制（1 风格冲突难读 → 5 和谐引人视觉元素增强吸引力），幻灯片渲染 jpg → 视觉 LLM 描述风格 → 语言 LLM 打分，是事后基准评测未接入生成循环。tencent-pptx 是生成期硬闸门（15-18 条返工规则 + Step6 每页 10 条自检），把"好看"拆成可逐项断言的工程化约束。

**落地决策 7 项**：模板文件格式 YAML frontmatter .md / CSS token 落地（契约→:root tokens + 版式类）/ 风格选择三层（关键词检索 BM25+IDF→垂直分支路由→4 卡预览）/ 抽取来源（python-pptx 读 srgbClr 计数 + 渲图）/ 评估准则双层（脚本硬校验管结构 + LLM 管语义 5 分制）/ 接入 PPTAgent（Design.yaml 第 2 步前插入选风格→加载契约→生成 global.css）/ 反 AI-slop（禁用通用 AI 视觉：Inter/Roboto 当 display、#6366f1 通用靛、紫渐变白底、全居中、雷同卡片网格）。

#### 3.8.11 文字约束调研（docs/research/2026-08-18-ppt-text-constraint-survey.md）

**核心结论：两派分化**：

| 模式 | 项目 | designer 消费 | 字数控制 | 溢出处理 |
|---|---|---|---|---|
| 忠实还原派 | PPTAgent(deeppresenter)、marp-core | 不动文字原样搬 | 靠版式硬扛/不处理 | 字号缩/溢出 |
| 精简改写派 | presenton、SlideCraft | 选取/改写/提炼成 slide 文案 | 内容侧约束 + 渲染侧校验 | rephrase/split |

成熟项目精简改写派效果更好。presenton 和 SlideCraft 明确契约"rephrase instead of clip"/"extract key points"；PPTAgent 忠实还原恰恰没解决溢出——与我们遇到的问题一致。

**5 项目文字约束 + designer 消费方式**：

- PPTAgent/DeepPresenter：忠实还原（Design.yaml:3 "将文稿忠实还原的转化为视觉平衡的幻灯片"）；Planner title≤15 字 context≤100 字；Research 无字数上限；Design 无显式字数约束仅字号≥18px；inspect_manuscript/inspect_slide 不检查字数。legacy 版有 schema 机制（从参考 PPT 归纳 suggested_characters，lengthy_rewrite 后处理改写超长文本），deeppresenter 新版丢失了这套
- presenton（文字约束最系统化）：精简改写（generate_slide_content.py:37 "rephrase instead of clip"）；大纲 100 词/页（MAX_OUTLINE_CONTENT_WORDS）；verbosity 三档（concise ~20 词/standard ~40 词/text-heavy ~60 词）；代码强制截断 trim_text_to_word_limit()；Smart 路径按 slide type 分级（title 80/visual 160/text 190/toc 220 词）；代码级硬校验 _validate_smart_slide_layout_safety() 超标抛 HTTPException + 最多 8 次重试；禁 overflow-auto/scroll/line-clamp/truncate/ellipsis
- SlideCraft：精简改写（SKILL.md:105 "Long paragraphs → Extract key points, split into digestible bullets"）；Content Density Limits 表格（Content 1 heading + 4-6 bullets OR 2 paragraphs；Code 8-10 行；Comparison 3-4 items/列）；溢出策略 "Split into multiple slides"
- marp-core：无文字约束，忠实渲染用户 Markdown，不处理底部溢出
- Office-PowerPoint-MCP：渲染后校验（行长>100 警告、文本>500 字符警告、字号 8-44pt 自适应）；validate_text_fit() 估算溢出 + validate_and_fix_slide() 自动缩字号；被动补救型

**verbosity 三档**（presenton）：concise ~20 词（极简标题型/视觉型页）/ standard ~40 词（默认平衡信息与留白）/ text-heavy ~60 词（文字密集页上限仍可控）。Smart 路径按 slide type 进一步分级。

**rephrase vs clip**：presenton 明确契约"rephrase instead of clip"——改写而非截断避免半句话。SlideCraft 同理。PPTAgent 忠实还原派不 rephrase 也不 clip 靠版式硬扛结果溢出。Office-MCP 走 clip 路线——validate_text_fit() + validate_and_fix_slide() 自动缩字号，被动补救。

**最佳实践综合**：按 slide type 分级阈值（presenton + SlideCraft）；"rephrase instead of clip"（presenton）；溢出优先级 rephrase → split into multiple slides → 字号缩小（最后手段）；内容侧 + 渲染侧双层（presenton）；代码级硬校验 + 重试（presenton Smart）；schema 归纳自适应阈值（PPTAgent legacy）。

**对本项目启示**：当前是"忠实还原派"（designer no omissions no rewrites），与 PPTAgent 同模式同样遇到溢出问题。调研指向"精简改写派"——但 presenton 是"上游就精简"，SlideCraft 是"单 agent 自提炼"，没有项目走"researcher 粗稿 + designer 精简"这条路。要走这条路需自行设计契约，关键风险是 designer 精简时丢信息。

#### 3.8.12 academic 设计规范核心（designer 四档之一）

academic 是 designer 四档设计规范（academic/consulting/redgold/general）之一，由 planner 场景路由命中后写入 alignment.style_tendency = "academic"，designer 读 designs/academic.md 落地 global.css。适用场景：高校答辩、科研结题、教学课件（理工医）、学术会议、学科评估、临床/医学汇报、课题开题、实验室组会、科研申报。

**风格 DNA**：学术可信（蓝白浅灰为基底，表达研究/证据/方法/结论，不做营销海报）；撑满优先（内容区元素累计高度≥96% 可用高，留白不是主要视觉手段）；证据化配图（L1 必须是论文截图/真实实验场景摄影/流程图/显微医学图之一）；卡体克制（常规卡浅底淡描边，深蓝实色卡只作语义凸显限频）；层次清楚（正文页至少标题+主体卡/图+底部结论或数据锚点）；色彩受控（宝蓝主导，红/黄只作重点或警示，金色为 0）；图文都要有内容（不得用大留白/空卡片/装饰图凑版面）；公式与学术真实（公式/定理/数据/结论必须真实且有据可查，禁止杜撰）。

**字号层级与字体策略**：

| 层级 | 字号(px) | 字重 | 行高 | 备注 |
|---|---|---|---|---|
| 封面主标题 | 60-96 | bold | 1.2 | — |
| 巨型数据锚点 | 72-120 | bold/Black | 1.1 | 必须与正文字重或字号不同 |
| 页面标题 | 32-40 | bold | 1.3 | — |
| 正文要点 | 22-28 | regular/medium | 1.5 | ≥22px 硬下限 |
| 卡内标题 | 24-28 | semibold | 1.4 | — |
| 引文 | 20-26 | italic | 1.5 | 「」 |
| 脚注/页码 | 14-16 | regular | 1.4 | 页脚条右下 |

字体个性策略（跨平台安全清单）：商务现代（微软雅黑/SimHei + Arial/Calibri，适合科技金融SaaS）/ 人文质感（微软雅黑正文+Times 引文 + Times/Georgia）/ 活力亲和（微软雅黑 + Arial/Calibri）/ 政务庄重（SimHei + Arial/Times）/ 科技未来（微软雅黑+letter-spacing 加大 + Arial）。关键规则：标题与正文允许不同字重；巨型数据锚点必须用与正文不同字重或字号；禁所有页面只用"系统默认无衬线"，global.css 必须写出具体字体名。公式字体 Cambria Math；block 公式字号=正文同级或+1级，颜色=文本主色，上下间距 8-12px；inline 公式字号=周围正文。

**信息密度门禁**：

| 页面类型 | 最少元素 | 正文字数下限 | 字数上限 | 图片下限 | 主视觉占内容区 |
|---|---|---|---|---|---|
| 封面 | 主标+副标+主视觉 | 20 | ≤60 | 1 | ≥35% |
| 目录 | N 条目+引导句 | 80(合计) | ≤150 | 0-1 | — |
| 内容页·单主题 | 标题+正文+主视觉 | 180 | ≤280 | 1 | ≥30% |
| 内容页·卡片组 | 标题+引导句+N卡 | 每卡≥100 | 每卡≤160 | 0-N | — |
| 数据/图表页 | 标题+主图+洞察 | 80 | ≤140 | 1主图 | ≥50% |
| 章节过渡 | 章节大字+小标 | 30 | ≤60 | 1 | ≥40% |
| 结束页 | 收束金句+落款 | 20 | ≤50 | 0-1 | — |

默认留白上限：常规内容页留白≤35%（封面/章节过渡/结束页及 global.css 显式声明"留白型"页不受此限）。容器填充率门禁：填充率≥85%（卡片内实际内容垂直占用≥容器高度 85%，高≥380px 卡正文≥100 字，高≥480px 卡正文≥130 字）；底栏锚定（卡片末尾引文条/标签条/按钮须用 margin-top:auto 或 justify-content:space-between 钉底）；横向兄弟卡三段 y 轴等高对齐（尾部 y 差>16px 返工）。

**配图与视觉元素（L1/L2/L3 三级）**：

| 等级 | 用途 | 最小尺寸/占比 | 接入方式 |
|---|---|---|---|
| L1 主视觉 | 承担页面主要叙事 | 内容区≥40%（560×420/640×480/半屏） | 卡片整体背景/一栏铺底/引文卡叠层 |
| L2 支撑图 | 强化某段落 | ≥280×180 | 段落旁/卡片头部/与正文并排 |
| L3 母版徽标 | 全篇统一角标 | ≤64×64 | 页脚条 C 区左侧，全篇位置一致 |

严禁：200×70 小尺寸图片塞标题块右侧当装饰；不同页 L3 位置不固定；全篇 L1 主视觉风格混杂。

**15 条最终硬闸门（出现任一必须返工）**：①内容页主视觉缺失或<30%内容区（单主题页）②卡片填充率<85%或高卡正文字数不足 ③卡片尾部元素未锚底悬浮中段 ④同行兄弟卡尾部 y 差>16px 三段不对齐 ⑤正文<22px 或巨型锚点与正文无差异 ⑥文字对比度<4.5:1 ⑦全篇每页色彩比例雷同（差异<10%）或单页≥2 套主色板 ⑧高饱和撞色铺满≥1/3 页面 ⑨视觉锚点缺失（全页元素趋近中间大小无尺度跳跃）⑩10 页以上 deck 缺 hero 页（<2 页视觉高潮）或连续≥2 页视觉重量雷同 ⑪200×70 装饰小贴片塞标题栏/L3 位置逐页漂移 ⑫全篇 L1 主视觉类型混杂（摄影/插画/3D 混用未显式声明）⑬使用 linear-gradient/box-shadow/内联 SVG 等会被引擎栅格化样式 ⑭占位文未清零 ⑮任意页可见文本字符数超过该 page-type 上限。

**引擎适配**：只用跨平台安全清单；禁 linear-gradient（改纯色块拼接）；禁 box-shadow（改 border 描边）；半透明叠加用 rgba() 纯色透明；禁内联 SVG（改纯盒模型 div+border+border-radius）。"大胆对比"靠纯色块面积差异 + 大字号字重跳跃 + 留白节奏实现。

