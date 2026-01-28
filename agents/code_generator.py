# =============================================================================
# Agent 3: コード生成エージェント
# =============================================================================

import json
import re

import anthropic
import pandas as pd

from config.settings import CLAUDE_MODEL
from utils.code_executor import execute_code


class CodeGeneratorAgent:
    """データプロファイルと提案に基づいてグラフ生成コードを作成するエージェント。"""

    def __init__(self, api_key: str):
        """
        コード生成エージェントを初期化する。

        Args:
            api_key: Anthropic APIキー
        """
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(
        self,
        data_profile: dict,
        proposal: dict,
        file_data: dict[str, pd.DataFrame],
    ) -> dict:
        """
        提案に基づいてPythonコードを生成し、実行する。

        Args:
            data_profile: Agent 1が生成したデータプロファイル
            proposal: Agent 2が生成した単一の提案辞書
            file_data: ファイル名からDataFrameへのマッピング

        Returns:
            code, chart_html, figure, errorを含む辞書
        """
        file_names = list(file_data.keys())
        prompt = self._build_prompt(data_profile, proposal, file_names)

        result = self._attempt_generate(prompt, file_data)

        # 失敗した場合、エラーメッセージを付加して1回リトライする
        if result["error"] is not None:
            retry_prompt = (
                f"{prompt}\n\n"
                f"前回の生成コードでエラーが発生しました。以下のエラーを修正してください:\n"
                f"エラー: {result['error']}\n\n"
                f"生成されたコード:\n```python\n{result['code']}\n```"
            )
            result = self._attempt_generate(retry_prompt, file_data)

        return result

    def _attempt_generate(
        self, prompt: str, file_data: dict[str, pd.DataFrame]
    ) -> dict:
        """
        コード生成と実行を1回試行する。

        Args:
            prompt: Claudeに送信するプロンプト
            file_data: ファイル名からDataFrameへのマッピング

        Returns:
            code, chart_html, figure, errorを含む辞書
        """
        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.content[0].text
            code = self._extract_code(response_text)

            if not code:
                return {
                    "code": "",
                    "chart_html": None,
                    "figure": None,
                    "error": "レスポンスからPythonコードを抽出できませんでした。",
                }

            # DataFrameをdf_0, df_1, ...として準備する
            variables = {}
            for i, (_, df) in enumerate(file_data.items()):
                variables[f"df_{i}"] = df

            exec_result = execute_code(code, variables)

            figure = exec_result.get("fig")
            chart_html = None
            if figure is not None:
                try:
                    chart_html = figure.to_html(include_plotlyjs="cdn", full_html=False)
                except Exception:
                    pass

            return {
                "code": code,
                "chart_html": chart_html,
                "figure": figure,
                "error": exec_result.get("error"),
            }

        except Exception as e:
            return {
                "code": "",
                "chart_html": None,
                "figure": None,
                "error": str(e),
            }

    def _extract_code(self, text: str) -> str:
        """
        レスポンステキストからPythonコードブロックを抽出する。

        Args:
            text: Claudeのレスポンステキスト

        Returns:
            抽出されたPythonコード文字列
        """
        pattern = r"```python\s*\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # フォールバック: 任意のコードブロック
        pattern = r"```\s*\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _build_prompt(
        self, data_profile: dict, proposal: dict, file_names: list[str]
    ) -> str:
        """
        Claude用のプロンプトを構築する。

        Args:
            data_profile: データプロファイル辞書
            proposal: グラフ提案辞書
            file_names: ファイル名のリスト

        Returns:
            構築されたプロンプト文字列
        """
        # ファイルとDataFrame変数のマッピング情報
        df_mapping = "\n".join(
            f"- {name} -> df_{i}" for i, name in enumerate(file_names)
        )

        prompt = f"""あなたはデータ可視化の専門家です。
以下のデータプロファイルとグラフ提案に基づいて、pandasとplotly.expressを使用したPythonコードを生成してください。

## データプロファイル
{json.dumps(data_profile, ensure_ascii=False, indent=2, default=str)}

## グラフ提案
{json.dumps(proposal, ensure_ascii=False, indent=2, default=str)}

## DataFrame変数のマッピング
{df_mapping}

## 要件
1. DataFrameは既に変数として読み込まれています（ファイル読み込みコードは不要）
2. 必要に応じてデータ型の変換や欠損値の処理を行ってください
3. 提案に従ってデータの集計・加工を行ってください
4. plotly.expressを使用してグラフを作成してください
5. グラフのラベル、タイトル、凡例はすべて日本語にしてください
6. 見やすいスタイリング（適切な色、フォントサイズなど）を適用してください
7. 最終的なplotlyのfigureオブジェクトを変数 `fig` に格納してください
8. fig.show() は呼び出さないでください

Pythonコードのみを```python```ブロックで出力してください。
"""
        return prompt
