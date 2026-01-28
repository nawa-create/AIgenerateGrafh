"""データ分析エージェント（Agent 1）

アップロードされたファイルのDataFrameを解析し、
カラム情報・ファイル間リレーション・サマリーを含むデータプロファイルを返す。
"""

import pandas as pd
import numpy as np


class DataAnalyzerAgent:
    """データ分析エージェント。

    各ファイルのDataFrameを解析し、カラムの型判定、統計情報の算出、
    ファイル間の関係性検出を行う。
    """

    # 日付関連キーワード
    _DATE_KEYWORDS: list[str] = ["日付", "date", "年月", "年", "月日", "期日", "期間", "datetime"]

    def analyze(self, files: list[dict]) -> dict:
        """複数ファイルのデータを分析し、データプロファイルを返す。

        Args:
            files: ファイル情報のリスト。各要素は {"name": str, "data": pd.DataFrame}。

        Returns:
            データプロファイル辞書。files, relationships, summary を含む。
        """
        file_profiles: list[dict] = []
        for f in files:
            file_profiles.append(self._profile_file(f["name"], f["data"]))

        relationships = self._detect_relationships(files)
        summary = self._generate_summary(file_profiles, relationships)

        return {
            "files": file_profiles,
            "relationships": relationships,
            "summary": summary,
        }

    # ------------------------------------------------------------------
    # ファイルプロファイリング
    # ------------------------------------------------------------------

    def _profile_file(self, name: str, df: pd.DataFrame) -> dict:
        """単一ファイルのプロファイルを作成する。

        Args:
            name: ファイル名。
            df: 対象のDataFrame。

        Returns:
            ファイルプロファイル辞書。
        """
        columns: list[dict] = []
        for col in df.columns:
            columns.append(self._profile_column(col, df[col]))

        # Correlation matrix for numeric columns
        numeric_df = df.select_dtypes(include="number")
        correlations = {}
        if len(numeric_df.columns) >= 2:
            corr_matrix = numeric_df.corr()
            correlations = {
                str(col): {str(k): self._to_python(v) for k, v in row.items()}
                for col, row in corr_matrix.to_dict().items()
            }

        # Data quality metrics
        total_cells = len(df) * len(df.columns)
        missing_cells = int(df.isna().sum().sum())
        quality = {
            "missing_percentage": round(missing_cells / total_cells * 100, 2) if total_cells > 0 else 0.0,
            "duplicate_rows": int(df.duplicated().sum()),
        }

        return {
            "name": name,
            "rows": len(df),
            "columns": columns,
            "correlations": correlations,
            "quality": quality,
        }

    def _profile_column(self, name: str, series: pd.Series) -> dict:
        """単一カラムのプロファイルを作成する。

        Args:
            name: カラム名。
            series: 対象のSeries。

        Returns:
            カラムプロファイル辞書。
        """
        col_type = self._detect_type(name, series)
        missing = int(series.isna().sum())
        unique_count = int(series.nunique())

        # サンプル値（先頭3件、NaN除外してからフォールバック）
        non_null = series.dropna()
        sample_values = non_null.head(3).tolist() if len(non_null) > 0 else series.head(3).tolist()
        # numpy型をPython標準型に変換
        sample = [self._to_python(v) for v in sample_values]

        profile: dict = {
            "name": str(name),
            "type": col_type,
            "sample": sample,
            "missing": missing,
            "unique_count": unique_count,
        }

        if col_type == "numeric":
            numeric = pd.to_numeric(series, errors="coerce")
            profile["min"] = self._to_python(numeric.min())
            profile["max"] = self._to_python(numeric.max())
            profile["mean"] = self._to_python(numeric.mean())

        return profile

    # ------------------------------------------------------------------
    # 型判定
    # ------------------------------------------------------------------

    def _detect_type(self, name: str, series: pd.Series) -> str:
        """カラムの型を判定する。

        判定ロジック:
            1. dtype が datetime64 またはカラム名に日付キーワードを含む場合 -> "date"
            2. pd.to_datetime で80%以上パースできる場合 -> "date"
            3. dtype が数値型 (int/float) -> "numeric"
            4. ユニーク数 < 20 またはユニーク比率 < 0.05 -> "category"
            5. それ以外 -> "string"

        Args:
            name: カラム名。
            series: 対象のSeries。

        Returns:
            "date", "numeric", "string", "category" のいずれか。
        """
        # 1. datetime64型チェック
        if pd.api.types.is_datetime64_any_dtype(series):
            return "date"

        # カラム名に日付キーワードが含まれるかチェック
        name_lower = str(name).lower()
        if any(kw in name_lower for kw in self._DATE_KEYWORDS):
            return "date"

        # 2. 文字列からの日付パース試行
        if series.dtype == object or pd.api.types.is_string_dtype(series):
            non_null = series.dropna()
            if len(non_null) > 0:
                try:
                    parsed = pd.to_datetime(non_null, errors="coerce")
                    success_ratio = parsed.notna().sum() / len(non_null)
                    if success_ratio > 0.8:
                        return "date"
                except Exception:
                    pass

        # 3. 数値型チェック
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"

        # 4. カテゴリ判定
        non_null = series.dropna()
        if len(non_null) > 0:
            unique_count = non_null.nunique()
            unique_ratio = unique_count / len(non_null)
            if unique_count < 20 or unique_ratio < 0.05:
                return "category"

        # 5. デフォルト
        return "string"

    # ------------------------------------------------------------------
    # リレーション検出
    # ------------------------------------------------------------------

    def _detect_relationships(self, files: list[dict]) -> list[dict]:
        """ファイル間のリレーションを検出する。

        同名カラムを持つファイルペアを探し、カーディナリティに基づいて
        リレーション種別を判定する。

        Args:
            files: ファイル情報のリスト。

        Returns:
            リレーション情報の辞書リスト。
        """
        relationships: list[dict] = []

        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                f1, f2 = files[i], files[j]
                df1, df2 = f1["data"], f2["data"]
                common_cols = set(df1.columns) & set(df2.columns)

                for col in common_cols:
                    rel_type = self._determine_cardinality(df1[col], df2[col])
                    relationships.append({
                        "file1": f1["name"],
                        "column1": str(col),
                        "file2": f2["name"],
                        "column2": str(col),
                        "type": rel_type,
                    })

        return relationships

    def _determine_cardinality(self, s1: pd.Series, s2: pd.Series) -> str:
        """2つのSeriesのカーディナリティを判定する。

        Args:
            s1: ファイル1のカラム。
            s2: ファイル2のカラム。

        Returns:
            "one-to-one", "many-to-one", "many-to-many" のいずれか。
        """
        s1_unique = s1.nunique() == len(s1.dropna())
        s2_unique = s2.nunique() == len(s2.dropna())

        if s1_unique and s2_unique:
            return "one-to-one"
        elif s1_unique or s2_unique:
            return "many-to-one"
        else:
            return "many-to-many"

    # ------------------------------------------------------------------
    # サマリー生成
    # ------------------------------------------------------------------

    def _generate_summary(self, file_profiles: list[dict], relationships: list[dict]) -> str:
        """データの概要を日本語で生成する。

        Args:
            file_profiles: ファイルプロファイルのリスト。
            relationships: リレーション情報のリスト。

        Returns:
            日本語の概要文字列。
        """
        parts: list[str] = []

        # ファイル概要
        total_files = len(file_profiles)
        total_rows = sum(fp["rows"] for fp in file_profiles)
        total_cols = sum(len(fp["columns"]) for fp in file_profiles)
        parts.append(f"データセットは{total_files}個のファイルで構成され、合計{total_rows}行・{total_cols}列を含みます。")

        # 各ファイルの要約
        for fp in file_profiles:
            type_counts: dict[str, int] = {}
            for c in fp["columns"]:
                t = c["type"]
                type_counts[t] = type_counts.get(t, 0) + 1
            type_desc = "、".join(f"{t}型{cnt}列" for t, cnt in type_counts.items())
            parts.append(f"「{fp['name']}」は{fp['rows']}行で、{type_desc}を含みます。")

        # リレーション
        if relationships:
            parts.append(f"ファイル間には{len(relationships)}件の関連カラムが検出されました。")

        return "".join(parts)

    # ------------------------------------------------------------------
    # ユーティリティ
    # ------------------------------------------------------------------

    @staticmethod
    def _to_python(value):
        """numpy/pandas型をPython標準型に変換する。

        Args:
            value: 変換対象の値。

        Returns:
            Python標準型の値。
        """
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return float(value)
        if isinstance(value, np.bool_):
            return bool(value)
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        if pd.isna(value):
            return None
        return value
