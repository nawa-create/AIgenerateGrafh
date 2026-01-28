"""オーケストレーター

エージェント間のフローを制御し、データ分析からグラフ生成までの
パイプラインを管理する中央制御モジュール。
"""

import logging
from typing import Any

import anthropic
import pandas as pd

from agents.data_analyzer import DataAnalyzerAgent
from agents.visualization_proposer import VisualizationProposerAgent
from agents.code_generator import CodeGeneratorAgent
from agents.insight_generator import InsightGeneratorAgent
from config.settings import CLAUDE_MODEL

logger = logging.getLogger(__name__)


class Orchestrator:
    """エージェント間のフローを制御するオーケストレーター。

    Simple モードでは自動でグラフ生成まで実行し、
    Advanced モードでは分析・提案フェーズと生成フェーズを分離して
    ユーザーによる提案選択を挟むことができる。
    """

    def __init__(self, api_key: str) -> None:
        """オーケストレーターを初期化する。

        Args:
            api_key: LLM API キー。
        """
        self.api_key = api_key
        self.data_analyzer = DataAnalyzerAgent()
        self.visualization_proposer = VisualizationProposerAgent(api_key)
        self.code_generator = CodeGeneratorAgent(api_key)
        self.insight_generator = InsightGeneratorAgent(api_key)
        self.claude_client = anthropic.Anthropic(api_key=api_key)
        self.state: dict[str, Any] = {}
        # Internal state
        self._files: dict[str, pd.DataFrame] = {}
        self._data_profile: dict | None = None
        self._proposals: list[dict] = []
        self._selected_proposals: list[dict] = []
        self._charts: list[dict] = []
        self._conversation_history: list[dict] = []
        self._user_goal: str = ""

    # ------------------------------------------------------------------
    # Simple モード
    # ------------------------------------------------------------------

    @staticmethod
    def _dict_to_list(files: dict[str, pd.DataFrame]) -> list[dict]:
        """dict[str, DataFrame] を list[dict] 形式に変換する。"""
        return [{"name": name, "data": df} for name, df in files.items()]

    def run_simple_mode(self, files: dict[str, pd.DataFrame]) -> dict:
        """シンプルモードでデータ分析からグラフ生成までを一括実行する。

        Args:
            files: ファイル名からDataFrameへのマッピング。

        Returns:
            data_profile, proposals, charts を含む結果辞書。
        """
        self._files.update(files)
        files_list = self._dict_to_list(self._files)

        # Agent 1: データ分析
        logger.debug("Agent 1: データ分析を開始")
        try:
            data_profile = self.data_analyzer.analyze(files_list)
            self._data_profile = data_profile
        except Exception as e:
            logger.error("データ分析に失敗: %s", e)
            return {"data_profile": None, "proposals": [], "charts": [], "error": str(e)}

        # Agent 2: 可視化提案
        logger.debug("Agent 2: 可視化提案を開始（simple モード）")
        try:
            proposals = self.visualization_proposer.propose(
                data_profile=data_profile,
                mode="simple",
            )
            self._proposals = proposals if isinstance(proposals, list) else proposals.get("proposals", [])
        except Exception as e:
            logger.error("可視化提案に失敗: %s", e)
            return {"data_profile": data_profile, "proposals": [], "charts": [], "error": str(e)}

        # 優先度上位3件を選択
        proposal_list = proposals if isinstance(proposals, list) else proposals.get("proposals", [])
        top_proposals = sorted(
            proposal_list, key=lambda p: p.get("priority", 0), reverse=True
        )[:3]

        # Agent 3: コード生成・グラフ実行
        charts = self._generate_charts(self._files, data_profile, top_proposals)
        self._charts = charts

        return {
            "data_profile": data_profile,
            "proposals": proposals,
            "charts": charts,
        }

    # ------------------------------------------------------------------
    # Advanced モード（フェーズ1: 分析・提案）
    # ------------------------------------------------------------------

    def run_advanced_mode_analyze(self, files: dict[str, pd.DataFrame], user_goal: str) -> dict:
        """アドバンスモードの第1フェーズ: データ分析と可視化提案を行う。

        グラフ生成は行わず、ユーザーが提案を選択できるようにする。

        Args:
            files: ファイル名からDataFrameへのマッピング。
            user_goal: ユーザーが入力した分析目的。

        Returns:
            data_profile と proposals を含む結果辞書。
        """
        self._files.update(files)
        self._user_goal = user_goal
        files_list = self._dict_to_list(self._files)

        # Agent 1: データ分析
        logger.debug("Agent 1: データ分析を開始")
        try:
            data_profile = self.data_analyzer.analyze(files_list)
            self._data_profile = data_profile
        except Exception as e:
            logger.error("データ分析に失敗: %s", e)
            return {"data_profile": None, "proposals": [], "error": str(e)}

        # Agent 2: 可視化提案（advanced モード）
        logger.debug("Agent 2: 可視化提案を開始（advanced モード）")
        try:
            proposals = self.visualization_proposer.propose(
                data_profile=data_profile,
                mode="advanced",
                user_goal=user_goal,
            )
            self._proposals = proposals if isinstance(proposals, list) else proposals.get("proposals", [])
        except Exception as e:
            logger.error("可視化提案に失敗: %s", e)
            return {"data_profile": data_profile, "proposals": [], "error": str(e)}

        return {
            "data_profile": data_profile,
            "proposals": proposals,
        }

    # ------------------------------------------------------------------
    # Advanced モード（フェーズ2: 生成）
    # ------------------------------------------------------------------

    def run_advanced_mode_generate(
        self,
        selected_proposals: list[dict],
    ) -> dict:
        """アドバンスモードの第2フェーズ: 選択された提案のグラフ生成とインサイト生成を行う。

        Uses internal state for files and data_profile.

        Args:
            selected_proposals: ユーザーが選択した提案のリスト。

        Returns:
            charts（インサイト付き）を含む結果辞書。
        """
        self._selected_proposals = selected_proposals
        data_profile = self._data_profile
        charts = self._generate_charts(self._files, data_profile, selected_proposals)

        # Agent 4: 成功したチャートにインサイトを付与
        for chart in charts:
            if chart["error"] is not None:
                continue
            logger.debug("Agent 4: インサイト生成を開始 - %s", chart["proposal"].get("title", ""))
            try:
                insight = self.insight_generator.generate_insights(
                    data_profile=data_profile,
                    chart_data=chart["proposal"],
                    proposal=chart["proposal"],
                )
                chart["insight"] = insight
            except Exception as e:
                logger.error("インサイト生成に失敗: %s", e)
                chart["insight"] = None
                chart["insight_error"] = str(e)

        self._charts = charts
        return {"charts": charts}

    # ------------------------------------------------------------------
    # 単一チャート再生成
    # ------------------------------------------------------------------

    def regenerate_chart(
        self,
        proposal: dict | None = None,
    ) -> dict:
        """単一チャートを再生成する（「別のグラフを提案」ボタン用）。

        Uses internal state for files and data_profile.

        Args:
            proposal: 再生成対象の提案。Noneの場合は内部状態を使用。

        Returns:
            proposal, code, figure, error を含む結果辞書。
        """
        if proposal is None and self._selected_proposals:
            proposal = self._selected_proposals[0]
        if proposal is None:
            return {"proposal": {}, "code": "", "figure": None, "error": "提案が指定されていません"}
        charts = self._generate_charts(self._files, self._data_profile, [proposal])
        return charts[0] if charts else {"proposal": proposal, "code": "", "figure": None, "error": "生成に失敗しました"}

    def regenerate(self) -> dict:
        """内部状態を使用して全チャートを再生成する。

        Returns:
            charts を含む結果辞書。
        """
        proposals = self._selected_proposals or self._proposals
        if not proposals:
            return {"charts": [], "error": "提案がありません"}
        return self.run_advanced_mode_generate(proposals)

    # ------------------------------------------------------------------
    # 内部ヘルパー
    # ------------------------------------------------------------------

    def _generate_charts(
        self,
        files: dict[str, pd.DataFrame],
        data_profile: dict,
        proposals: list[dict],
    ) -> list[dict]:
        """提案リストに対してコード生成・実行を行い、チャートリストを返す。

        Args:
            files: ファイル名からDataFrameへのマッピング。
            data_profile: データプロファイル。
            proposals: 提案のリスト。

        Returns:
            チャート結果の辞書リスト。
        """
        # Ensure files is dict[str, DataFrame]
        if isinstance(files, list):
            file_data = {f["name"]: f["data"] for f in files}
        else:
            file_data = files

        charts: list[dict] = []
        for proposal in proposals:
            logger.debug("Agent 3: コード生成を開始 - %s", proposal.get("title", ""))
            try:
                result = self.code_generator.generate(
                    data_profile=data_profile,
                    proposal=proposal,
                    file_data=file_data,
                )
                charts.append({
                    "proposal": proposal,
                    "code": result.get("code", ""),
                    "figure": result.get("figure"),
                    "error": result.get("error"),
                })
            except Exception as e:
                logger.error("コード生成に失敗: %s", e)
                charts.append({
                    "proposal": proposal,
                    "code": "",
                    "figure": None,
                    "error": str(e),
                })
        return charts

    # ------------------------------------------------------------------
    # チャット機能（本気分析モード）
    # ------------------------------------------------------------------

    def handle_chat_message(self, message: str) -> str:
        """本気分析モード用のチャットメッセージを処理する。

        Args:
            message: ユーザーからのメッセージ。

        Returns:
            AIからの応答文字列。
        """
        self._conversation_history.append({"role": "user", "content": message})

        system_prompt = "あなたはデータ分析の専門家です。ユーザーのデータに基づいてフォローアップの質問や分析の提案を行ってください。"
        if self._data_profile:
            import json
            system_prompt += f"\n\n## 現在のデータプロファイル\n{json.dumps(self._data_profile, ensure_ascii=False, default=str)}"

        try:
            response = self.claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2048,
                system=system_prompt,
                messages=self._conversation_history,
            )
            reply = response.content[0].text
            self._conversation_history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            logger.error("チャットメッセージ処理に失敗: %s", e)
            return f"エラーが発生しました: {e}"

    # ------------------------------------------------------------------
    # ファイル追加
    # ------------------------------------------------------------------

    def add_files(self, new_files: dict[str, pd.DataFrame]) -> None:
        """追加ファイルを内部状態にマージする。

        Args:
            new_files: 追加するファイル名からDataFrameへのマッピング。
        """
        self._files.update(new_files)
