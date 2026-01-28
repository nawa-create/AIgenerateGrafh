"""可視化提案エージェント。

データプロファイルに基づいて最適なグラフを提案するエージェント。
Claude APIを使用してインテリジェントなグラフ提案を生成する。
"""

import json
import logging

import anthropic

from config import settings

logger = logging.getLogger(__name__)

PROPOSAL_SYSTEM_PROMPT = """\
あなたはデータ可視化の専門家です。与えられたデータプロファイルを分析し、最適なグラフを提案してください。

## グラフ選択ルール
- 日付型 + 数値型 → 折れ線グラフ (line)
- カテゴリ型 + 数値型 → 棒グラフ (bar)
- 数値型 + 数値型 → 散布図 (scatter)
- カテゴリの割合（カテゴリ数が8未満）→ 円グラフ (pie)
- 日付型 + カテゴリ型 + 数値型 → 積み上げ面グラフ (stacked_area) または グループ棒グラフ (grouped_bar)
- 複数ファイルに関連性がある場合 → 結合グラフを提案

## 出力形式
必ず以下のJSON形式で回答してください。JSON以外のテキストは含めないでください。

```json
{
    "proposals": [
        {
            "id": 1,
            "title": "グラフタイトル（日本語）",
            "chart_type": "line|bar|scatter|pie|area|grouped_bar|stacked_bar|heatmap",
            "description": "このグラフの説明（日本語）",
            "x_axis": {"file": "ファイル名", "column": "列名"},
            "y_axis": {"file": "ファイル名", "column": "列名", "agg": "sum|mean|count"},
            "group_by": {"file": "ファイル名", "column": "列名"},
            "priority": "high|medium|low",
            "insight_potential": "このグラフから得られる可能性のある知見"
        }
    ],
    "additional_data_suggestions": [
        {
            "data_type": "追加データの説明",
            "reason": "なぜこのデータが必要か",
            "expected_columns": ["列名1", "列名2"]
        }
    ]
}
```

group_by は不要な場合は null にしてください。
additional_data_suggestions はadvancedモードの場合のみ含めてください。
"""


