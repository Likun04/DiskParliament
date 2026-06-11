---
name: disk-parliament
description: >
  专家议会 v3.1 — 多 Agent 盘上异步通信协议。基于 WHAT 模型（7工作阶段×5认知模态）
  从 DUTY-INDEX 匹配岗位→自动推导 toolset→spawn 子 Agent（支持逐专家绑定不同模型）
  →并发盘上写信（禁止 SendMessage）→自然停火→收敛冻结。
  引入岗位系统（22个预定义岗位，自带 stage×modality×antagonists），
  人格与岗位分离。不再按"功能维度"切分（根除流水线式专家召集），
  改为按"阶段-模态"映射必要性。
  议题肃正 → 阶段-模态必要性判定 → 从 DUTY-INDEX 匹配岗位 →
  toolset 矩阵推导 → spawn 子 Agent（并发启动，不限顺序）→
  盘上 mail 异步通信 → 收敛判定 → 冻结产出。
  Supervisor 只做轮询唤醒 + 收敛判定，不编排发言顺序。
  触发词：专家议会、盘上议会、开个议会、启动议会、开个讨论组、异步讨论、
  多Agent协作、DiskParliament、异步通信、Protocol启动、专家讨论、
  开个异步会议、角色扮演讨论、多角色碰撞、专家会诊、
  复杂问题分析、话题讨论、团队协作、分工讨论。
metadata:
  version: "3.1"
  protocol_version: "v6.0-WHAT"
  agent_created: true
  depends_on:
    - "ForGithub/duties/DUTY-INDEX.yaml"       # 22岗位枚举
    - "ForGithub/duties/toolbox-types.yaml"    # 7×5矩阵
    - "GateGuardian.ini"                        # v3.1: 私有算力门禁
    - "scripts/gate_guardian.py"                # v3.1: 门禁验证脚本
---

# 专家议会（DiskParliament）v3.0

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

### T0a-bis — 私有算力门禁（v3.1 新增）

**目的**：检查用户是否配置了私有算力 API，避免技能静默烧积分。

```
Supervisor 执行（按顺序）：

1. 运行门禁脚本
   python scripts/gate_guardian.py --check

2. 解析 JSON 输出：
   - gate.status == "BLOCKED" → 进入步骤 3
   - gate.status == "READY"   → 进入步骤 4

3. informed=false 时 — 引导用户配置
   向用户输出：
   """
   ⚠️ GateGuardian: 私有算力门禁未通过。

   技能需要确认你希望使用积计算力还是自定义算力来支撑专家团。
   如果你想使用自定义算力（不烧积分），请：
     1. 打开 {skill_dir}/GateGuardian.ini
     2. 在 [Models] 部分填入你的模型声明。
        格式：model_id = endpoint_url, api_key
        - 如果模型在 models.json 中存在：只写 model_id =
        - 如果模型不在 models.json 中：写完整 model_id = url, key
          然后运行 python scripts/gate_guardian.py --install 自动注入
     3. 配置好后重新验证

   现在你可以选择：
     a) 配置 GateGuardian.ini（使用自定义算力）
     b) 跳过，全部使用积分算力
   """
   等待用户回复。如果匹配到 installable 模型 → 主动提示 --install。
   运行 --install 后 → 重新执行 --validate。

4. informed=true 时 — 确认算力来源
   解析 gate_guardian.py --list-models 的输出，获取：
     - available: 可用模型列表（含 supportsImages 信息）
     - image_capable: 支持图像输入的模型

   向用户输出：
   """
   ✅ GateGuardian: 私有算力门禁通过。
   
   📋 可用的自定义模型（{n} 个）：
     | 模型 ID | 厂商 | 支持图像 |
     |---------|------|:------:|
     | id1     | xxx  | ✅/❌   |
     ...

   🔍 支持图像的模型（{m} 个）：{id1, id2, ...}

   请确认算力来源：
     a) 全部使用积分算力（WorkBuddy 默认）
     b) 全部使用自定义算力（上面的列表）
     c) 混合使用（图像岗位用积分，非图像用自定义）
     d) 每个专家单独配置
   """
   等待用户选择。

5. 图像岗位特殊处理
   如果议题需要的岗位涉及图像输入（如美术指导 art-director、
   趋势观察员 trend-observer 等需要视觉分析的岗位）：
   
   → 检查 image_capable 列表是否为空
   → 如果为空 → 强制告知用户：
     """
     ⚠️ 以下岗位可能需要图像输入能力：
       - {image_duty_list}
     当前自定义算力中没有支持图像的模型。
     这些岗位将 <b>必须使用积分算力</b>。
     确认继续？
     """
   → 如果非空 → 提示用户可以使用自定义图像模型，由用户选择。

6. 写入 CentralTopic.md 的模型配置段
   根据用户选择，在 CentralTopic.md 「模型配置」部分写入：
     - 全局模型 → 使用自定义模型的 id 列表
     - 专家个性化绑定 → 逐个标注
     - 图像岗位 → 标注为"积分算力"（如果用户选 c）

7. 门禁确认后 → 进入 T0b（格式肃正）
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
□ GateGuardian 门禁已通过（informed=true 或用户确认使用积分算力）
□ 图像岗位的算力来源已确认
□ 用户明确了模型配置（全局模型 / 个性化绑定 / 混合 / 积分默认）
□ 模型名已确认使用 models.json 的 id 格式（非 display name）
□ 议题边界已划定
□ 歧义关键词已消歧
□ 产出格式 Schema 已设计
□ 用户已确认以上全部
```

