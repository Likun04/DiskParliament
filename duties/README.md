# 岗位模板库（Duty Templates）

> DiskParliament v3.0 — WHAT 模型（7阶段 × 5模态）岗位体系。

## 文件清单

| 文件 | 说明 |
|------|------|
| `DUTY-INDEX.yaml` | 22 个预定义岗位完整枚举 |
| `toolbox-types.yaml` | 7×5 toolset 自动推导矩阵 |
| `developer.yaml` | 样板：S7 实施层开发者 |
| `data-analyst.yaml` | 样板：S5 计算层数据分析师 |
| `creative-planner.yaml` | 样板：S1 灵感层创意策划 |
| `framework-architect.yaml` | 样板：S6 框架层架构设计师 |

## 使用方式

Supervisor 在 T1 步骤② 读取 `DUTY-INDEX.yaml`，按 (stage, modalities) 匹配岗位。
匹配成功后自动继承该岗位的 attention_boundary、antagonists、toolset 推导规则。
