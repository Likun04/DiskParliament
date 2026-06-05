#!/usr/bin/env python3
"""
笔友协议 — 工作空间初始化脚本
Usage:
    python init-workspace.py <workspace_root> <topic_name> [timestamp]
"""

import sys
import os
from datetime import datetime


def init_workspace(root: str, topic: str, timestamp: str | None = None) -> str:
    ts = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_topic = topic.replace(" ", "-").replace("/", "-")
    ws_dir = os.path.join(root, f"pen-pal-{safe_topic}-{ts}")

    dirs = [
        ws_dir,
        os.path.join(ws_dir, "notes"),
        os.path.join(ws_dir, "doc"),
        os.path.join(ws_dir, "archive"),
    ]

    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  ✓  {d}")

    return ws_dir


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python init-workspace.py <workspace_root> <topic_name> [timestamp]")
        sys.exit(1)

    root = sys.argv[1]
    topic = sys.argv[2]
    ts = sys.argv[3] if len(sys.argv) > 3 else None

    print("笔友协议 — 工作空间初始化")
    print("=" * 40)
    ws = init_workspace(root, topic, ts)
    print("=" * 40)
    print(f"\n工作空间已创建：{ws}")
    print("\n接下来需要 Supervisor 写入：")
    print("  - CentralTopic.md")
    print("  - ROSTER.md（需求坍缩后生成）")
    print("  - PROTOCOL.md（协议编排配置）")
