# 实习工作详述 · AgentOS 项目（调优与质量）

## 三、AgentOS / PPT-Agentskill 项目（续）

### 3.9 调优与大重构

#### 3.9.1 调优过程关键问题（8 类）

| 问题                                                                         | 根因                                           | 解决                                                                    |
| ---------------------------------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------- |
| 相邻页同图 3 对 + 同图两用不同 alt                                           | LLM 盲配填槽                                   | 脚本硬门 adjacent_duplicate_ref high + 提示词约束双保险 + 子图语义对齐  |
| 关键数值无判断（"10.8% higher"实际 0.88% 差 12 倍）                          | LLM 数学盲区，inspect_slide 像素校验管不了语义 | 数据落点提示词 + 数值反算自审 (a-b)/b                                   |
| 18 页全缺 Source 标注                                                        | 默认约束未驱动                                 | user_guidance 驱动非默认（学术需标、商务强标生噪音）                    |
| outline.layout 孤儿字段（slide7 outline"右图左文" vs page-design"左图右文"） | designer 不读、researcher 弱冗余消费           | 孤儿字段彻底删不迁就旧产物                                              |
| GLM-5.2 reasoning_tokens=65536 撑满卡 647s                                   | 凭记忆搭 flex 容器易溢出                       | 骨架而非约束 reasoning 措辞 + inspect_slide 失败只读 stderr 针对性 Edit |
| 14px→10.5pt 投影不可读 inspect_slide silent pass                            | 设计契约纯 LLM                                 | designer_check 4 层 + 字号阈值 13.5pt 来自实测                          |
| 公式块
$$
video2grid
$$

/
$$
shuffle
$$

 完全丢弃                                      | html2pptx 引擎不支持 LaTeX                     | data-latex 标记 + inject_omml 后处理（最终方案）                        |
| EBUSY 后产两份产物 + error.txt 残留                                          | Office 锁 ~$ 文件                              | 启动清旧 + EBUSY 重试 + 成功自动清                                      |

#### 3.9.2 GLM 子 agent 停止问题（根因定位）

**现象**：GLM 模型下子 agent 会卡在"想完没做"的状态。典型片段：

```text
现在让我阅读 SKILL.md 和关键脚本...让我读取 convert_html_to_pptx.py...让我阅读 HTML指南参考...
我现在已经完全理解了任务要求、验证规则和设计指南。让我将第一个待办事项标记为已完成，并开始进行设计。
然后是停止不动了？
```

**根因**：思维链堆到一定长度被截断，子 agent 卡在"准备开始"状态。**方向**：控制思维链长度，或把准备性思考拆成显式步骤，避免"想完没做"。

#### 3.9.3 大重构与 PR 合并（2026-08-20，PR#7/#8）

全程遵循纯净原则。PR 列表：

- PR #7：`refactor(planner,researcher): 产物质量保障体系——HITL 转达显式化 + self-check 原则独立化`
- PR #8：`feat: 合并场景路由 + HITL/产物质量保障（!6 + !7 合并版）`

commit 分几类：子 agent、公式、校验等大修改。

#### 3.9.4 各角色调优明细（attachment-reader/planner/designer）

**attachment-reader 修复**：

- MinerU 只留 image-type block→imgN；table/chart 截图 + 孤儿装饰图一律删除
- engine_used 枚举 4 处统一 5 值同序（mineru/local-fallback/markitdown/image-copy/raw-text）
- _finalize_output 清空 dest_images 旧图片（修复跨跑残留泄漏：fallback 155 png + MinerU 11 jpg 叠加）
- 跨平台 attachments 引用检查："attachments/" in → "attachments" in（Windows 反斜杠漏检修复）

**planner 增强**：

- slides[] 加 3 推荐字段（visual_role/density/anti_pattern）为下游提供依据
- visual_role 三态枚举（anchor/atmosphere/evidence）脚本硬门 + 提示词双保险
- finalize.py alignment 校验：style_tendency/objective/audience 必填补；source_fidelity 无文档时 null 合法
- human-alignment.md P0-P4 五维度 + H1-H6 硬规则
- parse_document sections[] 增 has_table/has_formula（planner 据此设 density 图片0张）

**designer 调优**：

- 版式配色分离：1 版式类库（layout-base.css 7 .layout-*）消除 84 份冗余，12 颜色方案纯数据
- designer_check 4 层编排（L1 inspect_slide --all / L2 validate_template + contrast_check / L3 pptx_check / L4 deck_check）
- PER-PAGE QA LOOP（max 3 轮）+ FULL-DECK REGRESSION（修 HTML 不修 .pptx 必须 build_deck 重跑）
- 消除 poppler：PDF→JPG 从 pdf2image（依赖 poppler 系统二进制）改 PyMuPDF/fitz（纯 pip 包）
- build_deck 终态单一产物：启动清旧（同名 .pptx/.pdf + error.txt + Office ~$ 锁文件）+ EBUSY 重试 + 成功自动清 error.txt
- 布局驱动内容契约：从"忠实呈现 no omissions no rewrites"改为"按 page-type 定版式→重组文字" + 字数校验
- 声明式 page-type 拆循环推断（read_page_type 注释声明优先，缺失回落 infer）+ --precheck 秒级快检（0.38ms vs 700ms 快 1829x）

#### 3.9.1 workbuddy-align 分支完整 commit 清单（26 commit rebase 为 5+2，最完整）

基准 ppt_agent@778a5d7，2026-08-17 将 26 commit 按角色目录 rebase 合并为 5 commit（git reset --mixed 778a5d7 + 按目录分组 git add，环境不支持交互 rebase），内容零丢失（git diff f2c87d5 HEAD 为空）。后追加 2 个测试产物排查 fix commit。

