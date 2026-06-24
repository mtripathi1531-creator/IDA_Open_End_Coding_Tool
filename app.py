import io
import json
import re
from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="IDA Open End Coding Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom SaaS styling ──────────────────────────────────────────────────────

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

    <style>
        /* Hide Streamlit chrome */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }
        [data-testid="stHeader"] { display: none; }
        [data-testid="stToolbar"] { display: none; }
        [data-testid="stDecoration"] { display: none; }
        [data-testid="stStatusWidget"] { display: none; }
        .stDeployButton { display: none; }
        [data-testid="stSidebar"] { display: none; }
        .viewerBadge_container__r5tak { display: none; }
        .viewerBadge_link__qRIco { display: none; }
        ._container_gzau3_1, ._profileContainer_gzau3_53{ display: none !Important;}
        /* Global typography & layout */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .stApp {
            background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 40%, #FFFFFF 100%);
        }
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 1100px;
        }

        /* Hero */
        .ida-hero {
            text-align: center;
            padding: 3rem 1.5rem 2.5rem;
            margin-bottom: 0.5rem;
        }
        .ida-badge {
            display: inline-block;
            background: #EEF2FF;
            color: #4338CA;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            margin-bottom: 1.25rem;
        }
        .ida-hero h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: #0F172A;
            line-height: 1.2;
            margin: 0 0 0.75rem 0;
            letter-spacing: -0.025em;
        }
        .ida-hero .subtitle {
            font-size: 1.125rem;
            font-weight: 500;
            color: #6366F1;
            margin: 0 0 1rem 0;
        }
        .ida-hero .description {
            font-size: 1.05rem;
            color: #64748B;
            max-width: 620px;
            margin: 0 auto;
            line-height: 1.65;
        }

        /* Feature grid */
        .ida-features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin: 0 0 2rem 0;
            padding: 0 0.25rem;
        }
        .ida-feature {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.25rem 1rem;
            text-align: center;
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }
        .ida-feature:hover {
            border-color: #C7D2FE;
            box-shadow: 0 4px 16px rgba(99, 102, 241, 0.08);
        }
        .ida-feature .icon {
            font-size: 1.75rem;
            margin-bottom: 0.6rem;
            line-height: 1;
        }
        .ida-feature .label {
            font-size: 0.875rem;
            font-weight: 600;
            color: #334155;
            line-height: 1.4;
        }

        /* Security box */
        .ida-security {
            background: #F0FDF4;
            border: 1px solid #BBF7D0;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 2rem;
        }
        .ida-security .title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #166534;
            margin: 0 0 0.75rem 0;
        }
        .ida-security ul {
            list-style: none;
            margin: 0;
            padding: 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 0.4rem 1.5rem;
        }
        .ida-security li {
            font-size: 0.875rem;
            color: #15803D;
            line-height: 1.5;
        }

        /* Upload card */
        .ida-upload-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-bottom: none;
            border-radius: 16px 16px 0 0;
            padding: 2rem 2rem 1.25rem;
            margin-bottom: 0;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        }
        .ida-upload-card h2 {
            font-size: 1.25rem;
            font-weight: 700;
            color: #0F172A;
            margin: 0 0 0.5rem 0;
        }
        .ida-upload-card p {
            font-size: 0.925rem;
            color: #64748B;
            margin: 0 0 0.25rem 0;
            line-height: 1.5;
        }

        /* Footer */
        .ida-footer {
            text-align: center;
            padding: 2.5rem 1rem 1rem;
            margin-top: 3rem;
            border-top: 1px solid #E2E8F0;
        }
        .ida-footer p {
            font-size: 0.8125rem;
            color: #94A3B8;
            margin: 0;
        }
        .ida-footer a {
            color: #6366F1;
            text-decoration: none;
            font-weight: 500;
        }
        .ida-footer a:hover {
            text-decoration: underline;
        }

        /* Workflow sections (post-upload) */
        .ida-workflow {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 1.75rem 2rem;
            margin-top: 1.5rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        }
        .ida-section-label {
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #94A3B8;
            margin: 0 0 0.25rem 0;
        }

        /* Streamlit component polish */
        [data-testid="stFileUploader"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-top: 1px dashed #CBD5E1;
            border-radius: 0 0 16px 16px;
            padding: 1.5rem 2rem 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 24px rgba(15, 23, 42, 0.04);
            transition: border-color 0.2s ease, background 0.2s ease;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: #C7D2FE;
            background: #FAFBFF;
        }
        [data-testid="stFileUploader"] > div {
            background: #F8FAFC;
            border: 2px dashed #CBD5E1;
            border-radius: 12px;
            padding: 1.25rem;
        }
        [data-testid="stFileUploader"]:hover > div {
            border-color: #818CF8;
            background: #EEF2FF;
        }
        [data-testid="stFileUploader"] section {
            padding: 0.5rem;
        }
        [data-testid="stFileUploader"] small {
            color: #64748B !important;
        }
        .stButton > button[kind="primary"] {
            background: #4F46E5 !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.25rem !important;
            transition: background 0.2s ease !important;
        }
        .stButton > button[kind="primary"]:hover {
            background: #4338CA !important;
        }
        .stButton > button[kind="secondary"] {
            border-radius: 8px !important;
            font-weight: 500 !important;
        }
        [data-testid="stTabs"] button {
            font-weight: 500 !important;
            font-size: 0.875rem !important;
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
            color: #4F46E5 !important;
        }
        h2, h3 {
            color: #0F172A !important;
            font-weight: 700 !important;
            letter-spacing: -0.01em !important;
        }
        .stCaption, [data-testid="stCaptionContainer"] {
            color: #64748B !important;
        }
        [data-testid="stDataFrame"], .stDataFrame {
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            overflow: hidden;
        }
        div[data-testid="stExpander"] {
            border: 1px solid #E2E8F0 !important;
            border-radius: 10px !important;
        }
        .stTextArea textarea, .stNumberInput input, .stMultiSelect div {
            border-radius: 8px !important;
        }
        div[data-baseweb="select"] > div {
            border-radius: 8px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Modern full-width SaaS shell. The original component rules above are retained
# for compatibility; these scoped overrides define the current visual system.
st.markdown(
    """
    <style>
        :root { --ida-primary:#6D28D9; --ida-secondary:#8B5CF6; --ida-bg:#F8FAFC; --ida-text:#0F172A; }
        #MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stToolbar"],
        [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
        [data-testid="stSidebar"], .viewerBadge_container__1QSob, .viewerBadge_link__1S137,
        .viewerBadge_text__1JaDK, .viewerBadge_container__r5tak, .viewerBadge_link__qRIco,
        div[data-testid="stBottom"], iframe[title="streamlit badge"], button[kind="header"],
        button[data-testid*="profile"] { display:none !important; }
        iframe { border:none !important; }
        html, body, [class*="css"] { font-family:'Inter',sans-serif; color:var(--ida-text); }
        .stApp { background:var(--ida-bg); }
        .block-container { max-width:1400px !important; padding:5.75rem 2rem 2rem !important; }
        .ida-hero, .ida-features, .ida-security, .ida-upload-card { display:none !important; }
        .ida-nav { position:fixed; z-index:999; top:0; left:0; right:0; height:68px; display:flex;
            align-items:center; justify-content:space-between; padding:0 max(2rem,calc((100vw - 1400px)/2));
            background:rgba(255,255,255,.96); border-bottom:1px solid #E2E8F0; backdrop-filter:blur(12px); }
        .ida-brand { display:flex; align-items:center; gap:12px; }
        .ida-logo { width:38px; height:38px; display:grid; place-items:center; border-radius:11px;
            color:white; font-weight:800; background:linear-gradient(135deg,var(--ida-primary),var(--ida-secondary)); }
        .ida-brand-copy strong { display:block; font-size:.95rem; } .ida-brand-copy span { color:#64748B; font-size:.75rem; }
        .ida-sales-link { color:white !important; background:var(--ida-primary); padding:.68rem 1rem;
            border-radius:9px; text-decoration:none; font-size:.84rem; font-weight:700; }
        .ida-kicker { color:var(--ida-primary); font-weight:800; font-size:.76rem; letter-spacing:.1em; text-transform:uppercase; }
        .ida-landing-copy { padding:1.25rem 2rem 0 0; }
        .ida-landing-copy h1 { max-width:760px; margin:.65rem 0 .55rem; font-size:clamp(2.35rem,4vw,4.25rem);
            line-height:1.03; letter-spacing:-.055em; color:var(--ida-text); }
        .ida-landing-copy h2 { margin:0 0 1rem; color:var(--ida-primary) !important; font-size:1.25rem; }
        .ida-lead { max-width:720px; color:#475569; font-size:1.07rem; line-height:1.7; }
        .ida-feature-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:1.6rem 0; }
        .ida-mini-card { min-height:86px; padding:1rem; background:white; border:1px solid #E2E8F0; border-radius:13px;
            box-shadow:0 8px 25px rgba(15,23,42,.04); font-size:.84rem; font-weight:700; }
        .ida-mini-card span { display:block; margin-bottom:.45rem; color:var(--ida-primary); font-size:1.15rem; }
        .ida-security-new { padding:1.1rem 1.25rem; border:1px solid #DDD6FE; border-radius:14px; background:#F5F3FF; }
        .ida-security-new strong { display:block; margin-bottom:.7rem; }
        .ida-security-list { display:flex; flex-wrap:wrap; gap:.5rem 1.2rem; color:#5B21B6; font-size:.8rem; }
        .ida-steps { display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin-top:.85rem; }
        .ida-step { padding:.85rem .6rem; border-top:2px solid #C4B5FD; color:#475569; font-size:.76rem; font-weight:700; }
        .ida-step b { color:var(--ida-primary); margin-right:.3rem; }
        .ida-demo-card, .ida-panel, .ida-summary, .ida-user-card { background:white; border:1px solid #E2E8F0; border-radius:18px;
            box-shadow:0 16px 45px rgba(15,23,42,.07); }
        .ida-demo-card { padding:1.5rem 1.5rem .4rem; }
        .ida-demo-card .free { color:var(--ida-primary); font-size:.72rem; font-weight:800; letter-spacing:.12em; }
        .ida-demo-card h2 { margin:.3rem 0 .8rem; font-size:1.55rem; }
        .ida-checks { display:grid; gap:.4rem; margin-bottom:1rem; color:#334155; font-size:.86rem; }
        .ida-checks span::first-letter { color:var(--ida-primary); }
        .ida-limit { margin:.3rem 0 1.4rem; padding:1rem; border-radius:12px; background:#F8FAFC; color:#64748B; font-size:.8rem; line-height:1.55; }
        .ida-limit strong { display:block; color:#334155; font-size:.68rem; letter-spacing:.1em; margin-bottom:.35rem; }
        .ida-contact { display:block; text-align:center; margin-top:.75rem; padding:.72rem; border-radius:9px;
            background:#0F172A; color:white !important; text-decoration:none; font-weight:700; }
        .ida-user-card { margin:0 0 1rem; padding:1rem 1.05rem; background:linear-gradient(180deg,#FFFFFF 0%,#FAF7FF 100%);
            border-color:#DDD6FE; box-shadow:0 14px 35px rgba(109,40,217,.10); overflow:hidden; }
        .ida-user-card::before { content:""; display:block; width:44px; height:3px; border-radius:999px;
            background:linear-gradient(90deg,var(--ida-primary),var(--ida-secondary)); margin-bottom:.85rem; }
        .ida-user-card .welcome { margin:0 0 .65rem; color:#0F172A; font-size:1rem; font-weight:800; line-height:1.3; }
        .ida-user-card .company { display:flex; align-items:center; gap:.45rem; margin:0 0 .8rem; color:#475569;
            font-size:.86rem; font-weight:650; overflow-wrap:anywhere; }
        .ida-user-card .access { display:inline-flex; align-items:center; gap:.45rem; padding:.38rem .62rem; border-radius:999px;
            background:#ECFDF5; color:#047857; font-size:.74rem; font-weight:800; }
        .ida-user-card .status-dot { width:8px; height:8px; border-radius:999px; background:#10B981;
            box-shadow:0 0 0 4px rgba(16,185,129,.13); }
        [data-testid="stFileUploader"] { padding:.4rem 0 1rem !important; border:0 !important; box-shadow:none !important; background:white !important; }
        [data-testid="stFileUploader"] > div { min-height:180px; display:flex; align-items:center; justify-content:center;
            border:2px dashed var(--ida-primary) !important; border-radius:16px !important; background:#FAF7FF !important; }
        [data-testid="stFileUploader"] button { color:white !important; background:var(--ida-primary) !important;
            border:0 !important; border-radius:9px !important; font-weight:700 !important; }
        [data-testid="stFileUploader"] button { font-size:0 !important; }
        [data-testid="stFileUploader"] button::after { content:"Choose Excel File"; font-size:.82rem; }
        [data-testid="stFileUploader"] small { color:#64748B !important; }
        [data-testid="stHorizontalBlock"]:has(.ida-demo-card) > [data-testid="stColumn"]:last-child,
        [data-testid="stHorizontalBlock"]:has(.ida-summary) > [data-testid="stColumn"]:last-child {
            position:sticky; top:88px; align-self:flex-start;
        }
        .ida-workspace-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem; }
        .ida-workspace-head h1 { margin:0; font-size:1.7rem; letter-spacing:-.03em; }
        .ida-workspace-head p { margin:.25rem 0 0; color:#64748B; }
        .ida-panel { padding:1.35rem; margin-bottom:1rem; box-shadow:0 5px 20px rgba(15,23,42,.04); }
        .ida-panel-title { margin:0 0 .25rem; font-size:1.05rem; font-weight:800; }
        .ida-panel-sub { margin:0 0 1rem; color:#64748B; font-size:.83rem; }
        .ida-summary { position:sticky; top:88px; padding:1.25rem; }
        .ida-stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:.9rem 0; }
        .ida-stat { padding:.8rem; border-radius:11px; background:#F8FAFC; }
        .ida-stat b { display:block; font-size:1.25rem; } .ida-stat span { color:#64748B; font-size:.72rem; }
        .ida-status { display:inline-flex; padding:.35rem .6rem; border-radius:999px; background:#ECFDF5; color:#047857;
            font-size:.72rem; font-weight:800; }
        .ida-footer-new { display:flex; justify-content:space-between; flex-wrap:wrap; gap:1rem; margin-top:2.5rem;
            padding:1.5rem 0 .5rem; border-top:1px solid #E2E8F0; color:#64748B; font-size:.78rem; }
        .ida-footer-new a { color:#475569; text-decoration:none; margin-left:1rem; }
        .stButton>button, .stDownloadButton>button { border-radius:9px !important; font-weight:700 !important; }
        .stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"] { background:var(--ida-primary) !important; }
        @media(max-width:900px) { .block-container{padding:5.25rem 1rem 1.5rem !important}.ida-landing-copy{padding-right:0}
            .ida-feature-grid{grid-template-columns:repeat(2,1fr)}.ida-steps{grid-template-columns:1fr}.ida-summary{position:static}.ida-nav{padding:0 1rem}
            .ida-user-card{margin-top:.5rem}
            [data-testid="stHorizontalBlock"]:has(.ida-demo-card) > [data-testid="stColumn"]:last-child,
            [data-testid="stHorizontalBlock"]:has(.ida-summary) > [data-testid="stColumn"]:last-child {position:static;} }
    </style>
    <div class="ida-nav">
      <div class="ida-brand"><div class="ida-logo">IDA</div><div class="ida-brand-copy"><strong>Inside Data Analytics</strong><span>AI Open End Coding Tool</span></div></div>
      <a class="ida-sales-link" href="mailto:sales@insidedataanalytics.com">Contact Sales</a>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ida-hero">
        <div class="ida-badge">IDA Open End Coding Tool</div>
        <h1>AI-Powered Open End Coding Platform</h1>
        <p class="subtitle">Built for Market Research Teams</p>
        <p class="description">
            Generate codeframes, assign respondent-level codes, and export client-ready
            deliverables in minutes instead of hours.
        </p>
    </div>

    <div class="ida-features">
        <div class="ida-feature">
            <div class="icon">⚡</div>
            <div class="label">Automatic Codeframe Generation</div>
        </div>
        <div class="ida-feature">
            <div class="icon">🏷</div>
            <div class="label">Multi-Code Assignment</div>
        </div>
        <div class="ida-feature">
            <div class="icon">📊</div>
            <div class="label">Frequency Tables</div>
        </div>
        <div class="ida-feature">
            <div class="icon">📥</div>
            <div class="label">Excel Export</div>
        </div>
        <div class="ida-feature">
            <div class="icon">🔍</div>
            <div class="label">Respondent-Level Coding</div>
        </div>
    </div>

    <div class="ida-security">
        <p class="title">🔒 Secure Processing</p>
        <ul>
            <li>✓ Files processed over encrypted HTTPS</li>
            <li>✓ No client data used to train AI models</li>
            <li>✓ Temporary file processing</li>
            <li>✓ Private OpenAI API infrastructure</li>
        </ul>
    </div>

    <div class="ida-upload-card">
        <h2>Upload Survey Responses</h2>
        <p>Upload an Excel workbook containing open-ended survey responses.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

MODEL = "gpt-4o-mini"
MAX_DEMO_RESPONSES = 100
LEAD_COLUMNS = [
    "Date",
    "Name",
    "Email",
    "Company",
    "Upload_Count",
    "Total_Responses",
    "Last_Visit",
]
CODING_BATCH_SIZE = 15
MAX_RESPONSE_CHARS = 500
MAX_RESPONSES_FOR_CODEFRAME = 200
CODE_OTHER = 96
CODE_UNCODED = 99
STANDARD_CODES = {CODE_OTHER: "Other", CODE_UNCODED: "Uncoded"}


def _now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Google Sheets Lead Tracking
def get_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope,
    )
    client = gspread.authorize(creds)
    sheet = client.open("IDA Demo Leads").sheet1

    header = sheet.row_values(1)
    if header != LEAD_COLUMNS:
        sheet.update("A1:G1", [LEAD_COLUMNS])

    return sheet


def _sheet_rows(sheet):
    values = sheet.get_all_values()
    rows = []
    for idx, values_row in enumerate(values[1:], start=2):
        row = {
            column: values_row[col_idx] if col_idx < len(values_row) else ""
            for col_idx, column in enumerate(LEAD_COLUMNS)
        }
        if any(str(value).strip() for value in row.values()):
            rows.append((idx, row))
    return rows


def _find_user_row(sheet, email):
    email = str(email).strip().lower()
    for row_number, row in _sheet_rows(sheet):
        if str(row.get("Email", "")).strip().lower() == email:
            return row_number, row
    return None, None


def _to_int(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


# Save User Information
def save_user(name, email, company):
    name = str(name).strip()
    email = str(email).strip().lower()
    company = str(company).strip()
    now = _now_string()

    try:
        sheet = get_sheet()
        row_number, _ = _find_user_row(sheet, email)
        if row_number:
            sheet.update_cell(row_number, LEAD_COLUMNS.index("Last_Visit") + 1, now)
        else:
            sheet.append_row(
                [now, name, email, company, 0, 0, now],
                value_input_option="USER_ENTERED",
            )
        return True
    except Exception:
        st.warning("Lead tracking temporarily unavailable.")
        return False


# Update User Usage Statistics
def update_usage(email, responses_uploaded):
    email = str(email).strip().lower()
    responses_uploaded = int(responses_uploaded)
    now = _now_string()

    if not email:
        return False

    try:
        sheet = get_sheet()
        row_number, row = _find_user_row(sheet, email)
        if not row_number:
            return False

        upload_count = _to_int(row.get("Upload_Count")) + 1
        total_responses = _to_int(row.get("Total_Responses")) + responses_uploaded
        sheet.update(
            f"E{row_number}:G{row_number}",
            [[upload_count, total_responses, now]],
            value_input_option="USER_ENTERED",
        )
        return True
    except Exception:
        st.warning("Lead tracking temporarily unavailable.")
        return False


def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def call_openai_json(client: OpenAI, system: str, user: str) -> dict:
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    content = completion.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned an empty response.")
    return json.loads(content)


def truncate_responses(responses: list[str], limit: int = MAX_RESPONSES_FOR_CODEFRAME) -> list[str]:
    trimmed = [r[:MAX_RESPONSE_CHARS] for r in responses if r.strip()]
    if len(trimmed) > limit:
        return trimmed[:limit]
    return trimmed


def format_numbered_responses(responses: list[str]) -> str:
    return "\n".join(f"{i + 1}. {text}" for i, text in enumerate(responses))


def parse_code_number(value, valid_codes: set[int]) -> int | None:
    if value is None:
        return None
    if isinstance(value, int) and value in valid_codes:
        return value
    if isinstance(value, float) and not pd.isna(value) and int(value) in valid_codes:
        return int(value)
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit() and int(text) in valid_codes:
        return int(text)
    match = re.match(r"^(\d+)", text)
    if match and int(match.group(1)) in valid_codes:
        return int(match.group(1))
    for code in valid_codes:
        if text.lower() == str(code).lower():
            return code
    return None


def ensure_standard_codes(codeframe_df: pd.DataFrame) -> pd.DataFrame:
    df = codeframe_df.copy()
    df["Code"] = pd.to_numeric(df["Code"], errors="coerce")
    df = df.dropna(subset=["Code"])
    df["Code"] = df["Code"].astype(int)
    df["Label"] = df["Label"].fillna("").astype(str).str.strip()
    if "Description" not in df.columns:
        df["Description"] = ""
    df["Description"] = df["Description"].fillna("").astype(str)

    existing = set(df["Code"].tolist())
    for code, label in STANDARD_CODES.items():
        if code not in existing:
            description = (
                "Response mentions a theme not covered by thematic codes."
                if code == CODE_OTHER
                else "Response could not be assigned to a codeframe code."
            )
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [{"Code": code, "Label": label, "Description": description}]
                    ),
                ],
                ignore_index=True,
            )
    return df.sort_values("Code").reset_index(drop=True)


def suggest_id_columns(columns: list[str], oe_columns: list[str]) -> list[str]:
    id_patterns = ("id", "respondent", "case", "record", "uuid", "serial")
    candidates = [c for c in columns if c not in oe_columns]
    suggested = [c for c in candidates if any(p in c.lower() for p in id_patterns)]
    if suggested:
        return suggested
    return [candidates[0]] if candidates else []


def generate_draft_codeframe(
    client: OpenAI, question: str, responses: list[str], num_codes: int
) -> pd.DataFrame:
    sample = truncate_responses(responses)
    numbered = format_numbered_responses(sample)

    prompt = f"""You are a senior market research coder building a thematic codeframe.

Survey question:
{question}

Review these open-ended responses and create exactly {num_codes} distinct, mutually exclusive thematic codes.
Codes must use numeric values from 1 to {num_codes}. Do not use 96 or 99 (reserved).

Return JSON:
{{
  "codeframe": [
    {{"code": 1, "label": "Bank of America", "description": "Mentions Bank of America specifically."}},
  ...
  ]
}}

Rules:
- Provide exactly {num_codes} codes with integers 1 through {num_codes}.
- Labels must be short, unique theme names without leading numbers.
- Descriptions explain what belongs in each code and what to exclude.
- Cover the main themes present in the data; avoid overlap between codes.

Responses ({len(sample)} shown):
{numbered}"""

    parsed = call_openai_json(
        client,
        "You build market research codeframes. Reply with valid JSON only.",
        prompt,
    )
    items = parsed.get("codeframe")
    if not isinstance(items, list) or not items:
        raise ValueError("OpenAI did not return a valid codeframe.")

    rows = []
    for item in items:
        code = parse_code_number(item.get("code"), set(range(1, num_codes + 1)))
        label = str(item.get("label", "")).strip()
        description = str(item.get("description", "")).strip()
        if code is not None and label:
            rows.append({"Code": code, "Label": label, "Description": description})

    if not rows:
        raise ValueError("The generated codeframe contained no usable codes.")

    return ensure_standard_codes(pd.DataFrame(rows))


def format_codeframe_for_prompt(codeframe_df: pd.DataFrame) -> str:
    lines = []
    for _, row in codeframe_df.iterrows():
        code = int(row["Code"])
        label = row["Label"]
        description = row.get("Description", "")
        lines.append(f"- {code} {label}: {description}")
    return "\n".join(lines)


def normalize_code(value, valid_codes: set[int]) -> int:
    parsed = parse_code_number(value, valid_codes)
    if parsed is not None:
        return parsed
    return CODE_UNCODED


def normalize_secondary_codes(values, primary: int, valid_codes: set[int]) -> list[int]:
    if values is None:
        return []
    if isinstance(values, str):
        parts = [p.strip() for p in values.replace(",", ";").split(";")]
    elif isinstance(values, list):
        parts = [str(v).strip() for v in values]
    else:
        parts = [str(values).strip()]

    seen = set()
    normalized = []
    for part in parts:
        if not part:
            continue
        code = normalize_code(part, valid_codes)
        if code == CODE_UNCODED or code == primary or code in seen:
            continue
        seen.add(code)
        normalized.append(code)
    return normalized


def apply_codeframe_batch(
    client: OpenAI,
    question: str,
    codeframe_df: pd.DataFrame,
    responses: list[str],
) -> list[dict]:
    valid_codes = set(codeframe_df["Code"].astype(int).tolist())
    codeframe_text = format_codeframe_for_prompt(codeframe_df)
    numbered = format_numbered_responses([r[:MAX_RESPONSE_CHARS] for r in responses])

    prompt = f"""You are a market research open-end coder applying a fixed codeframe.

Survey question:
{question}

Codeframe:
{codeframe_text}

For each response below, assign:
1. primary_code — exactly one numeric code from the codeframe (the dominant theme).
2. secondary_codes — zero or more additional numeric codes from the codeframe (multi-coded responses allowed).

Rules:
- Use numeric codes exactly as listed in the codeframe.
- Secondary codes must differ from the primary code.
- Assign multiple secondary codes when the response clearly mentions several themes.
- Use {CODE_UNCODED} only if no codeframe code fits at all.
- Use {CODE_OTHER} when the response is on-topic but not covered by thematic codes.

Return JSON:
{{
  "results": [
    {{"index": 1, "primary_code": 1, "secondary_codes": [2]}},
    ...
  ]
}}

Responses:
{numbered}"""

    parsed = call_openai_json(
        client,
        "You apply market research codeframes with primary and secondary multi-codes. Reply with valid JSON only.",
        prompt,
    )
    results = parsed.get("results")
    if not isinstance(results, list):
        raise ValueError("Unexpected coding response format from OpenAI.")

    by_index: dict[int, dict] = {}
    for item in results:
        idx = item.get("index")
        if idx is None:
            continue
        primary = normalize_code(item.get("primary_code", CODE_UNCODED), valid_codes)
        secondary = normalize_secondary_codes(item.get("secondary_codes", []), primary, valid_codes)
        by_index[int(idx)] = {
            "primary_code": primary,
            "secondary_codes": secondary,
        }

    output = []
    for i in range(len(responses)):
        entry = by_index.get(i + 1, {"primary_code": CODE_UNCODED, "secondary_codes": []})
        output.append(entry)
    return output


def apply_codeframe(
    client: OpenAI,
    question: str,
    codeframe_df: pd.DataFrame,
    responses: list[str],
) -> list[list[int]]:
    coded_rows: list[list[int]] = []

    for start in range(0, len(responses), CODING_BATCH_SIZE):
        batch = responses[start : start + CODING_BATCH_SIZE]
        batch_results = apply_codeframe_batch(client, question, codeframe_df, batch)
        for item in batch_results:
            primary = item["primary_code"]
            secondary = item["secondary_codes"]
            coded_rows.append([primary] + secondary)

    return coded_rows


def build_frequency_table(coded_codes: list[list[int]], codeframe_df: pd.DataFrame) -> pd.DataFrame:
    labels = dict(zip(codeframe_df["Code"].astype(int), codeframe_df["Label"].astype(str)))
    all_codes = list(codeframe_df["Code"].astype(int))
    if CODE_UNCODED not in all_codes:
        all_codes.append(CODE_UNCODED)
        labels[CODE_UNCODED] = STANDARD_CODES[CODE_UNCODED]

    primary_counts = {code: 0 for code in all_codes}
    secondary_counts = {code: 0 for code in all_codes}

    for codes in coded_codes:
        if not codes:
            continue
        primary = codes[0]
        if primary in primary_counts:
            primary_counts[primary] += 1
        for sec in codes[1:]:
            if sec in secondary_counts:
                secondary_counts[sec] += 1

    rows = []
    for code in all_codes:
        primary = primary_counts[code]
        secondary = secondary_counts[code]
        rows.append(
            {
                "Code": code,
                "Label": labels.get(code, ""),
                "Primary Count": primary,
                "Secondary Count": secondary,
                "Total Mentions": primary + secondary,
            }
        )

    freq_df = pd.DataFrame(rows)
    return freq_df.sort_values("Total Mentions", ascending=False).reset_index(drop=True)


def build_codeframe_export(coding_results: dict[str, dict], oe_columns: list[str]) -> pd.DataFrame:
    rows = []
    multi_question = len(oe_columns) > 1
    for oe_col in oe_columns:
        result = coding_results.get(oe_col)
        if not result or "codeframe_df" not in result:
            continue
        codeframe_df = result["codeframe_df"]
        q_idx = oe_columns.index(oe_col) + 1
        for _, row in codeframe_df.iterrows():
            label = str(row["Label"]).strip()
            if multi_question:
                label = f"Q{q_idx} ({oe_col}): {label}"
            rows.append({"Code": int(row["Code"]), "Label": label})
    return pd.DataFrame(rows, columns=["Code", "Label"])


def build_coded_data_df(
    original_df: pd.DataFrame,
    id_columns: list[str],
    oe_columns: list[str],
    coding_results: dict[str, dict],
) -> pd.DataFrame:
    coded_df = original_df[id_columns].copy() if id_columns else pd.DataFrame(index=original_df.index)

    for q_idx, oe_col in enumerate(oe_columns, 1):
        result = coding_results.get(oe_col)
        if not result or "coded_codes" not in result:
            continue
        coded_codes = result["coded_codes"]
        max_slots = max(len(codes) for codes in coded_codes) if coded_codes else 0
        for slot in range(1, max_slots + 1):
            col_name = f"Q{q_idx}_{slot}"
            coded_df[col_name] = [
                codes[slot - 1] if len(codes) >= slot else None for codes in coded_codes
            ]

    return coded_df


def build_mr_workbook(
    original_df: pd.DataFrame,
    codeframe_df: pd.DataFrame,
    coded_data_df: pd.DataFrame,
) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        original_df.to_excel(writer, sheet_name="OriginalData", index=False)
        codeframe_df.to_excel(writer, sheet_name="CodeFrame", index=False)
        coded_data_df.to_excel(writer, sheet_name="CodedData", index=False)
    buffer.seek(0)
    return buffer.getvalue()


def handle_openai_errors(func):
    try:
        return func()
    except AuthenticationError:
        st.error("Invalid OpenAI API key. Please check your key and try again.")
    except RateLimitError:
        st.error("OpenAI rate limit reached. Please wait and try again.")
    except APIConnectionError:
        st.error("Could not connect to OpenAI. Check your internet connection.")
    except APIError as exc:
        st.error(f"OpenAI API error: {getattr(exc, 'message', str(exc))}")
    except (json.JSONDecodeError, ValueError) as exc:
        st.error(f"Failed to process OpenAI response: {exc}")
    except Exception as exc:
        st.error(f"An unexpected error occurred: {exc}")
    return None


# User Access Card
def render_user_access_card():
    lead_name = escape(st.session_state.get("lead_name", "Demo User"))
    lead_company = escape(st.session_state.get("lead_company", "Demo Workspace"))
    st.markdown(
        f"""
        <div class="ida-user-card">
          <p class="welcome">👋 Welcome, {lead_name}</p>
          <p class="company">🏢 {lead_company}</p>
          <span class="access"><span class="status-dot"></span>Demo Access Active</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        """
        <div class="ida-footer-new">
          <span>© Inside Data Analytics</span>
          <span><a href="https://www.insidedataanalytics.com/privacy-policy" target="_blank">Privacy Policy</a>
          <a href="mailto:sales@insidedataanalytics.com">sales@insidedataanalytics.com</a>
          <a href="https://www.insidedataanalytics.com" target="_blank">www.insidedataanalytics.com</a></span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_landing():
    st.session_state.setdefault("demo_access", False)
    left, right = st.columns([65, 35], gap="large")
    with left:
        st.markdown(
            """
            <div class="ida-landing-copy">
              <div class="ida-kicker">AI coding, built for research</div>
              <h1>AI-Powered Open End Coding Platform</h1>
              <h2>Built for Market Research Teams</h2>
              <p class="ida-lead">Generate codeframes, assign respondent-level codes, and export client-ready deliverables in minutes instead of hours.</p>
              <p class="ida-lead"><strong>Welcome to the AI Open-End Coding Demo</strong><br>Please provide your professional details to access the platform.</p>
              <div class="ida-feature-grid">
                <div class="ida-mini-card"><span>✦</span>Automatic Codeframe Generation</div>
                <div class="ida-mini-card"><span>⌘</span>Multi-Code Assignment</div>
                <div class="ida-mini-card"><span>▥</span>Frequency Tables</div>
                <div class="ida-mini-card"><span>↓</span>Excel Export</div>
                <div class="ida-mini-card"><span>◎</span>Respondent-Level Coding</div>
              </div>
              <div class="ida-security-new"><strong>Enterprise Security</strong>
                <div class="ida-security-list"><span>✓ HTTPS encrypted</span><span>✓ GDPR friendly</span><span>✓ No training on client data</span><span>✓ Temporary file processing</span><span>✓ Private OpenAI API</span></div>
              </div>
              <div class="ida-kicker" style="margin-top:1.5rem">How it works</div>
              <div class="ida-steps"><div class="ida-step"><b>1</b> Upload File</div><div class="ida-step"><b>2</b> Generate Codeframe</div><div class="ida-step"><b>3</b> Review &amp; Edit</div><div class="ida-step"><b>4</b> Apply Coding</div><div class="ida-step"><b>5</b> Download Deliverable</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        if st.session_state.get("demo_access"):
            render_user_access_card()
        st.markdown(
            """<div class="ida-demo-card"><div class="free">FREE DEMO</div><h2>Up to 100 Responses</h2>
            <div class="ida-checks"><span>✔ Up to 100 responses</span><span>✔ AI Codeframe Generation</span><span>✔ Multi-Code Assignment</span><span>✔ Frequency Tables</span><span>✔ Excel Export Deliverables</span></div>""",
            unsafe_allow_html=True,
        )
        st.file_uploader(
            "Drag & drop your Excel file here",
            type=["xlsx"],
            key="demo_upload",
            help="Maximum 100 responses. .xlsx only.",
        )
        st.markdown(
            """<div class="ida-limit"><strong>DEMO LIMITATION</strong>This demo version supports up to 100 responses.<br><br>For larger studies contact:<br><b>sales@insidedataanalytics.com</b><a class="ida-contact" href="mailto:sales@insidedataanalytics.com">Contact Sales</a></div></div>""",
            unsafe_allow_html=True,
        )


def render_lead_capture():
    st.markdown(
        """
        <div class="ida-demo-card">
          <div class="free">FREE DEMO</div>
          <h2>Welcome to the AI Open-End Coding Demo</h2>
          <p>Please provide your professional details to access the platform.</p>
          <div class="ida-checks">
            <span>✓ Up to 100 responses</span>
            <span>✓ AI Codeframe Generation</span>
            <span>✓ Multi-Code Assignment</span>
            <span>✓ Frequency Tables</span>
            <span>✓ Excel Export Deliverables</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("lead_capture_form"):
        full_name = st.text_input("Full Name *")
        work_email = st.text_input("Work Email *")
        company_name = st.text_input("Company Name *")
        submitted = st.form_submit_button("Continue to Demo", type="primary")

    if not submitted:
        return

    full_name = full_name.strip()
    work_email = work_email.strip().lower()
    company_name = company_name.strip()

    if not full_name or not work_email or not company_name:
        st.error("Please complete all required fields.")
        return
    if "@" not in work_email:
        st.error("Please enter a valid work email address.")
        return

    save_user(full_name, work_email, company_name)

    st.session_state["demo_access"] = True
    st.session_state["lead_name"] = full_name
    st.session_state["lead_email"] = work_email
    st.session_state["lead_company"] = company_name
    st.rerun()


st.session_state.setdefault("demo_access", False)

if not st.session_state["demo_access"]:
    render_lead_capture()
    render_footer()
    st.stop()

uploaded_file = st.session_state.get("demo_upload")
if uploaded_file is None:
    render_landing()
    render_footer()
    st.stop()

try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error("OpenAI API Key not configured in Streamlit Secrets.")
    st.stop()

file_id = f"{uploaded_file.name}_{uploaded_file.size}"
if st.session_state.get("file_id") != file_id:
    st.session_state["file_id"] = file_id
    for key in ("coding_results", "id_columns", "oe_columns"):
        st.session_state.pop(key, None)

try:
    original_df = pd.read_excel(uploaded_file, engine="openpyxl")
except Exception as exc:
    st.error(f"Could not read the Excel file: {exc}")
    st.stop()

if len(original_df) > MAX_DEMO_RESPONSES:
    st.warning(
        "This demo version supports up to 100 responses.\n\n"
        "Contact [sales@insidedataanalytics.com](mailto:sales@insidedataanalytics.com) for larger studies."
    )
    st.stop()

usage_key = f"{st.session_state.get('lead_email', '')}:{file_id}"
if st.session_state.get("usage_tracked_file") != usage_key:
    if update_usage(st.session_state.get("lead_email", ""), len(original_df)):
        st.session_state["usage_tracked_file"] = usage_key

all_columns = original_df.columns.tolist()
if not all_columns:
    st.error("The uploaded file contains no columns.")
    st.stop()

coding_results = st.session_state.setdefault("coding_results", {})
selected_oe = [c for c in st.session_state.get("oe_columns", []) if c in all_columns]
coded_oe_columns = [c for c in selected_oe if c in coding_results and "coded_codes" in coding_results[c]]

st.markdown(
    f"""<div class="ida-workspace-head"><div><div class="ida-kicker">Project workspace</div><h1>{uploaded_file.name}</h1><p>Configure, code, review, and export your open-end study.</p></div></div>""",
    unsafe_allow_html=True,
)

work_left, work_right = st.columns([72, 28], gap="large")
with work_left:
    st.markdown('<div class="ida-panel"><p class="ida-panel-title">Uploaded Data</p><p class="ida-panel-sub">Preview the source workbook before configuring your project.</p>', unsafe_allow_html=True)
    st.dataframe(original_df, use_container_width=True, height=260)
    st.markdown('</div><div class="ida-panel"><p class="ida-panel-title">Column Selection</p><p class="ida-panel-sub">Choose respondent identifiers and one or more open-end variables.</p>', unsafe_allow_html=True)

    default_oe = [c for c in st.session_state.get("oe_columns", []) if c in all_columns]
    oe_columns = st.multiselect("Open-end question columns", all_columns, default=default_oe, help="Select every open-end variable that should be coded.")
    st.session_state["oe_columns"] = oe_columns
    id_options = [c for c in all_columns if c not in oe_columns]
    default_ids = [c for c in st.session_state.get("id_columns", suggest_id_columns(all_columns, oe_columns)) if c in id_options]
    id_columns = st.multiselect("Respondent identifier columns", id_options, default=default_ids, help="Included in the CodedData sheet.")
    st.session_state["id_columns"] = id_columns
    st.markdown('</div>', unsafe_allow_html=True)

    if not oe_columns:
        st.info("Select at least one open-end question column to begin coding.")
    else:
        st.markdown('<div class="ida-panel"><p class="ida-panel-title">Question Setup & Codeframe Editor</p><p class="ida-panel-sub">Generate, review, and apply a codeframe for each selected variable.</p>', unsafe_allow_html=True)
        question_tabs = st.tabs(oe_columns)
        for tab_idx, (oe_col, tab) in enumerate(zip(oe_columns, question_tabs)):
            with tab:
                q_idx = tab_idx + 1
                existing = coding_results.get(oe_col, {})
                question_key = f"question_{oe_col}"
                question_text = st.text_area("Question text", value=existing.get("question_text", st.session_state.get(question_key, "")), placeholder=f"Enter the survey question for {oe_col}.", height=100, key=f"question_text_{oe_col}")
                st.session_state[question_key] = question_text
                num_codes = st.number_input("Number of thematic codes required", min_value=2, max_value=50, value=int(existing.get("num_codes", 8)), step=1, key=f"num_codes_{oe_col}")
                responses = original_df[oe_col].fillna("").astype(str).tolist()

                if st.button("Generate Draft Codeframe", type="primary", key=f"gen_codeframe_{oe_col}"):
                    if not api_key or not api_key.strip():
                        st.error("Please configure your OpenAI API key.")
                    elif not question_text.strip():
                        st.error("Please enter the survey question text.")
                    elif not responses or all(not r.strip() for r in responses):
                        st.warning(f"No responses found in column '{oe_col}'.")
                    else:
                        with st.spinner(f"Generating draft codeframe for {oe_col}..."):
                            def run_codeframe():
                                return generate_draft_codeframe(get_client(api_key.strip()), question_text.strip(), responses, int(num_codes))
                            codeframe_df = handle_openai_errors(run_codeframe)
                        if codeframe_df is not None:
                            coding_results[oe_col] = {"question_text": question_text.strip(), "num_codes": int(num_codes), "codeframe_df": codeframe_df}
                            st.session_state["coding_results"] = coding_results
                            st.success(f"Draft codeframe for {oe_col} created with {len(codeframe_df)} codes.")

                if oe_col in coding_results and "codeframe_df" in coding_results[oe_col]:
                    st.caption("Review and edit the draft codeframe before applying it to responses.")
                    edited_codeframe = st.data_editor(coding_results[oe_col]["codeframe_df"], num_rows="dynamic", use_container_width=True, column_config={"Code": st.column_config.NumberColumn("Code", required=True, format="%d"), "Label": st.column_config.TextColumn("Label", required=True), "Description": st.column_config.TextColumn("Description", help="Coding definition used by the AI coder (not exported).")}, key=f"codeframe_editor_{oe_col}")
                    if st.button("Apply Codeframe", key=f"apply_codeframe_{oe_col}"):
                        cleaned_codeframe = ensure_standard_codes(edited_codeframe)
                        if not api_key or not api_key.strip():
                            st.error("Please configure your OpenAI API key.")
                        elif cleaned_codeframe.empty:
                            st.error("The codeframe must contain at least one code.")
                        else:
                            with st.spinner(f"Coding responses in {oe_col}..."):
                                def run_coding():
                                    coded_codes = apply_codeframe(get_client(api_key.strip()), question_text.strip(), cleaned_codeframe, responses)
                                    return coded_codes, build_frequency_table(coded_codes, cleaned_codeframe), cleaned_codeframe
                                result = handle_openai_errors(run_coding)
                            if result is not None:
                                coded_codes, frequency_df, cleaned_codeframe = result
                                coding_results[oe_col] = {"question_text": question_text.strip(), "num_codes": int(num_codes), "codeframe_df": cleaned_codeframe, "coded_codes": coded_codes, "frequency_df": frequency_df}
                                st.session_state["coding_results"] = coding_results
                                st.success(f"Coded {len(coded_codes)} response(s) for {oe_col}.")

                    if "coded_codes" in coding_results.get(oe_col, {}):
                        st.markdown(f"**SPSS-style variables for Q{q_idx}**")
                        preview_data = build_coded_data_df(original_df, id_columns, [oe_col], {oe_col: coding_results[oe_col]})
                        st.dataframe(preview_data, use_container_width=True)
                        st.markdown("**Frequency Table**")
                        st.dataframe(coding_results[oe_col]["frequency_df"], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        completed_oe_columns = [
            col
            for col in oe_columns
            if col in coding_results and "coded_codes" in coding_results[col]
        ]
        if completed_oe_columns:
            codeframe_export = build_codeframe_export(coding_results, completed_oe_columns)
            coded_data_export = build_coded_data_df(
                original_df,
                id_columns,
                completed_oe_columns,
                coding_results,
            )
            workbook_bytes = build_mr_workbook(
                original_df,
                codeframe_export,
                coded_data_export,
            )

            with st.expander("Deliverable Preview"):
                st.markdown("**OriginalData** — all uploaded variables unchanged")
                st.dataframe(original_df.head(5), use_container_width=True)
                st.markdown("**CodeFrame** — numeric codes and labels")
                st.dataframe(codeframe_export, use_container_width=True)
                st.markdown("**CodedData** — identifiers plus SPSS-style coded variables")
                st.dataframe(coded_data_export.head(5), use_container_width=True)

            st.markdown("---")
            st.subheader("Export Deliverable")
            st.download_button(
                label="Download Coding_Deliverable.xlsx",
                data=workbook_bytes,
                file_name="Coding_Deliverable.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )

with work_right:
    render_user_access_card()
    st.markdown(f"""<div class="ida-summary"><div class="ida-kicker">Project summary</div><h3 style="margin:.4rem 0">{uploaded_file.name}</h3><span class="ida-status">Ready</span><div class="ida-stat-grid"><div class="ida-stat"><b>{len(original_df)}</b><span>Rows</span></div><div class="ida-stat"><b>{len(all_columns)}</b><span>Columns</span></div><div class="ida-stat"><b>{len(st.session_state.get('oe_columns', []))}</b><span>Selected variables</span></div><div class="ida-stat"><b>{len(coded_oe_columns)}</b><span>Coded variables</span></div></div><p style="font-size:.76rem;color:#64748B;margin-bottom:.4rem">Replace source file</p>""", unsafe_allow_html=True)
    st.file_uploader("Upload another .xlsx file", type=["xlsx"], key="demo_upload", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

render_footer()
st.stop()