---

## 二、需求空间坍缩 — WHAT 模型匹配（生成 ROSTER.md + PROTOCOL.md）

### T1 — 三步坍缩（v3.0：阶段-模态映射替代维度切面）

**输入**：CentralTopic.md 内容
**输出**：ROSTER.md（YAML）+ PROTOCOL.md
**依赖**：`ForGithub/duties/DUTY-INDEX.yaml` + `ForGithub/duties/toolbox-types.yaml`

> **⚠️ 重要变更 (v3.0)**：不再按"功能维度"切分问题域。按"阶段-模态"映射议题需求。
> 按功能维度切分（机制设计→数值计算→技术架构→代码实现）天然产生流水线席位 ——
> 这正是 v2.x 被验证为失败模式的原因。

#### 步骤①：议题的阶段-模态必要性判定

```
操作：分析议题需要哪些工作阶段参与，每个阶段需要哪些认知模态。

不预设维度名称，不预设维度数量。从议题本身推导"需要什么阶段位的人"。

S1 产生灵感 — 需要从外部世界获取信号吗？需要跳出框架吗？
S2 确定方向 — 需要从众多方向中做收敛决策吗？
S3 冒出点子 — 需要在方向上生成具体方案吗？
S4 补完创意 — 需要填充细节让方案可执行吗？
S5 计算内容 — 需要量化/模拟/验证方案可行性吗？
S6 精算框架 — 需要建立架构约束和系统边界吗？
S7 部署实施 — 需要将方案落为可运行产物吗？

对每个阶段：
  必要性判定 → 需要/不需要
  如果需要 → 列出所需的认知模态（perceiver / deducer / synthesizer / critic / diverger）

输出示例（GDD研讨会）：
  S1×[perceiver, diverger]           → 需要创意策划（1人）
  S2×[perceiver, deducer, critic]    → 需要产品经理（1人）
  S3×[perceiver, diverger, synthesizer] → 需要机制设计师（1人）
  S5×[deducer, critic]               → 需要数值策划（1人）
  S6×[deducer, critic]               → 需要架构设计师（1人）
  S7×[deducer, synthesizer]          → 需要开发者（1人）

⚠️ 不是每个议题都需要所有7个阶段。阶段必要性由议题性质决定。
⚠️ 不存在"S1产出→S2消费"的流水线关系。所有阶段的人并发启动。
```

#### 步骤②：从 DUTY-INDEX 匹配岗位 + 推导 toolset

