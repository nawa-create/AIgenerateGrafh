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
from utils.template_manager import save_template, list_templates, delete_template
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


def load_files(uploaded_files) -> dict[str, pd.DataFrame]:
    """Read uploaded files into a dict of name -> DataFrame.

    Validates file size and count limits. Raises ValueError on violation.
    """
    if len(uploaded_files) > MAX_FILES:
        raise ValueError(t("too_many_files", max=MAX_FILES))

    result: dict[str, pd.DataFrame] = {}
    for f in uploaded_files:
        # Size check
        size_mb = f.size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(t("file_too_large", name=f.name, max_mb=MAX_FILE_SIZE_MB))

        ext = os.path.splitext(f.name)[1].lower()
        if ext == ".csv":
            for encoding in ("utf-8", "shift_jis", "cp932", "euc-jp", "iso-2022-jp", "latin-1"):
                try:
                    f.seek(0)
                    df = pd.read_csv(f, encoding=encoding)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            else:
                raise ValueError(f"CSV文字コードを自動判定できませんでした: {f.name}")
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(f)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        result[f.name] = df

    return result


def get_api_key() -> str:
    """Retrieve API key with priority: user override → secrets → env."""
    # 1. User override from sidebar (highest priority)
    user_key = st.session_state.get("sidebar_api_key", "")
    if user_key:
        return user_key

    # 2. Streamlit secrets
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            return key
    except Exception:
        pass

    # 3. Environment variable
    return os.environ.get("ANTHROPIC_API_KEY", "")


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
        st.error(t("error_no_api_key"))
        return None

    orch = Orchestrator(api_key=api_key)
    st.session_state.orchestrator = orch
    return orch


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        st.header(t("settings"))

        # API key section
        env_key = os.environ.get("ANTHROPIC_API_KEY", "")
        try:
            secret_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            secret_key = ""

        has_system_key = bool(env_key or secret_key)

        if has_system_key:
            st.success(t("system_api_key_active"))
            with st.expander(t("use_own_key")):
                st.text_input(
                    t("api_key_label"),
                    type="password",
                    key="sidebar_api_key",
                    help=t("api_key_override_help"),
                )
        else:
            st.text_input(
                t("api_key_label"),
                type="password",
                key="sidebar_api_key",
                help=t("api_key_help"),
            )

        st.divider()

        # Current mode display
        mode = st.session_state.get("mode")
        step = st.session_state.get("step", "mode_select")
        if mode == SIMPLE_MODE:
            st.info(t("mode_label", mode=t("mode_simple")))
        elif mode == ADVANCED_MODE:
            st.info(t("mode_label", mode=t("mode_advanced")))
        else:
            st.info(t("mode_not_selected"))

        step_labels = {
            "mode_select": t("step_mode_select"),
            "simple_upload": t("step_simple_upload"),
            "simple_result": t("step_simple_result"),
            "advanced_hearing": t("step_advanced_hearing"),
            "advanced_proposals": t("step_advanced_proposals"),
            "advanced_result": t("step_advanced_result"),
        }
        st.caption(t("step_label", step=step_labels.get(step, step)))

        st.divider()

        # Language selector
        lang_options = get_available_languages()
        selected_lang = st.selectbox(
            get_text("language", st.session_state.language),
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=list(lang_options.keys()).index(st.session_state.language),
            key="sidebar_language_select",
        )
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()

        st.divider()

        if st.button(t("reset"), use_container_width=True, key="btn_reset"):
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
        if st.button(t("start_simple"), use_container_width=True, type="primary", key="btn_start_simple"):
            st.session_state.mode = SIMPLE_MODE
            st.session_state.step = "simple_upload"
            st.rerun()

    with col_right:
        st.markdown(f"### \U0001f52c {t('advanced_mode_name')}")
        st.markdown(f"**{t('advanced_mode_desc')}**")
        st.caption(t("advanced_mode_time"))
        st.markdown(t("advanced_mode_detail"))
        if st.button(t("start_advanced"), use_container_width=True, type="primary", key="btn_start_advanced"):
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
        if st.button(t("change_mode"), key="btn_change_mode_simple_upload"):
            reset_session()
            st.rerun()

    uploaded = st.file_uploader(
        t("upload_title"),
        accept_multiple_files=True,
        type=["xlsx", "xls", "csv"],
        help=t("upload_file_help"),
        key="upload_simple",
    )

    if not uploaded:
        return

    # Validate and show uploaded files
    try:
        files = load_files(uploaded)
    except ValueError as e:
        st.error(str(e))
        return

    st.subheader(t("uploaded_files"))
    for name, df in files.items():
        st.write(f"- **{name}**: {len(df)}行 x {len(df.columns)}列")

    st.write("")
    if st.button(t("generate"), type="primary", use_container_width=True, key="btn_generate_simple"):
        orch = _ensure_orchestrator()
        if orch is None:
            return

        try:
            with st.spinner(t("generating")):
                result = orch.run_simple_mode(files)
                st.session_state.orchestrator = orch
                st.session_state.files = files
                st.session_state.charts = result["charts"]
                st.session_state.step = "simple_result"
                st.rerun()
        except Exception as e:
            st.error(t("error_generation_failed", error=str(e)))


