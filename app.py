# =============================================================================
# AI Graph Generator - Main Streamlit Application
# =============================================================================

import os
import io
import streamlit as st
import pandas as pd
import plotly.io as pio

from dotenv import load_dotenv

from orchestrator import Orchestrator
from config.settings import (
    APP_TITLE,
    SIMPLE_MODE,
    ADVANCED_MODE,
    ALLOWED_EXTENSIONS,
)

load_dotenv()

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(page_title="AI Graph Generator", page_icon="\U0001f4ca", layout="wide")

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _init_session_state():
    """Initialize session state variables if not already present."""
    defaults = {
        "mode": None,
        "files": [],
        "data_profile": None,
        "proposals": None,
        "charts": [],
        "conversation": [],
        "step": "mode_select",
        "orchestrator": None,
        "user_goal": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_file(uploaded_file) -> dict:
    """Read an uploaded file into a DataFrame and return metadata dict."""
    name = uploaded_file.name
    ext = os.path.splitext(name)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(uploaded_file)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return {"name": name, "df": df, "rows": len(df), "columns": list(df.columns)}


def get_api_key() -> str:
    """Retrieve API key from secrets, environment, or sidebar input."""
    # 1. Streamlit secrets
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            return key
    except Exception:
        pass

    # 2. Environment variable
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key

    # 3. Sidebar input (already rendered elsewhere, read from session)
    return st.session_state.get("sidebar_api_key", "")


def reset_session():
    """Clear all session state and return to mode selection."""
    keys_to_clear = [
        "mode", "files", "data_profile", "proposals",
        "charts", "conversation", "step", "orchestrator", "user_goal",
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        st.header("Settings")

        # API key input if not in env / secrets
        env_key = os.environ.get("ANTHROPIC_API_KEY", "")
        try:
            secret_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            secret_key = ""

        if not env_key and not secret_key:
            st.text_input(
                "Anthropic API Key",
                type="password",
                key="sidebar_api_key",
                help="APIキーを入力してください",
            )

        st.divider()

        # Current mode display
        mode = st.session_state.get("mode")
        if mode == SIMPLE_MODE:
            st.info("現在のモード: 簡単作成")
        elif mode == ADVANCED_MODE:
            st.info("現在のモード: 本気分析")
        else:
            st.info("モード未選択")

        st.divider()

        if st.button("リセット", use_container_width=True):
            reset_session()
            st.rerun()


# -----------------------------------------------------------------------------
# Step Renderers
# -----------------------------------------------------------------------------

def render_mode_select():
    """Top page - mode selection."""
    st.markdown(
        f"<h1 style='text-align:center;'>\U0001f4ca {APP_TITLE}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:gray;'>データをアップロードするだけで、AIが最適なグラフを自動生成します</p>",
        unsafe_allow_html=True,
    )

    st.write("")
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.markdown("### \u26a1 簡単作成")
        st.markdown("**とりあえずグラフを作りたい**")
        st.caption("所要時間: 1〜2分")
        st.markdown(
            "ファイルをアップロードするだけで、AIがデータを読み取り最適なグラフを自動で提案・生成します。"
        )
        if st.button("簡単作成を始める", use_container_width=True, type="primary"):
            st.session_state.mode = SIMPLE_MODE
            st.session_state.step = "simple_upload"
            st.rerun()

    with col_right:
        st.markdown("### \U0001f52c 本気分析")
        st.markdown("**課題を深掘りして最適な分析を行う**")
        st.caption("所要時間: 5〜10分")
        st.markdown(
            "AIとの対話を通じて課題を明確にし、データに基づいた深い分析とインサイトを得られます。"
        )
        if st.button("本気分析を始める", use_container_width=True, type="primary"):
            st.session_state.mode = ADVANCED_MODE
            st.session_state.step = "advanced_hearing"
            st.rerun()


def render_simple_upload():
    """Simple mode - file upload step."""
    col_header, col_btn = st.columns([8, 2])
    with col_header:
        st.header("\u26a1 簡単作成モード")
    with col_btn:
        if st.button("モード変更"):
            reset_session()
            st.rerun()

    uploaded = st.file_uploader(
        "データファイルをアップロード",
        accept_multiple_files=True,
        type=["xlsx", "xls", "csv"],
        help="Excel (.xlsx, .xls) または CSV (.csv) ファイルを選択してください",
    )

    if uploaded:
        st.subheader("アップロードされたファイル")
        file_data_list = []
        for f in uploaded:
            try:
                file_info = load_file(f)
                file_data_list.append(file_info)
                st.write(f"- **{file_info['name']}**: {file_info['rows']}行 × {len(file_info['columns'])}列")
            except Exception as e:
                st.error(f"ファイル読み込みエラー ({f.name}): {e}")

        st.write("")
        if st.button("グラフを自動生成", type="primary", use_container_width=True):
            api_key = get_api_key()
            if not api_key:
                st.error("APIキーが設定されていません。サイドバーから入力してください。")
                return

            try:
                with st.spinner("AIがデータを分析してグラフを生成しています..."):
                    dataframes = {fd["name"]: fd["df"] for fd in file_data_list}
                    orch = Orchestrator(api_key=api_key)
                    result = orch.run_simple_mode(dataframes)
                    st.session_state.orchestrator = orch
                    st.session_state.files = file_data_list
                    st.session_state.charts = result.get("charts", [])
                    st.session_state.step = "simple_result"
                    st.rerun()
            except Exception as e:
                st.error(f"グラフ生成中にエラーが発生しました: {e}")


def render_simple_result():
    """Simple mode - results display."""
    col_header, col_btn = st.columns([8, 2])
    with col_header:
        st.header("\u26a1 簡単作成 - 結果")
    with col_btn:
        if st.button("モード変更"):
            reset_session()
            st.rerun()

    charts = st.session_state.get("charts", [])

    if not charts:
        st.warning("生成されたグラフがありません。")
    else:
        for i, chart in enumerate(charts):
            st.subheader(chart.get("title", f"グラフ {i + 1}"))
            fig = chart.get("figure")
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{i}")

                # Download buttons
                dl_col1, dl_col2 = st.columns(2)
                with dl_col1:
                    html_str = pio.to_html(fig, full_html=True)
                    st.download_button(
                        label="HTMLでダウンロード",
                        data=html_str,
                        file_name=f"chart_{i + 1}.html",
                        mime="text/html",
                        key=f"dl_html_{i}",
                    )
                with dl_col2:
                    try:
                        img_bytes = fig.to_image(format="png")
                        st.download_button(
                            label="PNGでダウンロード",
                            data=img_bytes,
                            file_name=f"chart_{i + 1}.png",
                            mime="image/png",
                            key=f"dl_png_{i}",
                        )
                    except Exception:
                        st.caption("PNG出力にはkaleidoパッケージが必要です")

            # Show generated code
            code = chart.get("code", "")
            if code:
                with st.expander("生成されたコードを表示"):
                    st.code(code, language="python")

            st.divider()

    # Action buttons
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("別のグラフを提案", use_container_width=True):
            orch = st.session_state.get("orchestrator")
            if orch is not None:
                try:
                    with st.spinner("別のグラフを生成中..."):
                        result = orch.regenerate()
                        st.session_state.charts = result.get("charts", [])
                        st.rerun()
                except Exception as e:
                    st.error(f"再生成中にエラーが発生しました: {e}")
    with btn_col2:
        if st.button("最初に戻る", use_container_width=True):
            reset_session()
            st.rerun()


def render_advanced_hearing():
    """Advanced mode - hearing / chat step."""
    col_header, col_btn = st.columns([8, 2])
    with col_header:
        st.header("\U0001f52c 本気分析モード")
    with col_btn:
        if st.button("モード変更"):
            reset_session()
            st.rerun()

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("ヒアリング")

        # Conversation history
        conversation = st.session_state.get("conversation", [])
        if not conversation:
            conversation = [{"role": "assistant", "content": "こんにちは！どんな課題を解決したいですか？"}]
            st.session_state.conversation = conversation

        for msg in conversation:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # User goal input
        user_goal = st.text_area(
            "解決したい課題を教えてください",
            value=st.session_state.get("user_goal", ""),
            key="goal_input",
            height=100,
        )
        st.session_state.user_goal = user_goal

        if user_goal:
            # File uploader (shown after goal is entered)
            st.write("")
            uploaded = st.file_uploader(
                "データファイルをアップロード",
                accept_multiple_files=True,
                type=["xlsx", "xls", "csv"],
                key="advanced_upload",
            )

            if uploaded:
                file_data_list = []
                for f in uploaded:
                    try:
                        file_info = load_file(f)
                        file_data_list.append(file_info)
                        st.write(f"- **{file_info['name']}**: {file_info['rows']}行")
                    except Exception as e:
                        st.error(f"ファイル読み込みエラー ({f.name}): {e}")

                if st.button("分析開始", type="primary", use_container_width=True):
                    api_key = get_api_key()
                    if not api_key:
                        st.error("APIキーが設定されていません。サイドバーから入力してください。")
                        return

                    try:
                        with st.spinner("AIがデータを分析しています..."):
                            dataframes = {fd["name"]: fd["df"] for fd in file_data_list}
                            orch = Orchestrator(api_key=api_key)
                            result = orch.run_advanced_mode_analyze(
                                user_goal=user_goal,
                                dataframes=dataframes,
                            )
                            st.session_state.orchestrator = orch
                            st.session_state.files = file_data_list
                            st.session_state.data_profile = result.get("data_profile")
                            st.session_state.proposals = result.get("proposals")
                            st.session_state.conversation.append(
                                {"role": "user", "content": user_goal}
                            )
                            st.session_state.conversation.append(
                                {"role": "assistant", "content": "データを分析しました。提案をご確認ください。"}
                            )
                            st.session_state.step = "advanced_proposals"
                            st.rerun()
                    except Exception as e:
                        st.error(f"分析中にエラーが発生しました: {e}")

    with right:
        st.subheader("結果エリア")
        st.caption("分析結果がここに表示されます")


def render_advanced_proposals():
    """Advanced mode - proposals display."""
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("会話履歴")
        for msg in st.session_state.get("conversation", []):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    with right:
        st.subheader("分析提案")

        # Data profile summary
        profile = st.session_state.get("data_profile")
        if profile:
            with st.expander("データプロファイル", expanded=True):
                if isinstance(profile, dict):
                    for key, val in profile.items():
                        st.write(f"**{key}**: {val}")
                else:
                    st.write(profile)

        # Additional data suggestions
        proposals_data = st.session_state.get("proposals") or {}
        suggestions = proposals_data.get("additional_data_suggestions", [])
        if suggestions:
            with st.expander("追加データの提案"):
                for s in suggestions:
                    st.write(f"- {s}")
                extra_upload = st.file_uploader(
                    "追加データをアップロード",
                    accept_multiple_files=True,
                    type=["xlsx", "xls", "csv"],
                    key="extra_upload",
                )

        # Proposals as checkboxes
        proposal_list = proposals_data.get("proposals", [])
        selected = []
        if proposal_list:
            st.markdown("#### 提案された分析")
            for j, prop in enumerate(proposal_list):
                title = prop if isinstance(prop, str) else prop.get("title", f"提案 {j + 1}")
                description = "" if isinstance(prop, str) else prop.get("description", "")
                checked = st.checkbox(title, value=True, key=f"prop_{j}")
                if description:
                    st.caption(description)
                if checked:
                    selected.append(prop)

        # Action buttons
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("選択した分析を実行", type="primary", use_container_width=True):
                _run_advanced_generate(selected)
        with btn_col2:
            if st.button("全部作成", use_container_width=True):
                _run_advanced_generate(proposal_list)


def _run_advanced_generate(selected_proposals):
    """Execute advanced mode generation with selected proposals."""
    orch = st.session_state.get("orchestrator")
    if orch is None:
        st.error("Orchestratorが初期化されていません。")
        return
    try:
        with st.spinner("選択された分析を実行しています..."):
            result = orch.run_advanced_mode_generate(proposals=selected_proposals)
            st.session_state.charts = result.get("charts", [])
            st.session_state.step = "advanced_result"
            st.rerun()
    except Exception as e:
        st.error(f"分析実行中にエラーが発生しました: {e}")


def render_advanced_result():
    """Advanced mode - results display."""
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("会話履歴")
        for msg in st.session_state.get("conversation", []):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    with right:
        st.subheader("分析結果")
        charts = st.session_state.get("charts", [])

        if not charts:
            st.warning("生成されたグラフがありません。")
        else:
            for i, chart in enumerate(charts):
                st.markdown(f"### {chart.get('title', f'グラフ {i + 1}')}")
                fig = chart.get("figure")
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True, key=f"adv_chart_{i}")

                # Insights
                insights = chart.get("insights", [])
                for insight in insights:
                    level = insight.get("level", "info")
                    text = insight.get("text", str(insight)) if isinstance(insight, dict) else str(insight)
                    if level == "warning":
                        st.warning(text)
                    else:
                        st.info(text)

                # Download buttons
                if fig is not None:
                    dl_col1, dl_col2 = st.columns(2)
                    with dl_col1:
                        html_str = pio.to_html(fig, full_html=True)
                        st.download_button(
                            label="HTMLでダウンロード",
                            data=html_str,
                            file_name=f"analysis_{i + 1}.html",
                            mime="text/html",
                            key=f"adv_dl_html_{i}",
                        )
                    with dl_col2:
                        try:
                            img_bytes = fig.to_image(format="png")
                            st.download_button(
                                label="PNGでダウンロード",
                                data=img_bytes,
                                file_name=f"analysis_{i + 1}.png",
                                mime="image/png",
                                key=f"adv_dl_png_{i}",
                            )
                        except Exception:
                            st.caption("PNG出力にはkaleidoパッケージが必要です")

                # Code display
                code = chart.get("code", "")
                if code:
                    with st.expander("生成されたコードを表示"):
                        st.code(code, language="python")

                st.divider()

        # Recommendations
        recommendations = []
        for chart in charts:
            recommendations.extend(chart.get("recommendations", []))
        if recommendations:
            st.markdown("### 推奨アクション")
            for rec in recommendations:
                st.write(f"- {rec}")

        if st.button("最初に戻る", use_container_width=True):
            reset_session()
            st.rerun()


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    _init_session_state()
    render_sidebar()

    step = st.session_state.get("step", "mode_select")

    if step == "mode_select":
        render_mode_select()
    elif step == "simple_upload":
        render_simple_upload()
    elif step == "simple_result":
        render_simple_result()
    elif step == "advanced_hearing":
        render_advanced_hearing()
    elif step == "advanced_proposals":
        render_advanced_proposals()
    elif step == "advanced_result":
        render_advanced_result()
    else:
        st.error(f"不明なステップ: {step}")
        reset_session()
        st.rerun()


if __name__ == "__main__":
    main()