| commit | 标题 | 根因/原则 |
|---|---|---|
| e49cc56 | 框架/HITL（SKILL/bind/workflow/dependencies/preflight） | team-leader 在 build_team 模式误推断需 swarmflow 工具；planner 正确 send_message 发需求对齐问题给 leader 但 leader 没真正调 ask_user——HITL 门失效。原则：只支持 build_team（不加 swarmflow 死代码分支）；[HITL-RELAY] 标记让 leader 识别"必须转达"vs 状态汇报，MUST 调 ask_user（唯一合法动作）；覆盖两门（1d 需求对齐 + ⑤ 大纲确认）；Step ⑤ 大纲确认硬门——"未经确认不得标记 stage-2 完成 + 不得创建 stage-3 任务" |
| b405ad2 | attachment-reader | 含原生 HTML 表格的页又插入表格图片（冗余）的三链根因之一——MinerU 对表格同时产出 .md 正文 table + tableN.png 截图。原则：_normalize_mineru_images 只保留 image-type block→imgN；table/chart 截图 + 孤儿装饰图一律删除；engine_used 枚举 4 处统一 5 值同序 |
| 1b7b7da | planner（叙事结构 + visual_role 枚举 + finalize alignment + human-alignment + parse_document sections） | planner 大纲每页仅 index/title/context，designer 定版式与 researcher 配图全凭判断；visual_role 自创词表让下游无法消费。原则：slides[] 加 3 推荐字段（visual_role/density/anti_pattern）；visual_role 三态枚举（anchor/atmosphere/evidence）脚本硬门 + 提示词双保险；human-alignment.md P0-P4 五维度 + H1-H6 硬规则；parse_document sections[] 增 has_table/has_formula |
| d7655c8 | researcher（配图策略 + 数据落点 + 数值自审 + inspect 告警 + 表格页免配图走 density 架构） | 相邻页同图 3 对；同图两用不同 alt；关键数值后无判断（"10.8% higher"实际 0.88% 差 12 倍）；表格页又插表格图片冗余。原则：配图是内容非填料；相邻页同图脚本硬门（adjacent_duplicate_ref high）；数据落点是 researcher 职责；数值一致性 LLM 自审；表格/公式页免配图走 density 统一架构不写特例 guard |
| 1bb4999 | designer（版式配色分离 + 7 版式类 + designer_check 4 层 + 逐页 QA + html2pptx-safe + 消除 poppler） | GLM-5.2 生成 slide 时 reasoning_tokens=65536 撑满上限卡 647s + 回读整个 HTML 致 input_tokens 67K；两测试 36 页定性三问题（版式布局与配色两套体系冲突/12 模板各含 7 版式类=84 份重复/图片死值 height 不看 ratio 致压扁溢出）；3 轮调研定性 4 缺口（html 层强但 pptx 层空白 + 设计契约纯 LLM + deck 跨页无脚本 + 渲染比对缺失，实测 14px→10.5pt 投影不可读 inspect_slide silent pass）。原则：版式配色分离（1 版式类库 7 .layout-* 消除 84 份冗余，12 颜色方案纯数据）；契约驱动生成 + 循环校验 + 全量回归（PAGE-DESIGN MAP + CONSISTENCY SELF-CHECK + PRE-SUBMIT 5✅ + PER-PAGE QA LOOP max 3 轮 + FULL-DECK REGRESSION）；designer_check 4 层编排（字号阈值 13.5pt 来自实测）；消除 poppler 改 PyMuPDF/fitz |
| fbfe3c5 | fix(researcher): attachments 引用检查跨平台 | inspect_manuscript.py:97 if "attachments/" in ref_path 正斜杠，Windows 反斜杠 attachments\material 漏检 → 7 处 attachment_ref 全未触发。修："attachments/" in → "attachments" in（跨平台去斜杠）；finalize_check 补同款硬错误 |
| cc5f07a | fix(designer): build_deck 终态单一产物 + 公式 LaTeX→HTML 富文本 | .html2pptx-error.txt 残留（build_deck 写 material.pptx 时 EBUSY——Office 锁 ~$material.pptx）+ 两份产物 + 公式解析（manuscript 6 个 LaTeX 公式被 designer 降级为纯文本）。修：build_deck 启动清旧 + EBUSY 重试 + 成功自动清 error.txt；公式 LaTeX→HTML 富文本映射（x_0→sub、\mathcal{V}→iV/i、\mathbb{R}→ℝ、\frac{a}{b}→a/b、\rightarrow→→） |

提示词全量纯净化（2026-08-17，并入各角色组无独立 commit）：4-agent 并行审计 + 合并旧 plan 未执行项，24 文件净 -32 行——元数据/provenance 清理（corporate-deep-blue.css 单行 header；7 脚本 docstring + README + human-alignment + finalize-planner + attachment_reader 删 deeppresenter/PPTAgent/tencent/九问/Phase4 溯源）；correctness（rewrite_image_links "硬阻塞"→软告警；9 处"路线 C"悬空标签删；html-guidelines ≤4→≤6 hex；planner alignment 必填补 objective/audience；engine_used 5 值统一）；跨层叙事（planner 删下游消费细节；html-guidelines 单页门禁删跨页项；researcher 删替 checker 解释严重度；bind 删 team_helpers 实现注解）。

#### 3.9.2 designer-opt 分支完整 commit 清单（16 commit，最长）

