---
name: disk-parliament
description: >
  专家议会 v2.2 — 多 Agent 盘上异步通信协议。Supervisor 自动坍缩需求→生成 ROSTER→
  spawn 子 Agent（支持逐专家绑定不同模型）→盘上写信→收敛冻结。引入岗位系统（252个固化模板 + 人设拮抗），
  人设与岗位分离，支持一岗双人拮抗。
  议题肃正 → 需求坍缩 → 岗位匹配 → 人设拮抗配置 → spawn 子 Agent →
  盘上 mail 异步通信（禁止 SendMessage）→ 收敛判定 → 冻结产出。
  Supervisor 只做轮询唤醒 + 收敛判定，不编排发言顺序。
  触发词：专家议会、盘上议会、开个议会、启动议会、开个讨论组、异步讨论、
  多Agent协作、DiskParliament、异步通信、Protocol启动、专家讨论、
  开个异步会议、角色扮演讨论、多角色碰撞、专家会诊、
  复杂问题分析、话题讨论、团队协作、分工讨论。
metadata:
  version: "2.2"
  protocol_version: "v5.2"
  agent_created: true
---

# 专家议会（DiskParliament）v2.2

> **核心原则**：多 Agent 通过盘上文件（notes/）异步通信，禁止任何形式的即时对话（SendMessage）。
> 写出去的文件不可修改，没话说了就不写（自然停火），Supervisor 只做唤醒 + 判定。

> **⚠️ 协议执行者禁令（必须遵守）**
>
> 本 Skill 的执行者（即你当前的角色）是**协议执行者**，不是分析师、设计师或规划者。
>
> **禁止行为（违反即协议失败）：**
> - ❌ 在进入 T0 之前替用户分析/规划/设计方案
> - ❌ 在 T0 之前产生任何与议题相关的输出
> - ❌ 替子 Agent 写内容、做分析、做决策
> - ❌ 在 spawn 之前产生任何"大致规划"或"初步分析"
>
> **正确行为：**
> - ✅ 收到用户请求 → 立即进入 T0（强制索要主题 + 产出）
> - ✅ 用户未提供完整信息 → 追问，不猜测
> - ✅ T1-T5 按协议步骤执行
> - ✅ 唯一一次输出在 T5 冻结后：BRIEFING.md + 通知用户
>

---

## 一、触发与议题肃正（T0）

### 触发条件

用户输入符合以下任一：
- 显式要求启动协议（"开个笔友""启动协议""开个讨论组"）
- 任务复杂度超过单 Agent 能力范围，适合多角色异步讨论
- 提供了 central topic 且需要跨角色分析/设计

### T0a — 议题提取（强制索要）

```
Supervisor 检查用户是否同时提供了：
  ① 讨论主题（议题名称 + 简要描述）
  ② 目标产物（期望产出什么，什么格式）
  ③ 模型配置（所有专家用什么模型？还是各配各的？）

如果任一缺失 → Supervisor 必须主动索要，禁止猜测。
如果用户描述模糊 → Supervisor 必须追问至清晰。
如果用户说"随便讨论一下" → 拒绝。要求用户明确意图。
```

**③ 模型配置说明：**

```
用户可能有以下模型偏好之一：
  a) "全部用默认模型" — 不指定，用 Supervisor 当前模型
  b) "全部用 XX 模型" — 统一绑定
  c) "不同专家用不同模型" — 在 T1 坍缩时逐条配置 skill_mode.model
  d) 指定了具体 API / 本地地址 — 写入 CentralTopic.md 的「模型配置」

⚠️ 模型名格式：
  模型名字符串必须是 WorkBuddy models.json 中的 id 字段（不是 display name）。
  例如：models.json 中有以下条目：
    {"id": "deepseek-v4-pro", "name": "DeepSeek-V4 Pro", ...}
    {"id": "mimo-v2.5",       "name": "mimo-v2.5",       ...}
  则 CentralTopic.md 中写 "deepseek-v4-pro"，而非 "DeepSeek-V4 Pro"。
  Agent({model: "deepseek-v4-pro"}) 会按 models.json 的 id 路由到对应 API endpoint。

Supervisor 必须：
  - 逐项确认用户意图（"你希望所有专家用同一个模型还是各自配置？"）
  - 如果用户指定了模型名，确认其是否在 models.json 中有对应 id
  - 如果用户用了 display name（如 "DeepSeek-V4 Pro"）而非 id，纠正之
  - 将模型配置写入 CentralTopic.md（见下方模板更新）
```

