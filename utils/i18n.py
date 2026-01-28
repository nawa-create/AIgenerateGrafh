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

        # File upload
        "upload_title": "Excelファイルをアップロード",
        "upload_hint": "ドラッグ&ドロップ または クリックして選択（複数ファイル可）",
        "uploaded_files": "アップロード済み",
        "rows": "行",
        "file_too_large": "ファイルサイズが上限({max_mb}MB)を超えています: {name}",
        "too_many_files": "ファイル数が上限({max})を超えています",

        # Simple mode
        "generate_button": "グラフを自動生成",
        "generating": "AIがグラフを生成中...",
        "generated_charts": "生成されたグラフ",
        "regenerate": "別のグラフを提案",
        "regenerating": "別のグラフを生成中...",
        "back_to_start": "最初に戻る",
        "change_mode": "モード変更",
        "generated_code": "生成されたコード",
        "copy": "コピー",

        # Downloads
        "download_html": "HTML保存",
        "download_png": "PNG保存",
        "download_pdf": "PDFレポート",
        "download_pptx": "PPTX保存",
        "download_csv": "データCSV",

        # Advanced mode
        "hearing_greeting": "こんにちは！どんな課題を解決したいですか？\n\n例えば：\n- 売上の傾向を把握したい\n- 製造と出荷のバランスを見たい\n- コスト削減のヒントがほしい",
        "input_placeholder": "メッセージを入力...",
        "start_analysis": "分析を開始",
        "analyzing": "データを分析中...",
        "data_profile_title": "データプロファイル",
        "additional_data": "追加データの提案",
        "add_data": "追加",
        "proposals_title": "分析提案",
        "run_selected": "選択した分析を実行",
        "run_all": "全て作成",
        "generating_charts": "グラフを生成中...",

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
        "saved_templates": "保存済みテンプレート",
        "no_templates": "保存済みテンプレートはありません",

        # Sidebar
        "api_key_label": "Anthropic APIキー",
        "current_mode": "現在のモード",
        "reset": "リセット",
        "language": "言語",

        # Errors
        "error_no_api_key": "APIキーを設定してください",
        "error_no_files": "ファイルをアップロードしてください",
        "error_generation_failed": "グラフ生成に失敗しました: {error}",
        "error_analysis_failed": "分析に失敗しました: {error}",

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

        # File upload
        "upload_title": "Upload Excel Files",
        "upload_hint": "Drag & drop or click to select (multiple files allowed)",
        "uploaded_files": "Uploaded files",
        "rows": "rows",
        "file_too_large": "File size exceeds limit ({max_mb}MB): {name}",
        "too_many_files": "Number of files exceeds limit ({max})",

        # Simple mode
        "generate_button": "Auto-generate Charts",
        "generating": "AI is generating charts...",
        "generated_charts": "Generated Charts",
        "regenerate": "Suggest Different Charts",
        "regenerating": "Generating alternative charts...",
        "back_to_start": "Back to Start",
        "change_mode": "Change Mode",
        "generated_code": "Generated Code",
        "copy": "Copy",

        # Downloads
        "download_html": "Save HTML",
        "download_png": "Save PNG",
        "download_pdf": "PDF Report",
        "download_pptx": "Save PPTX",
        "download_csv": "Data CSV",

        # Advanced mode
        "hearing_greeting": "Hello! What challenge would you like to solve?\n\nFor example:\n- Understand sales trends\n- Analyze production vs. shipment balance\n- Find cost reduction opportunities",
        "input_placeholder": "Type your message...",
        "start_analysis": "Start Analysis",
        "analyzing": "Analyzing data...",
        "data_profile_title": "Data Profile",
        "additional_data": "Suggested Additional Data",
        "add_data": "Add",
        "proposals_title": "Analysis Proposals",
        "run_selected": "Run Selected Analysis",
        "run_all": "Run All",
        "generating_charts": "Generating charts...",

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
        "saved_templates": "Saved Templates",
        "no_templates": "No saved templates",

        # Sidebar
        "api_key_label": "Anthropic API Key",
        "current_mode": "Current Mode",
        "reset": "Reset",
        "language": "Language",

        # Errors
        "error_no_api_key": "Please set your API key",
        "error_no_files": "Please upload files",
        "error_generation_failed": "Chart generation failed: {error}",
        "error_analysis_failed": "Analysis failed: {error}",

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