# -----------------------------------------------------------------------------
# Step: Simple Result
# -----------------------------------------------------------------------------

def _render_chart(chart: dict, prefix: str, idx: int):
    """Render a single chart card with downloads, customization, and template save."""
    proposal = chart.get("proposal", {})
    chart_title = proposal.get("title", t("chart_default_title", index=idx + 1)) if isinstance(proposal, dict) else t("chart_default_title", index=idx + 1)
    chart_idx = f"{prefix}_{idx}"
    st.subheader(chart_title)

    fig = chart.get("figure")
    error = chart.get("error")

    if fig is not None:
        st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_chart_{idx}")
    elif error:
        st.error(f"グラフ生成エラー: {error}")
    else:
        st.warning("グラフが生成されませんでした。コードを確認してください。")

        # Download buttons
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            html_str = pio.to_html(fig, full_html=True)
            st.download_button(
                label=t("download_html_button"),
                data=html_str,
                file_name=f"{prefix}_{idx + 1}.html",
                mime="text/html",
                key=f"{prefix}_dl_html_{idx}",
            )
        with dl_col2:
            try:
                img_bytes = fig.to_image(format="png")
                st.download_button(
                    label=t("download_png_button"),
                    data=img_bytes,
                    file_name=f"{prefix}_{idx + 1}.png",
                    mime="image/png",
                    key=f"{prefix}_dl_png_{idx}",
                )
            except Exception:
                st.caption(t("png_requires_kaleido"))

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
                    st.success(t("template_saved", name=template_name))

    # Proposal text
    proposal_info = chart.get("proposal", "")
    if isinstance(proposal_info, dict):
        desc = proposal_info.get("description", "")
        if desc:
            st.caption(desc)
    elif proposal_info:
        st.caption(str(proposal_info))

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
        if st.button(t("change_mode"), key="btn_change_mode_simple_result"):
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
    _render_report_export(prefix="simple")

    # Action buttons
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button(t("regenerate"), use_container_width=True, key="btn_regenerate_simple"):
            orch = st.session_state.get("orchestrator")
            if orch is not None:
                try:
                    with st.spinner(t("regenerating")):
                        result = orch.regenerate()
                        st.session_state.charts = result["charts"]
                        st.rerun()
                except Exception as e:
                    st.error(t("error_regeneration", error=str(e)))
    with btn_col2:
        if st.button(t("back_to_start"), use_container_width=True, key="btn_back_simple_result"):
            reset_session()
            st.rerun()


# -----------------------------------------------------------------------------
# Report Export Helper
# -----------------------------------------------------------------------------

