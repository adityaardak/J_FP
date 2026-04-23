from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import quote

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


st.set_page_config(
    page_title="BMW Sales Intelligence Studio",
    page_icon="BMW",
    layout="wide",
    initial_sidebar_state="expanded",
)


BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "EXCEL BMW sales data (2010-2024).xlsx"
ARTIFACT_DIR = BASE_DIR / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "bmw_price_catboost.cbm"

POWER_BI_BASE_URL = (
    "https://app.powerbi.com/reportEmbed?"
    "reportId=3c2edaec-6fda-4c9c-8f1a-bd50ec405e6f"
    "&autoAuth=true"
    "&ctid=1490b17d-5dc9-4cbf-aeba-a2e854f521b8"
)

DEFAULT_REPORT_PAGES: Dict[str, str] = {
    "Executive Overview": "ReportSection",
    "Product Performance": "ReportSection1",
    "Regional Market Analysis": "ReportSection2",
    "Customer Preference": "ReportSection3",
    "Technology & Performance": "ReportSection4",
}

COLOR_MAP = {
    "Europe": "#63B3FF",
    "Asia": "#5AE4A8",
    "South America": "#F97316",
    "North America": "#0EA5E9",
    "Africa": "#94A3B8",
    "Middle East": "#FF4D57",
}