| commit | 标题 | 根因/要点 |
|---|---|---|
| 87102eb | chore: 纯净审计——去平台痕迹/WorkBuddy 溯源/迁移措辞 | 4 文件 +7/-9 |
| be79e1d | feat(designer): 布局驱动内容契约 + 字数校验 | designer 契约从"忠实呈现 no omissions no rewrites"改为"按 §6 page-type 定版式→重组文字"。inspect_slide.py 加 count_visible_text/infer_page_type/STYLE_TEXT_LIMITS/check_text_limit。9 文件 +202/-80 |
| 7a3ffbd | feat: 移植 PR#7 的 HITL 双门转达 + self-check 体系 + 大纲确认硬禁令 | 16 文件 +507/-157 |
| 75a80d1 | feat(designer): 原生 OMML 可编辑公式 + 排版约束 + 纯净审计 | 手写递归下降 LaTeX parser → OMML XML（参考 banana-slides pptx_math.py）。WPS 已验证可见 + 零新依赖 + 可编辑。92 公式全类别测试 100% 注入成功。13 文件 +755/-1 |
| 2352a00 | feat(designer): 公式样式 data-attribute 控制 + 结构统一/冗余/死链纯净审计 | 19 文件 +113/-65 |
| 0dacf7e | fix(designer): 公式 block 对齐 data-align 可控 + 清零 margin 双重计入 | 7 文件 +53/-17 |
| 6eefb75 | feat(researcher): LaTeX 公式智能识别规范 + inject_omml \text{} 结构修复 | m:e 直接挂 m:oMath 下 WPS 不渲染，改平铺 m:r。4 文件 +157/-5 |
| b09cac9 | fix(designer): inspect_slide style 注释校验 | trace 实证——designer agent 第 4 轮卡死在 slide_06/09/10 TEXT OVERFLOW。根因：global.css 首行是 Academic Style 非 style_tendency: academic，check_text_limit read_style_id 正则匹配不到 → 返 None → limit=DEFAULT_TEXT_LIMIT=280。修：加 style 注释存在性+合法性校验，缺失/非法时报 [STYLE MISSING]/[STYLE UNKNOWN] 阻塞。7 文件 +24/-6 |
| eb215cc | fix: 产物校验机制完善——outline 路径/overview 格式/缺页/交叉校验四缺口 | 四缺口——A outline.json 路径无校验（planner finalize.py 加 workspace_dir 参数）；B outline 丢失非阻塞（inspect_manuscript 的 outline_not_found/outline_parse_error 从 medium 提到 high）；C overview.json 无校验+--output 覆盖（parse_document.py 删 --output 参数）；D page_count 与 slides 不交叉校验（planner finalize.py 加 alignment.page_count == len(slides)）。12 文件 +82/-29 |
| 0c28fc7 | fix(designer): 公式系统调优——降级泄漏/文档矛盾/裸LaTeX检测/纯净 | 公式系统代码层面到位但实测从未被触发——19 页 HTML 零 data-latex。P1 文档矛盾修复（self-check.md 与 html-guidelines.md 不一致）；P2 降级路径 bug 修复（\text{shuffle} 降级成 textshuffle → 修为提取 {} 内容得 shuffle；\sqrt[3]{n} 降级不匹配 → 修为 √[3](n)）；P3 纯净；P0 裸 LaTeX 检测（inspect_slide 加 check_raw_latex）。5 文件 +50/-14 |
| 3bc49aa | fix: 产物路径契约校验——researcher/designer finalize 加 workspace 路径约束 | 8 文件 +47/-20 |
| 82d6ca4 | fix: 纯净审计修复——文档同步遗漏 + 用户消息占位符 + 注释精度 | 5 文件 +5/-5 |
| ea136a2 | docs: 运行时校验机制总览文档 validation.md | 2 文件 +284/-1 |
| 5a71545 | fix(designer): 字数校验修根因——排除表格cell + 放宽bigimage/preface/table上限 | trace 实证——designer agent 反复修 TEXT OVERFLOW 死循环（traces-2026-08-20.jsonl，3 轮重试 slide_03/04/05/06 字数不变）。两根因：① count_visible_text 把 table cell 数据算进字数；② bigimage/preface 的 350 上限偏严。修：count_visible_text 排除 table 块；STYLE_TEXT_LIMITS 放宽（academic bigimage/preface 350→450、table 80→200；redgold preface 350→450）。4 文件 +16/-10 |
| 0102a34 | fix: HITL 工具名修正——ask_user_question→ask_user | trace 排查——planner 返回"Stage 2 大纲设计已完成，用户已确认"无 [HITL-RELAY] 标记。trace 发现 planner line248 正确发 [HITL-RELAY]，line256（37 秒后）自己发"用户已确认"，leader 全程 0 次 ask_user 调用。根因：skill 规范写的工具名 ask_user_question 在 jiuwenswarm 平台不存在——平台内置工具名是 ask_user。修：全部 ask_user_question/AskUserQuestion → ask_user（8 文件 12+处）。7 文件 +19/-19 |
| bdb6bb5 | feat(designer): 声明式 page-type 拆循环推断 + --precheck 秒级快检 | p-r-test 18 页 academic 基线实测 pipeline 卡设计阶段。核验 infer_page_type 按成品文本量反推 page-type，而文本量正是上限要约束的东西——循环。双向不准实证：封面 216 字（真实 cover 上限 60）被推断 single（280）通过；目录 325 字（真实 catalog 80）被推断 preface（450）通过。修：阶段1 声明式 page-type（VALID_PAGE_TYPES 从 STYLE_TEXT_LIMITS 派生单一数据源；read_page_type 读 HTML 注释 <!-- page-type: <key> -->；check_text_limit 声明优先缺失回落 infer）；阶段2 --precheck 快检（只跑纯 Python，跳过 convert_html_to_pptx 和 heavy）。验证：precheck 单页 0.38ms vs 完整校验 ~700ms（快 ~1829x）。7 文件 +162/-16 |
| dc7cdac | fix: 纯净审计修复——16条清单（溯源/死字段/裂隙/特例guard/语言） | 19 文件 +126/-96 |

#### 3.9.3 feat-native-preserve-v2 分支（8 commit，已合并入上游 778a5d7）

| commit | 标题 | 要点 |
|---|---|---|
| 8677e9e | v2 看齐提示词——原生结构保留 + 信息美学 + 大纲简化 | planner Output Schema 简化为 index/title/context（删 section/subsections/images）；researcher Identity "fully-illustrated"→"information-aesthetic"，新增 Native Structure Preservation 段 + Visual Asset Strategy 段 |
| f7fa115 | v2 看齐同步——大纲简化 + 原生保留 + 配图策略 | planner workflow.md 删 images；researcher workflow.md 步骤③硬约束加 3 行（原生表格/LaTeX 保留/table.chart 不进 images/） |
| 594e518 | 启动预检脚本化——preflight.py + dependencies.yaml 补 python_packages | 独立实现 preflight.py（零依赖标准库；内置极简 YAML 解析器不依赖 PyYAML）；探测工具 shutil.which + Python 包 importlib + node_modules；退出码 0/1/2 |
| bb864fb | 默认自动安装缺失依赖——pip/npm/playwright + --no-install 选项 | 新增 3 安装函数（install_py_pkg/install_node_modules/install_playwright_browser，镜像 baked in） |
| e61a806 | 清空 dest_images 残留 + image_count 与 md 引用对齐 | 根因：_finalize_output 移入新图前不清空 dest_images，跨跑残留泄漏——fallback 产 155 png + MinerU 产 11 jpg 叠加。验证：fallback 155 png→不清目录 MinerU→images/=11 jpg（修复前 166） |
| bed7e78 | 纯净性——去版本标签+过渡文档+finalize拒额外字段+死代码+文档对齐 | 溯源尾巴根因链（3 环）：planner 文档列 section/subsections 为可选 → finalize.py 不拒额外字段放行 → researcher 读 section 写 Source: 尾巴。finalize.py 拒额外字段 |
| f235a05 | researcher 补 v2 内容写作风格——核心洞察/金字塔/可信源 | 新增 Content Style 段：one core insight per slide + pyramid principle + bold sparingly + credible sources first |
| 97ad8da | designer 补 v2 主动设计指导——画布/字号/安全字体/版式 | 新增 Design Guidelines 段：Canvas & layout（body 固定 1280×720/960×720/794×1123，数值取自 inspect_slide.py ASPECT_RATIOS；字号≥18px）+ Typography（跨平台安全字体清单，禁网络字体） |

#### 3.9.4 refactor 分支（5 commit，Level 1 清理）