def _render_report_export(prefix: str = "report"):
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
                key=f"dl_pdf_{prefix}",
            )
        except Exception as e:
            st.warning(t("error_pdf", error=str(e)))
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
                key=f"dl_pptx_{prefix}",
            )
        except Exception as e:
            st.warning(t("error_pptx", error=str(e)))


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
        st.header(f"\U0001f52c {t('mode_advanced')}")
    with col_btn:
        if st.button(t("change_mode"), key="btn_change_mode_adv_hearing"):
            reset_session()
            st.rerun()

    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader(t("hearing"))

        # Initialize conversation with first AI message
        conversation = st.session_state.get("conversation", [])
        if not conversation:
            conversation = [{"role": "assistant", "content": t("hearing_greeting")}]
            st.session_state.conversation = conversation

        # Display conversation
        _render_conversation()

        # Chat input
        user_input = st.chat_input(t("input_placeholder"), key="chat_input_hearing")
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
                        {"role": "assistant", "content": t("error_chat", error=str(e))}
                    )
            st.rerun()

    with right:
        st.subheader(t("data_upload"))

        # Show file uploader after at least one user message
        has_user_message = any(
            m["role"] == "user" for m in st.session_state.get("conversation", [])
        )

        if not has_user_message:
            st.caption(t("please_share_goal"))
            return

        uploaded = st.file_uploader(
            t("upload_data_file"),
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

            if st.button(t("start_analysis"), type="primary", use_container_width=True, key="btn_start_analysis"):
                orch = _ensure_orchestrator()
                if orch is None:
                    return

                user_goal = st.session_state.get("user_goal", "")
                try:
                    with st.spinner(t("analyzing")):
                        result = orch.run_advanced_mode_analyze(files, user_goal)
                        st.session_state.analysis_result = result
                        st.session_state.conversation.append(
                            {"role": "assistant", "content": t("analysis_complete")}
                        )
                        st.session_state.step = "advanced_proposals"
                        st.rerun()
                except Exception as e:
                    st.error(t("error_analysis_failed", error=str(e)))
        else:
            st.caption(t("upload_related_data"))


# -----------------------------------------------------------------------------
# Step: Advanced Proposals
# -----------------------------------------------------------------------------

def render_advanced_proposals():
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader(t("conversation_history"))
        _render_conversation()

        # Continue chat
        user_input = st.chat_input(t("additional_message_placeholder"), key="chat_input_proposals")
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
                        {"role": "assistant", "content": t("error_chat", error=str(e))}
                    )
            st.rerun()

    with right:
        st.subheader(t("proposals_title"))

        analysis = st.session_state.get("analysis_result", {}) or {}

        # Data profile summary
        profile = analysis.get("data_profile")
        if profile:
            with st.expander(t("data_profile_title"), expanded=True):
                if isinstance(profile, dict):
                    for key, val in profile.items():
                        st.write(f"**{key}**: {val}")
                else:
                    st.write(profile)

        # Additional data suggestions
        suggestions = analysis.get("additional_data_suggestions", [])
        if suggestions:
            with st.expander(t("additional_data")):
                for s in suggestions:
                    st.write(f"- {s}")
                extra_upload = st.file_uploader(
                    t("upload_additional_data"),
                    accept_multiple_files=True,
                    type=["xlsx", "xls", "csv"],
                    key="extra_upload",
                )
                if extra_upload and st.button(t("add_data"), key="add_extra_files"):
                    orch = st.session_state.get("orchestrator")
                    if orch is not None:
                        try:
                            new_files = load_files(extra_upload)
                            orch.add_files(new_files)
                            st.session_state.files.update(new_files)
                            st.success(t("files_added"))
                            st.rerun()
                        except Exception as e:
                            st.error(t("error_file_add", error=str(e)))

        # Proposals as checkboxes
        proposals = analysis.get("proposals", [])
        selected = []
        if proposals:
            st.markdown(f"#### {t('proposed_analyses')}")
            for j, prop in enumerate(proposals):
                if isinstance(prop, str):
                    title = prop
                    description = ""
                else:
                    title = prop.get("title", t("proposal_default_title", index=j + 1))
                    description = prop.get("description", "")

                checked = st.checkbox(title, value=True, key=f"prop_{j}")
                if description:
                    st.caption(description)
                if checked:
                    selected.append(prop)

        # Action buttons
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button(t("run_selected"), type="primary", use_container_width=True, key="btn_run_selected"):
                if not selected:
                    st.warning(t("select_at_least_one"))
                else:
                    _run_advanced_generate(selected)
        with btn_col2:
            if st.button(t("run_all"), use_container_width=True, key="btn_run_all"):
                _run_advanced_generate(proposals)


def _run_advanced_generate(selected_proposals: list[dict]):
    """Execute advanced mode generation with selected proposals."""
    orch = st.session_state.get("orchestrator")
    if orch is None:
        st.error(t("error_orchestrator"))
        return
    try:
        with st.spinner(t("running_analysis")):
            result = orch.run_advanced_mode_generate(selected_proposals)
            st.session_state.charts = result["charts"]
            st.session_state.selected_proposals = selected_proposals
            st.session_state.step = "advanced_result"
            st.rerun()
    except Exception as e:
        st.error(t("error_analysis_exec", error=str(e)))


# -----------------------------------------------------------------------------
# Step: Advanced Result
# -----------------------------------------------------------------------------

def render_advanced_result():
    # グラフをメインエリアにフル幅で表示（視認性最優先）
    st.subheader(t("generated_charts"))
    charts = st.session_state.get("charts", [])

    if not charts:
        st.warning(t("no_charts"))
    else:
        for i, chart in enumerate(charts):
            _render_chart(chart, "adv", i)

            # Insights
            insights_data = chart.get("insights") or chart.get("insight", {})
            if isinstance(insights_data, dict):
                insight_list = insights_data.get("insights", [])
                recommendations = insights_data.get("recommendations", [])
            else:
                insight_list = insights_data if isinstance(insights_data, list) else []
                recommendations = []

            if insight_list or recommendations:
                insight_col, rec_col = st.columns(2)
                with insight_col:
                    for insight in insight_list:
                        if isinstance(insight, dict):
                            severity = insight.get("severity", "info")
                            text = insight.get("message") or insight.get("text", str(insight))
                        else:
                            severity = "info"
                            text = str(insight)

                        if severity == "warning":
                            st.warning(text)
                        else:
                            st.info(text)

                with rec_col:
                    for rec in recommendations:
                        st.success(rec if isinstance(rec, str) else str(rec))

            st.divider()

    # Report export
    _render_report_export(prefix="advanced")

    # 会話履歴を折りたたみで下部に配置
    with st.expander(t("conversation_history"), expanded=False):
        _render_conversation()

        user_input = st.chat_input(t("additional_question_placeholder"), key="chat_input_adv_result")
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
                        {"role": "assistant", "content": t("error_chat", error=str(e))}
                    )
            st.rerun()

    # Bottom action buttons
    if st.button(t("back_to_start"), use_container_width=True, key="btn_back_adv_result"):
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
        st.error(t("error_unknown_step", step=step))
        reset_session()
        st.rerun()


if __name__ == "__main__":
    main()