TARGET_COLUMN = "Price_USD"
MODEL_FEATURE_COLUMNS = [
    "Manufacturing_Year",
    "Region",
    "Fuel_Type",
    "Transmission",
    "Engine_Size_L",
    "Vehicle_Type",
    "Claimed_Mileage_KM_L",
    "Development_Nation",
    "Color",
]
CATEGORICAL_FEATURE_COLUMNS = [
    "Region",
    "Fuel_Type",
    "Transmission",
    "Vehicle_Type",
    "Development_Nation",
    "Color",
]
NUMERIC_FEATURE_COLUMNS = [
    "Manufacturing_Year",
    "Engine_Size_L",
    "Claimed_Mileage_KM_L",
]


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Orbitron:wght@500;700;800&display=swap');

            :root {
                --bg-0: #040609;
                --bg-1: #09111b;
                --bg-2: #0d1724;
                --panel: rgba(10, 16, 27, 0.82);
                --panel-strong: rgba(8, 13, 21, 0.92);
                --text-primary: #edf3fa;
                --text-secondary: #a7b7ca;
                --text-faint: #7e90a6;
                --line: rgba(126, 154, 194, 0.18);
                --line-bright: rgba(93, 188, 255, 0.34);
                --silver: #dbe4ef;
                --blue: #34a6ff;
                --red: #ff4d57;
                --green: #4ade80;
                --shadow: 0 22px 48px rgba(0, 0, 0, 0.42);
            }

            .stApp {
                background:
                    radial-gradient(circle at 12% 10%, rgba(52, 166, 255, 0.12), transparent 22%),
                    radial-gradient(circle at 88% 18%, rgba(255, 77, 87, 0.10), transparent 18%),
                    radial-gradient(circle at 50% 100%, rgba(52, 166, 255, 0.06), transparent 30%),
                    linear-gradient(180deg, #081018 0%, #05080d 42%, #030406 100%);
                color: var(--text-primary);
                font-family: "Manrope", sans-serif;
            }

            [data-testid="stAppViewContainer"] > .main {
                background: transparent;
            }

            .block-container {
                max-width: 1480px;
                padding-top: 1rem;
                padding-bottom: 2rem;
            }

            [data-testid="stHeader"], footer {
                display: none;
            }

            section[data-testid="stSidebar"] {
                background:
                    linear-gradient(180deg, rgba(8, 11, 18, 0.98) 0%, rgba(7, 11, 19, 0.92) 100%);
                border-right: 1px solid rgba(103, 125, 163, 0.18);
            }

            section[data-testid="stSidebar"] > div {
                padding-top: 0.8rem;
            }

            section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
                background: transparent;
            }

            ::-webkit-scrollbar {
                width: 10px;
                height: 10px;
            }

            ::-webkit-scrollbar-track {
                background: rgba(8, 13, 22, 0.88);
            }

            ::-webkit-scrollbar-thumb {
                border-radius: 999px;
                background: linear-gradient(180deg, rgba(52, 166, 255, 0.82), rgba(110, 128, 150, 0.72));
            }

            .hero-shell {
                position: relative;
                overflow: hidden;
                display: grid;
                grid-template-columns: 1.35fr 0.75fr;
                gap: 1.5rem;
                padding: 2rem;
                margin-bottom: 1.2rem;
                border: 1px solid rgba(116, 152, 199, 0.18);
                border-radius: 30px;
                background:
                    linear-gradient(145deg, rgba(14, 22, 35, 0.95) 0%, rgba(9, 14, 24, 0.86) 55%, rgba(10, 16, 28, 0.92) 100%);
                box-shadow: var(--shadow);
            }

            .hero-shell::before {
                content: "";
                position: absolute;
                right: -80px;
                top: -50px;
                width: 360px;
                height: 360px;
                background: radial-gradient(circle, rgba(52, 166, 255, 0.22), transparent 62%);
                pointer-events: none;
            }

            .hero-shell::after {
                content: "";
                position: absolute;
                left: -100px;
                bottom: -120px;
                width: 320px;
                height: 260px;
                background: radial-gradient(circle, rgba(255, 77, 87, 0.10), transparent 62%);
                pointer-events: none;
            }

            .eyebrow {
                display: inline-flex;
                align-items: center;
                gap: 0.65rem;
                padding: 0.55rem 0.9rem;
                border: 1px solid rgba(124, 154, 192, 0.18);
                border-radius: 999px;
                background: rgba(13, 21, 34, 0.58);
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 0.18rem;
                font-size: 0.74rem;
            }

            .eyebrow .dot {
                width: 0.6rem;
                height: 0.6rem;
                border-radius: 50%;
                background: linear-gradient(135deg, var(--green), var(--blue));
                box-shadow: 0 0 12px rgba(74, 222, 128, 0.72);
            }

            .hero-title {
                margin: 1.05rem 0 0.45rem;
                font-family: "Orbitron", sans-serif;
                font-size: clamp(2.2rem, 4vw, 3.7rem);
                line-height: 1.02;
                letter-spacing: 0.03rem;
                color: #f5f8fc;
            }

            .hero-copy {
                margin: 0;
                max-width: 760px;
                color: var(--text-secondary);
                font-size: 1rem;
                line-height: 1.75;
            }

            .hero-status {
                display: flex;
                flex-wrap: wrap;
                gap: 0.9rem;
                margin-top: 1.5rem;
            }

            .status-pill, .accent-spec {
                padding: 0.95rem 1rem;
                border-radius: 20px;
                border: 1px solid rgba(125, 151, 187, 0.14);
                background: rgba(12, 18, 30, 0.62);
            }

            .status-pill {
                min-width: 180px;
            }

            .status-label, .accent-spec label, .metric-label, .mini-label, .prediction-label {
                display: block;
                color: var(--text-faint);
                text-transform: uppercase;
                letter-spacing: 0.12rem;
                font-size: 0.72rem;
            }

            .status-pill strong, .accent-spec strong {
                display: block;
                margin-top: 0.45rem;
                font-size: 1rem;
                color: var(--text-primary);
            }

            .hero-accent-card {
                position: relative;
                padding: 1.5rem;
                border-radius: 26px;
                border: 1px solid rgba(126, 154, 194, 0.16);
                background:
                    linear-gradient(180deg, rgba(13, 21, 35, 0.78) 0%, rgba(8, 13, 22, 0.72) 100%);
            }

            .hero-accent-card::before {
                content: "";
                position: absolute;
                inset: auto -30px -40px auto;
                width: 240px;
                height: 240px;
                background: radial-gradient(circle, rgba(52, 166, 255, 0.18), transparent 60%);
            }

            .accent-chip, .section-kicker {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                color: #81c6ff;
                text-transform: uppercase;
                letter-spacing: 0.16rem;
                font-size: 0.76rem;
            }

            .accent-chip {
                padding: 0.5rem 0.8rem;
                border-radius: 999px;
                border: 1px solid rgba(101, 175, 255, 0.24);
                background: rgba(14, 28, 46, 0.78);
            }

            .hero-accent-card .accent-spec {
                margin-top: 0.9rem;
            }

            .section-heading {
                margin: 0.4rem 0 1rem;
                font-family: "Orbitron", sans-serif;
                font-size: 1.08rem;
                letter-spacing: 0.1rem;
                text-transform: uppercase;
                color: #edf3fa;
            }

            .metric-card {
                position: relative;
                overflow: hidden;
                padding: 1rem 1.05rem;
                min-height: 122px;
                border-radius: 18px;
                border: 1px solid rgba(124, 152, 190, 0.14);
                background: linear-gradient(180deg, rgba(12, 19, 30, 0.84) 0%, rgba(8, 14, 22, 0.70) 100%);
                box-shadow: 0 16px 34px rgba(0, 0, 0, 0.32);
            }

            .metric-value {
                display: block;
                margin-top: 0.75rem;
                color: var(--silver);
                font-size: 1.6rem;
                font-weight: 800;
            }

            .metric-foot {
                display: block;
                margin-top: 0.45rem;
                color: var(--text-secondary);
                font-size: 0.82rem;
                line-height: 1.45;
            }

            [data-testid="stVerticalBlockBorderWrapper"] {
                border: 1px solid rgba(126, 154, 194, 0.18) !important;
                border-radius: 24px !important;
                background: linear-gradient(180deg, rgba(12, 19, 31, 0.90) 0%, rgba(8, 12, 19, 0.78) 100%) !important;
                box-shadow: var(--shadow) !important;
                backdrop-filter: blur(18px) !important;
            }

            [data-testid="stVerticalBlockBorderWrapper"] > div {
                background: transparent !important;
            }

            section[data-testid="stSidebar"] div[role="radiogroup"] {
                gap: 0.55rem;
            }

            section[data-testid="stSidebar"] div[role="radiogroup"] label {
                margin: 0 0 0.45rem;
                padding: 0.15rem;
                border-radius: 18px;
                border: 1px solid rgba(94, 125, 165, 0.12);
                background: rgba(13, 18, 28, 0.70);
                transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
            }

            section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
                transform: translateX(2px);
                border-color: rgba(96, 178, 255, 0.25);
            }

            section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
                display: none;
            }

            section[data-testid="stSidebar"] div[role="radiogroup"] label p {
                width: 100%;
                margin: 0;
                padding: 0.88rem 0.95rem;
                color: #d7e4f3;
                font-weight: 700;
                border-radius: 14px;
            }

            section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
                border-color: rgba(52, 166, 255, 0.58);
                background: linear-gradient(90deg, rgba(12, 27, 43, 0.95) 0%, rgba(12, 35, 59, 0.95) 100%);
                box-shadow: 0 16px 34px rgba(0, 0, 0, 0.30), inset 0 0 0 1px rgba(52, 166, 255, 0.14);
            }

            section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
                color: #f8fbff;
                text-shadow: 0 0 12px rgba(82, 177, 255, 0.55);
            }

            section[data-testid="stSidebar"] .stMultiSelect label,
            section[data-testid="stSidebar"] .stSelectbox label,
            section[data-testid="stSidebar"] .stSlider label,
            section[data-testid="stSidebar"] .stTextInput label,
            section[data-testid="stSidebar"] .stNumberInput label,
            section[data-testid="stSidebar"] .stRadio label {
                color: #a4b6ca !important;
                font-size: 0.82rem !important;
                text-transform: uppercase;
                letter-spacing: 0.08rem;
            }

            .stSelectbox [data-baseweb="select"] > div,
            .stMultiSelect [data-baseweb="select"] > div,
            .stTextInput input,
            .stNumberInput input {
                background: rgba(11, 16, 24, 0.92) !important;
                border-color: rgba(104, 130, 164, 0.22) !important;
                color: #eef4fb !important;
                border-radius: 16px !important;
            }

            .stSlider [data-baseweb="slider"] * {
                color: #eef4fb !important;
            }

            .stButton > button, .stFormSubmitButton > button {
                width: 100%;
                padding: 0.9rem 1rem;
                border-radius: 16px;
                border: 1px solid rgba(52, 166, 255, 0.35);
                background: linear-gradient(90deg, rgba(12, 27, 43, 0.95) 0%, rgba(12, 35, 59, 0.95) 100%);
                color: #f8fbff;
                font-weight: 700;
                transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
            }

            .stButton > button:hover, .stFormSubmitButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 14px 28px rgba(0, 0, 0, 0.28);
                border-color: rgba(88, 186, 255, 0.62);
            }

            .mini-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(156px, 1fr));
                gap: 0.75rem;
                margin-bottom: 0.8rem;
            }

            .mini-card, .prediction-card, .similar-card, .story-card {
                padding: 0.95rem 1rem;
                border-radius: 18px;
                border: 1px solid rgba(126, 154, 194, 0.14);
                background: rgba(12, 19, 30, 0.68);
            }

            .mini-value {
                display: block;
                margin-top: 0.45rem;
                font-weight: 700;
                font-size: 1rem;
                color: var(--text-primary);
            }

            .spec-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.7rem;
            }

            .spec-card {
                padding: 0.85rem 0.95rem;
                border-radius: 16px;
                background: rgba(12, 18, 30, 0.70);
                border: 1px solid rgba(107, 136, 177, 0.16);
            }

            .spec-label {
                color: #8aa0b9;
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.12rem;
            }

            .spec-value {
                margin-top: 0.35rem;
                color: #eff4fa;
                font-size: 0.98rem;
                font-weight: 700;
            }

            .predictor-subtitle {
                margin: -0.35rem 0 1rem;
                color: var(--text-secondary);
                line-height: 1.7;
            }

            .compact-alert {
                padding: 1rem 1.1rem;
                border-radius: 16px;
                border: 1px solid rgba(255, 77, 87, 0.22);
                background: rgba(38, 12, 18, 0.42);
                color: #f6d2d7;
                line-height: 1.6;
            }

            .prediction-card.primary {
                background: linear-gradient(145deg, rgba(12, 27, 43, 0.95) 0%, rgba(12, 35, 59, 0.92) 100%);
                border-color: rgba(52, 166, 255, 0.32);
            }

            .prediction-value {
                display: block;
                margin-top: 0.45rem;
                color: #f5f8fc;
                font-size: 1.9rem;
                font-weight: 800;
            }

            .prediction-foot {
                margin-top: 0.35rem;
                color: #aed4ff;
                font-size: 0.85rem;
            }

            .story-card {
                margin-top: 0.8rem;
            }

            .story-card ul {
                margin: 0.45rem 0 0;
                padding-left: 1.1rem;
                color: var(--text-secondary);
                line-height: 1.7;
            }

            .similar-title {
                margin: 0 0 0.85rem;
                font-family: "Orbitron", sans-serif;
                font-size: 0.96rem;
                letter-spacing: 0.06rem;
                color: #edf3fa;
            }

            .sidebar-title {
                margin: 0.2rem 0 0.7rem;
                font-family: "Orbitron", sans-serif;
                font-size: 1rem;
                letter-spacing: 0.08rem;
                text-transform: uppercase;
                color: #edf3fa;
            }

            .sidebar-copy {
                margin: 0 0 1rem;
                color: var(--text-secondary);
                font-size: 0.88rem;
                line-height: 1.6;
            }

            @media (max-width: 980px) {
                .hero-shell {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def clean_column_name(name: str) -> str:
    return (
        str(name)
        .strip()
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )


def clean_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(r"[^0-9.\-]", "", regex=True)
        .replace("", np.nan)
    )
    return pd.to_numeric(cleaned, errors="coerce")


@st.cache_data(show_spinner=False)
def load_bmw_data() -> pd.DataFrame:
    raw_df = pd.read_excel(DATA_FILE, engine="openpyxl")
    raw_df.columns = [clean_column_name(column) for column in raw_df.columns]

    numeric_columns = [
        "Manufacturing_Year",
        "Engine_Size_L",
        "Odometer_Reading_KM",
        "Price_USD",
        "Sales_Volume",
        "Revenue",
        "Claimed_Mileage_KM_L",
    ]
    for column in numeric_columns:
        raw_df[column] = clean_numeric(raw_df[column])

    categorical_columns = [
        "Model_Name",
        "Region",
        "Color",
        "Fuel_Type",
        "Transmission",
        "Sales_Classification",
        "Vehicle_Type",
        "Development_Nation",
    ]
    for column in categorical_columns:
        raw_df[column] = raw_df[column].fillna("Unknown").astype(str).str.strip()

    return raw_df


def preprocess_bmw_data(df: pd.DataFrame) -> pd.DataFrame:
    predictor_df = df[["Model_Name"] + MODEL_FEATURE_COLUMNS + [TARGET_COLUMN]].copy()
    predictor_df = predictor_df.dropna(subset=[TARGET_COLUMN])

    for column in NUMERIC_FEATURE_COLUMNS:
        predictor_df[column] = predictor_df[column].fillna(predictor_df[column].median())

    for column in CATEGORICAL_FEATURE_COLUMNS + ["Model_Name"]:
        predictor_df[column] = predictor_df[column].fillna("Unknown").astype(str)

    predictor_df["Manufacturing_Year"] = predictor_df["Manufacturing_Year"].round().astype(int)
    return predictor_df


def evaluate_model(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "R2": float(r2_score(y_true, y_pred)),
    }


@st.cache_resource(show_spinner=False)
def train_price_model(file_mtime: float) -> Dict[str, object]:
    df = load_bmw_data()
    predictor_df = preprocess_bmw_data(df)

    X = predictor_df[MODEL_FEATURE_COLUMNS].copy()
    y = predictor_df[TARGET_COLUMN].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    cat_features = [X.columns.get_loc(column) for column in CATEGORICAL_FEATURE_COLUMNS]
    model = CatBoostRegressor(
        iterations=320,
        depth=6,
        learning_rate=0.05,
        loss_function="RMSE",
        eval_metric="RMSE",
        random_seed=42,
        od_type="Iter",
        od_wait=40,
        thread_count=-1,
        verbose=False,
    )
    model.fit(
        X_train,
        y_train,
        cat_features=cat_features,
        eval_set=(X_test, y_test),
        use_best_model=True,
    )

    y_pred = model.predict(X_test)
    metrics = evaluate_model(y_test, y_pred)

    ARTIFACT_DIR.mkdir(exist_ok=True)
    model.save_model(str(MODEL_PATH))

    feature_importance = pd.DataFrame(
        {
            "feature": MODEL_FEATURE_COLUMNS,
            "importance": model.get_feature_importance(),
        }
    ).sort_values("importance", ascending=False)

    numeric_medians = predictor_df[NUMERIC_FEATURE_COLUMNS].median().to_dict()
    numeric_ranges = (
        predictor_df[NUMERIC_FEATURE_COLUMNS].max()
        - predictor_df[NUMERIC_FEATURE_COLUMNS].min()
    ).replace(0, 1.0).to_dict()

    price_quantiles = predictor_df[TARGET_COLUMN].quantile([0.25, 0.50, 0.75]).to_dict()

    return {
        "model": model,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "reference_df": predictor_df.copy(),
        "numeric_medians": numeric_medians,
        "numeric_ranges": numeric_ranges,
        "price_quantiles": price_quantiles,
        "model_path": str(MODEL_PATH),
    }


def apply_filters(df: pd.DataFrame, filters: Dict[str, Iterable[object]]) -> pd.DataFrame:
    filtered = df.copy()
    for column, selected_values in filters.items():
        values = list(selected_values)
        if values:
            filtered = filtered[filtered[column].isin(values)]
    return filtered


def build_powerbi_url(page_id: str | None) -> str:
    url = (
        f"{POWER_BI_BASE_URL}"
        "&navContentPaneEnabled=false"
        "&filterPaneEnabled=false"
    )
    if page_id:
        url += f"&pageName={quote(page_id)}"
    return url


def format_currency(value: float) -> str:
    if pd.isna(value):
        return "$0"
    absolute = abs(value)
    if absolute >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if absolute >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if absolute >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if absolute >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:,.0f}"