```
对步骤①输出的每个 (阶段, 模态集)：
  
  1. 查 DUTY-INDEX.yaml
     匹配条件：stage 匹配 ∧ modalities 覆盖度 ≥ 80%
     → 如精确匹配 → 直接采用该岗位
        继承：name, desc, focus, exclude, antagonists, org_map
     → 如无精确匹配 → 取最接近岗位 + 手工调 modalities

  2. 推导 toolset
     从 toolbox-types.yaml 矩阵查：
       baseline: [Read, Write]
       ∪ ∪_{m ∈ modalities} matrix[stage][m].builtins
     → 自动生成 toolset.builtins
     → 自动生成 toolset.skills（目前为空，后续可扩展）

  3. 拮抗关系
     → 从 DUTY-INDEX 的 antagonists 字段自动获取
     → 如果 antagonists 包含 "all"（S7 实施层）→ 标记为全阶段拮抗
     → 不需要 Supervisor 手工配置对立立场

  4. 人设参数
     → cognitive_label, preference_label, hobby_scene 仍需 Supervisor 生成
     → 这些是人设层面的变量，不是岗位层面的固定值
```

#### 步骤③：确定团队规模 + 人设填充

```
团队规模 = 步骤②匹配到的岗位数量。

约束：
  - 最少 2 人（至少有两个阶段位参与），最多 8 人
  - 一个阶段最多匹配一个岗位（如果需要多个岗位在同一阶段 → 让 modalities 覆盖不同模态）
  - 与 v2.x 的"维度切面"不同：每个岗位来自(阶段,模态)组合，不是来自功能拆分

人设填充（按 v5.x 规则）：
  - id: 机器用标识符
  - name: 角色名（中文 2-4 字或英文名，与项目调性匹配）
  - stance: 核心立场（从岗位 focus 推导）
  - cognitive_label, preference_label, hobby_scene: 按现有规则生成
  - 禁止使用任何预设角色名
```

### ROSTER 字段数据流 (v3.0 WHAT)

```
字段              来源                                    示例
──────────────────────────────────────────────────────────────────
id                步骤③                                    "mechanics-designer"
name              步骤③                                    "齿轮"
stage             步骤①匹配 DUTY-INDEX                       "S3"
modalities        步骤①匹配 DUTY-INDEX                       [perceiver, diverger, synthesizer]
profession        步骤②岗位 name                            "机制设计师"
antagonists       步骤②岗位 antagonists                     [framework-architect, balance-designer]
dimension         步骤① 阶段名                               "冒出点子"（仅用于产出目录名）

knowledge_scope   步骤③（人设生成）                          "机制设计理论..."
attention_focus   步骤②岗位 focus + 步骤③调整               ["机制创新", "玩法新颖性"]
attention_ignore  步骤②岗位 exclude + 步骤③调整             ["代码实现", "UI设计"]

stance            步骤③（人设生成）                          "机制至上。玩法不够新颖就不值得做。"
tags              从 attention_focus 取前 3 条                ["机制设计", "第一性原理", "玩法创新"]
default_init_prompt  公式："我是{name}（{profession}）。{stance}你需要我帮你分析什么？"

deliverables      从 CentralTopic.md 产出物清单分配            ["GDD文档", "机制规格表"]
toolset           步骤② 矩阵推导                             builtins: [Read, Write, Edit, WebSearch, Glob, Grep]

cognitive_label   步骤③（人设生成）                          "系统思维·拓扑优先"
preference_label  步骤③（人设生成）                          "偏好涌现规则而非硬编码"
hobby_scene       步骤③（人设生成）                          "双脚踩下踏板..."
skill_mode        步骤②或 T0 用户指定模型                    模型绑定
```

### ROSTER → 岗位模板注入

```
Supervisor spawn 时执行：

1. 选择岗位模板：duties/{roster[i].id}.yaml
   如 roster[i].id="mechanics-designer" → 选 duties/mechanics-designer.yaml
   如果没有对应 yaml → 从 DUTY-INDEX.yaml 直接读取

2. 将 ROSTER 字段注入模板占位符：
   {{displayName}}     ← roster[i].name
   {{stage}}           ← roster[i].stage（新增）
   {{modalities}}      ← roster[i].modalities（新增）
   {{profession}}      ← roster[i].profession
   {{deliverables}}    ← roster[i].deliverables
   {{toolset}}         ← roster[i].toolset（矩阵自动推导）
   {{stance}}          ← roster[i].stance
   {{attention_focus}}  ← roster[i].attention_focus
   {{attention_ignore}} ← roster[i].attention_ignore
   {{antagonists}}     ← roster[i].antagonists（新增：岗位自带）
   {{cognitive_label}}  ← roster[i].cognitive_label
   {{preference_label}} ← roster[i].preference_label
   {{hobby_scene}}      ← roster[i].hobby_scene
   {{tags}}             ← roster[i].tags
   {{default_init_prompt}} ← roster[i].default_init_prompt

3. 注入后的完整文本 = Agent 的 spawn prompt
```

