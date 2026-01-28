"""グラフテンプレート管理モジュール"""

import json
import os
from datetime import datetime
from pathlib import Path


TEMPLATE_DIR = Path.home() / ".ai_graph_generator" / "templates"


def _ensure_dir():
    """テンプレートディレクトリを確保する"""
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)


def save_template(name: str, chart_config: dict) -> str:
    """
    テンプレートを保存する

    Args:
        name: テンプレート名
        chart_config: グラフ設定（proposal + customization）
            {
                "proposal": dict,  # Original proposal from Agent 2
                "customization": dict,  # User customizations (title, colors, etc.)
                "code": str,  # Generated code
            }

    Returns:
        保存されたテンプレートのID
    """
    _ensure_dir()
    template_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name.replace(' ', '_')}"
    template = {
        "id": template_id,
        "name": name,
        "created_at": datetime.now().isoformat(),
        "config": chart_config,
    }
    filepath = TEMPLATE_DIR / f"{template_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2, default=str)
    return template_id


def load_template(template_id: str) -> dict | None:
    """
    テンプレートを読み込む

    Returns:
        テンプレートdict or None
    """
    filepath = TEMPLATE_DIR / f"{template_id}.json"
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_templates() -> list[dict]:
    """
    保存済みテンプレート一覧を返す

    Returns:
        [{"id": str, "name": str, "created_at": str}]
    """
    _ensure_dir()
    templates = []
    for filepath in sorted(TEMPLATE_DIR.glob("*.json"), reverse=True):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                templates.append({
                    "id": data["id"],
                    "name": data["name"],
                    "created_at": data["created_at"],
                })
        except (json.JSONDecodeError, KeyError):
            continue
    return templates


def delete_template(template_id: str) -> bool:
    """テンプレートを削除する"""
    filepath = TEMPLATE_DIR / f"{template_id}.json"
    if filepath.exists():
        filepath.unlink()
        return True
    return False
