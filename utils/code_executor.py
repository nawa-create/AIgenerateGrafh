"""安全なコード実行エンジン - 生成されたPlotlyコードをサンドボックス内で実行する。"""

import io
import re
import signal
import sys
import traceback

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots

from config.settings import BLOCKED_OPERATIONS, TIMEOUT_SECONDS


def _timeout_handler(signum, frame):
    """タイムアウト時に呼び出されるシグナルハンドラ。"""
    raise TimeoutError("コードの実行がタイムアウトしました。")


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
        # Use word boundary matching to reduce false positives
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

    # 標準出力をキャプチャする
    stdout_capture = io.StringIO()

    # タイムアウトを設定する
    effective_timeout = min(timeout, TIMEOUT_SECONDS)
    old_handler = None

    try:
        # Linuxではsignal.alarmでタイムアウトを設定する
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(effective_timeout)

        old_stdout = sys.stdout
        sys.stdout = stdout_capture
        try:
            exec(code, namespace)  # noqa: S102
        finally:
            sys.stdout = old_stdout

        signal.alarm(0)

        # figを名前空間から取得する
        figure = namespace.get("fig", None)

        return {
            "success": True,
            "figure": figure,
            "error": None,
            "output": stdout_capture.getvalue(),
        }

    except TimeoutError as e:
        return {
            "success": False,
            "figure": None,
            "error": str(e),
            "output": stdout_capture.getvalue(),
        }
    except Exception:
        return {
            "success": False,
            "figure": None,
            "error": traceback.format_exc(),
            "output": stdout_capture.getvalue(),
        }
    finally:
        if old_handler is not None:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