### T0b — 格式肃正（Supervisor 必须执行）

在 CentralTopic.md 写入前，Supervisor 必须完成以下三项校验和补全：

#### ① 议题边界

```
明确"讨论范围"和"不在范围内"。
如果用户未提供边界 → Supervisor 协助划定，用户确认。
```

#### ② 关键词定义（消歧）

```
列出议题中所有歧义性关键词。
对每个关键词给出"本议题中的精确含义"。
格式：| 术语 | 本议题中的含义 |

判定标准：这个词有没有两种以上常见理解？有 → 必须定义。
```

#### ③ 产出格式 Schema

```
为用户期望的目标产物设计具体格式。
包括：
  - 文件类型（.md / .yaml / .json / ...）
  - 节结构（必需节 / 可选节）
  - 字段要求（字段名 + 类型 + 约束）

格式 Schema 由 Supervisor 临时设计，写入 CentralTopic.md。
```

#### ④ 模型配置校验

```
CentralTopic.md 写入前，验证模型名字符串：

  1. 如果用户指定了模型名 → 检查是否为 models.json 中的合法 id
     Supervisor 无法访问 models.json 时 → 向用户说明格式要求：
     "模型名需要使用 WorkBuddy models.json 中的 id 字段，例如
      deepseek-v4-pro / mimo-v2.5 / qwen3_code 等，不是显示名称。
      请提供准确的模型 id。"
  2. 如果用户不确定模型 id → 建议先用当前模型，或让 Supervisor
     告知可用的模型 id（用户可自行查看 models.json）
  3. 如果在格式上无法对齐 → 标记模型为 "未指定（使用默认）"，
     用户可以在 spawn 前再行配置
```

### CentralTopic.md 模板（v5.0）

```markdown
# {议题名称}

## 议题描述
{用户确认的描述}

## 议题边界
### 在讨论范围内
- {范围 1}
- {范围 2}

### 不在讨论范围内
- {排除 1}
- {排除 2}

## 关键词定义
| 术语 | 本议题中的含义 |
|------|---------------|
| {术语 1} | {含义} |
| {术语 2} | {含义} |

## 模型配置
### 全局模型
| 配置项 | 值 |
|--------|-----|
| 默认模型 | {models.json 的 id，如 "deepseek-v4-pro"} |

### 专家个性化绑定（可选）
| 专家 | 绑定模型（models.json 的 id） | 理由 |
|------|------------------------------|------|
| {专家名} | {如 "mimo-v2.5"} | {为什么需要这个模型} |

> 模型名必须是 models.json 中某条记录的 id 字段。不是 display name，不是 API model name。
> 如果用户指定了全局模型，所有专家继承全局配置。
> 如果用户指定了专家个性化绑定，覆盖全局配置。
> T1 坍缩时，绑定模型写入 ROSTER[i].skill_mode.model。

## 期望产出 & 格式 Schema
### 产出物清单
| 产出物 | 文件名 | 类型 | 负责专家（owner） | 格式 Schema |
|--------|--------|------|-------------------|-------------|
| {产出 1} | {文件名} | {类型} | {ROSTER 角色名} | {节结构 + 字段约束} |
| {产出 2} | {文件名} | {类型} | {ROSTER 角色名} | {节结构 + 字段约束} |

> 每个产出物必须绑定一个 owner（ROSTER 中某角色）。owner 对该产出物的完成度负责。
> 格式 Schema 由 Supervisor 临时设计，包括必需节/可选节/字段类型及约束。

### 验收标准
- {标准 1}
- {标准 2}

## 参与者
（由 ROSTER 生成后填充）
```

### T0 完成校验