def format_number(value: float) -> str:
    if pd.isna(value):
        return "0"
    absolute = abs(value)
    if absolute >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if absolute >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:,.0f}"


def safe_mode(series: pd.Series, default: str = "Unknown") -> str:
    mode_values = series.dropna().mode()
    return mode_values.iat[0] if not mode_values.empty else default


def safe_normalize(value: float, maximum: float) -> float:
    if maximum <= 0:
        return 0.0
    return round((value / maximum) * 100, 1)


def render_section_header(kicker: str, title: str) -> None:
    st.markdown(
        f"""
        <div class="section-kicker">{kicker}</div>
        <div class="section-heading">{title}</div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(filtered_df: pd.DataFrame) -> None:
    years = filtered_df["Manufacturing_Year"].dropna()
    min_year = int(years.min()) if not years.empty else 0
    max_year = int(years.max()) if not years.empty else 0
    st.markdown(
        f"""
        <div class="hero-shell">
            <div>
                <div class="eyebrow"><span class="dot"></span>Luxury Automotive Intelligence Portal</div>
                <div class="hero-title">BMW Sales Intelligence Studio</div>
                <p class="hero-copy">
                    A premium command deck for BMW demand, pricing, product mix, and launch-value forecasting.
                    Power BI drives the strategic report layer while live Streamlit intelligence adds decision-grade analytics and an ML launch-price studio.
                </p>
                <div class="hero-status">
                    <div class="status-pill">
                        <span class="status-label">Embedded Report</span>
                        <strong>{st.session_state.get("active_report_page", "Executive Overview")}</strong>
                    </div>
                    <div class="status-pill">
                        <span class="status-label">Dataset Window</span>
                        <strong>{min_year} - {max_year}</strong>
                    </div>
                    <div class="status-pill">
                        <span class="status-label">Records In Focus</span>
                        <strong>{len(filtered_df):,}</strong>
                    </div>
                </div>
            </div>
            <div class="hero-accent-card">
                <span class="accent-chip">BMW Insight Grid</span>
                <div class="accent-spec">
                    <label>Performance Mode</label>
                    <strong>Live Analytics + CatBoost Forecasting</strong>
                </div>
                <div class="accent-spec">
                    <label>Visual Language</label>
                    <strong>Graphite / Silver / Electric Blue</strong>
                </div>
                <div class="accent-spec">
                    <label>Control Layer</label>
                    <strong>Custom Dashboard Navigation</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_strip(filtered_df: pd.DataFrame) -> None:
    if filtered_df.empty:
        total_revenue = total_sales = average_price = 0
        top_model = top_region = "N/A"
    else:
        total_revenue = filtered_df["Revenue"].fillna(0).sum()
        total_sales = filtered_df["Sales_Volume"].fillna(0).sum()
        average_price = filtered_df["Price_USD"].dropna().mean()
        top_model = (
            filtered_df.groupby("Model_Name")["Revenue"].sum().idxmax()
            if filtered_df["Revenue"].notna().any()
            else "N/A"
        )
        top_region = (
            filtered_df.groupby("Region")["Revenue"].sum().idxmax()
            if filtered_df["Revenue"].notna().any()
            else "N/A"
        )

    metrics = [
        ("Total Revenue", format_currency(total_revenue), "Aggregate revenue inside current filter scope"),
        ("Total Sales Volume", format_number(total_sales), "Total units represented in active selection"),
        ("Average Price", format_currency(average_price), "Mean transaction value across filtered rows"),
        ("Top Model", top_model, "Highest revenue-driving BMW model"),
        ("Top Region", top_region, "Strongest regional market by revenue"),
    ]

    columns = st.columns(len(metrics), gap="small")
    for column, (label, value, foot) in zip(columns, metrics):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <span class="metric-label">{label}</span>
                    <span class="metric-value">{value}</span>
                    <span class="metric-foot">{foot}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_dashboard_frame(selected_page: str, page_id: str, filtered_df: pd.DataFrame) -> None:
    active_models = filtered_df["Model_Name"].nunique()
    active_regions = filtered_df["Region"].nunique()
    embed_url = build_powerbi_url(page_id)

    embed_markup = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                font-family: "Manrope", sans-serif;
                background: transparent;
                color: #edf4fb;
            }}
            .stage {{
                border-radius: 28px;
                padding: 1.15rem 1.15rem 1rem;
                border: 1px solid rgba(114, 142, 180, 0.22);
                background: linear-gradient(180deg, rgba(10, 16, 28, 0.94) 0%, rgba(7, 11, 20, 0.92) 100%);
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.42);
                backdrop-filter: blur(18px);
            }}
            .meta {{
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
                gap: 0.75rem;
                margin-bottom: 0.95rem;
                align-items: center;
            }}
            .title {{
                display: flex;
                align-items: center;
                gap: 0.7rem;
                font-family: "Orbitron", sans-serif;
                font-size: 1.02rem;
                letter-spacing: 0.12rem;
                text-transform: uppercase;
            }}
            .title span {{
                display: inline-flex;
                width: 0.55rem;
                height: 0.55rem;
                border-radius: 50%;
                background: linear-gradient(135deg, #33a8ff 0%, #80d1ff 100%);
                box-shadow: 0 0 14px rgba(51, 168, 255, 0.75);
            }}
            .chips {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
            }}
            .chip {{
                padding: 0.48rem 0.76rem;
                border-radius: 999px;
                font-size: 0.74rem;
                color: #d9e8f7;
                background: rgba(18, 31, 48, 0.86);
                border: 1px solid rgba(93, 130, 177, 0.22);
                letter-spacing: 0.08rem;
                text-transform: uppercase;
            }}
            .frame {{
                border-radius: 22px;
                overflow: hidden;
                border: 1px solid rgba(103, 132, 169, 0.18);
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
            }}
            iframe {{
                display: block;
                width: 100%;
                height: 455px;
                border: 0;
                background: #0b0f15;
            }}
        </style>
    </head>
    <body>
        <div class="stage">
            <div class="meta">
                <div class="title"><span></span>BMW Command Stage | {selected_page}</div>
                <div class="chips">
                    <div class="chip">Models {active_models}</div>
                    <div class="chip">Regions {active_regions}</div>
                    <div class="chip">Streamlit Controlled Navigation</div>
                </div>
            </div>
            <div class="frame">
                <iframe src="{embed_url}" allowfullscreen="true" loading="lazy"></iframe>
            </div>
        </div>
    </body>
    </html>
    """
    components.html(embed_markup, height=535)


def create_model_spotlight_chart(filtered_df: pd.DataFrame, model_name: str) -> go.Figure:
    model_summary = (
        filtered_df.groupby("Model_Name")
        .agg(
            {
                "Price_USD": "mean",
                "Sales_Volume": "sum",
                "Revenue": "sum",
                "Claimed_Mileage_KM_L": "mean",
                "Engine_Size_L": "mean",
            }
        )
        .rename(
            columns={
                "Price_USD": "avg_price",
                "Sales_Volume": "total_sales",
                "Revenue": "total_revenue",
                "Claimed_Mileage_KM_L": "mileage",
                "Engine_Size_L": "engine",
            }
        )
        .fillna(0)
    )
    current = model_summary.loc[model_name]
    current_engine = float(current.get("engine", current.get("Engine_Size_L", 0.0)))
    max_engine = float(
        model_summary.get("engine", model_summary.get("Engine_Size_L", pd.Series([0.0]))).max()
    )
    axes = {
        "Sales Strength": safe_normalize(current["total_sales"], model_summary["total_sales"].max()),
        "Revenue Strength": safe_normalize(current["total_revenue"], model_summary["total_revenue"].max()),
        "Price Level": safe_normalize(current["avg_price"], model_summary["avg_price"].max()),
        "Mileage Efficiency": safe_normalize(current["mileage"], model_summary["mileage"].max()),
        "Engine Proxy": safe_normalize(current_engine, max_engine),
    }

    categories = list(axes.keys()) + [next(iter(axes))]
    values = list(axes.values()) + [next(iter(axes.values()))]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            mode="lines+markers",
            line=dict(color="#38bdf8", width=3),
            marker=dict(size=8, color="#ff4d57"),
            fillcolor="rgba(56, 189, 248, 0.22)",
            hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
            name=model_name,
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#d8e4f1", family="Manrope"),
        margin=dict(l=40, r=40, t=20, b=20),
        height=340,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color="#8ea4bd"),
                gridcolor="rgba(125, 145, 176, 0.22)",
                linecolor="rgba(125, 145, 176, 0.22)",
            ),
            angularaxis=dict(
                tickfont=dict(color="#e4eef7", size=12),
                gridcolor="rgba(125, 145, 176, 0.12)",
                linecolor="rgba(125, 145, 176, 0.12)",
            ),
        ),
        showlegend=False,
    )
    return fig


def create_regional_demand_chart(filtered_df: pd.DataFrame) -> go.Figure:
    regional = (
        filtered_df.groupby(["Manufacturing_Year", "Region"], as_index=False)
        .agg(
            avg_price=("Price_USD", "mean"),
            sales_volume=("Sales_Volume", "sum"),
            revenue=("Revenue", "sum"),
            development_nation=("Development_Nation", lambda x: safe_mode(x)),
        )
        .sort_values("Manufacturing_Year")
    )

    fig = px.scatter(
        regional,
        x="avg_price",
        y="sales_volume",
        size="revenue",
        color="Region",
        animation_frame="Manufacturing_Year",
        hover_name="Region",
        hover_data={
            "avg_price": ":,.0f",
            "sales_volume": ":,.0f",
            "revenue": ":,.0f",
            "development_nation": True,
            "Manufacturing_Year": False,
        },
        color_discrete_map=COLOR_MAP,
        size_max=54,
        labels={
            "avg_price": "Average Price (USD)",
            "sales_volume": "Sales Volume",
        },
    )
    fig.update_traces(
        marker=dict(opacity=0.84, line=dict(width=1.2, color="rgba(255,255,255,0.18)"))
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#d8e4f1", family="Manrope"),
        margin=dict(l=10, r=10, t=28, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(gridcolor="rgba(125, 145, 176, 0.16)", zeroline=False),
        yaxis=dict(gridcolor="rgba(125, 145, 176, 0.16)", zeroline=False),
    )
    return fig


def create_product_mix_heatmap(filtered_df: pd.DataFrame) -> go.Figure:
    heatmap_frame = (
        filtered_df.pivot_table(
            index="Vehicle_Type",
            columns="Fuel_Type",
            values="Sales_Volume",
            aggfunc="sum",
            fill_value=0,
        )
        .sort_index()
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_frame.values,
            x=heatmap_frame.columns,
            y=heatmap_frame.index,
            colorscale=[
                [0.0, "#0b1220"],
                [0.25, "#123763"],
                [0.5, "#1d75d8"],
                [0.75, "#4cc9f0"],
                [1.0, "#ff4d57"],
            ],
            colorbar=dict(title="Sales Volume"),
            hovertemplate="Vehicle Type: %{y}<br>Fuel Type: %{x}<br>Sales Volume: %{z:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#d8e4f1", family="Manrope"),
        margin=dict(l=20, r=20, t=25, b=20),
        xaxis=dict(side="top", tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11)),
    )
    return fig


def predict_new_variant_price(model_bundle: Dict[str, object], launch_profile: Dict[str, object]) -> Dict[str, float | str]:
    feature_frame = pd.DataFrame([launch_profile], columns=MODEL_FEATURE_COLUMNS)

    for column in NUMERIC_FEATURE_COLUMNS:
        feature_frame[column] = pd.to_numeric(feature_frame[column], errors="coerce").fillna(
            model_bundle["numeric_medians"][column]
        )

    for column in CATEGORICAL_FEATURE_COLUMNS:
        feature_frame[column] = feature_frame[column].fillna("Unknown").astype(str)

    feature_frame["Manufacturing_Year"] = feature_frame["Manufacturing_Year"].round().astype(int)

    predicted_price = float(model_bundle["model"].predict(feature_frame)[0])
    mae = float(model_bundle["metrics"]["MAE"])
    lower_bound = max(predicted_price - mae, 0)
    upper_bound = predicted_price + mae

    q25 = model_bundle["price_quantiles"].get(0.25, predicted_price)
    q50 = model_bundle["price_quantiles"].get(0.50, predicted_price)
    q75 = model_bundle["price_quantiles"].get(0.75, predicted_price)

    if predicted_price <= q25:
        price_band = "Entry Premium Band"
    elif predicted_price <= q50:
        price_band = "Core Premium Band"
    elif predicted_price <= q75:
        price_band = "Upper Premium Band"
    else:
        price_band = "Flagship Launch Band"

    return {
        "predicted_price": predicted_price,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "price_band": price_band,
    }


def find_similar_historical_cars(
    model_bundle: Dict[str, object], launch_profile: Dict[str, object], top_n: int = 3
) -> pd.DataFrame:
    reference_df = model_bundle["reference_df"].copy()

    numeric_score = pd.Series(0.0, index=reference_df.index)
    for column in NUMERIC_FEATURE_COLUMNS:
        scale = float(model_bundle["numeric_ranges"].get(column, 1.0)) or 1.0
        numeric_score += (reference_df[column] - float(launch_profile[column])).abs() / scale
    numeric_score = numeric_score / len(NUMERIC_FEATURE_COLUMNS)

    categorical_score = pd.Series(0.0, index=reference_df.index)
    for column in CATEGORICAL_FEATURE_COLUMNS:
        categorical_score += (reference_df[column] != str(launch_profile[column])).astype(float)
    categorical_score = categorical_score / len(CATEGORICAL_FEATURE_COLUMNS)

    reference_df["distance"] = 0.65 * numeric_score + 0.35 * categorical_score
    similar_cars = reference_df.sort_values("distance").head(top_n).copy()
    similar_cars["distance_rank"] = np.arange(1, len(similar_cars) + 1)
    return similar_cars


def build_price_explanation(
    launch_profile: Dict[str, object], model_bundle: Dict[str, object], prediction: Dict[str, float | str]
) -> List[str]:
    reference_df = model_bundle["reference_df"]
    overall_avg = reference_df[TARGET_COLUMN].mean()
    insights: List[tuple[float, str]] = []

    engine_median = reference_df["Engine_Size_L"].median()
    if float(launch_profile["Engine_Size_L"]) >= engine_median:
        insights.append(
            (
                abs(float(launch_profile["Engine_Size_L"]) - engine_median),
                "A larger engine sits above the historical BMW median and typically pushes launch pricing upward.",
            )
        )
    else:
        insights.append(
            (
                abs(float(launch_profile["Engine_Size_L"]) - engine_median),
                "A smaller engine profile tempers the launch estimate versus higher-displacement BMW variants.",
            )
        )

    mileage_median = reference_df["Claimed_Mileage_KM_L"].median()
    if float(launch_profile["Claimed_Mileage_KM_L"]) >= mileage_median:
        insights.append(
            (
                abs(float(launch_profile["Claimed_Mileage_KM_L"]) - mileage_median),
                "Mileage efficiency is above the historical median, which supports a polished premium-positioning narrative.",
            )
        )

    for feature_name, label in [
        ("Vehicle_Type", "vehicle type"),
        ("Transmission", "transmission"),
        ("Fuel_Type", "fuel choice"),
        ("Region", "region"),
        ("Development_Nation", "market maturity"),
        ("Color", "color"),
    ]:
        feature_average = (
            reference_df.groupby(feature_name)[TARGET_COLUMN].mean().to_dict()
        )
        chosen_value = str(launch_profile[feature_name])
        chosen_avg = float(feature_average.get(chosen_value, overall_avg))
        delta = chosen_avg - overall_avg
        if abs(delta) > overall_avg * 0.015:
            direction = "above" if delta > 0 else "below"
            verb = "supports" if delta > 0 else "softens"
            insights.append(
                (
                    abs(delta),
                    f"{chosen_value} {label} tends to price {direction} the overall BMW average, which {verb} this forecast.",
                )
            )

    insights.sort(key=lambda item: item[0], reverse=True)
    messages = [item[1] for item in insights[:4]]
    messages.append(
        f"The predicted launch lands in the {prediction['price_band'].lower()}, based on learned pricing patterns across historical BMW variants."
    )
    return messages[:5]


def render_model_spotlight(filtered_df: pd.DataFrame, spotlight_model: str) -> None:
    spotlight_df = filtered_df[filtered_df["Model_Name"] == spotlight_model]
    specs = {
        "Average Price": format_currency(spotlight_df["Price_USD"].mean()),
        "Sales Volume": format_number(spotlight_df["Sales_Volume"].fillna(0).sum()),
        "Total Revenue": format_currency(spotlight_df["Revenue"].fillna(0).sum()),
        "Mileage": f"{spotlight_df['Claimed_Mileage_KM_L'].mean():.1f} KM/L",
        "Engine Size": f"{spotlight_df['Engine_Size_L'].mean():.1f} L",
        "Fuel Type": safe_mode(spotlight_df["Fuel_Type"]),
        "Transmission": safe_mode(spotlight_df["Transmission"]),
        "Vehicle Type": safe_mode(spotlight_df["Vehicle_Type"]),
    }

    with st.container(border=True):
        render_section_header("Module 1", "Model Performance Spotlight")
        selected_model = st.selectbox(
            "Spotlight model",
            sorted(filtered_df["Model_Name"].unique()),
            index=sorted(filtered_df["Model_Name"].unique()).index(spotlight_model),
            key="spotlight_model_select",
        )

        if selected_model != spotlight_model:
            spotlight_df = filtered_df[filtered_df["Model_Name"] == selected_model]
            specs = {
                "Average Price": format_currency(spotlight_df["Price_USD"].mean()),
                "Sales Volume": format_number(spotlight_df["Sales_Volume"].fillna(0).sum()),
                "Total Revenue": format_currency(spotlight_df["Revenue"].fillna(0).sum()),
                "Mileage": f"{spotlight_df['Claimed_Mileage_KM_L'].mean():.1f} KM/L",
                "Engine Size": f"{spotlight_df['Engine_Size_L'].mean():.1f} L",
                "Fuel Type": safe_mode(spotlight_df["Fuel_Type"]),
                "Transmission": safe_mode(spotlight_df["Transmission"]),
                "Vehicle Type": safe_mode(spotlight_df["Vehicle_Type"]),
            }
            spotlight_model = selected_model

        left, right = st.columns([0.92, 1.08], gap="medium")
        with left:
            st.markdown(
                f"""
                <div class="mini-grid">
                    <div class="mini-card">
                        <span class="mini-label">Current Model</span>
                        <span class="mini-value">{spotlight_model}</span>
                    </div>
                    <div class="mini-card">
                        <span class="mini-label">DNA Signal</span>
                        <span class="mini-value">Performance Profile</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            spec_markup = "".join(
                f"""
                <div class="spec-card">
                    <div class="spec-label">{label}</div>
                    <div class="spec-value">{value}</div>
                </div>
                """
                for label, value in specs.items()
            )
            st.markdown(f'<div class="spec-grid">{spec_markup}</div>', unsafe_allow_html=True)

        with right:
            try:
                st.plotly_chart(
                    create_model_spotlight_chart(filtered_df, spotlight_model),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            except Exception:
                st.markdown(
                    """
                    <div class="compact-alert">
                        The model DNA chart could not be rendered for this selection.
                        The summary specifications are still available on the left.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_regional_demand(filtered_df: pd.DataFrame) -> None:
    region_by_sales = filtered_df.groupby("Region")["Sales_Volume"].sum().idxmax()
    region_by_revenue = filtered_df.groupby("Region")["Revenue"].sum().idxmax()
    region_by_price = filtered_df.groupby("Region")["Price_USD"].mean().idxmax()

    with st.container(border=True):
        render_section_header("Module 2", "Regional Demand Pulse")
        st.markdown(
            f"""
            <div class="mini-grid">
                <div class="mini-card">
                    <span class="mini-label">Top Sales Region</span>
                    <span class="mini-value">{region_by_sales}</span>
                </div>
                <div class="mini-card">
                    <span class="mini-label">Top Revenue Region</span>
                    <span class="mini-value">{region_by_revenue}</span>
                </div>
                <div class="mini-card">
                    <span class="mini-label">Highest Pricing Region</span>
                    <span class="mini-value">{region_by_price}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            create_regional_demand_chart(filtered_df),
            use_container_width=True,
            config={"displayModeBar": False},
        )


def render_product_mix(filtered_df: pd.DataFrame) -> None:
    best_vehicle = filtered_df.groupby("Vehicle_Type")["Sales_Volume"].sum().idxmax()
    best_fuel = filtered_df.groupby("Fuel_Type")["Sales_Volume"].sum().idxmax()
    best_transmission = filtered_df.groupby("Transmission")["Sales_Volume"].sum().idxmax()
    best_combo = (
        filtered_df.groupby(["Vehicle_Type", "Fuel_Type", "Transmission"], as_index=False)
        .agg(sales_volume=("Sales_Volume", "sum"), revenue=("Revenue", "sum"))
        .sort_values(["revenue", "sales_volume"], ascending=False)
        .iloc[0]
    )

    with st.container(border=True):
        render_section_header("Module 3", "Product Mix Intelligence")
        st.markdown(
            f"""
            <div class="mini-grid">
                <div class="mini-card">
                    <span class="mini-label">Strongest Mix</span>
                    <span class="mini-value">{best_combo['Vehicle_Type']} | {best_combo['Fuel_Type']} | {best_combo['Transmission']}</span>
                </div>
                <div class="mini-card">
                    <span class="mini-label">Best-Selling Vehicle</span>
                    <span class="mini-value">{best_vehicle}</span>
                </div>
                <div class="mini-card">
                    <span class="mini-label">Preferred Transmission</span>
                    <span class="mini-value">{best_transmission}</span>
                </div>
                <div class="mini-card">
                    <span class="mini-label">Strongest Fuel Type</span>
                    <span class="mini-value">{best_fuel}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            create_product_mix_heatmap(filtered_df),
            use_container_width=True,
            config={"displayModeBar": False},
        )


def render_similar_car_cards(similar_cars: pd.DataFrame) -> None:
    st.markdown('<div class="similar-title">3 Most Similar Historical BMW Variants</div>', unsafe_allow_html=True)
    cards = st.columns(len(similar_cars), gap="small")
    for column, (_, row) in zip(cards, similar_cars.iterrows()):
        with column:
            st.markdown(
                f"""
                <div class="similar-card">
                    <span class="mini-label">Historical Match {int(row['distance_rank'])}</span>
                    <span class="mini-value">{row['Model_Name']}</span>
                    <div style="margin-top:0.65rem; color:#a7b7ca; line-height:1.7;">
                        {int(row['Manufacturing_Year'])} | {row['Fuel_Type']}<br>
                        {row['Transmission']} | {row['Engine_Size_L']:.1f} L<br>
                        {row['Vehicle_Type']}<br>
                        Actual Price: <span style="color:#edf3fa; font-weight:700;">{format_currency(row['Price_USD'])}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def create_prediction_comparison_chart(
    prediction: Dict[str, float | str], similar_cars: pd.DataFrame
) -> go.Figure:
    labels = ["Predicted Launch"] + [
        f"{row.Model_Name} ({int(row.Manufacturing_Year)})" for row in similar_cars.itertuples()
    ]
    values = [prediction["predicted_price"]] + similar_cars["Price_USD"].tolist()
    colors = ["#34a6ff", "#dbe4ef", "#94a3b8", "#ff4d57"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker=dict(color=colors[: len(labels)], line=dict(color="rgba(255,255,255,0.18)", width=1)),
                text=[format_currency(value) for value in values],
                textposition="outside",
                hovertemplate="%{x}<br>Price: %{y:$,.0f}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#d8e4f1", family="Manrope"),
        margin=dict(l=10, r=10, t=20, b=50),
        yaxis=dict(title="Price (USD)", gridcolor="rgba(125, 145, 176, 0.14)", zeroline=False),
        xaxis=dict(tickangle=-12),
    )
    return fig


def render_prediction_panel(model_bundle: Dict[str, object], full_df: pd.DataFrame) -> None:
    reference_df = model_bundle["reference_df"]
    metrics = model_bundle["metrics"]

    defaults = {
        "year": int(reference_df["Manufacturing_Year"].max()),
        "region": safe_mode(reference_df["Region"]),
        "fuel": safe_mode(reference_df["Fuel_Type"]),
        "transmission": safe_mode(reference_df["Transmission"]),
        "engine": float(reference_df["Engine_Size_L"].median()),
        "vehicle": safe_mode(reference_df["Vehicle_Type"]),
        "mileage": float(reference_df["Claimed_Mileage_KM_L"].median()),
        "development": safe_mode(reference_df["Development_Nation"]),
        "color": safe_mode(reference_df["Color"]),
    }

    with st.container(border=True):
        render_section_header("ML Feature", "New Model Price Predictor")
        st.markdown(
            """
            <div class="predictor-subtitle">
                Forecast the launch price of a new BMW variant using a CatBoostRegressor trained on historical specification patterns.
                The model focuses on launch-style attributes rather than post-launch sales outcomes.
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_cols = st.columns(4, gap="small")
        for column, (label, value) in zip(
            metric_cols,
            [
                ("Model Type", "CatBoostRegressor"),
                ("MAE", format_currency(metrics["MAE"])),
                ("RMSE", format_currency(metrics["RMSE"])),
                ("R2 Score", f"{metrics['R2']:.3f}"),
            ],
        ):
            with column:
                st.markdown(
                    f"""
                    <div class="mini-card">
                        <span class="mini-label">{label}</span>
                        <span class="mini-value">{value}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        left, right = st.columns([0.92, 1.08], gap="large")
        with left:
            with st.form("new_model_price_predictor_form"):
                manufacturing_year = st.selectbox(
                    "Manufacturing Year",
                    sorted(reference_df["Manufacturing_Year"].unique()),
                    index=sorted(reference_df["Manufacturing_Year"].unique()).index(defaults["year"]),
                )
                region = st.selectbox("Region", sorted(reference_df["Region"].unique()), index=sorted(reference_df["Region"].unique()).index(defaults["region"]))
                fuel_type = st.selectbox("Fuel Type", sorted(reference_df["Fuel_Type"].unique()), index=sorted(reference_df["Fuel_Type"].unique()).index(defaults["fuel"]))
                transmission = st.selectbox("Transmission", sorted(reference_df["Transmission"].unique()), index=sorted(reference_df["Transmission"].unique()).index(defaults["transmission"]))
                engine_size = st.slider("Engine Size (L)", 1.5, 5.0, float(defaults["engine"]), 0.1)
                vehicle_type = st.selectbox("Vehicle Type", sorted(reference_df["Vehicle_Type"].unique()), index=sorted(reference_df["Vehicle_Type"].unique()).index(defaults["vehicle"]))
                claimed_mileage = st.slider("Claimed Mileage (KM/L)", 0.0, 47.0, float(defaults["mileage"]), 0.5)
                development_nation = st.selectbox(
                    "Development Nation",
                    sorted(reference_df["Development_Nation"].unique()),
                    index=sorted(reference_df["Development_Nation"].unique()).index(defaults["development"]),
                )
                color = st.selectbox("Color", sorted(reference_df["Color"].unique()), index=sorted(reference_df["Color"].unique()).index(defaults["color"]))
                submitted = st.form_submit_button("Forecast Launch Price", use_container_width=True)

        launch_profile = {
            "Manufacturing_Year": int(manufacturing_year),
            "Region": region,
            "Fuel_Type": fuel_type,
            "Transmission": transmission,
            "Engine_Size_L": float(engine_size),
            "Vehicle_Type": vehicle_type,
            "Claimed_Mileage_KM_L": float(claimed_mileage),
            "Development_Nation": development_nation,
            "Color": color,
        }

        if submitted or "price_predictor_result" not in st.session_state:
            prediction = predict_new_variant_price(model_bundle, launch_profile)
            similar_cars = find_similar_historical_cars(model_bundle, launch_profile)
            explanation = build_price_explanation(launch_profile, model_bundle, prediction)
            st.session_state["price_predictor_result"] = {
                "prediction": prediction,
                "similar_cars": similar_cars,
                "explanation": explanation,
                "launch_profile": launch_profile,
            }

        result = st.session_state["price_predictor_result"]

        with right:
            prediction = result["prediction"]
            st.markdown(
                f"""
                <div class="prediction-card primary">
                    <span class="prediction-label">Predicted Price (USD)</span>
                    <span class="prediction-value">{format_currency(prediction['predicted_price'])}</span>
                    <div class="prediction-foot">{prediction['price_band']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            band_cols = st.columns(2, gap="small")
            with band_cols[0]:
                st.markdown(
                    f"""
                    <div class="prediction-card">
                        <span class="prediction-label">Lower Expected Range</span>
                        <span class="mini-value">{format_currency(prediction['lower_bound'])}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with band_cols[1]:
                st.markdown(
                    f"""
                    <div class="prediction-card">
                        <span class="prediction-label">Upper Expected Range</span>
                        <span class="mini-value">{format_currency(prediction['upper_bound'])}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"""
                <div class="story-card">
                    <span class="mini-label">Model Artifact</span>
                    <span class="mini-value">{MODEL_PATH.name}</span>
                    <div style="margin-top:0.4rem; color:#a7b7ca; line-height:1.65;">
                        Saved locally at <span style="color:#edf3fa;">{model_bundle['model_path']}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_similar_car_cards(result["similar_cars"])

        lower_left, lower_right = st.columns([1.05, 0.95], gap="large")
        with lower_left:
            st.plotly_chart(
                create_prediction_comparison_chart(result["prediction"], result["similar_cars"]),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with lower_right:
            explanation_markup = "".join(f"<li>{message}</li>" for message in result["explanation"])
            st.markdown(
                f"""
                <div class="story-card">
                    <span class="mini-label">Why This Price?</span>
                    <ul>{explanation_markup}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_empty_state() -> None:
    st.warning("No matching rows remain after the current filter stack. Ease one or more filters to restore the analytics panels.")


def main() -> None:
    inject_global_styles()
    df = load_bmw_data()
    model_bundle = train_price_model(DATA_FILE.stat().st_mtime)

    if "active_report_page" not in st.session_state:
        st.session_state["active_report_page"] = next(iter(DEFAULT_REPORT_PAGES))

    with st.sidebar:
        st.markdown('<div class="sidebar-title">Control Rail</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-copy">Switch Power BI pages, refine the current BMW slice, and keep the premium dashboard centered.</div>',
            unsafe_allow_html=True,
        )

        selected_page = st.radio(
            "Dashboard Page",
            options=list(DEFAULT_REPORT_PAGES.keys()),
            index=list(DEFAULT_REPORT_PAGES.keys()).index(st.session_state["active_report_page"]),
            key="dashboard_page_radio",
            label_visibility="collapsed",
        )
        st.session_state["active_report_page"] = selected_page

        with st.expander("Advanced report mapping", expanded=False):
            st.caption(
                "Power BI page buttons use internal section IDs. Adjust the mapping below if the report uses different page names."
            )
            report_page_map = {}
            for index, (label, default_id) in enumerate(DEFAULT_REPORT_PAGES.items()):
                report_page_map[label] = st.text_input(
                    f"{label} page ID",
                    value=default_id,
                    key=f"report_page_id_{index}",
                ).strip()

        filters = {
            "Model_Name": st.multiselect("Model", sorted(df["Model_Name"].dropna().unique())),
            "Manufacturing_Year": st.multiselect(
                "Manufacturing Year",
                sorted(df["Manufacturing_Year"].dropna().astype(int).unique()),
            ),
            "Region": st.multiselect("Region", sorted(df["Region"].dropna().unique())),
            "Fuel_Type": st.multiselect("Fuel Type", sorted(df["Fuel_Type"].dropna().unique())),
            "Transmission": st.multiselect("Transmission", sorted(df["Transmission"].dropna().unique())),
            "Vehicle_Type": st.multiselect("Vehicle Type", sorted(df["Vehicle_Type"].dropna().unique())),
        }

    filtered_df = apply_filters(df, filters)

    render_hero(filtered_df)
    render_section_header("Main Page", "Performance Snapshot")
    render_kpi_strip(filtered_df)

    render_section_header("Power BI", "Strategic Dashboard Embed")
    active_page_id = report_page_map.get(selected_page, DEFAULT_REPORT_PAGES[selected_page])
    render_dashboard_frame(selected_page, active_page_id, filtered_df)

    render_section_header("Custom Intelligence", "BMW Premium Analytics Panels")
    if filtered_df.empty:
        render_empty_state()
    else:
        spotlight_default = (
            filters["Model_Name"][0]
            if len(filters["Model_Name"]) == 1
            else filtered_df.groupby("Model_Name")["Revenue"].sum().idxmax()
        )

        top_row_left, top_row_right = st.columns([1, 1], gap="large")
        with top_row_left:
            render_model_spotlight(filtered_df, spotlight_default)
        with top_row_right:
            render_regional_demand(filtered_df)
        render_product_mix(filtered_df)

    render_prediction_panel(model_bundle, df)


if __name__ == "__main__":
    main()