| commit | 标题 | 要点 |
|---|---|---|
| 74189e6 | 删架构矛盾文档 + designer_finalize.py 重复 | 删 attachment-reader/DESIGN.md（flat 路径）、ppt-planner/DESIGN.md（flat + 虚构 per-role SKILL.md）、2 份 references/workflow.md（flat + 失效链接）、ppt-designer/designer_finalize.py（与 finalize.py 字节级一致）。共 −1597 行。⚠️ 误删两份 workflow.md，经 fdefb58 恢复 |
| 935443f | 清 pyc 缓存 + 新建 .gitignore | git rm --cached 2 tracked .pyc；删 3 __pycache__/；新建 .gitignore |
| 5ce9f63 | 删 --no-install + 溯源措辞 + 路径/注释 | 保留自动 npm install；删 --no-install 死选项；溯源措辞（9 处"完全一致"→"从 PPTAgent 提取"）；路径（5 处 script/→scripts/ppt-designer/） |
| 4abdec7 | bind.md 确认门矛盾修正 | "no timeout"→"no hard timeout, but after 5 revision rounds escalate to manual edit"；手动编辑 outline.json 即用户接管确认 |
| fdefb58 | 恢复 2 份 workflow.md（误删纠正）+ 修正为 by-role | 撤销 74189e6 误删。路径 flat → by-role；调用方式 skill_tool(skill_name) → {swarm_skill_directory} + workdir；失效链接 ../SKILL.md→../../../SKILL.md |

### 3.10 纯净原则审计

**纯净原则审计清单（4 大类 16 项）**：

- A. 溯源残留：标签式溯源 / 正文嵌版本号 / 分组按批次而非维度
- B. 装饰与冗余：装饰性 diagram / benchmark 角标 / 重复冗余 / 特例 guard
- C. 死内容：死指令 / 死链接 / 死字段死参数
- D. doc/impl 裂隙：校验项与动作不对应 / 产物路径与矩阵不同步 / 跨实例共享结构 drift / 章节编号跳号
- E. 语言与平台残留：语言混用 / 平台工具实现痕迹

**27 个 skill md 文件全量纯净审计**（docs/audit/skill-md-purity-audit/summary.md）：

- 审计范围：27 个 skill md（约 4500 行），6 子 agent 并行 + 16 条清单，基于 skill 设计思想 70 条 + CLAUDE.md 纯净原则 16 条
- 已修复 15 项：4 处 doc-impl 裂隙 + designer.md Inline Persona 4 项硬规则遗漏 + 9 个长文档 TOC + redgold 字号硬闸门漏洞
- 保留 10 项（判定为设计属性非违规）
- 建议项 8 项已全量修复

### 3.11 校验脚本体系

#### inspect_slide.py（819 行，逐页质检，Level 0/1/2 降级链）

**Level 0**（Python 秒级，Level0Checker 类）：

- advisory 项（不阻断）：check_text_limit（字数溢出 [TEXT OVERFLOW]）、check_bullet_limit（bullet ≤6 [BULLET ADVISORY]）、check_bare_text_advisory（_BareTextFinder 轻量 HTML 解析器找有 inline 视觉样式的容器里的直接文本节点 [BARE TEXT ADVISORY]）、check_style_id（style 缺失/非法 [STYLE MISSING]/[STYLE UNKNOWN]）
- 硬阻断项：check_raw_latex（裸 $...\...$ LaTeX [RAW LATEX]）、check_font_safety（@font-face/Google Fonts [FONT UNSAFE]）、check_rasterization_styles（gradient/shadow/SVG/filter [RASTERIZATION]）、check_min_font_size（<18px [FONT TOO SMALL] / >5334px [FONT TOO LARGE]）、check_page_type_match（声明 table 无 table / 声明 bigimage 无 img [PAGE-TYPE MISMATCH]）

**Level 1**（Node --validate，Level1Validator 类）：调 convert_html_to_pptx 做 validate-only 转换。校验点：内容溢出 body、layout 尺寸不符、textbox 越界（底边距 <0.5"）、表格无单元格、图片缺失、背景图缺失、文本与图片重叠（>30% 硬阻断）。validateVisualQuality（html2pptx.js:210）还跑颜色对比度/内容撑满/图片最小尺寸<240×160/主体元素>6（advisory）与图片变形（>15% 硬阻断）。

**Level 2**（heavy 视觉渲染，Level2Renderer 类）：Playwright → PDF → JPG → base64。60s 超时兜底（asyncio.wait_for + HEAVY_TIMEOUT_SECONDS=60）。失败降级不阻断（ok=True + degrade_reason + .fail.txt）。

**--precheck 快检**：precheck 只跑纯 Python（check_text_limit + check_raw_latex + check_bare_text_advisory），跳过 convert_html_to_pptx 和 heavy。单页 0.38ms vs 完整校验 ~700ms（快 ~1829x）。

**留痕产物**（ArtifactWriter 类）：write_jpg（成功写 .jpg 删 stale .fail.txt）、write_fail（失败/heavy 降级写 .fail.txt 含原因+重跑入口，删 stale .jpg）。**重试计数器**（RetryGuard 类）：MAX_RETRIES=3，jpg 写入成功时清零，heavy 降级不清零。

#### STYLE_TEXT_LIMITS 字数上限表（style × page-type 字符数）

| style | cover | catalog | section | preface | single | card | bigimage | data | table | model | structure | summary | ending |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| academic | 60 | 80 | 100 | 450 | — | 180 | 450 | 160 | 200 | — | — | — | — |
| consulting | 50 | 150 | 40 | — | 200 | 80 | — | 120 | — | 260 | 100 | 260 | — |
| redgold | 30 | 150 | 60 | 450 | 280 | 160 | — | 140 | — | 360 | — | — | — |
| general | 60 | 150 | 60 | — | 280 | 160 | — | 140 | — | — | — | — | 50 |

DEFAULT_TEXT_LIMIT=280（推断失败兜底）；VALID_PAGE_TYPES 从 STYLE_TEXT_LIMITS 各档键并集派生（单一数据源）；count_visible_text 排除 table cell 数据。bigimage/preface 上限 450、table 200（覆盖全页可见文本含标题/页脚/KPI，非纯正文）。

#### verify_deck.py（350 行，build_deck 产 .pptx 后终态校验）

| # | 校验规则 | 类型 |
|---|---|---|
| 1 | 产物是 .pptx（非 .pdf 回退冒充） | 硬 |
| 2 | .pptx 存在 + python-pptx 能打开（合法） | 硬 |
| 2b | PPTX 包结构完整（ZIP + [Content_Types].xml + OPC 关系无悬空） | 硬 |
| 3 | 页数 == outline.json slides 数（防转换丢页） | 硬（交叉） |
| 4 | 每页 ≥1 shape（防空页） | 硬 |
| 5 | 无 FORMULA_PLACEHOLDER 残留（inject_omml 未替换） | 硬 |
| 6 | 无 .html2pptx-error.txt 残留 | 硬 |
| 7 | 每页 QA 产物齐全（slides/.inspect/slide_XX.jpg 存在且无 .fail.txt） | 硬 |
| 8 | 无 pptx shape 间重叠（交集 > 较小 shape 面积 30% 硬阻断，只检测内容 shape 文本/图片/表格；>85% slide 面积的背景图除外） | 硬 |
| 9 | soft 降级报告（.html2pptx-soft-degraded.txt 存在） | 软告警 |

