"""安全なコード実行エンジン - 生成されたPlotlyコードをサンドボックス内で実行する。"""

import io
import re
import sys
import threading
import traceback

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots

from config.settings import BLOCKED_OPERATIONS, TIMEOUT_SECONDS


def execute_code(
    code: str, dataframes: dict[str, pd.DataFrame], timeout: int = 30
) -> dict:
    """生成されたコードを安全に実行し、Plotlyフィギュアを返す。

    Args:
        code: 実行するPythonコード文字列
        dataframes: キーがファイル名、値がDataFrameの辞書
        timeout: 実行タイムアウト秒数（デフォルト: 30）

    Returns:
        実行結果を含む辞書:
        {
            "success": bool,
            "figure": plotlyフィギュアまたはNone,
            "error": エラーメッセージまたはNone,
            "output": 標準出力の文字列
        }
    """
    # ブロック対象の操作を検証する
    for blocked in BLOCKED_OPERATIONS:
        pattern = re.escape(blocked)
        if re.search(r'(?<!\w)' + pattern, code):
            return {
                "success": False,
                "figure": None,
                "error": f"セキュリティエラー: '{blocked}' の使用は禁止されています。",
                "output": "",
            }

    # 制限された名前空間を構築する
    namespace = {
        "pd": pd,
        "np": np,
        "px": px,
        "go": go,
        "make_subplots": plotly.subplots.make_subplots,
    }

    # DataFrameをdf_0, df_1, ...として注入する
    for i, (name, df) in enumerate(dataframes.items()):
        namespace[f"df_{i}"] = df.copy()

    # スレッドベースのタイムアウト実行
    effective_timeout = min(timeout, TIMEOUT_SECONDS)
    stdout_capture = io.StringIO()
    result_holder = {"error": None}

    def _run():
        old_stdout = sys.stdout
        sys.stdout = stdout_capture
        try:
            exec(code, namespace)  # noqa: S102
        except Exception:
            result_holder["error"] = traceback.format_exc()
        finally:
            sys.stdout = old_stdout

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=effective_timeout)

    if thread.is_alive():
        return {
            "success": False,
            "figure": None,
            "error": "コードの実行がタイムアウトしました。",
            "output": stdout_capture.getvalue(),
        }

    if result_holder["error"] is not None:
        return {
            "success": False,
            "figure": None,
            "error": result_holder["error"],
            "output": stdout_capture.getvalue(),
        }

    # figを名前空間から取得する（複数の変数名に対応）
    figure = namespace.get("fig", None)
    if figure is None:
        figure = namespace.get("figure", None)
    if figure is None:
        # 名前空間からPlotlyフィギュアオブジェクトを探す
        for val in namespace.values():
            if hasattr(val, "to_html") and hasattr(val, "update_layout"):
                figure = val
                break

    return {
        "success": True,
        "figure": figure,
        "error": None,
        "output": stdout_capture.getvalue(),
    }