**拮抗关系说明（v3.0 — 自动化）：**

拮抗不再由 Supervisor 在步骤⑤手工配置。改为：
- 每个岗位的 `antagonists` 字段在 DUTY-INDEX.yaml 中预定义
- Supervisor 在匹配岗位时自动继承拮抗关系
- S7 实施层岗位（developer, infrastructure-engineer, qa-tester）的 antagonists 为 `[all]`
- 四条天然对抗线（见 WHAT 模型笔记 §2.2）无需手动配置：
  1. S1↔S4（灵感 vs 补完）→ S2 敲脑瓜
  2. S3↔S6（点子 vs 框架）→ S5 敲脑瓜
  3. S4↔S5（美学 vs 数据）→ S6 敲脑瓜
  4. S1~S6 ↔ S7（认知 vs 物理规律）—— S7 不敲脑瓜，直接跑实证

### ROSTER.md 格式（坍缩终产物，v3.0 WHAT）

```yaml
# ROSTER.md — 由 WHAT 模型阶段-模态匹配生成，供 Supervisor 逐条解析 spawn

roster:
  - id: "<步骤③>"
    name: "<步骤③>"
    # ── WHAT 模型三轴（新增）──
    stage: "<S1~S7，来自步骤①>"                              # ← v3.0 新增
    modalities: ["<perceiver>", "<deducer>", ...]             # ← v3.0 新增
    antagonists: ["<id>", "<id>", ...]                       # ← v3.0 新增（岗位自带）
    # ── 岗位字段 ──
    profession: "<岗位名，如「机制设计师」>"                    # 来自 DUTY-INDEX
    stance: "<核心立场>"
    tags: ["<标签1>", "<标签2>", "<标签3>"]
    default_init_prompt: "<首次问候>"
    # ── 硬性界定 ──
    dimension: "<阶段名，如「冒出点子」>"
    knowledge_scope: "<步骤③>"
    attention_boundary:
      focus: ["<步骤② focus + 步骤③调整>"]
      ignore: ["<步骤② exclude + 步骤③调整>"]
    deliverables: ["<该专家负责的产出物列表>"]
    toolset:                             # ← v3.0: 矩阵自动推导，不再手工写
      builtins: ["Read", "Write", ...]
      skills: []
    # ── 软性标签 ──
    cognitive_label: "<步骤③>"
    preference_label: "<步骤③>"
    hobby_scene: "<步骤③>"
    # ── 技能模式扩展 ──
    skill_mode:
      model: "<可选，models.json 的 id>"
```

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
□ 议题的阶段-模态必要性已逐阶段判定（步骤①）
□ 所有匹配的岗位来自 DUTY-INDEX 精确匹配或最接近匹配（步骤②）
□ toolset 从 toolbox-types.yaml 矩阵自动推导，非手工拍脑袋
□ antagonists 从 DUTY-INDEX 自动继承，非手工配置
□ 不存在"按功能维度切分"的流水线席位
□ 团队规模 2-8 人，与阶段必要性匹配
□ 每个角色有完整的 knowledge_scope + attention_boundary
□ 每个角色有 cognitive_label + preference_label + hobby_scene
□ 每个角色的 deliverables 与 CentralTopic.md 产出物清单一致
□ hobby_scene 满足注意力平均化构造规则
□ ROSTER 包含 stage、modalities、antagonists 三个新字段
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
├── ROSTER.md              ← 角色名单（坍缩终产物，格式 v3.0 WHAT）
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

【岗位坐标 — WHAT 模型】
工作阶段：{stage}（七阶段之一：S1灵感→S2方向→S3点子→S4补完→S5计算→S6框架→S7实施）
认知模态：{modalities}（五模态：perceiver·deducer·synthesizer·critic·diverger）
工作方式：并发盘上通信。你和同议会的所有专家同时启动，不限顺序。
         你可以回溯任何早期阶段的笔记，提出反驳或补充。
         你不是流水线工人，你的阶段不是工序站。