OPC 关系悬空校验补 python-pptx 对 OPC 关系断裂容错的真空（python-pptx 能打开悬空 r:id 的 PPTX，PowerPoint/WPS 严格会报修复）。shape 重叠检测阈值与 html2pptx.js:260 一致（30%），范围更广（PPTX 侧所有内容 shape 两两，JS 仅 text↔image）。

#### build_deck.py 降级链（183 行）

ConversionPipeline.run：① strict 转换（convert_html_to_pptx soft_parsing=False）→ 成功清理 error_txt + soft_marker + FormulaPostProcessor.run → 返回 pptx_path；② soft 重试（仅当非 soft 模式且失败非依赖缺失类——"Cannot find module"/"dependencies are missing" 不重试）→ convert_html_to_pptx soft_parsing=True → 成功写 soft_marker + 清 error_txt + FormulaPostProcessor.run → 返回 pptx_path；③ PDF 回退（soft 仍失败/依赖缺失/已 soft 模式）→ fallback = pptx_path.with_suffix(".pdf") + error_txt.write_text(strict+soft 两级错误 + traceback) → 返回 fallback。FormulaPostProcessor.run 读 sidecar .formulas.json 调 inject_omml.inject_omml（失败仅 warn 不阻断，占位符已由 latex_to_display_text 兜底）。PDF 备份无论转换成功与否都执行。

#### preflight.py 依赖探测（371 行，零外部依赖）

内置极简 YAML 解析器（parse_deps 微型状态机，仅处理 dependencies.yaml 固定结构）。探测函数：probe_tool（shutil.which + playwright 特殊处理）、probe_py_pkg（importlib.util.find_spec，PY_IMPORT_ALIAS 映射 pymupdf→fitz/fake-useragent→fake_useragent/Pillow→PIL/python-pptx→pptx）、probe_node_modules、playwright_browser_dir。自动安装函数：install_py_pkg（pip install -i PIP_MIRROR tuna）、install_node_modules（npm ci）、install_playwright_browser（npx playwright install chromium，PLAYWRIGHT_DOWNLOAD_HOST=PLAYWRIGHT_MIRROR npmmirror）。300s 超时。退出码 0 全部就绪 / 1 optional 缺失（降级模式） / 2 required 缺失（中止）。

### 3.12 tencent-pptx 三处调优

基于 2026-08-14 workbuddytest rave_ppt 实测（RAVE CVPR 2024 论文 18 页 PPT，用 dsflash 生成，无图片理解能力，最终 1.2MB 排版良好）。三处递进：planner 大纲加叙事字段（让生成有依据）→ designer 加逐页映射表+量化自检（让生成即好）→ designer 加生成后校验-修复循环（让校验兜底）。

**调优一：planner 大纲从 3 字段升级为叙事契约**

我方现状：outline.json 每页只有 index/title/context，designer 拿到大纲后每页版式/配图位置/留白/禁止项全凭自己判断。tencent 解法（STORY.md）：每页 11 字段叙事契约（type/role/rhythm/layout/visual/visual_role/density/anti_pattern/description），最有价值四字段：anti_pattern（每页明确写"禁止什么版式"）、visual_role 三态（anchor/atmosphere/evidence）、layout（版式名 designer 照填不发明）、density（字数约XXX / 图片N张 / 留白约XX% 三段式）。落地：workbuddy-align commit 1b7b7da 实现了 visual_role/density/anti_pattern 三字段（删 layout 孤儿字段——designer 不读、researcher 弱冗余消费，实测 slide7 outline"右图左文" vs page-design"左图右文"即此幻影契约）。

**调优二：designer 从通用规则升级为逐页映射表 + 量化自检**

我方现状：designer 无逐页设计参数表，靠 Design Guidelines 通用建议 + 记忆生成；html-guidelines.md 只有 3 条引擎校验，且明说"NOT enforced by inspect_slide.py...violating them silently passes validation but degrades the deck"。tencent 解法（DESIGN.md）：逐页映射表（每页 9 字段：类型/角色/版式/L1文件/字数/留白%/色彩分配/关键约束）+ 10 条量化硬闸门（内容页未撑满 C 区<476px/红+黄>5%或出现金色/正文<22px 卡内标题<24px/深蓝实色卡单页>1全篇>3/文字溢出卡片对比度<4.5:1 等）。落地：workbuddy-align commit 1bb4999 实现了 PAGE-DESIGN MAP + CONSISTENCY SELF-CHECK + PRE-SUBMIT 5✅ + PER-PAGE QA LOOP + FULL-DECK REGRESSION + designer_check 4 层编排。

**调优三：designer 加生成后校验-修复循环（质变，最大差距）**

我方现状：生成 slide_XX.html → inspect_slide.py --html XX → 通过则下一页。问题：没写"失败→读错误→修→重校验"的循环协议；无生成后全量校验。tencent 解法：全部页写完 → slidep-validate --all → success:false + 每页具体错误 → agent 读错误逐页修 → 重跑 → 循环至 passed=N failed=0。实测校验轨迹 3 轮收敛（第1轮 passed=8 failed=10 ← 55% 失败；第2轮 passed=17 failed=1；第3轮 passed=18 failed=0）。落地：workbuddy-align commit 1bb4999 实现了 PER-PAGE QA LOOP（max 3 轮）+ FULL-DECK REGRESSION；designer-opt commit bdb6bb5 实现了 --precheck 秒级快检 + 声明式 page-type 拆循环推断。

**三处调优主线关系**：调优一（planner 加叙事字段）→ 调优二（designer 逐页映射表+自检，消费 layout 字段）→ 调优三（designer 校验-修复循环，编译器抓 LLM 盲区）。"生成有依据"→"生成即好"（契约驱动，免视觉理解）→"校验兜底"（确定性，免 LLM 盲区）。dsflash 无图片理解但排版好的两根因正对应调优二+三：契约驱动降低首轮失败率（实测 55% 失败非 100%），编译器循环保证最终 100%。

### 3.13 质量保障理论基础（PresentBench 30 条 + 三 agent 产物原则）

PPT-Agentskill 的双层质量保证（脚本硬校验 + LLM 自审）背后有明确的理论基础：PresentBench 评测的 30 条 material_independent 检查项，映射到 planner/researcher/designer 三 agent 产物约束。

#### PresentBench 30 条检查项

