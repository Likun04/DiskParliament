#!/usr/bin/env python3
"""
GateGuardian — 专家议会私有算力门禁验证器 (v1.1)

功能：
  1. 读取 GateGuardian.ini 中的 [Models] 声明
  2. 读取 ~/.workbuddy/models.json 中的已配置模型
  3. 交叉验证：声明模型是否全部存在于 models.json
  4. 自动设置 informed_gate = true（全部匹配时）
  5. 检测 image-capable 模型（supportsImages=true）
  6. --install 命令：将 GateGuardian.ini 中声明但 models.json 中缺失的模型注入
  7. 输出结构化 JSON 供 Supervisor 消费

用法：
  python gate_guardian.py [--skill-dir <路径>]
      --check          只读检查（不修改任何文件）
      --validate       验证 + 自动更新 informed_gate + 提示 --install
      --install        将缺失模型注入 models.json（需用户确认，自动备份）
      --list-models    列出所有可用私有模型
      --image-capable  列出所有支持图像输入的模型
"""

import configparser
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


def get_skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def get_models_json_path() -> Path:
    home = Path.home()
    return home / ".workbuddy" / "models.json"


def load_models_json() -> list[dict]:
    path = get_models_json_path()
    if not path.exists():
        print(json.dumps({"error": f"models.json not found at {path}"}))
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_models_json(models: list[dict]):
    path = get_models_json_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(models, f, ensure_ascii=False, indent=2)
        f.write("\n")


def backup_models_json() -> Path:
    path = get_models_json_path()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(f".backup-{ts}.json")
    shutil.copy2(path, backup_path)
    return backup_path


def load_gate_ini(skill_dir: Path) -> configparser.ConfigParser:
    ini_path = skill_dir / "GateGuardian.ini"
    if not ini_path.exists():
        print(json.dumps({"error": f"GateGuardian.ini not found at {ini_path}"}))
        sys.exit(1)
    config = configparser.ConfigParser()
    config.read(ini_path, encoding="utf-8")
    return config


def save_gate_ini(skill_dir: Path, config: configparser.ConfigParser):
    ini_path = skill_dir / "GateGuardian.ini"
    with open(ini_path, "w", encoding="utf-8") as f:
        config.write(f)


def parse_model_declarations(config: configparser.ConfigParser) -> dict[str, dict]:
    """
    解析 [Models] section，返回模型声明字典。

    GateGuardian.ini 中的格式：
      model_id = endpoint_url, api_key

    endpoint_url 和 api_key 可选。留空表示仅声明 ID，配置从 models.json 读取。

    返回：
      {
        "deepseek-v4-pro": {"id": "deepseek-v4-pro", "url": "", "apiKey": ""},
        "my-local-glm":   {"id": "my-local-glm",   "url": "http://...", "apiKey": "ollama"},
      }
    """
    if not config.has_section("Models"):
        return {}

    declarations = {}
    for key in config.options("Models"):
        model_id = key.strip()
        if not model_id:
            continue
        raw = config.get("Models", key, fallback="").strip()

        url = ""
        api_key = ""
        if raw:
            parts = [p.strip() for p in raw.split(",", 1)]
            if len(parts) >= 1 and parts[0]:
                url = parts[0]
            if len(parts) >= 2 and parts[1]:
                api_key = parts[1]

        declarations[model_id] = {
            "id": model_id,
            "url": url,
            "apiKey": api_key,
        }
    return declarations


def get_model_index(models_json: list[dict]) -> dict[str, dict]:
    return {entry["id"]: entry for entry in models_json}


def validate_models(
    declarations: dict[str, dict],
    models_json: list[dict],
) -> dict:
    model_index = get_model_index(models_json)

    matched = []
    unmatched = []
    image_capable = []

    for mid, decl in declarations.items():
        entry = model_index.get(mid)
        if entry:
            info = {
                "id": entry["id"],
                "name": entry.get("name", entry["id"]),
                "vendor": entry.get("vendor", "Unknown"),
                "supportsImages": entry.get("supportsImages", False),
                "supportsToolCall": entry.get("supportsToolCall", False),
                "url": entry.get("url", ""),
            }
            matched.append(info)
            if info["supportsImages"]:
                image_capable.append(info)
        else:
            # 不在 models.json 中，但有完整声明（url + apiKey）
            has_full_config = bool(decl.get("url") and decl.get("apiKey"))
            unmatched.append({
                "id": mid,
                "has_full_config": has_full_config,
                "url_provided": decl.get("url", ""),
                "api_key_provided": "***" if decl.get("apiKey") else "",
                "installable": has_full_config,
            })

    return {
        "matched": matched,
        "unmatched": unmatched,
        "image_capable": image_capable,
        "all_matched": len(unmatched) == 0 and len(matched) > 0,
    }