【天然拮抗】
{antagonists}
（你和以上岗位存在天然视角冲突。看到他们的笔记时，用你的视角去挑战。
 如果你在 S7（实施层），你对所有 S1~S6 的结论持实证性怀疑——直接跑代码验证而非口头争论。）

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
roster[i].stage              → {stage}（v3.0 新增）
roster[i].modalities         → {modalities}（v3.0 新增）
roster[i].antagonists        → {antagonists}（v3.0 新增）
roster[i].profession         → {profession}（岗位名）
roster[i].knowledge_scope    → {knowledge_scope}
roster[i].attention_focus    → {attention_focus}
roster[i].attention_ignore   → {attention_ignore}
roster[i].toolset            → {toolset}（矩阵自动推导）
roster[i].stance             → {stance}
roster[i].cognitive_label    → {cognitive_label}
roster[i].preference_label   → {preference_label}
roster[i].hobby_scene        → {hobby_scene}
roster[i].deliverables       → {deliverables}
roster[i].tags               → {tags}
roster[i].default_init_prompt→ {default_init_prompt}

固定参数（协议内部）：
- {stage} = roster[i].stage（七阶段，用于doc/目录名）
- {modalities} = roster[i].modalities（五模态认知标注）
- {antagonists} = roster[i].antagonists（天然对立岗位名列表）
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

## 九、工具/脚本/依赖数据

### 依赖数据文件（v3.0 新增）

| 文件 | 路径 | 用途 |
|------|------|------|
| DUTY-INDEX | `ForGithub/duties/DUTY-INDEX.yaml` | 22个预定义岗位枚举（stage×modality×antagonists） |
| toolbox-types | `ForGithub/duties/toolbox-types.yaml` | 7阶段×5模态 toolset 推导矩阵 |
| WHAT 模型 | `Skill/11-duty-what-model.md` | 模型推导完整笔记 |

### 使用 WorkBuddy 工具

| 工具 | 用途 |
|------|------|
| Agent (spawn) | 生成子 Agent 并注入 prompt |
| Read / Write / Bash | 文件操作 |
| TaskCreate / TaskList | 任务跟踪（可选） |

### 已废弃（v2.x 产物，v3.0 不再使用）

| 工具/目录 | 状态 | 原因 |
|----------|------|------|
| TeamCreate | 已废弃 | 暴露 SendMessage，违反盘上异步原则 |
| positions/ 目录 | 已废弃 | replaced by DUTY-INDEX.yaml |

### v3.1 新增

| 文件 | 路径 | 用途 |
|------|------|------|
| GateGuardian.ini | `GateGuardian.ini` | 私有算力门禁配置（模型ID声明） |
| gate_guardian.py | `scripts/gate_guardian.py` | 门禁验证+注入脚本（--check/--validate/--install/--list-models） |

---

## 十、完整流程一览

```
用户触发 —→ T0a: 议题提取（强制索要主题 + 产出）
                │
                ↓
         T0a-bis: GateGuardian 私有算力门禁
                 → scripts/gate_guardian.py --check
                 → informed=false? 引导用户配置或使用积分
                 → informed=true? 列出可用模型，确认算力来源
                 → 图像岗位特殊处理
                │
                ↓
         T0b: 格式肃正（边界 / 关键词消歧 / 产出 Schema）
                │
                ├──→ 写入 CentralTopic.md（格式 v5.0）
                │
                ↓
         T1: 阶段-模态匹配（v3.0 WHAT，三步）
                ① 议题的阶段-模态必要性判定（不是维度切面！）
                ② 从 DUTY-INDEX 匹配岗位 + toolbox-types.yaml 推导 toolset
                ③ 确定团队规模 + 人设填充
                │
                ├──→ 写入 ROSTER.md（YAML，格式 v3.0 WHAT）
                └──→ 写入 PROTOCOL.md
                │
                ↓
         T2: 搭子工作空间（目录结构）
                │
                ↓
         T3: 遍历 ROSTER，在无 Team 模式下 spawn 子 Agent ←☆☆☆☆☆ 并发启动！
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
关键变更(v3.0)：不再按功能维度切分 → 阶段-模态并发映射 → 根除流水线席位
```
