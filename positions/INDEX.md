# 岗位系统索引

> 这是 DiskParliament 的**岗位模板库**，251 个固化岗位。
> 来源：WorkBuddy 预设专家 prompt，已清洗为 DiskParliament 格式。
>
> 每个岗位模板 = 岗位骨架（知能边界/铁律/产出物/工作流/沟通风格/工具箱）
> + ROSTER 注入点（{displayName}/{stance}/{attention_focus} 等）
> + 通信规则（协议固定层）
>
> 岗位与人设分离：岗位选这个库，人设来自 ROSTER 条目。

---

## 岗位 vs ROSTER 条目

```
Supervisor 建立专家议会时：

1. 确定讨论需要哪些维度
2. 从 positions/ 挑选对应岗位模板
3. 在 ROSTER 中填入该岗位的 profession、知识范围、注意力边界等
4. 加上人设数据：stance、cognitive_label、preference_label、hobby_scene
5. spawn 时：岗位模板 + 人设数据 = 完整个体
```

## 完整文件体系

```
ForGithub/
├── SKILL.md              ← 协议核心（含 Shared Agent Template）
├── positions/            ← 251 个岗位模板（选这个库）
│   └── INDEX.md          ← 本文件
├── templates/            ← WorkBuddy 原始 prompt（不动）
│
WrokBuddyExpers/          ← WorkBuddy 原始 prompt 全量备份
│
Skill/                    ← 方法论笔记（设计文档）
set/                      ← 项目运行数据
```

## 岗位模板结构（7 段）

每个 `positions/{name}.md` 包含：

1. **角色定义** — 你是谁
2. **核心使命和注意力边界** — 知识范围 + 关注/不关注
3. **铁律** — 岗位级别的专业约束（最精华）
4. **技术产出物** — 内嵌输出模板和格式
5. **工作流程** — 分步骤工作方法
6. **沟通风格** — 语气和表达方式
7. **工具箱** — 工具链

加：人格锚点（协议层）+ 通信规则（协议层）

## 岗位选择策略

Supervisor 根据 ROSTER 的 dimension 选择最匹配的岗位：

1. 按文件名关键词精确匹配
2. 按 manifest 分类模糊匹配
3. 兜底：senior-developer / business-analyst