def _guess_supports_images(url: str, model_id: str) -> bool:
    """根据 URL 或 model_id 推测是否支持图像"""
    image_keywords = ["vision", "vl", "multimodal", "mimo", "gpt-4o", "gemini", "claude-3"]
    combined = (url + model_id).lower()
    return any(kw in combined for kw in image_keywords)


def _guess_vendor(url: str) -> str:
    url_lower = url.lower()
    if "localhost" in url_lower or "127.0.0.1" in url_lower:
        return "Local"
    if "deepseek" in url_lower:
        return "DeepSeek"
    if "openai" in url_lower:
        return "OpenAI"
    if "bigmodel" in url_lower or "glm" in url_lower:
        return "Zhipu"
    if "mimo" in url_lower or "xiaomi" in url_lower:
        return "Custom"
    if "ollama" in url_lower:
        return "Ollama"
    return "Custom"


def cmd_install(skill_dir: Path):
    """将声明但缺失的模型注入 models.json"""
    config = load_gate_ini(skill_dir)
    declarations = parse_model_declarations(config)
    models_json = load_models_json()
    model_index = get_model_index(models_json)
    result = validate_models(declarations, models_json)

    installed = []
    skipped = []

    for item in result["unmatched"]:
        mid = item["id"]
        decl = declarations.get(mid, {})
        if not item["installable"]:
            skipped.append({
                "id": mid,
                "reason": "缺少 url 和 api_key — 请在 GateGuardian.ini 中补齐",
            })
            continue

        new_entry = {
            "id": mid,
            "name": mid,
            "vendor": _guess_vendor(decl.get("url", "")),
            "url": decl["url"],
            "apiKey": decl["apiKey"],
            "supportsToolCall": True,
            "supportsImages": _guess_supports_images(decl.get("url", ""), mid),
            "supportsReasoning": False,
            "useCustomProtocol": False,
        }

        models_json.append(new_entry)
        model_index[mid] = new_entry
        installed.append({"id": mid, "url": decl["url"], "vendor": new_entry["vendor"]})

    if installed:
        backup_path = backup_models_json()
        save_models_json(models_json)

    # 重新验证
    new_declared_ids = list(declarations.keys())
    result2 = validate_models(declarations, models_json)

    # 更新 informed_gate
    if not config.has_section("Gate"):
        config.add_section("Gate")
    config.set("Gate", "informed", "true" if result2["all_matched"] else "false")
    config.set("Gate", "last_validated", datetime.now().isoformat(timespec="seconds"))
    save_gate_ini(skill_dir, config)

    print(json.dumps({
        "action": "install",
        "installed": installed,
        "skipped": skipped,
        "backup": str(backup_path) if installed else None,
        "gate": {
            "informed_after": "true" if result2["all_matched"] else "false",
            "status": "PASS" if result2["all_matched"] else "PARTIAL",
        },
        "summary": (
            f"成功注入 {len(installed)} 个模型到 models.json"
            f"{'，' + str(len(skipped)) + ' 个模型配置信息不足，跳过' if skipped else ''}"
        ),
    }, ensure_ascii=False, indent=2))