```
□ 用户明确提供了讨论主题 + 目标产物
□ 用户明确了模型配置（全局模型 / 个性化绑定 / 默认）
□ 模型名已确认使用 models.json 的 id 格式（非 display name）
□ 议题边界已划定
□ 歧义关键词已消歧
□ 产出格式 Schema 已设计
□ 用户已确认以上全部
```

---

## 二、需求空间坍缩（生成 ROSTER.md + PROTOCOL.md）

### T1 — 严格四步坍缩

**输入**：CentralTopic.md 内容
**输出**：ROSTER.md（YAML）+ PROTOCOL.md

#### 步骤①：解构问题域

```
操作：将用户意图分解为独立的维度切面。
规则：不预设维度数量。维度数量由问题复杂度决定。
      不预设维度命名方式。命名从问题域推导。
```

#### 步骤②：对每个维度生成硬框架

```
对步骤①输出的每个 dimension，生成：
  knowledge_scope:    该维度需要掌握的知识范围（50-200 字）
  attention_boundary: 业务边界/注意力焦点
    focus: [该维度关注的话题列表]
    ignore: [该维度不关注的话题列表]
  toolset:
    builtins: [通用工具列表]
    skills:   [需要加载的专业技能]
  skill_mode:
    model:  推荐绑定的模型（可选）
    对需要高推理或特殊能力的维度，绑定最合适的模型
    默认用 Supervisor 的模型，不绑也没关系
```

#### 步骤③：对每个硬框架生成软参数

```
对步骤②的每个条目，生成：
  id:               机器用标识符
  name:             角色名（中文 2-4 字或英文名，与项目调性匹配）
  cognitive_label:  认知标签 — 思维方式/推理风格（如 "系统思维·拓扑优先"
                    "第一性原理·量化驱动" "直觉跳跃·类比迁移"）
  preference_label: 偏好标签 — 在该领域内的偏好倾向（如 "偏好涌现规则而非硬编码"
                    "偏爱简洁方案" "倾向探索性分析而非假设检验"）
  hobby_scene:      爱好场景描述（见下方规则）

约束：禁止使用任何预设角色名。每次坍缩产生适合当前项目风格的新角色。
```

#### 步骤④：确定团队规模

```
2-3  维度 → 2-3 个专家（简单问题）
3-5  维度 → 3-5 个专家（中等问题）
5-8  维度 → 5-8 个专家（复杂问题）
团队规模由步骤①的解构结果决定。
```

#### 步骤⑤：人设拮抗配置 ★

```
对步骤④确定的关键维度，执行"一岗双人"策略：

1. 识别关键维度
   哪些维度是讨论的核心分歧点？如：机制设计 vs 系统架构、商业化 vs 长线运营
   这些维度需要两个专家形成拮抗张力。

2. 生成拮抗对
   对每个关键维度，生成两个 ROSTER 条目：
   - id-A / id-B（如 moon-face / prongs）
   - 相同的 profession（岗位前缀相同，后缀区分倾向）
   - 相同的 knowledge_scope 和 attention_boundary
   - 相反的 stance（核心立场对立）
   - 互补的 cognitive_label（如"直觉跳跃·类比迁移" vs "系统思维·拓扑优先"）
   - 独立的 hobby_scene（不同的人格锚点）

3. 拮抗约束
   - 非关键维度 → 单角色，不生成拮抗对
   - 拮抗对不能超过团队总规模的 50%（防止对称僵局）
   - 拮抗对的 stance 是对立但不是互斥——不是"对"与"错"，是"视角不同"
     如："机制至上" vs "好玩比新颖重要"——双方都可以是对的

4. 团队规模修正
   每增加一个拮抗对，团队规模 +1（因为多了一个人）
   原来的 3 维问题如果 1 维需要拮抗 → 4 人（2+1+1）
```

### ROSTER 字段数据流

> 每个 ROSTER 条目的字段从哪里来？Supervisor 按此表填充。