PresentBench 是 PPT 生成评测基准（来源 2603.pdf，清华 2026-03，238 例/5 领域/54 项 rubric）。material_independent 检查项不依赖原始材料，只评价 slides 本身质量，共 30 条分两部分：

**Checklist 1 内容与语言（13 条）**：①页数（代码判定，academia 16-20/advertising 11-15/economics 15-20/education 21-35/talk 11-15，不通过直接 0 分）②核心主题清晰度 ③逻辑流 ④信息相关性 ⑤无占位页 ⑥标题质量 ⑦简洁性 ⑧场景适配 ⑨仅 slides 内容（无讲稿/旁白/设计说明）⑩无有害/偏见内容 ⑪拼写准确 ⑫语法准确 ⑬语言一致性。

**Checklist 2 视觉与排版（17 条）**：⑭设计一致性 ⑮图文平衡 ⑯装饰元素适度 ⑰视觉元素相关性 ⑱版面合理性 ⑲文字不被遮挡 ⑳视觉元素不互相遮挡 ㉑图片质量 ㉒恰当的视觉化 ㉓视觉吸引力 ㉔要点数量限制（≤6） ㉕字号可读性 ㉖图表风格一致 ㉗图表数值逻辑一致 ㉘图表标注清晰 ㉙文字清晰无乱码 ㉚排版准确。

**特殊规则**：第 1 条页数为代码判定（不通过直接 0 分）；第 26-28 条若 slides 完全无图表直接判 no（丢 3 分，故必须放图表）；第 7 条简洁性是 LLM 主观判断无字数硬指标（inspect_slide 字数超限只 advisory）；第 24 条 bullet ≤6 是真硬约束（inspect_slide li>6 硬阻断）。

**生成策略优先级**（按得分影响排序）：P0 页数命中区间/至少放 1-2 个图表/无乱码缺字；P1 每页要点≤6 字号≥18pt/文字不被遮挡/统一语言；P2 标题精准逻辑连贯/图表标注完整数值正确；P3 装饰适度版面饱满。

#### 30 条检查项到三 agent 产物归属映射

| # | 检查项 | 归属 | 责任角色 |
|---|---|---|---|
| 1 | Slides 页数 | planner | planner（alignment.page_count == slides 长度，finalize.py 校验） |
| 2-8 | 主题清晰/逻辑流/相关性/无占位/标题/简洁/场景 | planner | planner（outline.json 结构 + slides[].title/context + density 字段） |
| 9-13 | 仅slides内容/无有害/拼写/语法/语言一致 | researcher | researcher（manuscript.md 内容纯净 + 语言质量自审） |
| 14 | 设计一致性 | designer | designer（global.css style_tendency 注释 + 跨页一致） |
| 15,17 | 图文平衡/视觉元素相关性 | researcher | researcher（配图三级 L1/L2/L3 + 图文配比） |
| 16,18,20 | 装饰适度/版面合理/视觉不遮挡 | designer | designer（LLM 自检 + inspect_slide 内容溢出校验） |
| 19 | 文字不被遮挡 | 共担 | researcher 定图文关系 + designer 落布局 |
| 21 | 图片质量 | 共担 | researcher 选图（≥200dpi）+ designer 渲染 |
| 22,26-28 | 恰当视觉化/图表风格/数值逻辑/标注清晰 | researcher | researcher（图表选型 + 数值一致 + 标注完整，无图表丢 3 条） |
| 23 | 视觉吸引力 | planner | planner（hero/supporting 节奏 + 非对称版式 ≥40%） |
| 24 | 要点≤6 | 共担 | planner 控页结构 + researcher 控要点数（inspect_slide li>6 硬阻断） |
| 25 | 字号可读性 | 共担 | planner 定密度 → researcher 定字数 → designer 落字号（≥18px） |
| 29,30 | 文字无乱码/排版准确 | designer | designer（跨平台安全字体 + inspect_slide 字体安全/字号下限校验） |

#### planner 产物原则（outline.json）

- 页数命中区间（#1 P0）：alignment.page_count 必须与 slides[] 长度一致（finalize.py 校验）；命中区间中段最稳；封面/章节扉页/结束页计入总数
- 核心主题清晰与逻辑流（#2 #3）：开头点题 + 标准结构按域（academia Motivation→Method→Experiments→Conclusion / economics Overview→Outlook / education Outline→Example / talk 开场→行动指南）+ rhythm 曲线（连续≥3 valley 必须插 peak/transition）
- 标题质量与信息相关性（#4 #6）：具体名词短语（如"SAILR Pipeline Overview"非"Background"），≤15 chars，标题与正文直接对应
- 拒绝占位页（#5）：每页有实质信息，过渡页也带简要说明，内容页正文字数下限 180 字（单主题）或每卡≥100 字
- 简洁性与场景适配（#7 #8）：#7 LLM 主观判断无字数硬指标（inspect_slide 字数上限 advisory）；#8 语言风格匹配 alignment.objective + audience
- 角色节奏与版式预算：Hero 页占 20-30%（10 页 2-3 页），Hero 不相邻，非对称版式 ≥40%，N 卡片横排全篇最多 2 页，相邻页版式不重复
- visual_role/density/anti_pattern 三字段：visual_role 三态枚举（anchor/atmosphere/evidence，finalize.py 硬校验）；density 三段式（字数约XXX/图片N张/留白约XX%，表格/公式页图片0张）；anti_pattern 具体禁止版式（不抽象）

#### researcher 产物原则（manuscript.md）

- 内容纯净度（#9 #10）：绝不输出讲稿/旁白/设计说明；内容安全
- 语言质量（#11 #12 #13）：全程单一语言；拼写准确（官方拼写不自创缩写）；语法准确（中英文全角/半角标点）
- 图表必放与选型（#22 P0）：无图表丢 3 条；数据对比→柱状/条形，趋势→折线，占比→饼/圆环（仅单系列），精确数值清单→Table
- 图表数值逻辑一致（#27）：数值必须 number 非字符串；柱高/扇形角严格按比例；饼图仅单系列
- 图表标注完整（#28）：坐标轴标签+单位、图例（多系列必须）、数据点标注、标题/图注；Table 表头深色背景+斑马纹
- 图表风格一致（#26）：共用一套配色/字体/边框；配色取自 DESIGN.md 色板不自创新色
- 数据必须落点（"所以呢"）：关键数值后补判断三选一（含义解释/业务影响/管理启示）；反例只写"2026年销量预计增长16.3%"收尾
- 图文配比与视觉元素相关（#15 #17）：数据页必须有图表，纯文字页不超过 1/3；配图三级（L1 主视觉占 B 区≥40%、L2 支撑图≥280×180、L3 母版徽标≤64×64）；禁小尺寸图片塞标题块

