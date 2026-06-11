# INDEX.md — 岗位枚举表

> 专家议会 v3.0 预定义岗位完整列表。
> 基于 WHAT 模型（7工作阶段 × 5认知模态），22个岗位自带 stage×modality×antagonists。

## 七阶段覆盖

| 阶段 | 岗位数 | 岗位列表 |
|------|--------|---------|
| S1 产生灵感 | 3 | creative-planner, trend-observer, brainstorm-facilitator |
| S2 确定方向 | 2 | product-manager, project-manager |
| S3 冒出点子 | 2 | mechanics-designer, narrative-designer |
| S4 补完创意 | 4 | refinement-designer, art-director, ux-designer, copy-editor |
| S5 计算内容 | 3 | data-analyst, balance-designer, performance-evaluator |
| S6 精算框架 | 2 | framework-architect, system-auditor |
| S7 部署实施 | 3 | developer, infrastructure-engineer, qa-tester |

## 拮抗线

| 对抗线 | 敲脑瓜位 |
|--------|---------|
| S1 灵感 ↔ S4 补完 | S2 方向 |
| S3 点子 ↔ S6 框架 | S5 计算 |
| S4 美学 ↔ S5 数据 | S6 框架 |
| S1~S6 ↔ S7 物理规律 | 无（S7 是真理） |

## 文件

| 文件 | 用途 |
|------|------|
| `DUTY-INDEX.yaml` | 22岗位完整枚举 |
| `toolbox-types.yaml` | 7×5 toolset 推导矩阵 |
| `*.yaml` | 样板岗位（4个） |

数据源：`ForGithub/duties/`。协议定义：`ForGithub/SKILL.md`。模型推导：`Skill/11-duty-what-model.md`。
