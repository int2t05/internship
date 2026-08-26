#!/usr/bin/env python3
"""根据 manuscript.md 批量生成 slide_XX.html"""
import re, os

OUTPUT_DIR = r"d:\Project\Person\internship\slides"

CSS_LINK = '<link rel="stylesheet" href="global.css">'

def html_template(page_type, header_title, content_html, page_num):
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
{CSS_LINK}
</head>
<body>
<!-- page-type: {page_type} -->
<div class="region-header"><h1>{header_title}</h1></div>
<div class="region-content">
{content_html}
</div>
<div class="region-footer"><span>田沛康 · SAIE业务域</span><span>{page_num}/22</span></div>
</body>
</html>"""

def cover_html():
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
{CSS_LINK}
</head>
<body>
<!-- page-type: cover -->
<div class="region-content cover">
<div class="cover-title">实习生答辩</div>
<div class="cover-info">
<strong>员工：</strong>田沛康　　<strong>部门：</strong>SAIE业务域<br>
<strong>导师：</strong>向云武　　<strong>直接主管：</strong>李兆星<br>
<strong>实习周期：</strong>2026.07 — 2026.08
</div>
</div>
</body>
</html>"""

def toc_html(num):
    return html_template("toc", "目录", f"""
<div class="toc-list">
<div class="toc-item"><span class="toc-num">1</span><span>自我介绍</span></div>
<div class="toc-item"><span class="toc-num">2</span><span>学习及工作内容</span></div>
<div class="toc-item"><span class="toc-num">3</span><span>主要工作输出及总结</span></div>
<div class="toc-item"><span class="toc-num">4</span><span>自我反思及下一步学习计划</span></div>
</div>""", num)