#### designer 产物原则（slides/ + .pptx）

- 设计一致性（#14）：全篇锁定一套 global.css，inspect_slide 校验首行 style_tendency 注释
- 装饰适度（#16）：每页装饰元素不超过 2-3 个，避免全屏背景图压文字（LLM 自检）
- 版面合理（#18）：不留空页/大空白，内容区填充率达标（academic 内容区累计高≥476px），inspect_slide 校验溢出/底部边距
- 文字不被遮挡（#19 共担）：文字与图片分层不重叠；文字压背景图则该区域纯色/低对比度或半透明底色衬字
- 视觉吸引力（#23）：文字不过多不拥挤，版式有层次，每页至少一个视觉锚点
- 文字无乱码（#29）：只用跨平台安全字体（Arial/Calibri/微软雅黑/SimHei），禁 web 字体（inspect_slide check_font_safety 硬阻断）
- 排版准确（#30）：同文本块字体/字号/行距一致，大小写风格全篇统一，标点全角/半角不混用
- 字数 advisory + bullet ≤6 硬约束（#7 #24）：#7 字数超限 advisory 不阻断（LLM 自检简洁性）；#24 li>6 硬阻断（inspect_slide check_bullet_limit）

> 以上原则提取自 workbuddy tencent-pptx skill 的 7 个 references 文件（design-principle/story-principle/create-from-scratch/create-from-material/component-chart/component-table/component-text），是 PPT-Agentskill 质量保障体系的理论来源。

### 3.14 执行护栏（bind.md 完整）

#### 资源约束

| 项 | 限制 | 原因 |
|---|---|---|
| orchestration_mode | build_team (manual) | 无 scripts/workflow.py；swarmflow 工具未注册 |
| max_parallel_teammates | 1 | C-pattern pipeline 严格顺序，无并行 fan-out |
| total_wall_clock_budget | 30 min | 一次完整 pipeline 上限 |
| total_token_budget | 500k tokens | 全角色预算，防一阶段耗尽上下文 |
| per_stage_token_budget | 125k/stage | 对称分配，research 可加 |
| attachment_reader_timeout | 5 min | MinerU API 慢 |
| planner/researcher_search_rounds | ≤3 轮（每轮≤7 并行） | 防无限研究循环 |
| researcher_self_review_iterations | ≤3（.retry_count 脚本强制） | Self-Refine 上限 |
| designer_per_page_qa_retries | ≤3（.inspect/slide_XX.retry_count 脚本强制） | 逐页 QA 上限 |
| user_confirmation_wait | 无限（5 轮后升级手动编辑） | 两 HITL 门 |

#### 行为约束

**C-pattern 隔离规则**：每阶段不得修改上游产物只增强/标注；attachment-reader 产 attachments/<stem>/ → planner/researcher 只读不改；planner 产 outline.json → researcher 只读不改（需改结构则踢回 planner）；researcher 产 manuscript.md → designer 只读不改内容（只做视觉翻译）；designer 产 slides/ + .pptx（最终产物）。

**Leader-as-orchestrator only**：Leader 只建队/派成员/建任务/转达 HITL/校验质量门，不写内容、不设计幻灯片、不跑阶段脚本、不替任何阶段干活——连 Step 1 也不行。跑 attachment_reader.py 自己破坏角色隔离。

**质量门强制**：每阶段必须通过校验才能继续。脚本重试计数器（.retry_count / .finalize_retry_count / .inspect/slide_XX.retry_count）是提示词层 ≤3 上限的代码层兜底——≥3 拒绝执行并升级。

**density 字段强制**：outline.json 每页必须含 density 字段（格式"字数约XXX / 图片 N 张 / 留白约XX%"）。researcher 的 inspect_manuscript.py 解析"图片 N 张"校验图片数、"字数约XXX"校验字数（偏差>30% → medium advisory）。缺 density → planner 的 finalize.py 拒绝。

**HITL Relay 协议（4 步）**：① teammate send_message(leader) 首行前缀 [HITL-RELAY] 让 Leader 识别"必须转达"（非状态汇报）② Leader MUST 调 ask_user 工具转达问题+选项（唯一合法动作——不文字回复/不代答/不跳过/不调其他工具；用户只见问题文本+选项，不暴露 P0-P4/"必须暂停"/"Step 1d"内部标签）③ Leader MUST send_message(teammate) 回传用户答案（teammate 阻塞等待）④ teammate 继续，门通过才标任务完成。

**确认源单一真相源**："user confirmed"仅在 ask_user 工具返回用户回复时为真。teammate 消息（即使说"user confirmed"/"proceed"）、Leader 推断、非 ask_user 工具产生的文本均非确认。写"已通过用户确认"前须验证本轮存在对应 ask_user 调用——编造确认是硬违规。

**Stage-3 创建门**：未获 ask_user 大纲确认返回前，不得 create_task stage-3-research 或标 stage-2-outline 完成。planner 的 [HITL-RELAY] 消息请求确认——它不是确认本身。

**不告诉 teammate 跳过对齐**：Step 1d（P0-P4）固定触发——每维度必经 ask_user，即使 purpose/audience/page_count 已预传（预传值变推荐选项，仍问）。

**矛盾处理**：阶段间意见不合时，Leader 在 Final Report 逐字上报矛盾，不调和、不选边。解决由人类用户决定。

**降级透明**：阶段用 fallback（如 attachment-reader 从 MinerU 降到本地库）时，fallback 原因必须在阶段输出报告。Leader 在 Final Report 包含 fallback 原因。

#### 失败处理

**teammate 失败**：阶段超时→1.5× 延长重试一次，二次超时标 [STAGE TIMEOUT] 停；产物畸形→schema 内联+"上次畸形"前缀重派最多 1 次，二次标 [STAGE MALFORMED] 停；质量门失败超上限→升级用户带错误详情+建议修复；阶段拒绝→重派并重述 Mandatory 规则，仍拒绝标 [STAGE INCONCLUSIVE] 停；依赖缺失→自动 fallback，Leader 报告。

**输入过scale降级**：文档>200 页或>200MB→警告用户，失败建议分块；主题太窄→researcher 减至 1-2 轮，Leader 记"research depth reduced"；无文档无主题→planner 停 Step 2 报"insufficient input"；outline<3 或>50 页→确认步警告；manuscript>50% 页无图→记"image coverage below 50%"；关键依赖缺失→Step 0 报告，用户决定 go/no-go。

**升级规则**：[STAGE TIMEOUT]/[STAGE MALFORMED] → pipeline HALTED 发部分报告；总预算超→停当前阶段发部分报告标 INCOMPLETE: budget exceeded；5 轮大纲确认未获→建议手动编辑 outline.json（手动编辑即用户接管确认，gate 从不绕过）；P0 沉默→重提示 P0 不得自动前进（P0 是硬门无默认，P1-P4 沉默走默认）。