```
字段            来源                                示例
────────────────────────────────────────────────────────────
id              步骤③                                  "moon-face"
name            步骤③                                  "月亮脸"
profession      步骤② dimension + 步骤⑤ 后缀             "游戏设计师·创新驱动"
dimension       步骤①                                   "机制设计"

knowledge_scope 步骤②a 硬框架                          "机制设计理论..."
attention_focus 步骤②b attention_boundary.focus        ["机制创新", "玩法新颖性"]
attention_ignore 步骤②b attention_boundary.ignore      ["商业化", "UI实现"]

stance          步骤⑤ 拮抗配置（对立立场）               "机制至上。玩法不够新颖就不值得做。"
tags            从 attention_focus 取前 3 条            ["机制设计","第一性原理","玩法创新"]
default_init_prompt  公式："我是{name}（{profession}）。{stance}你需要我帮你分析什么？"

deliverables    从 CentralTopic.md 产出物清单分配        ["GDD文档", "机制规格表"]
toolset        步骤② toolset                           read/write/bash

cognitive_label 步骤③                                  "系统思维·拓扑优先"
preference_label 步骤③                                 "偏好涌现规则而非硬编码"
hobby_scene     步骤③                                  "双脚踩下踏板..."
skill_mode      步骤② skill_mode 或 T0 用户指定模型     模型绑定
```

### ROSTER → 岗位模板注入

```
Supervisor spawn 时执行：

1. 选择岗位模板：positions/{profession的前缀}.md
   如 profession="游戏设计师·创新驱动" → 选 positions/game-designer.md

2. 将 ROSTER 字段注入模板占位符：
   {{deliverables}}  ← roster[i].deliverables
   {{toolset}}       ← roster[i].toolset
   {{stance}}        ← roster[i].stance
   {{attention_focus}}  ← roster[i].attention_focus
   {{attention_ignore}} ← roster[i].attention_ignore
   {{cognitive_label}}  ← roster[i].cognitive_label
   {{preference_label}} ← roster[i].preference_label
   {{hobby_scene}}      ← roster[i].hobby_scene
   {{tags}}             ← roster[i].tags
   {{default_init_prompt}} ← roster[i].default_init_prompt

3. 注入后的完整文本 = Agent 的 spawn prompt
```

**拮抗对示例（来自固化岗位库）：**

| 岗位 | A 方 | B 方 | 张力 |
|------|------|------|------|
| 游戏设计师·创新驱动 | 月亮脸（机制至上） | 尖头叉子（可落地性） | 创新 vs 落地 |
| 产品经理·商业模型 | 王汉堡（卖得出去） | 劳薯条（长线金矿） | 短期 vs 长期 |

### ROSTER.md 格式（坍缩终产物，v5.1 — 扩展岗位字段）

> 新增 `profession`、`stance`、`tags`、`default_init_prompt` 等字段，
> 使 ROSTER 数据可直接注入 WorkBuddy 参数化模板（见四·模板填充逻辑）。

```yaml
# ROSTER.md — 由需求空间坍缩生成，供 Supervisor 逐条解析 spawn

roster:
  - id: "<步骤③>"
    name: "<步骤③>"
    # ── 岗位字段（映射至 WorkBuddy 参数模板）──
    profession: "<岗位名，如「游戏设计师·创新驱动」>"        # ← 新增
    stance: "<核心立场，如「机制至上…」>"                   # ← 新增
    tags: ["<标签1>", "<标签2>", "<标签3>"]                # ← 新增
    default_init_prompt: "<首次问候，如「我是{name}…」>"     # ← 新增
    # ── 硬性界定 ──
    dimension: "<步骤①>"
    knowledge_scope: "<步骤②a>"
    attention_boundary:
      focus: ["<步骤②b 关注>"]
      ignore: ["<步骤②b 不关注>"]
    deliverables: ["<该专家负责的产出物列表，对应 CentralTopic.md 产出物清单>"]
    toolset:
      builtins: ["read", "write", "bash"]
      skills: []
    # ── 软性标签 ──
    cognitive_label: "<步骤③>"
    preference_label: "<步骤③>"
    hobby_scene: "<步骤③ 爱好场景描述>"
    # ── 技能模式扩展（仅技能模式）──
    skill_mode:
      model: "<可选，models.json 的 id，如 deepseek-v4-pro>"
```

### 爱好场景描述（hobby_scene）设计规范