def ending_html():
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
{CSS_LINK}
</head>
<body>
<!-- page-type: ending -->
<div class="region-content cover">
<div class="cover-title">致　谢</div>
<div class="cover-info">
感谢在座的评委、各位领导百忙中抽出时间参与本次答辩！<br><br>
感谢导师向云武、主管李兆星、周围的同事的指导与帮助！<br><br>
感谢所有给予过帮助指导和工作支持的人们！
</div>
</div>
</body>
</html>"""

def content_page(title, page_type, body, num):
    return html_template(page_type, title, body, num)

def points(items):
    return '<div class="points">' + ''.join(f'<div class="point">{x}</div>' for x in items) + '</div>'

def summary(text):
    return f'<div class="summary-line"><p style="margin:0;">{text}</p></div>'

def mermaid(code):
    return f'<div class="mermaid-box"><pre class="mermaid">{code}</pre></div>'

def table(headers, rows):
    h = '<tr>' + ''.join(f'<th>{x}</th>' for x in headers) + '</tr>'
    body = ''
    for r in rows:
        body += '<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>'
    return f'<table><thead>{h}</thead><tbody>{body}</tbody></table>'

pages = []

# 1 封面
pages.append(cover_html())

# 2 目录
pages.append(toc_html(2))

# 3 自我介绍
pages.append(content_page("自我介绍", "section", f"""
<div class="cover-info" style="text-align:left;font-size:20px;line-height:2.2;">
<strong>教育经历</strong><br>
2023.09 — 2027.06　华南理工大学　计算机科学与技术<br><br>
<strong>入职华为</strong><br>
2026.07.01　SAIE业务域（ICT BG）<br>
Omni生态 大数据方向
</div>
""", 3))

# 4 目录
pages.append(toc_html(4))

# 5 学习及工作内容
pages.append(content_page("学习及工作内容介绍", "table", table(
    ["分类", "工作学习任务", "输出和收获"],
    [
        ["个人相关", "1、大数据基础学习（Flink/Spark/鲲鹏生态）2、Agent生态调研（九问平台、27方案）", "建立流处理全貌认知 理清skill驱动机制"],
        ["工作相关", "1、OmniStream表达式开发 2、PPT-Agentskill开发与调优", "10+表达式提PR 4角色流水线落地 公式原生插入WPS验证"],
    ]
) + summary("学习与工作交织推进，个人相关打基础、工作相关出产出，两者相互支撑"), 5))

# 6 目录
pages.append(toc_html(6))

# 7 OmniStream项目背景
pages.append(content_page("项目背景：OmniStream--基于Flink生态的流处理性能加速项目", "section", mermaid(
"""flowchart LR
    subgraph Flink瓶颈
    A1[GC停顿] --- A2[JIT预热慢] --- A3[对象序列化]
    end
    subgraph OmniStream对策
    B1[C++原生算子] --- B2[向量化SIMD] --- B3[整链下沉] --- B4[状态缓存]
    end
    A1 --> B1
    A2 --> B2
    A3 --> B3"""
) + points([
    "Flink跑在JVM上，高负载下三类瓶颈",
    "内存回收停顿打断低延迟",
    "字节码预热慢，热点才编译",
    "对象序列化开销逐条放大",
    "OmniStream用C++重写算子，配合向量化指令",
    "消除JVM开销，端到端提升流处理性能",
]), 7))

# 8 三仓库双层架构
pages.append(content_page("三仓库双层架构：Java适配层 + C++核心层", "structure", mermaid(
"""flowchart LR
    U[SQL/数据流/UDF] --> J[Java适配层 OmniAdaptor]
    J -->|原生调用| C[C++核心层 OmniStream]
    C --> K[OmniOperator 向量化内核]
    J -.->|不支持回退| F[Flink原生Java]"""
) + table(
    ["仓库", "职责", "产物"],
    [["OmniStream", "原生运行时框架", "libtnel.so"], ["OmniAdaptor", "Flink桥接与算子替换决策", "flink-tnel.jar"], ["OmniOperator", "底层向量化算子内核", "5×.so + 2×.jar"]]
) + summary("零侵入接入，只改两个配置文件，不改Flink内核代码"), 8))

# 9 表达式开发总览
pages.append(content_page("表达式开发总览：让SQL表达式走Native加速路径", "structure", mermaid(
"""flowchart TD
    E[表达式] --> P{可向量化?}
    P -->|是| V[向量化执行]
    P -->|否| C{可即时编译?}
    C -->|是| G[编译成机器码]
    C -->|否| J[回退Java]"""
) + points([
    "5阶段生命周期：规划→部署→解析→编译→运行",
    "四类分类体系：Type A标量函数、Type B特殊语法、Type C聚合、Type D别名",
    "双执行后端：向量化优先，即时编译次选，都不行回退Java",
    "选路公式：优先向量化，不行才即时编译",
]), 9))

# 10 表达式开发案例
pages.append(content_page("表达式开发案例：三类范式覆盖", "table", table(
    ["案例", "范式", "要点"],
    [["IFNULL", "别名映射", "一行代码完成原生化"], ["LEFT/RIGHT", "纯向量化", "Unicode安全，码点不截断"], ["BETWEEN", "借原语编译", "语义可拆，组合执行"], ["SIMILAR TO", "专用函数", "正则不可拆，解释执行"]]
) + points([
    "IFNULL：语义等价已有函数，一行映射完成原生化",
    "LEFT/RIGHT：按UTF-8码点切片，绝不切断多字节字符",
    "BETWEEN：语义可拆成两个比较，借已有原语组合执行",
    "SIMILAR TO：正则不可拆，需专用函数解释执行",
]), 10))

# 11 问题排查
pages.append(content_page("问题排查：BETWEEN崩溃定位与vanilla对照组二分法", "model", mermaid(
"""flowchart TD
    B[崩溃现象] --> V{原生Flink也崩?}
    V -->|是| U[上游缺陷：规避输入]
    V -->|否| N[本侧bug：修复]"""
) + points([
    "问题：BETWEEN在反向区间下崩溃",
    "方法：用原生Flink做对照组二分法",
    "投影路径：原生也崩 = Flink源码缺陷，规避输入",
    "过滤路径：原生正常 = 本侧bug，修复",
    "让\"甩锅还是背锅\"有客观依据",
]), 11))

# 12 AgentOS项目背景
pages.append(content_page("项目背景：AgentOS--一体机办公Agent与PPT-Agentskill", "section", mermaid(
"""flowchart BT
    L5[jiuwenswarm 多智能体] --> L4[开发平台+技能分发]
    L4 --> L3[Agent框架 agent-core]
    L3 --> L2[分布式运行时]
    L2 --> L1[系统服务底座]"""
) + points([
    "基于九问Agent平台开发一体机办公Agent",
    "把大模型能力做成本地化、可编辑交付的办公智能体",
    "产物必须可编辑（中文办公刚需）",
    "本地化部署，接一体机模型降本",
    "WPS兼容性是硬约束，催生公式原生插入核心难题",
]), 12))

# 13 4角色流水线
pages.append(content_page("4角色流水线架构：attachment-reader → planner → researcher → designer", "structure", mermaid(
"""flowchart LR
    R[附件提取] --> P[大纲规划]
    P -->|outline.json| RE[文稿研究]
    RE -->|manuscript.md| D[视觉设计]
    D -->|slides + pptx| OUT[交付]"""
) + points([
    "4角色各司其职，强制分工与校验",
    "attachment-reader：MinerU-first提取结构化内容",
    "ppt-planner：设计大纲结构+需求对齐",
    "ppt-researcher：调研信息+写文稿+自审",
    "ppt-designer：视觉平衡HTML幻灯片+逐页QA",
    "双层质量保证：脚本硬校验 + LLM自审",
]), 13))

# 14 PPTv2agent参考
pages.append(content_page("PPTv2agent参考：DeepPresenter双Agent架构与Content Style", "model", mermaid(
"""flowchart LR
    R[Researcher 深度检索] -->|共享观察空间| P[Presenter 设计生成]
    P -->|渲染像素图| F[环境接地反思]
    F -.->|反馈修正| P"""
) + points([
    "DeepPresenter ACL2026 SOTA（均分4.44超Gamma 4.36）",
    "双Agent共享观察空间 + 环境接地反思",
    "信息加工成半成品而非原材料",
    "每页围绕一个核心洞察，金字塔原则",
    "图片承载信息而非填空，优先可信来源",
    "学术参考方法论，PPT-Agentskill是工程落地",
]), 14))

# 15 skill框架比较
pages.append(content_page("skill框架比较：ppt-pipeline-swarm vs 标准swarm-skill vs PPTv2agent", "table", table(
    ["维度", "标准swarm-skill", "ppt-pipeline-swarm"],
    [["编排", "工具跑原语", "手动建队编排"], ["质量门", "脚本内嵌", "脚本+LLM双层"], ["人机交互", "原语", "转达协议"]]
) + points([
    "相比标准形态：简化为手动编排，适合固定流水线",
    "相比PPTv2agent：平台上的工程实现，非学术方法",
    "设计器引擎源自PPTAgent v2提取重写为独立CLI",
    "选型依据：固定流水线+断点续跑→编排式",
]), 15))

# 16 公式原生插入问题
pages.append(content_page("项目背景：公式原生插入--可编辑OMML方程而非图片", "section", mermaid(
"""flowchart LR
    F1[转图片 不可编辑] -->|迭代| F2[转换库 WPS不渲染]
    F2 -->|迭代| F3[重型工具 太重]
    F3 -->|最终| F4[手写解析器 WPS可见]"""
) + points([
    "需求：公式必须可编辑，WPS兼容",
    "Python PPT库不支持原生公式（2019年至今未解决）",
    "PowerPoint需特殊命名空间包装",
    "WPS渲染有多个兼容陷阱：不渲染直立体、不认某些包装",
    "方案四次迭代：图片→转换库→重型工具→手写解析器",
]), 16))

# 17 公式原生插入方案
pages.append(content_page("产出：公式原生插入方案与验证", "model", mermaid(
"""flowchart LR
    R[文稿写公式] --> D[设计器标记]
    D --> C[收集到sidecar]
    C --> I[后处理注入原生方程]
    I --> P[PPTX 可编辑公式]"""
) + points([
    "手写递归下降解析器直接生成OMML",
    "全链路：文稿→设计器标记→收集→注入原生方程",
    "26个公式全部成功，WPS可见",
    "零新增依赖，复用已有库",
    "文件更小（32KB vs 图片96KB）",
    "配套公式识别规范决策表与校验脚本",
]), 17))

# 18 Wiki产出
pages.append(content_page("Wiki产出：工作指南、知识拓展、基础学习、工程实践21篇", "table", table(
    ["分类", "篇数", "内容"],
    [["基础学习", "5", "PPTAgent框架解析、九问skill机制、swarmflow原语"], ["知识拓展", "6", "4种组装方式选型、公式插入8项目对比、样式模板调研"], ["工作指南", "2", "PresentBench 30条检查项、三agent产物设计原则"], ["工程实践", "8", "4分支审计+纯净性总结，50+commit可追溯"]]
) + points([
    "21篇约34万字，5个开源项目横向调研",
    "公式方案26公式端到端验证，12套CSS模板确定性物化",
]), 18))

# 19 目录
pages.append(toc_html(19))

# 20 收获与不足
pages.append(content_page("收获和体会/有待改进之处", "data", mermaid(
"""quadrantChart
    title 收获与不足分布
    x-axis "深度低" --> "深度高"
    y-axis "成长有限" --> "成长显著"
    "工程能力": [0.7, 0.85]
    "方法论": [0.6, 0.9]
    "底层深度": [0.25, 0.4]"""
) + points([
    "收获：代码开发能力提高、培养工程化思维",
    "收获：方法论沉淀（vanilla二分法、可观察性、纯净原则）",
    "不足：底层向量化内核与编译器实现了解不够清楚",
    "不足：skill包零实战验证，最佳实践陈述非工作流提炼",
    "不足：8月切入Agent项目后OmniStream深度推进受限",
]), 20))

# 21 下一步学习计划
pages.append(content_page("下一步学习计划", "summary", points([
    "1、OmniStream开发继续推进：补齐剩余表达式类型，推进性能验证与开源贡献",
    "2、底层深度补齐：深入向量化内核与编译器实现，从能用走向吃透",
    "3、Agent工程化实战：推进skill包真实场景跑通，深化公式原生插入能力扩展",
]) + mermaid(
"""flowchart LR
    A[OmniStream开发推进] --> B[底层深度补齐]
    B --> C[Agent工程化实战]"""
), 21))

# 22 致谢
pages.append(ending_html())

# 写入文件
for i, html in enumerate(pages, 1):
    path = os.path.join(OUTPUT_DIR, f"slide_{i:02d}.html")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  wrote {path}")

print(f"\n共生成 {len(pages)} 个 slide")
