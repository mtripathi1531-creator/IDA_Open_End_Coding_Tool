import io
import json
import re

import pandas as pd
import streamlit as st
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError

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
CODING_BATCH_SIZE = 15
MAX_RESPONSE_CHARS = 500
MAX_RESPONSES_FOR_CODEFRAME = 200
CODE_OTHER = 96
CODE_UNCODED = 99
STANDARD_CODES = {CODE_OTHER: "Other", CODE_UNCODED: "Uncoded"}


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


try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error("OpenAI API Key not configured in Streamlit Secrets.")
    st.stop()

uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    st.markdown('<div class="ida-workflow">', unsafe_allow_html=True)

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

    all_columns = original_df.columns.tolist()
    if not all_columns:
        st.error("The uploaded file contains no columns.")
        st.stop()

    st.subheader("Uploaded Data")
    st.dataframe(original_df, use_container_width=True)

    st.subheader("Column Selection")
    st.caption(
        "Select respondent identifier columns and one or more open-end question columns to code."
    )

    default_oe = st.session_state.get("oe_columns", [])
    default_oe = [c for c in default_oe if c in all_columns]

    oe_columns = st.multiselect(
        "Open-end question columns",
        options=all_columns,
        default=default_oe,
        help="Select every open-end variable that should be coded.",
    )
    st.session_state["oe_columns"] = oe_columns

    id_options = [c for c in all_columns if c not in oe_columns]
    default_ids = st.session_state.get("id_columns", suggest_id_columns(all_columns, oe_columns))
    default_ids = [c for c in default_ids if c in id_options]

    id_columns = st.multiselect(
        "Respondent identifier columns",
        options=id_options,
        default=default_ids,
        help="These columns are included in the CodedData sheet (e.g. RespondentID, CaseID).",
    )
    st.session_state["id_columns"] = id_columns

    if not oe_columns:
        st.info("Select at least one open-end question column to begin coding.")
    else:
        if "coding_results" not in st.session_state:
            st.session_state["coding_results"] = {}

        coding_results = st.session_state["coding_results"]

        st.subheader("Coding Setup")
        question_tabs = st.tabs([f"{col}" for col in oe_columns])

        for tab_idx, (oe_col, tab) in enumerate(zip(oe_columns, question_tabs)):
            with tab:
                q_idx = tab_idx + 1
                existing = coding_results.get(oe_col, {})
                question_key = f"question_{oe_col}"
                question_default = existing.get("question_text", st.session_state.get(question_key, ""))

                question_text = st.text_area(
                    "Question text",
                    value=question_default,
                    placeholder=f"Enter the survey question for {oe_col}.",
                    height=100,
                    key=f"question_text_{oe_col}",
                )
                st.session_state[question_key] = question_text

                num_codes = st.number_input(
                    "Number of thematic codes required",
                    min_value=2,
                    max_value=50,
                    value=int(existing.get("num_codes", 8)),
                    step=1,
                    key=f"num_codes_{oe_col}",
                )

                responses = original_df[oe_col].fillna("").astype(str).tolist()

                if st.button("Generate Draft Codeframe", type="primary", key=f"gen_codeframe_{oe_col}"):
                    if not api_key or not api_key.strip():
                        st.error("Please enter your OpenAI API key in the sidebar.")
                    elif not question_text.strip():
                        st.error("Please enter the survey question text.")
                    elif not responses or all(not r.strip() for r in responses):
                        st.warning(f"No responses found in column '{oe_col}'.")
                    else:
                        with st.spinner(f"Generating draft codeframe for {oe_col}..."):

                            def run_codeframe():
                                client = get_client(api_key.strip())
                                return generate_draft_codeframe(
                                    client,
                                    question_text.strip(),
                                    responses,
                                    int(num_codes),
                                )

                            codeframe_df = handle_openai_errors(run_codeframe)
                            if codeframe_df is not None:
                                coding_results[oe_col] = {
                                    "question_text": question_text.strip(),
                                    "num_codes": int(num_codes),
                                    "codeframe_df": codeframe_df,
                                }
                                st.session_state["coding_results"] = coding_results
                                st.success(
                                    f"Draft codeframe for {oe_col} created with {len(codeframe_df)} codes."
                                )

                if oe_col in coding_results and "codeframe_df" in coding_results[oe_col]:
                    st.caption("Review and edit the draft codeframe before applying it to responses.")
                    edited_codeframe = st.data_editor(
                        coding_results[oe_col]["codeframe_df"],
                        num_rows="dynamic",
                        use_container_width=True,
                        column_config={
                            "Code": st.column_config.NumberColumn("Code", required=True, format="%d"),
                            "Label": st.column_config.TextColumn("Label", required=True),
                            "Description": st.column_config.TextColumn(
                                "Description",
                                help="Coding definition used by the AI coder (not exported).",
                            ),
                        },
                        key=f"codeframe_editor_{oe_col}",
                    )

                    if st.button("Apply Codeframe", key=f"apply_codeframe_{oe_col}"):
                        cleaned_codeframe = ensure_standard_codes(edited_codeframe)
                        if not api_key or not api_key.strip():
                            st.error("Please enter your OpenAI API key in the sidebar.")
                        elif cleaned_codeframe.empty:
                            st.error("The codeframe must contain at least one code.")
                        else:
                            with st.spinner(f"Coding responses in {oe_col}..."):

                                def run_coding():
                                    client = get_client(api_key.strip())
                                    coded_codes = apply_codeframe(
                                        client,
                                        question_text.strip(),
                                        cleaned_codeframe,
                                        responses,
                                    )
                                    frequency_df = build_frequency_table(coded_codes, cleaned_codeframe)
                                    return coded_codes, frequency_df, cleaned_codeframe

                                result = handle_openai_errors(run_coding)
                                if result is not None:
                                    coded_codes, frequency_df, cleaned_codeframe = result
                                    coding_results[oe_col] = {
                                        "question_text": question_text.strip(),
                                        "num_codes": int(num_codes),
                                        "codeframe_df": cleaned_codeframe,
                                        "coded_codes": coded_codes,
                                        "frequency_df": frequency_df,
                                    }
                                    st.session_state["coding_results"] = coding_results
                                    st.success(f"Coded {len(coded_codes)} response(s) for {oe_col}.")

                    if oe_col in coding_results and "coded_codes" in coding_results[oe_col]:
                        st.markdown(f"**SPSS-style variables for Q{q_idx}**")
                        preview_slots = max(
                            len(c) for c in coding_results[oe_col]["coded_codes"]
                        )
                        preview_cols = [f"Q{q_idx}_{slot}" for slot in range(1, preview_slots + 1)]
                        preview_data = build_coded_data_df(
                            original_df,
                            id_columns,
                            [oe_col],
                            {oe_col: coding_results[oe_col]},
                        )
                        st.dataframe(
                            preview_data[id_columns + preview_cols] if id_columns else preview_data,
                            use_container_width=True,
                        )

                        st.markdown("**Frequency Table**")
                        st.dataframe(
                            coding_results[oe_col]["frequency_df"],
                            use_container_width=True,
                        )

        coded_oe_columns = [
            col for col in oe_columns if col in coding_results and "coded_codes" in coding_results[col]
        ]
        if coded_oe_columns:
            st.subheader("Download Deliverable")
            st.caption(
                "Single Excel workbook with OriginalData, CodeFrame, and CodedData sheets "
                "(standard market research coding deliverable)."
            )

            codeframe_export = build_codeframe_export(coding_results, coded_oe_columns)
            coded_data_export = build_coded_data_df(
                original_df,
                id_columns,
                coded_oe_columns,
                coding_results,
            )
            workbook_bytes = build_mr_workbook(original_df, codeframe_export, coded_data_export)

            st.download_button(
                label="Download Coding_Deliverable.xlsx",
                data=workbook_bytes,
                file_name="Coding_Deliverable.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )

            with st.expander("Deliverable preview"):
                st.markdown("**OriginalData** — all uploaded variables unchanged")
                st.dataframe(original_df.head(5), use_container_width=True)
                st.markdown("**CodeFrame** — numeric codes and labels")
                st.dataframe(codeframe_export, use_container_width=True)
                st.markdown("**CodedData** — identifiers plus SPSS-style coded variables")
                st.dataframe(coded_data_export.head(5), use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="ida-footer">
        <p>Powered by Inside Data Analytics &nbsp;·&nbsp;
        <a href="https://www.insidedataanalytics.com" target="_blank" rel="noopener noreferrer">
            www.insidedataanalytics.com
        </a></p>
    </div>
    """,
    unsafe_allow_html=True,
)