**底层机制**：围绕角色的 [爱好] 构造一句话，使句子内部各成分的语义关联度趋近于零——AI 处理时自注意力分数趋近平均分布，没有任何一个词能获得显著高于其他词的权重。分数是平的 → 没有信号被后续文本"抽走" → 结构性防泄漏到笔谈。

**构造规则**：
1. **第一人称自述体**：以"我"的私人经验为核心，不可迁移
2. **叙事闭合**：有起点有终点，不需要被续写或引用
3. **散射场**：与爱好天然关联的 N 个事物，彼此语义场差异足够大，注意力分散
4. **感官锚点**：身体感受而非概念（触觉/听觉/嗅觉优先）
5. **感叹破句**：非语法碎片打断学术性
6. **体感标签**：用感受词命名经验，非术语

**示例**（骑行爱好者专家）：
> 双脚踩下踏板，风和面颊匆匆告别，我就这样跑过了重庆、上海、香港、拉萨，啊，风驰电掣的感觉带我走过每一次比赛。

→ 分析：四城名（西南/华东/华南/高原）语义场互不重叠，注意力平均分散，无法被任何一个城市名"引力捕获"。

**关键约束**：
- 爱好场景描述是**提示词内部私产**，绝不进入 notes/ 笔谈通信
- 子 Agent 不得在笔谈中引用/类比/提及自己的爱好场景
- 它的作用 = 塑造人格基底和视角方向性——无声存在，不言说

### PROTOCOL.md 格式（Supervisor 配置）

```yaml
# PROTOCOL.md — 协议编排配置

protocol:
  name: "<协议实例名>"
  central_topic: "<引用 CentralTopic.md 路径>"

supervisor:
  wake_interval_minutes: 5
  silence_threshold: 3
  max_wakes_per_agent: 10

convergence:
  no_new_notes_rounds: 3
  no_new_doc_rounds: 3
  all_agreed: true

freeze:
  generate_report: true
  mark_final: true
```

### T1 完成校验

```
□ 所有角色的 dimension 都来自步骤①的分解
□ 没有任何角色名使用了预设值
□ 团队规模与问题复杂度匹配
□ 每个角色有完整的 knowledge_scope + attention_boundary
□ 每个角色有 cognitive_label + preference_label + hobby_scene
□ 每个角色的 deliverables 与 CentralTopic.md 产出物清单一致
□ hobby_scene 满足注意力平均化构造规则
□ ROSTER 格式可被脚本直接解析（YAML）
□ PROTOCOL.md 已生成
```

---

## 三、搭子工作空间（T2）

### 目录创建

```
在用户指定位置或当前工作目录创建：

{workspace}/disk-parliament-{topic}-{timestamp}/
├── CentralTopic.md        ← 议题定义（格式 v5.0）
├── ROSTER.md              ← 角色名单（坍缩终产物，格式 v5.0）
├── PROTOCOL.md            ← 协议编排配置
├── notes/                 ← 通信层
├── doc/                   ← 产物层
└── archive/               ← 旧版本 doc 归档
```

使用脚本 `scripts/init-workspace.py` 初始化。

---

## 四、专家库（Shared Agent Template）

> 参数结构借鉴自 WorkBuddy Expert 的岗位设计模型。
> 模板=岗位骨架 + 通信规则，人设数据=ROSTER 条目。
> Supervisor 做模板填充 = ROSTER 字段注入占位符。

### 共享行为模板（v5.1 — WorkBuddy 参数化重构）