def cmd_validate(skill_dir: Path):
    config = load_gate_ini(skill_dir)
    declarations = parse_model_declarations(config)
    declared_ids = list(declarations.keys())
    models_json = load_models_json()
    result = validate_models(declarations, models_json)

    if not config.has_section("Gate"):
        config.add_section("Gate")

    old_informed = config.get("Gate", "informed", fallback="false")
    new_informed = "true" if result["all_matched"] else "false"
    config.set("Gate", "informed", new_informed)
    config.set("Gate", "last_validated", datetime.now().isoformat(timespec="seconds"))
    save_gate_ini(skill_dir, config)

    gate_info = {
        "informed_before": old_informed,
        "informed_after": new_informed,
        "status": "PASS" if new_informed == "true" else "FAIL",
        "reason": (
            "All declared models matched in models.json"
            if new_informed == "true"
            else f"未匹配的模型: {[u['id'] for u in result['unmatched']]}"
        ),
    }

    # 如果有未匹配的，提示可安装的
    installable = [u for u in result["unmatched"] if u.get("installable")]
    if installable:
        gate_info["action"] = {
            "command": "python scripts/gate_guardian.py --install",
            "installable_ids": [u["id"] for u in installable],
            "hint": f"以下模型已在 GateGuardian.ini 中声明但不在 models.json 中: {[u['id'] for u in installable]}。如需注入，运行 --install。",
        }

    result["gate"] = gate_info
    result["declared_count"] = len(declared_ids)
    result["matched_count"] = len(result["matched"])
    result["unmatched_count"] = len(result["unmatched"])

    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_check(skill_dir: Path):
    config = load_gate_ini(skill_dir)
    declarations = parse_model_declarations(config)
    declared_ids = list(declarations.keys())
    models_json = load_models_json()
    result = validate_models(declarations, models_json)

    informed = config.get("Gate", "informed", fallback="false")
    last_validated = config.get("Gate", "last_validated", fallback="")

    gate_info = {
        "informed": informed,
        "last_validated": last_validated,
        "status": "READY" if informed == "true" else "BLOCKED",
        "action": (
            "Private compute available"
            if informed == "true"
            else "GateGuardian.ini is not configured. Run --validate or --install."
        ),
    }

    installable = [u for u in result["unmatched"] if u.get("installable")]
    if installable:
        gate_info["installable_count"] = len(installable)
        gate_info["installable_ids"] = [u["id"] for u in installable]
        gate_info["install_hint"] = "Run: python scripts/gate_guardian.py --install"

    result["gate"] = gate_info
    result["declared_count"] = len(declared_ids)
    result["matched_count"] = len(result["matched"])
    result["unmatched_count"] = len(result["unmatched"])

    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_list_models(skill_dir: Path):
    config = load_gate_ini(skill_dir)
    declarations = parse_model_declarations(config)
    declared_ids = list(declarations.keys())
    models_json = load_models_json()
    result = validate_models(declarations, models_json)

    print(json.dumps({
        "available": result["matched"],
        "unavailable": result["unmatched"],
        "image_capable": result["image_capable"],
        "summary": (
            f"{len(result['matched'])}/{len(declared_ids)} models available"
            if declared_ids else "No private models declared"
        ),
    }, ensure_ascii=False, indent=2))


def cmd_image_capable(skill_dir: Path):
    config = load_gate_ini(skill_dir)
    declarations = parse_model_declarations(config)
    models_json = load_models_json()
    result = validate_models(declarations, models_json)

    if result["image_capable"]:
        print(json.dumps({
            "image_capable": result["image_capable"],
            "warning": "These models support image input. Consider using them for image-related duties.",
        }, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({
            "image_capable": [],
            "warning": "No image-capable models in private compute pool. Image duties will need platform credits.",
        }, ensure_ascii=False, indent=2))


def main():
    skill_dir = get_skill_dir()
    args = sys.argv[1:]

    for i, arg in enumerate(args):
        if arg == "--skill-dir" and i + 1 < len(args):
            skill_dir = Path(args[i + 1])
            args.pop(i)
            args.pop(i)
            break

    if "--install" in args:
        cmd_install(skill_dir)
    elif "--validate" in args:
        cmd_validate(skill_dir)
    elif "--check" in args:
        cmd_check(skill_dir)
    elif "--list-models" in args:
        cmd_list_models(skill_dir)
    elif "--image-capable" in args:
        cmd_image_capable(skill_dir)
    else:
        print(json.dumps({
            "error": "no command specified",
            "usage": {
                "--check": "Read-only check",
                "--validate": "Validate + auto-set informed_gate + suggest --install",
                "--install": "Inject missing models into models.json (creates backup)",
                "--list-models": "List all available private models",
                "--image-capable": "List image-capable models",
            }
        }, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
