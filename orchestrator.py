"""オーケストレーター

エージェント間のフローを制御し、データ分析からグラフ生成までの
パイプラインを管理する中央制御モジュール。
"""

import logging
from typing import Any

from agents.data_analyzer import DataAnalyzerAgent
from agents.visualization_proposer import VisualizationProposerAgent
from agents.code_generator import CodeGeneratorAgent
from agents.insight_generator import InsightGeneratorAgent

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
        self.data_analyzer = DataAnalyzerAgent()
        self.visualization_proposer = VisualizationProposerAgent(api_key)
        self.code_generator = CodeGeneratorAgent(api_key)
        self.insight_generator = InsightGeneratorAgent(api_key)
        self.state: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Simple モード
    # ------------------------------------------------------------------

    def run_simple_mode(self, files: list[dict]) -> dict:
        """シンプルモードでデータ分析からグラフ生成までを一括実行する。

        Args:
            files: ファイル情報のリスト。各要素は {"name": str, "data": pd.DataFrame}。

        Returns:
            data_profile, proposals, charts を含む結果辞書。
        """
        # Agent 1: データ分析
        logger.debug("Agent 1: データ分析を開始")
        try:
            data_profile = self.data_analyzer.analyze(files)
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
        except Exception as e:
            logger.error("可視化提案に失敗: %s", e)
            return {"data_profile": data_profile, "proposals": [], "charts": [], "error": str(e)}

        # 優先度上位3件を選択
        top_proposals = sorted(
            proposals, key=lambda p: p.get("priority", 0), reverse=True
        )[:3]

        # Agent 3: コード生成・グラフ実行
        charts = self._generate_charts(files, data_profile, top_proposals)

        return {
            "data_profile": data_profile,
            "proposals": proposals,
            "charts": charts,
        }

    # ------------------------------------------------------------------
    # Advanced モード（フェーズ1: 分析・提案）
    # ------------------------------------------------------------------

    def run_advanced_mode_analyze(self, files: list[dict], user_goal: str) -> dict:
        """アドバンスモードの第1フェーズ: データ分析と可視化提案を行う。

        グラフ生成は行わず、ユーザーが提案を選択できるようにする。

        Args:
            files: ファイル情報のリスト。
            user_goal: ユーザーが入力した分析目的。

        Returns:
            data_profile と proposals を含む結果辞書。
        """
        # Agent 1: データ分析
        logger.debug("Agent 1: データ分析を開始")
        try:
            data_profile = self.data_analyzer.analyze(files)
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
        files: list[dict],
        data_profile: dict,
        selected_proposals: list[dict],
    ) -> dict:
        """アドバンスモードの第2フェーズ: 選択された提案のグラフ生成とインサイト生成を行う。

        Args:
            files: ファイル情報のリスト。
            data_profile: 第1フェーズで得たデータプロファイル。
            selected_proposals: ユーザーが選択した提案のリスト。

        Returns:
            charts（インサイト付き）を含む結果辞書。
        """
        charts = self._generate_charts(files, data_profile, selected_proposals)

        # Agent 4: 成功したチャートにインサイトを付与
        for chart in charts:
            if chart["error"] is not None:
                continue
            logger.debug("Agent 4: インサイト生成を開始 - %s", chart["proposal"].get("title", ""))
            try:
                insight = self.insight_generator.generate(
                    data_profile=data_profile,
                    proposal=chart["proposal"],
                    figure=chart["figure"],
                )
                chart["insight"] = insight
            except Exception as e:
                logger.error("インサイト生成に失敗: %s", e)
                chart["insight"] = None
                chart["insight_error"] = str(e)

        return {"charts": charts}

    # ------------------------------------------------------------------
    # 単一チャート再生成
    # ------------------------------------------------------------------

    def regenerate_chart(
        self,
        files: list[dict],
        data_profile: dict,
        proposal: dict,
    ) -> dict:
        """単一チャートを再生成する（「別のグラフを提案」ボタン用）。

        Args:
            files: ファイル情報のリスト。
            data_profile: データプロファイル。
            proposal: 再生成対象の提案。

        Returns:
            proposal, code, figure, error を含む結果辞書。
        """
        charts = self._generate_charts(files, data_profile, [proposal])
        return charts[0] if charts else {"proposal": proposal, "code": "", "figure": None, "error": "生成に失敗しました"}

    # ------------------------------------------------------------------
    # 内部ヘルパー
    # ------------------------------------------------------------------

    def _generate_charts(
        self,
        files: list[dict],
        data_profile: dict,
        proposals: list[dict],
    ) -> list[dict]:
        """提案リストに対してコード生成・実行を行い、チャートリストを返す。

        Args:
            files: ファイル情報のリスト。
            data_profile: データプロファイル。
            proposals: 提案のリスト。

        Returns:
            チャート結果の辞書リスト。
        """
        charts: list[dict] = []
        for proposal in proposals:
            logger.debug("Agent 3: コード生成を開始 - %s", proposal.get("title", ""))
            try:
                result = self.code_generator.generate(
                    data_profile=data_profile,
                    proposal=proposal,
                    files=files,
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