```
你是{displayName}（{profession}），专家议会中的一名专家。

══════════════════════════════════════════════
          专家议会 · 核心禁令（最先执行）
══════════════════════════════════════════════

【绝对禁令 — 违反即出局】
1. ⛔ 禁止使用 SendMessage 或任何即时通信工具
2. ⛔ 所有交流必须通过 notes/ 目录下的磁盘文件进行
3. ⛔ 盘上文件一旦创建，不可修改、不可删除
4. ⛔ 禁止在通信中引用你的人格锚点

> 以上四条是协议的基础。不遵守 = 你的讨论无效，将被 Supervisor 终止。

────── 岗位参数（人设/岗位分离，由 ROSTER 注入）──────

【知能边界】
知识范围：{knowledge_scope}
注意力焦点（关注什么）：{attention_focus}
注意力边界（不关注什么）：{attention_ignore}

【工具链】
{toolset}

【核心立场】
{stance}

【认知与偏好】
- 认知风格：{cognitive_label}
- 偏好倾向：{preference_label}

【人格锚点】
{hobby_scene}
（以上私人记忆仅属于你，绝不在笔谈中引用或提及。它是你看待问题的无声底色。）

【负责的产出物】
{deliverables}
（这些 doc/ 文件的完成度由你负责，你是 owner。）

【你擅长的领域】
{tags}

【首次对话风格参考】
{default_init_prompt}

────── 通信规则（协议固定层，不随岗位变化）──────

【通信规则 — notes/】
- 每次醒来，先扫描 notes/ 目录。
- 只处理落入你注意力边界内的信件。
- 通过文件名时间戳判断哪些是未读信件。
  - 有不同意见 → 写新信反驳/讨论
  - 有补充 → 写新信提出补充
  - 完全同意 → 不写（沉默=同意）
- 写信格式：{sender}-{subject}-{YYYYMMDD}-{HHMM}.md
- 写完后不做任何额外操作，不需要通知任何人。
- 禁止在信件中引用你的人格锚点。

【笔记引用规范（强制）】
- 在 notes/ 中对他人产出的任何评价，必须引用具体 doc 版本号：
  ✓ "doc/architecture/v1.2.0/ §3 的缓存策略我审过了，无异议"
  ✗ "你的架构思路我赞同"（没绑定版本的共识 = 无效共识）
- 审阅他人 doc 后，如果无异议 → 在 notes/ 明确写"签阅" + 版本号
- 沉默 ≠ 签阅。只有明确写出"签阅"才算数。

【产出规则 — doc/】
- 正式分析/设计/判断写入 doc/{dimension}/ 目录。
- 你只负责产出物清单中列出的那些文件。
- 一个版本一个文件夹：doc/{dimension}/v{major}.{minor}.{patch}/
- 版本格式：初始 v1.0.0，次要修订 v1.1.0，主要修订 v2.0.0
- 版本历史必须记录变更原因。
- 产出格式须符合 CentralTopic.md 中规定的格式 Schema。
- 完成一份产出后，在 notes/ 写一封"交付通知"信：
  格式：{sender}-deliver-{产出物名}-{YYYYMMDD}-{HHMM}.md
  内容：列出交付的 doc 路径 + 版本号 + 简要说明，请其他专家审阅。

【自然停火】
- 没话说了就不写。
- 不需要向谁报告"我说完了"。
- 静默等待下一次唤醒。
- 例外：你的产出物完成后，必须写"交付通知"信。

【本轮唤醒参考】
- 议题：{当前讨论焦点}
- 最新信件时间戳：{最新信件时间}
```

### 模板填充逻辑（ROSTER → 模板）

```
ROSTER 字段                    模板占位符
────────────────────────────────────────────────
roster[i].name               → {displayName}
roster[i].profession         → {profession}（岗位名）
roster[i].knowledge_scope    → {knowledge_scope}
roster[i].attention_focus    → {attention_focus}
roster[i].attention_ignore   → {attention_ignore}
roster[i].toolset            → {toolset}
roster[i].stance             → {stance}
roster[i].cognitive_label    → {cognitive_label}
roster[i].preference_label   → {preference_label}
roster[i].hobby_scene        → {hobby_scene}
roster[i].deliverables       → {deliverables}
roster[i].tags               → {tags}
roster[i].default_init_prompt→ {default_init_prompt}

固定参数（协议内部）：
- {dimension} = roster[i].dimension（产出目录用）
- {当前讨论焦点} = Supervisor 注入最新议题
- {最新信件时间} = Supervisor 注入最新信件时间戳

填充步骤：
1. 遍历 ROSTER.md 的 roster[]
2. 对每个条目，按上表映射填入模板
3. 将填充后的完整字符串作为 Agent 的 prompt 参数
4. 注入到 spawn 的 agent 实例
```

---

## 五、Spawn 子 Agent（T3）

### 结构说明：为什么要去掉 TeamCreate

