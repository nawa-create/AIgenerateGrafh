# =============================================================================
# AI Graph Generator - Main Streamlit Application
# =============================================================================

import os
import streamlit as st
import pandas as pd
import plotly.io as pio
from datetime import datetime
from dotenv import load_dotenv

from orchestrator import Orchestrator
from utils.i18n import get_text, get_available_languages
from utils.template_manager import save_template, load_template, list_templates, delete_template
from utils.report_generator import generate_pdf_report, generate_pptx_report
from config.settings import (
    APP_TITLE,
    SIMPLE_MODE,
    ADVANCED_MODE,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_MB,
    MAX_FILES,
)

load_dotenv()

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(page_title="AI Graph Generator", page_icon="\U0001f4ca", layout="wide")

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
INITIAL_AI_MESSAGE = (
    "こんにちは！どんな課題を解決したいですか？\n\n"
    "例えば：\n"
    "- 売上の傾向を把握したい\n"
    "- 製造と出荷のバランスを見たい\n"
    "- コスト削減のヒントがほしい"
)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _init_session_state():
    """Initialize session state variables if not already present."""
    defaults = {
        "mode": None,
        "step": "mode_select",
        "orchestrator": None,
        "files": {},           # dict[str, DataFrame]
        "charts": [],
        "selected_proposals": [],
        "conversation": [],
        "user_goal": "",
        "analysis_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if "language" not in st.session_state:
        st.session_state.language = "ja"
    if "templates" not in st.session_state:
        st.session_state.templates = []


def load_files(uploaded_files) -> dict[str, pd.DataFrame]:
    """Read uploaded files into a dict of name -> DataFrame.

    Validates file size and count limits. Raises ValueError on violation.
    """
    if len(uploaded_files) > MAX_FILES:
        raise ValueError(f"ファイル数が上限を超えています（最大{MAX_FILES}ファイル）")

    result: dict[str, pd.DataFrame] = {}
    for f in uploaded_files:
        # Size check
        size_mb = f.size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(
                f"{f.name} のサイズが上限を超えています "
                f"({size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB)"
            )

        ext = os.path.splitext(f.name)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(f)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(f)
        else:
            raise ValueError(f"未対応のファイル形式: {ext}")

        result[f.name] = df

    return result


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

    # 3. Sidebar input
    return st.session_state.get("sidebar_api_key", "")


def t(key, **kwargs):
    """Shortcut for i18n text lookup."""
    return get_text(key, st.session_state.get("language", "ja"), **kwargs)


def reset_session():
    """Clear all session state and return to mode selection."""
    keys_to_clear = list(st.session_state.keys())
    for k in keys_to_clear:
        if k != "sidebar_api_key":
            del st.session_state[k]


def _ensure_orchestrator() -> Orchestrator | None:
    """Return existing orchestrator or create one if API key is available."""
    orch = st.session_state.get("orchestrator")
    if orch is not None:
        return orch

    api_key = get_api_key()
    if not api_key:
        st.error("APIキーが設定されていません。サイドバーから入力してください。")
        return None

    orch = Orchestrator(api_key=api_key)
    st.session_state.orchestrator = orch
    return orch


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        st.header("設定")

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
        step = st.session_state.get("step", "mode_select")
        if mode == SIMPLE_MODE:
            st.info("モード: 簡単作成")
        elif mode == ADVANCED_MODE:
            st.info("モード: 本気分析")
        else:
            st.info("モード未選択")

        step_labels = {
            "mode_select": "モード選択",
            "simple_upload": "ファイルアップロード",
            "simple_result": "結果表示",
            "advanced_hearing": "ヒアリング",
            "advanced_proposals": "提案確認",
            "advanced_result": "分析結果",
        }
        st.caption(f"ステップ: {step_labels.get(step, step)}")

        st.divider()

        # Language selector
        lang_options = get_available_languages()
        selected_lang = st.selectbox(
            get_text("language", st.session_state.language),
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=list(lang_options.keys()).index(st.session_state.language)
        )
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()

        st.divider()

        if st.button("リセット", use_container_width=True):
            reset_session()
            st.rerun()

        st.divider()
        st.subheader(t("saved_templates"))
        templates = list_templates()
        if templates:
            for tmpl in templates[:5]:
                col_t1, col_t2 = st.columns([3, 1])
                col_t1.write(tmpl["name"])
                if col_t2.button("🗑️", key=f"del_{tmpl['id']}"):
                    delete_template(tmpl["id"])
                    st.rerun()
        else:
            st.caption(t("no_templates"))


# -----------------------------------------------------------------------------
# Step: Mode Select
# -----------------------------------------------------------------------------

def render_mode_select():
    st.markdown(
        f"<h1 style='text-align:center;'>\U0001f4ca {t('app_title')}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center; color:gray;'>"
        f"{t('app_subtitle')}"
        f"</p>",
        unsafe_allow_html=True,
    )

    st.write("")
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.markdown(f"### \u26a1 {t('simple_mode_name')}")
        st.markdown(f"**{t('simple_mode_desc')}**")
        st.caption(t("simple_mode_time"))
        st.markdown(t("simple_mode_detail"))
        if st.button(t("start_simple"), use_container_width=True, type="primary"):
            st.session_state.mode = SIMPLE_MODE
            st.session_state.step = "simple_upload"
            st.rerun()

    with col_right:
        st.markdown(f"### \U0001f52c {t('advanced_mode_name')}")
        st.markdown(f"**{t('advanced_mode_desc')}**")
        st.caption(t("advanced_mode_time"))
        st.markdown(t("advanced_mode_detail"))
        if st.button(t("start_advanced"), use_container_width=True, type="primary"):
            st.session_state.mode = ADVANCED_MODE
            st.session_state.step = "advanced_hearing"
            st.rerun()


# -----------------------------------------------------------------------------
# Step: Simple Upload
# -----------------------------------------------------------------------------

def render_simple_upload():
    col_header, col_btn = st.columns([8, 2])
    with col_header:
        st.header(f"\u26a1 {t('simple_mode_name')}")
    with col_btn:
        if st.button(t("change_mode")):
            reset_session()
            st.rerun()

    uploaded = st.file_uploader(
        t("upload_title"),
        accept_multiple_files=True,
        type=["xlsx", "xls", "csv"],
        help="Excel (.xlsx, .xls) または CSV (.csv) ファイルを選択してください",
    )

    if not uploaded:
        return

    # Validate and show uploaded files
    try:
        files = load_files(uploaded)
    except ValueError as e:
        st.error(str(e))
        return

    st.subheader("アップロードされたファイル")
    for name, df in files.items():
        st.write(f"- **{name}**: {len(df)}行 x {len(df.columns)}列")

    st.write("")
    if st.button(t("generate"), type="primary", use_container_width=True):
        orch = _ensure_orchestrator()
        if orch is None:
            return

        try:
            with st.spinner("AIがデータを分析してグラフを生成しています..."):
                charts = orch.run_simple_mode(files)
                st.session_state.orchestrator = orch
                st.session_state.files = files
                st.session_state.charts = charts
                st.session_state.step = "simple_result"
                st.rerun()
        except Exception as e:
            st.error(f"グラフ生成中にエラーが発生しました: {e}")


# -----------------------------------------------------------------------------
# Step: Simple Result
# -----------------------------------------------------------------------------

def _render_chart(chart: dict, prefix: str, idx: int):
    """Render a single chart card with downloads, customization, and template save."""
    chart_title = chart.get("title", f"グラフ {idx + 1}")
    chart_idx = f"{prefix}_{idx}"
    st.subheader(chart_title)

    fig = chart.get("figure")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_chart_{idx}")

        # Download buttons
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            html_str = pio.to_html(fig, full_html=True)
            st.download_button(
                label="HTMLでダウンロード",
                data=html_str,
                file_name=f"{prefix}_{idx + 1}.html",
                mime="text/html",
                key=f"{prefix}_dl_html_{idx}",
            )
        with dl_col2:
            try:
                img_bytes = fig.to_image(format="png")
                st.download_button(
                    label="PNGでダウンロード",
                    data=img_bytes,
                    file_name=f"{prefix}_{idx + 1}.png",
                    mime="image/png",
                    key=f"{prefix}_dl_png_{idx}",
                )
            except Exception:
                st.caption("PNG出力にはkaleidoパッケージが必要です")

        # Chart customization
        with st.expander(t("customize_title")):
            new_title = st.text_input(
                t("chart_title_label"),
                value=chart_title,
                key=f"title_{chart_idx}"
            )
            color_schemes = {
                "plotly": "Plotly Default",
                "ggplot2": "ggplot2",
                "seaborn": "Seaborn",
                "plotly_white": "White",
                "plotly_dark": "Dark",
                "presentation": "Presentation",
            }
            selected_scheme = st.selectbox(
                t("color_scheme"),
                options=list(color_schemes.keys()),
                format_func=lambda x: color_schemes[x],
                key=f"scheme_{chart_idx}"
            )
            if st.button(t("apply_changes"), key=f"apply_{chart_idx}"):
                fig.update_layout(
                    title_text=new_title,
                    template=selected_scheme
                )
                st.rerun()

        # Template save
        with st.expander(t("save_template")):
            template_name = st.text_input(
                t("template_name"),
                key=f"tmpl_name_{chart_idx}"
            )
            if st.button(t("save_template"), key=f"save_tmpl_{chart_idx}"):
                if template_name:
                    config = {
                        "proposal": chart.get("proposal", {}),
                        "customization": {
                            "title": new_title,
                            "color_scheme": selected_scheme,
                        },
                        "code": chart.get("code", ""),
                    }
                    save_template(template_name, config)
                    st.success(f"テンプレート '{template_name}' を保存しました")

    # Proposal text
    proposal = chart.get("proposal", "")
    if proposal:
        st.caption(proposal)

    # Code display
    code = chart.get("code", "")
    if code:
        with st.expander(t("generated_code")):
            st.code(code, language="python")


def render_simple_result():
    col_header, col_btn = st.columns([8, 2])
    with col_header:
        st.header(f"\u26a1 {t('simple_mode_name')} - {t('generated_charts')}")
    with col_btn:
        if st.button(t("change_mode")):
            reset_session()
            st.rerun()

    charts = st.session_state.get("charts", [])

    if not charts:
        st.warning(t("no_charts"))
    else:
        for i, chart in enumerate(charts):
            _render_chart(chart, "simple", i)
            st.divider()

    # Report export
    _render_report_export()

    # Action buttons
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button(t("regenerate"), use_container_width=True):
            orch = st.session_state.get("orchestrator")
            if orch is not None:
                try:
                    with st.spinner("別のグラフを生成中..."):
                        charts = orch.regenerate()
                        st.session_state.charts = charts
                        st.rerun()
                except Exception as e:
                    st.error(f"再生成中にエラーが発生しました: {e}")
    with btn_col2:
        if st.button(t("back_to_start"), use_container_width=True):
            reset_session()
            st.rerun()


# -----------------------------------------------------------------------------
# Report Export Helper
# -----------------------------------------------------------------------------

def _render_report_export():
    """Render PDF and PPTX export buttons."""
    charts = st.session_state.get("charts", [])
    if not charts:
        return
    st.divider()
    col_pdf, col_pptx = st.columns(2)
    with col_pdf:
        try:
            pdf_bytes = generate_pdf_report(
                charts=charts,
                data_profile=getattr(st.session_state.get("orchestrator"), "_data_profile", None),
                title=t("report_title"),
                subtitle=t("report_generated_by"),
            )
            st.download_button(
                label=t("download_pdf"),
                data=pdf_bytes,
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.warning(f"PDF生成に失敗: {e}")
    with col_pptx:
        try:
            pptx_bytes = generate_pptx_report(
                charts=charts,
                data_profile=getattr(st.session_state.get("orchestrator"), "_data_profile", None),
                title=t("report_title"),
                subtitle=t("report_generated_by"),
            )
            st.download_button(
                label=t("download_pptx"),
                data=pptx_bytes,
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
        except Exception as e:
            st.warning(f"PPTX生成に失敗: {e}")


# -----------------------------------------------------------------------------
# Step: Advanced Hearing (Phase 2)
# -----------------------------------------------------------------------------

def _render_conversation():
    """Display the conversation history using chat messages."""
    conversation = st.session_state.get("conversation", [])
    for msg in conversation:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def render_advanced_hearing():
    col_header, col_btn = st.columns([8, 2])
    with col_header:
        st.header("\U0001f52c 本気分析モード")
    with col_btn:
        if st.button("モード変更"):
            reset_session()
            st.rerun()

    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader("ヒアリング")

        # Initialize conversation with first AI message
        conversation = st.session_state.get("conversation", [])
        if not conversation:
            conversation = [{"role": "assistant", "content": INITIAL_AI_MESSAGE}]
            st.session_state.conversation = conversation

        # Display conversation
        _render_conversation()

        # Chat input
        user_input = st.chat_input("メッセージを入力...")
        if user_input:
            # Add user message
            st.session_state.conversation.append({"role": "user", "content": user_input})
            st.session_state.user_goal = user_input

            # Get AI response
            orch = _ensure_orchestrator()
            if orch is not None:
                try:
                    ai_response = orch.handle_chat_message(user_input)
                    st.session_state.conversation.append(
                        {"role": "assistant", "content": ai_response}
                    )
                except Exception as e:
                    st.session_state.conversation.append(
                        {"role": "assistant", "content": f"エラーが発生しました: {e}"}
                    )
            st.rerun()

    with right:
        st.subheader("データアップロード")

        # Show file uploader after at least one user message
        has_user_message = any(
            m["role"] == "user" for m in st.session_state.get("conversation", [])
        )

        if not has_user_message:
            st.caption("まずはAIとの会話で課題を教えてください")
            return

        uploaded = st.file_uploader(
            "データファイルをアップロード",
            accept_multiple_files=True,
            type=["xlsx", "xls", "csv"],
            key="advanced_upload",
        )

        if uploaded:
            try:
                files = load_files(uploaded)
            except ValueError as e:
                st.error(str(e))
                return

            for name, df in files.items():
                st.write(f"- **{name}**: {len(df)}行 x {len(df.columns)}列")

            st.session_state.files = files

            if st.button("分析を開始", type="primary", use_container_width=True):
                orch = _ensure_orchestrator()
                if orch is None:
                    return

                user_goal = st.session_state.get("user_goal", "")
                try:
                    with st.spinner("AIがデータを分析しています..."):
                        result = orch.run_advanced_mode_analyze(files, user_goal)
                        st.session_state.analysis_result = result
                        st.session_state.conversation.append(
                            {"role": "assistant", "content": "データを分析しました。提案をご確認ください。"}
                        )
                        st.session_state.step = "advanced_proposals"
                        st.rerun()
                except Exception as e:
                    st.error(f"分析中にエラーが発生しました: {e}")
        else:
            st.caption("課題に関連するデータファイルをアップロードしてください")


# -----------------------------------------------------------------------------
# Step: Advanced Proposals
# -----------------------------------------------------------------------------

def render_advanced_proposals():
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader("会話履歴")
        _render_conversation()

        # Continue chat
        user_input = st.chat_input("追加のメッセージを入力...")
        if user_input:
            st.session_state.conversation.append({"role": "user", "content": user_input})
            orch = st.session_state.get("orchestrator")
            if orch is not None:
                try:
                    ai_response = orch.handle_chat_message(user_input)
                    st.session_state.conversation.append(
                        {"role": "assistant", "content": ai_response}
                    )
                except Exception as e:
                    st.session_state.conversation.append(
                        {"role": "assistant", "content": f"エラーが発生しました: {e}"}
                    )
            st.rerun()

    with right:
        st.subheader("分析提案")

        analysis = st.session_state.get("analysis_result", {}) or {}

        # Data profile summary
        profile = analysis.get("data_profile")
        if profile:
            with st.expander("データプロファイル", expanded=True):
                if isinstance(profile, dict):
                    for key, val in profile.items():
                        st.write(f"**{key}**: {val}")
                else:
                    st.write(profile)

        # Additional data suggestions
        suggestions = analysis.get("additional_data_suggestions", [])
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
                if extra_upload and st.button("追加", key="add_extra_files"):
                    orch = st.session_state.get("orchestrator")
                    if orch is not None:
                        try:
                            new_files = load_files(extra_upload)
                            orch.add_files(new_files)
                            st.session_state.files.update(new_files)
                            st.success("ファイルを追加しました")
                            st.rerun()
                        except Exception as e:
                            st.error(f"ファイル追加エラー: {e}")

        # Proposals as checkboxes
        proposals = analysis.get("proposals", [])
        selected = []
        if proposals:
            st.markdown("#### 提案された分析")
            for j, prop in enumerate(proposals):
                if isinstance(prop, str):
                    title = prop
                    description = ""
                else:
                    title = prop.get("title", f"提案 {j + 1}")
                    description = prop.get("description", "")

                checked = st.checkbox(title, value=True, key=f"prop_{j}")
                if description:
                    st.caption(description)
                if checked:
                    selected.append(prop)

        # Action buttons
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("選択した分析を実行", type="primary", use_container_width=True):
                if not selected:
                    st.warning("少なくとも1つの提案を選択してください")
                else:
                    _run_advanced_generate(selected)
        with btn_col2:
            if st.button("全て作成", use_container_width=True):
                _run_advanced_generate(proposals)


def _run_advanced_generate(selected_proposals: list[dict]):
    """Execute advanced mode generation with selected proposals."""
    orch = st.session_state.get("orchestrator")
    if orch is None:
        st.error("Orchestratorが初期化されていません。")
        return
    try:
        with st.spinner("選択された分析を実行しています..."):
            charts = orch.run_advanced_mode_generate(selected_proposals)
            st.session_state.charts = charts
            st.session_state.selected_proposals = selected_proposals
            st.session_state.step = "advanced_result"
            st.rerun()
    except Exception as e:
        st.error(f"分析実行中にエラーが発生しました: {e}")


# -----------------------------------------------------------------------------
# Step: Advanced Result
# -----------------------------------------------------------------------------

def render_advanced_result():
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader("会話履歴")
        _render_conversation()

        user_input = st.chat_input("追加の質問を入力...")
        if user_input:
            st.session_state.conversation.append({"role": "user", "content": user_input})
            orch = st.session_state.get("orchestrator")
            if orch is not None:
                try:
                    ai_response = orch.handle_chat_message(user_input)
                    st.session_state.conversation.append(
                        {"role": "assistant", "content": ai_response}
                    )
                except Exception as e:
                    st.session_state.conversation.append(
                        {"role": "assistant", "content": f"エラーが発生しました: {e}"}
                    )
            st.rerun()

    with right:
        st.subheader(t("generated_charts"))
        charts = st.session_state.get("charts", [])

        if not charts:
            st.warning(t("no_charts"))
        else:
            for i, chart in enumerate(charts):
                _render_chart(chart, "adv", i)

                # Insights
                insights_data = chart.get("insights", {})
                if isinstance(insights_data, dict):
                    insight_list = insights_data.get("insights", [])
                    recommendations = insights_data.get("recommendations", [])
                else:
                    insight_list = insights_data if isinstance(insights_data, list) else []
                    recommendations = []

                for insight in insight_list:
                    if isinstance(insight, dict):
                        level = insight.get("type", "info")
                        text = insight.get("text", str(insight))
                    else:
                        level = "info"
                        text = str(insight)

                    if level == "warning":
                        st.warning(text)
                    else:
                        st.info(text)

                # Recommendations per chart
                for rec in recommendations:
                    st.success(rec if isinstance(rec, str) else str(rec))

                st.divider()

        # Report export
        _render_report_export()

        # Bottom action buttons
        if st.button(t("back_to_start"), use_container_width=True):
            reset_session()
            st.rerun()


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    _init_session_state()
    render_sidebar()

    step = st.session_state.get("step", "mode_select")

    renderers = {
        "mode_select": render_mode_select,
        "simple_upload": render_simple_upload,
        "simple_result": render_simple_result,
        "advanced_hearing": render_advanced_hearing,
        "advanced_proposals": render_advanced_proposals,
        "advanced_result": render_advanced_result,
    }

    renderer = renderers.get(step)
    if renderer:
        renderer()
    else:
        st.error(f"不明なステップ: {step}")
        reset_session()
        st.rerun()


if __name__ == "__main__":
    main()
