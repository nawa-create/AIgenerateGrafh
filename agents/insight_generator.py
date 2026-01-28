"""インサイト生成エージェント - データ分析から洞察と推奨事項を生成する。"""

import json

import anthropic

from config.settings import CLAUDE_MODEL


class InsightGeneratorAgent:
    """本気分析モード用のインサイト生成エージェント。Claude APIを使用してデータから洞察を抽出する。"""

    def __init__(self, api_key: str):
        """エージェントを初期化する。

        Args:
            api_key: Anthropic APIキー
        """
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_insights(self, data_profile: dict, chart_data: dict, proposal: dict) -> dict:
        """データプロファイルとチャートデータを分析し、インサイトと推奨事項を生成する。

        Args:
            data_profile: データの統計プロファイル情報
            chart_data: チャート作成に使用された集計データ
            proposal: チャート提案の内容

        Returns:
            インサイトと推奨事項を含む辞書:
            {
                "insights": [{"type": str, "severity": str, "message": str}, ...],
                "recommendations": [str, ...]
            }
        """
        prompt = f"""あなたはデータ分析の専門家です。以下のデータを分析し、インサイトと推奨事項を日本語で返してください。

## データプロファイル
{json.dumps(data_profile, ensure_ascii=False, default=str)}

## チャート用集計データ
{json.dumps(chart_data, ensure_ascii=False, default=str)}

## チャート提案内容
{json.dumps(proposal, ensure_ascii=False, default=str)}

以下の観点で分析してください:
1. トレンド検出: 増加・減少・横ばいの傾向を特定する
2. 異常値検出: 平均から標準偏差の2倍以上乖離している値を見つける
3. パターン発見: 曜日別、季節性などの周期的パターンを探す
4. 比較分析: カテゴリ間やグループ間の比較を行う

以下のJSON形式で回答してください。インサイトは最大5件、推奨事項は最大3件としてください。
すべて日本語で記述してください。

```json
{{
    "insights": [
        {{
            "type": "trend|anomaly|pattern|comparison",
            "severity": "info|warning",
            "message": "日本語での説明"
        }}
    ],
    "recommendations": [
        "日本語での推奨事項"
    ]
}}
```

JSONのみを返してください。"""

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text

            # JSON部分を抽出する
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            result = json.loads(response_text.strip())

            # 件数制限を適用する
            result["insights"] = result.get("insights", [])[:5]
            result["recommendations"] = result.get("recommendations", [])[:3]

            return result

        except (json.JSONDecodeError, IndexError, KeyError):
            return {
                "insights": [
                    {
                        "type": "pattern",
                        "severity": "info",
                        "message": "インサイトの生成中にエラーが発生しました。データ形式を確認してください。",
                    }
                ],
                "recommendations": ["データの形式や内容を確認し、再度分析を実行してください。"],
            }
        except anthropic.APIError:
            return {
                "insights": [
                    {
                        "type": "pattern",
                        "severity": "warning",
                        "message": "APIとの通信中にエラーが発生しました。",
                    }
                ],
                "recommendations": ["APIキーとネットワーク接続を確認してください。"],
            }