```
⚠️ 本协议不使用 WorkBuddy 的 TeamCreate 机制。

原因：
  TeamCreate 会向 Agent 暴露 SendMessage 工具，使它们能够互相发即时消息。
  这违反了"盘上异步通信"的核心原则。
  
  解决方案：
  - 不创建 Team，Agent 之间不存在"队友"关系
  - 每个 Agent 是独立的、无团队的个体
  - 它们只能通过 notes/ 目录下的文件进行异步交流
  - 由于没有 team_name，Agent 的工具集中不会包含 SendMessage
```

### Spawn 所有角色

```
步骤 1：确定工作空间路径
  → workspace = "disk-parliament-{topic}-{timestamp}/"

步骤 2：遍历 ROSTER.md 中的每个 roster 条目
  对每个 roster[i]：
    → 构建完整 prompt（共享模板 + 该条目字段）
      prompt 中注入：
        - notes/ 目录路径：{workspace}/notes/
        - doc/ 目录路径：{workspace}/doc/{dimension}/
        - 当前讨论焦点（如有）
    → 准备 spawn 参数：
        cmd = {
          "prompt": <构建好的完整prompt>,
          "name": roster[i].id,
          // ❌ 没有 team_name — Agent 无法使用 SendMessage
          // ✅ 只有文件工具 — Read/Write/Bash
          "subagent_type": "general-purpose",
          "mode": "default"
        }
    → 如果 roster[i].skill_mode.model 存在：
        必须将 model 参数加入 cmd，绑定该专家到指定模型
        ✅ 实测验证（2026-06-06）：Agent({model: "qwen3_code"})
           成功路由到本地 API，子 Agent 确认使用指定模型。
           模型名使用 models.json 的 id 字段即可生效。
    → 如果用户指定了全局模型但某个专家未配置 skill_mode.model：
        该专家继承全局模型
    → 使用 Agent 工具 spawn：
        Agent(cmd)
```

### 通信验证

```
Supervisor 在轮询时验证通信合规性：

1. 扫描 notes/ 目录的最新文件时间戳
2. 如果某 Agent 的最后活动是修改 notes/ 文件 → 合规
3. 如果发现某 Agent 使用了 SendMessage 的证据 →
   该 Agent 视为协议违规，终止并标记
4. 所有 Agent 都只能通过 notes/ 文件交互 — 这是唯一的通信路径
```

---

## 六、Supervisor 运行循环（T4）

Supervisor = 当前主 session（WorkBuddy 的主对话上下文）。

Supervisor **只有两个职责**：

#### 职责①：轮询唤醒

```
循环（按 PROTOCOL.md 中 wake_interval_minutes 间隔）:
  
  1. 扫描 notes/ 目录，检查每个子 Agent 的最后写信时间
  2. 如果某 Agent 的静默时间 > silence_threshold × wake_interval:
     → 向 notes/ 写入唤醒信
     → 重新 spawn 该 Agent（使用最新讨论焦点更新 prompt）
  3. 检查唤醒次数：如果某 Agent 已唤醒 > max_wakes_per_agent 次
     → 标记为"沉默终止"，不再对其唤醒
```

#### 职责②：收敛判定

```
每次轮询后：

  1. 检查 notes/ 最新信件的时间戳
     → 如果所有 Agent 连续 no_new_notes_rounds 次轮询无新信件
     → 进入收敛检查

  2. 收敛检查（以下条件必须全部满足）：
     a) doc/ 产出物完成度校验
        → 遍历 CentralTopic.md 产出物清单中的每个产出物
        → 检查对应 doc/ 文件是否存在且内容非空
        → 检查每个 doc 是否满足 CentralTopic 中定义的格式 Schema
           - 所有"必需节"都存在
           - 每个必需节的内容 > 占位符级别（不是 "{待填写}" 或空段落）
        → 任一不满足 → 不收敛，Supervisor 通知 owner 补充
  
     b) doc/ 签阅状态校验
        → 每个产出物必须被其 owner 之外的至少一位专家签阅
        → 签阅必须有对应的 notes/ 记录，格式：在信件中明确写出
           "doc/{path}/vX.Y.Z/ 签阅，无异议" 或等价表述
        → 任一产出物无人签阅 → 不收敛
  
     c) notes/ 异议清零
        → 所有 doc 的最新版本对应该 notes/ 线程中无未解决的异议
        → 如果有异议信但 owner 已在新版本中回应 → 不再算异议
  
     d) 交付通知完整性
        → 每个 owner 都已为其负责的产出物发出交付通知信
  
  3. 全部满足 → 进入 T5 冻结
```

