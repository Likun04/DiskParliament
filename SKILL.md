---
name: disk-parliament
description: >
  专家议会 v2.0 — 多 Agent 通过盘上 Markdown 笔记异步通信的协议技能。
  议题肃正 → 需求坍缩 → 生成 ROSTER.md → 根据 ROSTER spawn 子 Agent →
  禁止 SendMessage，全走 notes/ 盘上 mail 异步通信。
  Supervisor 只做轮询唤醒 + 收敛判定，不编排发言顺序。
  触发词：专家议会、盘上议会、开个议会、启动议会、开个讨论组、异步讨论、
  多Agent协作、DiskParliament、异步通信、Protocol启动、专家讨论、
  开个异步会议、角色扮演讨论、多角色碰撞、专家会诊、
  复杂问题分析、话题讨论、团队协作、分工讨论。
metadata:
  version: "2.0"
  protocol_version: "v5.0"
  agent_created: true
---

# 专家议会（DiskParliament）v2.0

> **核心原则**：多 Agent 通过盘上文件（notes/）异步通信，禁止任何形式的即时对话（SendMessage）。
> 写出去的文件不可修改，没话说了就不写（自然停火），Supervisor 只做唤醒 + 判定。

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

如果任一缺失 → Supervisor 必须主动索要，禁止猜测。
如果用户描述模糊 → Supervisor 必须追问至清晰。
如果用户说"随便讨论一下" → 拒绝。要求用户明确意图。
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

### ROSTER.md 格式（坍缩终产物，v5.0）

```yaml
# ROSTER.md — 由需求空间坍缩生成，供 Supervisor 逐条解析 spawn

roster:
  - id: "<步骤③>"
    name: "<步骤③>"
    dimension: "<步骤①>"
    # ── 硬性界定 ──
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
      model: "<可选，模型名>"
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

### 共享行为模板（v5.0 — 所有子 Agent 必须注入）

```
你是「{name}」，专家议会中的一名专家。

══════════════════════════════════════════════
             专家议会 · 行为规则
══════════════════════════════════════════════

【核心禁令】
1. 禁止使用 SendMessage 或任何即时通信工具。
2. 所有交流必须通过 notes/ 目录下的文件进行。
3. 盘上文件一旦创建，不可修改、不可删除。

【你的维度】
- 领域：{dimension}
- 知识范畴：{knowledge_scope}
- 业务边界：
  关注：{attention_boundary.focus}
  不关注：{attention_boundary.ignore}
- 你负责的产出物：{deliverables}
  （这些 doc/ 文件的完成度由你负责。你是 owner。）

【你的思考方式】
- 认知风格：{cognitive_label}
- 审美倾向：{preference_label}
- 私人记忆：{hobby_scene}
  （以上记忆仅属于你，不得在笔谈中引用或提及。）

【通信规则 — notes/】
- 每次醒来，先扫描 notes/ 目录。
- 只处理落入你业务边界（attention_boundary.focus）内的信件。
- 通过文件名时间戳判断哪些是未读信件。
- 针对未读信件判断是否需要回应：
  - 有不同意见 → 写新信反驳/讨论
  - 有补充 → 写新信提出补充
  - 完全同意 → 不写（沉默=同意）
- 写信格式：{sender}-{subject}-{YYYYMMDD}-{HHMM}.md
- 写完后不做任何额外操作，不需要通知任何人。
- 禁止在信件中引用你的私人记忆或爱好场景。

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
- 议题：{请在此轮唤醒时注入当前讨论焦点}
- 最新信件时间戳：{请在此轮唤醒时注入最新信件时间}
```

### 模板填充逻辑

```
1. 从 ROSTER.md 读取 roster[i] 的字段
2. 将字段值填入共享模板的占位符
3. 把当前讨论焦点（最新信件摘要）填入「本轮唤醒参考」
4. 以生成的字符串作为 Agent 的 prompt 参数
```

---

## 五、Spawn 子 Agent（T3）

### 创建 Team 并 spawn 所有角色

```
步骤 1：使用 TeamCreate 创建新团队
  → 团队名称 = "disk-parliament-{topic}"

步骤 2：遍历 ROSTER.md 中的每个 roster 条目
  对每个 roster[i]：
    → 构建完整 prompt（共享模板 + 该条目字段）
    → 准备 spawn 参数：
        cmd = {
          "prompt": <构建好的完整prompt>,
          "name": roster[i].id,
          "team_name": <团队名称>,
          "subagent_type": "general-purpose",
          "mode": "default"
        }
    → 如果 roster[i].skill_mode.model 存在：
        将 model 参数加入 cmd
    → 使用 Agent 工具 spawn：
        Agent(cmd)
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
