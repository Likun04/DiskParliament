#!/usr/bin/env python3
"""
笔友协议 — ROSTER.md 解析器
读取 ROSTER.md（YAML 格式），输出每个角色的 spawn 配置 JSON。
Supervisor 可用此输出逐条 spawn 子 Agent。

Usage:
    python parse-roster.py <path/to/ROSTER.md>
    python parse-roster.py <path/to/ROSTER.md> --json      # JSON 输出
    python parse-roster.py <path/to/ROSTER.md> --agent-cmds # WorkBuddy Agent 命令格式
"""

import sys
import json
import yaml
from pathlib import Path


SHARED_TEMPLATE = """你是「{name}」，笔友协议中的一名专家。

══════════════════════════════════════════════
             笔友协议 · 行为规则
══════════════════════════════════════════════

【核心禁令】
1. 禁止使用 SendMessage 或任何即时通信工具。
2. 所有交流必须通过 notes/ 目录下的文件进行。
3. 盘上文件一旦创建，不可修改、不可删除。

【你的维度】
- 领域：{dimension}
- 知识范畴：{knowledge_scope}
- 业务边界：
  关注：{attention_focus}
  不关注：{attention_ignore}
- 你负责的产出物：{deliverables}
  （这些 doc/ 文件的完成度由你负责。你是 owner。）

【你的思考方式】
- 认知风格：{cognitive_label}
- 审美倾向：{preference_label}
- 私人记忆：{hobby_scene}
  （以上记忆仅属于你，不得在笔谈中引用或提及。）

【通信规则 — notes/】
- 每次醒来，先扫描 notes/ 目录。
- 只处理落入你业务边界内的信件。
- 通过文件名时间戳判断哪些是未读信件。
- 针对未读信件判断是否需要回应：
  - 有不同意见 → 写新信反驳/讨论
  - 有补充 → 写新信提出补充
  - 完全同意 → 不写（沉默=同意）
- 写信格式：{{sender}}-{{subject}}-{{YYYYMMDD}}-{{HHMM}}.md
- 写完后不做任何额外操作，不需要通知任何人。
- 禁止在信件中引用你的私人记忆或爱好场景。

【笔记引用规范（强制）】
- 在 notes/ 中对他人产出的任何评价，必须引用具体 doc 版本号
- 审阅他人 doc 后，如果无异议 → 在 notes/ 明确写"签阅" + 版本号
- 沉默 ≠ 签阅。只有明确写出"签阅"才算数。

【产出规则 — doc/】
- 正式分析/设计/判断写入 doc/{dimension}/ 目录。
- 你只负责产出物清单中列出的那些文件。
- 一个版本一个文件夹：doc/{dimension}/v{{major}}.{{minor}}.{{patch}}/
- 版本格式：初始 v1.0.0，次要修订 v1.1.0，主要修订 v2.0.0
- 版本历史必须记录变更原因。
- 产出格式须符合 CentralTopic.md 中规定的格式 Schema。
- 完成一份产出后，在 notes/ 写一封"交付通知"信：
  格式：{{sender}}-deliver-{{产出物名}}-{{YYYYMMDD}}-{{HHMM}}.md

【自然停火】
- 没话说了就不写。
- 不需要向谁报告"我说完了"。
- 静默等待下一次唤醒。
- 例外：你的产出物完成后，必须写"交付通知"信。

【本轮唤醒参考】
- 议题：（由 Supervisor 在唤醒时注入）
- 最新信件时间戳：（由 Supervisor 在唤醒时注入）
"""


def load_roster(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    data = yaml.safe_load(content)
    return data.get("roster", [])


def build_prompt(entry: dict) -> str:
    boundary = entry.get("attention_boundary", {})
    focus = ", ".join(boundary.get("focus", []))
    ignore = ", ".join(boundary.get("ignore", []))
    deliverables = ", ".join(entry.get("deliverables", []))
    return SHARED_TEMPLATE.format(
        name=entry.get("name", ""),
        dimension=entry.get("dimension", ""),
        knowledge_scope=entry.get("knowledge_scope", entry.get("knowledge_domain", "")),
        attention_focus=focus,
        attention_ignore=ignore,
        deliverables=deliverables,
        cognitive_label=entry.get("cognitive_label", ""),
        preference_label=entry.get("preference_label", ""),
        hobby_scene=entry.get("hobby_scene", ""),
    )


def output_json(roster: list[dict]):
    result = []
    for entry in roster:
        result.append({
            "id": entry.get("id"),
            "name": entry.get("name"),
            "prompt": build_prompt(entry),
            "model": entry.get("skill_mode", {}).get("model"),
            "toolset": entry.get("toolset", {}).get("builtins", []),
        })
    print(json.dumps(result, indent=2, ensure_ascii=False))


def output_agent_cmds(roster: list[dict]):
    for entry in roster:
        cmd = {
            "tool": "Agent",
            "params": {
                "prompt": build_prompt(entry).split("\n"),
                "name": entry.get("id"),
                "subagent_type": "general-purpose",
                "mode": "default",
            }
        }
        model = entry.get("skill_mode", {}).get("model")
        if model:
            cmd["params"]["model"] = model
        print(json.dumps(cmd, indent=2, ensure_ascii=False))
        print("---")


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse-roster.py <path/to/ROSTER.md> [--json|--agent-cmds]")
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: File not found: {path}")
        sys.exit(1)

    roster = load_roster(path)
    if not roster:
        print("Warning: No roster entries found in ROSTER.md")
        sys.exit(0)

    mode = "--agent-cmds" if len(sys.argv) < 3 else sys.argv[2]

    print(f"笔友协议 — ROSTER 解析结果")
    print(f"= 共 {len(roster)} 个角色 =")
    for entry in roster:
        print(f"  [{entry.get('id')}] {entry.get('name')} — {entry.get('dimension')}")
    print()

    if mode == "--json":
        output_json(roster)
    elif mode == "--agent-cmds":
        output_agent_cmds(roster)
    else:
        output_json(roster)


if __name__ == "__main__":
    main()