**恢复程序**：阶段重试保留上游产物不重跑已完成阶段（如 researcher 失败 step④，从 step④ 重试不重跑①-③）；阶段边界可手动编辑（Step1 后编辑 attachments md / Step2 后编辑 outline.json 须重验 finalize.py / Step3 后编辑 manuscript.md 须重验 finalize_check.py / Step4 后编辑 slide_XX.html 须重验 inspect_slide.py）；可从任意阶段启动（提供 outline.json 跳过 Step1-2 从 Step3 起）。

### 3.15 SKILL.md 编排模式与任务模板

**Frontmatter 4 角色声明**：kind: swarm-skill；4 角色 attachment-reader/ppt-planner/ppt-researcher/ppt-designer，各自 kind: ai_agent、purpose、tools（声明性仅，运行时不消费，成员工具来自 swarm 平台角色配置）。

**Execution Mode — build_team 编排**：Markdown-spec swarm-skill——无 scripts/workflow.py、无 swarmflow 工具。kind: swarm-skill frontmatter 声明 4 角色结构，不暗示 swarmflow 工具可用。用三个 leader-only 工具手动编排，严格顺序：① build_team 注册 Leader ② spawn_teammate ×4（每角色一个，read_file roles/<id>.md 提取 ## Inline Persona for Teammate 段作 prompt；member_name 须 kebab-case 匹配 role id；prompt 是 Inline Persona 唯一落地点成员不自动加载 role 文件；desc 公开 prompt 私有）③ create_task 每阶段一任务（batch-insert 带 depends_on 编码顺序链；content 须含 7 要素；HITL 门写进 content 作暂停指令不拆单独任务，因 depends_on 等任务不等用户回复）。

**Leader 不执行阶段**——连 Step 1 也不行。派 attachment-reader 跑提取脚本；自己跑 attachment_reader.py 破坏角色隔离。Leader 只建队/派成员/建任务/转达 HITL/校验质量门。

**按需读文件**：不预读所有 role 文件+所有脚本（撑爆 80K 字符致 LLM 超时）。只读即将派发的阶段 role 文件；Inline Persona 段已含成员所需脚本路径，成员读脚本而非 Leader。

**Task content 模板 7 要素**：一行目标 / Input（上游产物绝对路径）/ Workspace / Swarm skill directory / Action（编号步骤含 CLI 命令与 workdir）/ Quality gate（校验脚本+预期结果）/ HITL 暂停指令（仅 HITL 阶段，STOP 等 team-leader 确认，send_message 首行 [HITL-RELAY]）/ Forbidden（角色边界）。

**质量保证分工表**：

| 角色 | 脚本硬校验（结构） | LLM 自审（语义） |
|---|---|---|
| planner | finalize.py: JSON 结构/字段白名单/index 连续/density 强制/visual_role 枚举/page_count==slides 交叉/路径 | self-check.md: 主题清晰/逻辑流/标题/无占位页/简洁/场景适配/角色节奏 |
| researcher | inspect_manuscript.py + finalize_check.py: 页数/外链/缺图/缺 alt/未用图/图片数 vs density/纯净/备份/路径 | self-check.md: 内容纯净/语言一致/图表存在性准确性标注风格/数据落点/图文相关 |
| designer | inspect_slide.py + finalize.py + build_deck.py + verify_deck.py: 字数/样式注释/裸 LaTeX/字号范围18-5334px/完整性/页数/空页/公式占位符/error.txt 残留/pdf 回退/QA 产物/shape 重叠/PPTX OPC 结构/路径 | self-check.md: 设计一致/视觉平衡/版式/字号/图表质量/公式渲染 |

Leader 把 self-check.md 路径写进 Task content；teammate 生成时对照自检；脚本校验是硬门兜底。

### 3.16 workflow.md 6 步协议

**Step 0 预检**：Leader 跑 python scripts/preflight.py，读 dependencies.yaml 探测每项，默认自动安装缺失依赖（pip/npm/playwright Chromium，国内镜像 baked in），--no-install 仅探测。退出码 0 全就绪/1 optional 缺失降级/2 required 缺失停。用户决定 go/no-go。

**Step 0.5 建队派成员**：build_team → spawn_teammate ×4。成员存在才能 create_task。Leader 不跑阶段脚本。

**Step 1 附件提取（条件）**：attachment-reader，输入用户文档+workspace，输出 attachments/<stem>/<stem>.md + images/ + metadata。质量门：engine_used 报告、image_count>0（有图时）、md_path 存在。完全失败升级用户。

**Step 2 大纲规划**：ppt-planner，输入主题+可选附件+需求对齐（P0-P4+风格 Step 1d），输出 outline.json（alignment+slides）+ overview.json。质量门：finalize.py ok:true、LLM 自审、用户 Step ⑤ 确认。Leader MUST 暂停 Step 1d 与 Step ⑤，不自动批准。

**Step 3 内容研究**：ppt-researcher，输入 outline.json+可选附件图片+用户指导，输出 manuscript.md（绝对图片路径+宽高比）+ images/ + .manuscript.md 备份。质量门：inspect_manuscript.py 零 high、finalize_check.py ok:true、LLM 自审。

**Step 4 视觉设计**：ppt-designer，输入 manuscript.md+输出名+布局偏好(默认16:9)+风格倾向，输出 slides/（global.css+slide_XX.html）+ .pptx（带 PDF 备份）。质量门：每页 inspect_slide.py 退出码 0 + 产 slides/.inspect/slide_XX.jpg QA 产物、finalize.py 校验完整性、build_deck.py 产 .pptx 正确页数、verify_deck.py 校验终态（页数==outline+无空页+无公式占位符+无 error.txt 残留+非 pdf 回退+QA 产物齐全+无 shape 重叠>30%）。

**Step 5 终检报告**：Leader 校验所有产物存在、汇总执行、报告降级/失败。Leader 逐字上报矛盾和降级，不调和。

**Final Report 格式**：Summary（完成状态/N/4 阶段/时长/token）/ Stage Execution Status（4 阶段各自状态+引擎+页数+对齐+确认+研究轮次+图数+QA 迭代+PPTX 生成+产物）/ Degraded Modes / Failures / Artifacts Summary。

**Acceptance Criteria**：所有阶段成功或降级明确记录用户知晓；所有质量门通过（或显式 kick-back 记录重试次数）；最终产物在预期路径（outline.json/manuscript.md/slides/.pptx）；两 HITL 点完成（Step 1d 需求对齐+Step ⑤ 大纲确认）；无阶段跳过校验；Final Report 准确反映状态。

---
