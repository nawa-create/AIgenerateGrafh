"""多言語対応モジュール"""

# All UI text strings organized by language
TRANSLATIONS = {
    "ja": {
        # Top page
        "app_title": "AI Graph Generator",
        "app_subtitle": "ExcelをアップロードするだけでAIがグラフを自動生成",
        "mode_simple": "簡単作成",
        "mode_simple_desc": "とりあえずグラフを作りたい",
        "mode_simple_time": "所要時間: 1〜2分",
        "mode_advanced": "本気分析",
        "mode_advanced_desc": "課題を深掘りして最適な分析を行う",
        "mode_advanced_time": "所要時間: 5〜10分",
        "select": "選択",
        "simple_mode_name": "簡単作成",
        "simple_mode_desc": "とりあえずグラフを作りたい",
        "simple_mode_time": "所要時間: 1〜2分",
        "simple_mode_detail": "Excelをアップロードするだけで、AIが最適なグラフを自動生成します。",
        "advanced_mode_name": "本気分析",
        "advanced_mode_desc": "課題を深掘りして最適な分析を行う",
        "advanced_mode_time": "所要時間: 5〜10分",
        "advanced_mode_detail": "AIとの対話で課題を明確にし、データに基づいた深い分析を行います。",
        "start_simple": "選択",
        "start_advanced": "選択",

        # File upload
        "upload_title": "Excelファイルをアップロード",
        "upload_hint": "ドラッグ&ドロップ または クリックして選択（複数ファイル可）",
        "uploaded_files": "アップロードされたファイル",
        "rows": "行",
        "file_too_large": "ファイルサイズが上限({max_mb}MB)を超えています: {name}",
        "too_many_files": "ファイル数が上限({max})を超えています",

        # Simple mode
        "generate_button": "グラフを自動生成",
        "generate": "グラフを自動生成",
        "generating": "AIがデータを分析してグラフを生成しています...",
        "generated_charts": "生成されたグラフ",
        "regenerate": "別のグラフを提案",
        "regenerating": "別のグラフを生成中...",
        "back_to_start": "最初に戻る",
        "change_mode": "モード変更",
        "generated_code": "生成されたコード",
        "copy": "コピー",
        "no_charts": "グラフが生成されませんでした",

        # Downloads
        "download_html": "HTML保存",
        "download_png": "PNG保存",
        "download_pdf": "PDFレポート",
        "download_pptx": "PPTX保存",
        "download_csv": "データCSV",

        # Advanced mode
        "hearing_greeting": "こんにちは！どんな課題を解決したいですか？\n\n例えば：\n- 売上の傾向を把握したい\n- 製造と出荷のバランスを見たい\n- コスト削減のヒントがほしい",
        "hearing": "ヒアリング",
        "input_placeholder": "メッセージを入力...",
        "data_upload": "データアップロード",
        "please_share_goal": "まずはAIとの会話で課題を教えてください",
        "upload_data_file": "データファイルをアップロード",
        "start_analysis": "分析を開始",
        "analyzing": "AIがデータを分析しています...",
        "analysis_complete": "データを分析しました。提案をご確認ください。",
        "upload_related_data": "課題に関連するデータファイルをアップロードしてください",
        "conversation_history": "会話履歴",
        "additional_question_placeholder": "追加の質問を入力...",
        "additional_message_placeholder": "追加のメッセージを入力...",
        "data_profile_title": "データプロファイル",
        "additional_data": "追加データの提案",
        "upload_additional_data": "追加データをアップロード",
        "add_data": "追加",
        "files_added": "ファイルを追加しました",
        "proposals_title": "分析提案",
        "proposed_analyses": "提案された分析",
        "run_selected": "選択した分析を実行",
        "run_all": "全て作成",
        "running_analysis": "選択された分析を実行しています...",
        "generating_charts": "グラフを生成中...",
        "select_at_least_one": "少なくとも1つの提案を選択してください",

        # Insights
        "insights_title": "AIの気づき",
        "recommendations_title": "推奨アクション",

        # Customization
        "customize_title": "グラフカスタマイズ",
        "chart_title_label": "タイトル",
        "color_scheme": "配色テーマ",
        "apply_changes": "変更を適用",

        # Templates
        "save_template": "テンプレートとして保存",
        "load_template": "テンプレートから作成",
        "template_name": "テンプレート名",
        "template_saved": "テンプレート '{name}' を保存しました",
        "saved_templates": "保存済みテンプレート",
        "no_templates": "保存済みテンプレートはありません",

        # Sidebar
        "settings": "設定",
        "api_key_label": "Anthropic APIキー",
        "api_key_help": "Anthropic APIキーを入力してください。console.anthropic.com で取得できます。",
        "api_key_override_help": "自分のキーを入力すると、システムキーの代わりに使用されます",
        "system_api_key_active": "システムAPIキーが設定済みです",
        "use_own_key": "自分のAPIキーを使う",
        "current_mode": "現在のモード",
        "mode_label": "モード: {mode}",
        "mode_not_selected": "モード未選択",
        "step_label": "ステップ: {step}",
        "reset": "リセット",
        "language": "言語",

        # Step labels
        "step_mode_select": "モード選択",
        "step_simple_upload": "ファイルアップロード",
        "step_simple_result": "結果表示",
        "step_advanced_hearing": "ヒアリング",
        "step_advanced_proposals": "提案確認",
        "step_advanced_result": "分析結果",

        # Errors
        "error_no_api_key": "APIキーが設定されていません。サイドバーから入力してください。",
        "error_no_files": "ファイルをアップロードしてください",
        "error_generation_failed": "グラフ生成中にエラーが発生しました: {error}",
        "error_analysis_failed": "分析中にエラーが発生しました: {error}",
        "error_chat": "エラーが発生しました: {error}",
        "error_regeneration": "再生成中にエラーが発生しました: {error}",
        "error_file_add": "ファイル追加エラー: {error}",
        "error_pdf": "PDF生成に失敗: {error}",
        "error_pptx": "PPTX生成に失敗: {error}",
        "error_orchestrator": "Orchestratorが初期化されていません。",
        "error_analysis_exec": "分析実行中にエラーが発生しました: {error}",
        "error_unknown_step": "不明なステップ: {step}",
        "png_requires_kaleido": "PNG出力にはkaleidoパッケージが必要です",
        "download_html_button": "HTMLでダウンロード",
        "download_png_button": "PNGでダウンロード",
        "upload_file_help": "Excel (.xlsx, .xls) または CSV (.csv) ファイルを選択してください",
        "chart_default_title": "グラフ {index}",
        "proposal_default_title": "提案 {index}",

        # Report
        "report_title": "分析レポート",
        "report_generated_by": "AI Graph Generator により自動生成",
        "report_data_summary": "データ概要",
        "report_charts": "グラフ分析結果",
        "report_insights": "分析インサイト",
        "report_recommendations": "推奨アクション",
    },
    "en": {
        # Top page
        "app_title": "AI Graph Generator",
        "app_subtitle": "Upload Excel files and let AI automatically generate charts",
        "mode_simple": "Quick Create",
        "mode_simple_desc": "Generate charts quickly",
        "mode_simple_time": "Estimated time: 1-2 min",
        "mode_advanced": "Deep Analysis",
        "mode_advanced_desc": "Dive deep into your data with AI-guided analysis",
        "mode_advanced_time": "Estimated time: 5-10 min",
        "select": "Select",
        "simple_mode_name": "Quick Create",
        "simple_mode_desc": "Generate charts quickly",
        "simple_mode_time": "Estimated time: 1-2 min",
        "simple_mode_detail": "Just upload an Excel file and AI will automatically generate the best charts.",
        "advanced_mode_name": "Deep Analysis",
        "advanced_mode_desc": "Dive deep into your data with AI-guided analysis",
        "advanced_mode_time": "Estimated time: 5-10 min",
        "advanced_mode_detail": "Clarify your challenges through AI conversation and perform deep data-driven analysis.",
        "start_simple": "Select",
        "start_advanced": "Select",

        # File upload
        "upload_title": "Upload Excel Files",
        "upload_hint": "Drag & drop or click to select (multiple files allowed)",
        "uploaded_files": "Uploaded Files",
        "rows": "rows",
        "file_too_large": "File size exceeds limit ({max_mb}MB): {name}",
        "too_many_files": "Number of files exceeds limit ({max})",

        # Simple mode
        "generate_button": "Auto-generate Charts",
        "generate": "Auto-generate Charts",
        "generating": "AI is analyzing data and generating charts...",
        "generated_charts": "Generated Charts",
        "regenerate": "Suggest Different Charts",
        "regenerating": "Generating alternative charts...",
        "back_to_start": "Back to Start",
        "change_mode": "Change Mode",
        "generated_code": "Generated Code",
        "copy": "Copy",
        "no_charts": "No charts were generated",

        # Downloads
        "download_html": "Save HTML",
        "download_png": "Save PNG",
        "download_pdf": "PDF Report",
        "download_pptx": "Save PPTX",
        "download_csv": "Data CSV",

        # Advanced mode
        "hearing_greeting": "Hello! What challenge would you like to solve?\n\nFor example:\n- Understand sales trends\n- Analyze production vs. shipment balance\n- Find cost reduction opportunities",
        "hearing": "Hearing",
        "input_placeholder": "Type your message...",
        "data_upload": "Data Upload",
        "please_share_goal": "Please share your challenge through the chat first",
        "upload_data_file": "Upload data file",
        "start_analysis": "Start Analysis",
        "analyzing": "AI is analyzing data...",
        "analysis_complete": "Analysis complete. Please review the proposals.",
        "upload_related_data": "Please upload data files related to your challenge",
        "conversation_history": "Conversation History",
        "additional_question_placeholder": "Type additional question...",
        "additional_message_placeholder": "Type additional message...",
        "data_profile_title": "Data Profile",
        "additional_data": "Suggested Additional Data",
        "upload_additional_data": "Upload additional data",
        "add_data": "Add",
        "files_added": "Files added",
        "proposals_title": "Analysis Proposals",
        "proposed_analyses": "Proposed Analyses",
        "run_selected": "Run Selected Analysis",
        "run_all": "Run All",
        "running_analysis": "Running selected analyses...",
        "generating_charts": "Generating charts...",
        "select_at_least_one": "Please select at least one proposal",

        # Insights
        "insights_title": "AI Insights",
        "recommendations_title": "Recommended Actions",

        # Customization
        "customize_title": "Chart Customization",
        "chart_title_label": "Title",
        "color_scheme": "Color Scheme",
        "apply_changes": "Apply Changes",

        # Templates
        "save_template": "Save as Template",
        "load_template": "Create from Template",
        "template_name": "Template Name",
        "template_saved": "Template '{name}' saved",
        "saved_templates": "Saved Templates",
        "no_templates": "No saved templates",

        # Sidebar
        "settings": "Settings",
        "api_key_label": "Anthropic API Key",
        "api_key_help": "Enter your Anthropic API key. Get one at console.anthropic.com",
        "api_key_override_help": "Enter your own key to use instead of the system key",
        "system_api_key_active": "System API key is configured",
        "use_own_key": "Use your own API key",
        "current_mode": "Current Mode",
        "mode_label": "Mode: {mode}",
        "mode_not_selected": "Mode not selected",
        "step_label": "Step: {step}",
        "reset": "Reset",
        "language": "Language",

        # Step labels
        "step_mode_select": "Mode Selection",
        "step_simple_upload": "File Upload",
        "step_simple_result": "Results",
        "step_advanced_hearing": "Hearing",
        "step_advanced_proposals": "Proposal Review",
        "step_advanced_result": "Analysis Results",

        # Errors
        "error_no_api_key": "API key is not set. Please enter it in the sidebar.",
        "error_no_files": "Please upload files",
        "error_generation_failed": "Error occurred during chart generation: {error}",
        "error_analysis_failed": "Error occurred during analysis: {error}",
        "error_chat": "An error occurred: {error}",
        "error_regeneration": "Error occurred during regeneration: {error}",
        "error_file_add": "File add error: {error}",
        "error_pdf": "PDF generation failed: {error}",
        "error_pptx": "PPTX generation failed: {error}",
        "error_orchestrator": "Orchestrator is not initialized.",
        "error_analysis_exec": "Error occurred during analysis execution: {error}",
        "error_unknown_step": "Unknown step: {step}",
        "png_requires_kaleido": "kaleido package is required for PNG output",
        "download_html_button": "Download HTML",
        "download_png_button": "Download PNG",
        "upload_file_help": "Select Excel (.xlsx, .xls) or CSV (.csv) files",
        "chart_default_title": "Chart {index}",
        "proposal_default_title": "Proposal {index}",

        # Report
        "report_title": "Analysis Report",
        "report_generated_by": "Auto-generated by AI Graph Generator",
        "report_data_summary": "Data Summary",
        "report_charts": "Chart Analysis Results",
        "report_insights": "Analysis Insights",
        "report_recommendations": "Recommended Actions",
    }
}

def get_text(key: str, lang: str = "ja", **kwargs) -> str:
    """翻訳テキストを取得する"""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["ja"]).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text

def get_available_languages() -> dict:
    """利用可能な言語を返す"""
    return {"ja": "日本語", "en": "English"}