class VisualizationProposerAgent:
    """データプロファイルに基づいてグラフの提案を生成するエージェント。

    Claude APIを使用してデータに最適な可視化方法を提案する。
    API呼び出しが失敗した場合はルールベースのフォールバックを使用する。
    """

    def __init__(self, api_key: str):
        """エージェントを初期化する。

        Args:
            api_key: Anthropic APIキー。
        """
        self.client = anthropic.Anthropic(api_key=api_key)

    def propose(self, data_profile: dict, mode: str = "simple", user_goal: str = None) -> dict:
        """データプロファイルに基づいてグラフ提案を生成する。

        Args:
            data_profile: データ分析エージェントから取得したデータプロファイル。
            mode: 'simple'（1-3件の基本提案）または 'advanced'（3-6件の詳細提案）。
            user_goal: ユーザーの分析目的（advancedモードで使用）。

        Returns:
            提案されたグラフ情報を含む辞書。
        """
        try:
            return self._propose_with_api(data_profile, mode, user_goal)
        except Exception as e:
            logger.warning("Claude API呼び出しに失敗しました。ルールベースのフォールバックを使用します: %s", e)
            return self._fallback_propose(data_profile, mode)

    def _build_user_prompt(self, data_profile: dict, mode: str, user_goal: str = None) -> str:
        """Claude APIに送信するユーザープロンプトを構築する。"""
        prompt_parts = [
            f"## データプロファイル\n```json\n{json.dumps(data_profile, ensure_ascii=False, indent=2)}\n```",
            f"\n## モード: {mode}",
        ]

        if mode == "simple":
            prompt_parts.append("1〜3件の基本的なグラフを提案してください。additional_data_suggestionsは不要です。")
        else:
            prompt_parts.append(
                "3〜6件の詳細なグラフを提案してください。additional_data_suggestionsも含めてください。"
            )

        if user_goal:
            prompt_parts.append(f"\n## ユーザーの分析目的\n{user_goal}")

        return "\n".join(prompt_parts)

    def _propose_with_api(self, data_profile: dict, mode: str, user_goal: str = None) -> dict:
        """Claude APIを使用してグラフ提案を生成する。"""
        user_prompt = self._build_user_prompt(data_profile, mode, user_goal)

        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=4096,
            system=PROPOSAL_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = response.content[0].text
        return self._parse_response(raw_text, mode)

    def _parse_response(self, raw_text: str, mode: str) -> dict:
        """Claude APIのレスポンスからJSONをパースする。"""
        text = raw_text.strip()

        # コードブロックで囲まれている場合は除去
        if text.startswith("```"):
            first_newline = text.index("\n")
            text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[: text.rfind("```")]

        result = json.loads(text.strip())

        if "proposals" not in result:
            raise ValueError("レスポンスに 'proposals' キーがありません")

        # simpleモードではadditional_data_suggestionsを除去
        if mode == "simple":
            result.pop("additional_data_suggestions", None)

        return result

    # ------------------------------------------------------------------
    # ルールベースのフォールバック
    # ------------------------------------------------------------------

    def _fallback_propose(self, data_profile: dict, mode: str) -> dict:
        """APIが利用できない場合のルールベースの提案を生成する。"""
        proposals = []
        proposal_id = 0

        files_info = data_profile.get("files", [])
        if not files_info:
            # files キーが無い場合はトップレベルを1ファイル分として扱う
            files_info = [{"name": "data", "columns": data_profile.get("columns", [])}]

        for file_profile in files_info:
            filename = file_profile.get("name", "data")
            columns_list = file_profile.get("columns", [])

            date_cols = [c["name"] for c in columns_list if c.get("type") in ("datetime", "date")]
            numeric_cols = [c["name"] for c in columns_list if c.get("type") in ("int64", "float64", "numeric", "number")]
            category_cols = [c["name"] for c in columns_list if c.get("type") in ("object", "category", "string", "categorical")]

            # Build a lookup for unique_count by column name
            col_lookup = {c["name"]: c for c in columns_list}

            # 日付 + 数値 → 折れ線グラフ
            for date_col in date_cols:
                for num_col in numeric_cols:
                    proposal_id += 1
                    proposals.append(
                        {
                            "id": proposal_id,
                            "title": f"{num_col}の時系列推移",
                            "chart_type": "line",
                            "description": f"{date_col}に対する{num_col}の推移を表示します。",
                            "x_axis": {"file": filename, "column": date_col},
                            "y_axis": {"file": filename, "column": num_col, "agg": "sum"},
                            "group_by": None,
                            "priority": "high",
                            "insight_potential": "時系列トレンドの把握",
                        }
                    )

            # カテゴリ + 数値 → 棒グラフ
            for cat_col in category_cols:
                unique_count = col_lookup[cat_col].get("unique_count", 999)
                for num_col in numeric_cols:
                    proposal_id += 1
                    chart_type = "pie" if unique_count < 8 and not date_cols else "bar"
                    proposals.append(
                        {
                            "id": proposal_id,
                            "title": f"{cat_col}別の{num_col}",
                            "chart_type": chart_type,
                            "description": f"{cat_col}ごとの{num_col}を比較します。",
                            "x_axis": {"file": filename, "column": cat_col},
                            "y_axis": {"file": filename, "column": num_col, "agg": "sum"},
                            "group_by": None,
                            "priority": "medium",
                            "insight_potential": "カテゴリ間の比較",
                        }
                    )

            # 数値 + 数値 → 散布図
            if len(numeric_cols) >= 2:
                proposal_id += 1
                proposals.append(
                    {
                        "id": proposal_id,
                        "title": f"{numeric_cols[0]}と{numeric_cols[1]}の関係",
                        "chart_type": "scatter",
                        "description": f"{numeric_cols[0]}と{numeric_cols[1]}の相関を確認します。",
                        "x_axis": {"file": filename, "column": numeric_cols[0]},
                        "y_axis": {"file": filename, "column": numeric_cols[1], "agg": "mean"},
                        "group_by": None,
                        "priority": "medium",
                        "insight_potential": "変数間の相関関係の発見",
                    }
                )

        # モードに応じて件数を制限
        max_proposals = 3 if mode == "simple" else 6
        proposals = proposals[:max_proposals]

        if not proposals:
            proposals.append(
                {
                    "id": 1,
                    "title": "データ概要",
                    "chart_type": "bar",
                    "description": "利用可能なデータの概要を表示します。",
                    "x_axis": {"file": "", "column": ""},
                    "y_axis": {"file": "", "column": "", "agg": "count"},
                    "group_by": None,
                    "priority": "low",
                    "insight_potential": "データの基本構造の把握",
                }
            )

        result = {"proposals": proposals}
        if mode == "advanced":
            result["additional_data_suggestions"] = []

        return result