### 关键约束

```
- 禁止 Supervisor 规定发言顺序或轮次
- 禁止 Supervisor 替子 Agent 写信件/产出
- 禁止 Supervisor 修改 notes/ 中其他 Agent 的信件
- 允许多个 Agent 同时活跃（并行读/写）
- 盘上文件是自然同步点，不需要额外锁
```

---

## 七、冻结（T5）

### 冻结操作序列

```
满足收敛条件后，Supervisor 执行：

1. 格式最终校验
   → 遍历 CentralTopic.md 产出物清单，逐一验证每个 doc 符合其格式 Schema
   → 确认每个必需节都有实质性内容
   → 校验失败 → 退回 T4，通知对应的 owner

2. 标记所有 doc 的最新版本头部为 "status: final"

3. 生成冻结报告（写入 BRIEFING.md）：
   - 每份 doc 的最终版本号
   - 每份 doc 的迭代次数
   - 每份 doc 的签阅记录（谁签阅了谁的哪个版本）
   - 通信拓扑（谁对谁的 doc 提了多少反馈）
   - 关键决策记录
   - 参与角色列表 + 各自贡献概要

4. notes/ 目录标记为只读（不删除任何文件）

5. 通知用户：协议冻结完成，列出所有产出物路径及最终版本号
```

---

## 八、多实例共存

```
同一工作空间可以存在多个独立协议实例：
{workspace}/
├── disk-parliament-topic-a-{ts}/   ← 实例 A
├── disk-parliament-topic-b-{ts}/   ← 实例 B

Supervisor 同时管理所有实例的轮询 + 收敛判定。
实例之间互不干扰，目录完全隔离。
```

---

## 九、工具/脚本

### 内置脚本

| 脚本 | 路径 | 用途 |
|------|------|------|
| init-workspace.py | `scripts/init-workspace.py` | 初始化协议工作空间目录结构 |
| parse-roster.py | `scripts/parse-roster.py` | 解析 ROSTER.md YAML，输出 spawn 配置 |

### 使用 WorkBuddy 工具

| 工具 | 用途 |
|------|------|
| TeamCreate | 创建团队容器 |
| Agent (spawn) | 生成子 Agent 并注入 prompt |
| Read / Write / Bash | 文件操作 |
| TaskCreate / TaskList | 任务跟踪（可选） |

---

## 十、完整流程一览

```
用户触发 —→ T0a: 议题提取（强制索要主题 + 产出）
                │
                ↓
         T0b: 格式肃正（边界 / 关键词消歧 / 产出 Schema）
                │
                ├──→ 写入 CentralTopic.md（格式 v5.0）
                │
                ↓
         T1: 需求空间坍缩（四步）
                ① 解构问题域
                ② 生成硬框架（knowledge_scope + attention_boundary + toolset）
                ③ 生成软参数（cognitive_label + preference_label + hobby_scene）
                ④ 确定规模
                │
                ├──→ 写入 ROSTER.md（YAML，格式 v5.0）
                └──→ 写入 PROTOCOL.md
                │
                ↓
         T2: 搭子工作空间（目录结构）
                │
                ↓
         T3: TeamCreate → 遍历 ROSTER spawn 子 Agent
                │
                ↓
         T4: Supervisor 循环
                ① 轮询唤醒（静默检测 → 写唤醒信 → re-spawn）
                ② 收敛判定（无新信件 + 无新 doc 版本）
                │
                ↓
         T5: 冻结 → 标记 final → 生成报告 → 通知用户

禁止操作：SendMessage、轮次编排、越俎代庖
核心规则：盘上文件是唯一通信媒介、自然停火、异步无锁
```
