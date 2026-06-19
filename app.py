import io
import json

import pandas as pd
import streamlit as st
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError

st.set_page_config(page_title="IDA Open End Coding Tool", layout="wide")
st.title("IDA Open End Coding Tool")
st.caption("Professional market research open-end coding")

MODEL = "gpt-4o-mini"
CODING_BATCH_SIZE = 15
MAX_RESPONSE_CHARS = 500
MAX_RESPONSES_FOR_CODEFRAME = 200


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


def generate_draft_codeframe(
    client: OpenAI, question: str, responses: list[str], num_codes: int
) -> pd.DataFrame:
    sample = truncate_responses(responses)
    numbered = format_numbered_responses(sample)

    prompt = f"""You are a senior market research coder building a thematic codeframe.

Survey question:
{question}

Review these open-ended responses and create exactly {num_codes} distinct, mutually exclusive codes.
Each code needs a short label and a clear coding definition.

Return JSON:
{{
  "codeframe": [
    {{"code": "001 Product quality", "description": "Mentions product quality, durability, or craftsmanship."}},
    ...
  ]
}}

Rules:
- Provide exactly {num_codes} codes.
- Code labels must be unique and start with a three-digit number (001, 002, ...).
- Descriptions must explain what belongs in each code and what to exclude.
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
        code = str(item.get("code", "")).strip()
        description = str(item.get("description", "")).strip()
        if code:
            rows.append({"Code": code, "Description": description})

    if not rows:
        raise ValueError("The generated codeframe contained no usable codes.")

    return pd.DataFrame(rows)


def format_codeframe_for_prompt(codeframe_df: pd.DataFrame) -> str:
    lines = []
    for _, row in codeframe_df.iterrows():
        lines.append(f"- {row['Code']}: {row['Description']}")
    return "\n".join(lines)


def normalize_code(value: str, valid_codes: set[str]) -> str:
    cleaned = str(value).strip()
    if cleaned in valid_codes:
        return cleaned
    for code in valid_codes:
        if cleaned.lower() == code.lower():
            return code
    return ""


def normalize_secondary_codes(values, primary: str, valid_codes: set[str]) -> list[str]:
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
        if not code or code == primary or code in seen:
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
    valid_codes = set(codeframe_df["Code"].astype(str).tolist())
    codeframe_text = format_codeframe_for_prompt(codeframe_df)
    numbered = format_numbered_responses([r[:MAX_RESPONSE_CHARS] for r in responses])

    prompt = f"""You are a market research open-end coder applying a fixed codeframe.

Survey question:
{question}

Codeframe:
{codeframe_text}

For each response below, assign:
1. primary_code — exactly one code label from the codeframe (the dominant theme).
2. secondary_codes — zero or more additional code labels from the codeframe (multi-coded responses allowed).

Rules:
- Use code labels exactly as written in the codeframe.
- Secondary codes must differ from the primary code.
- Assign multiple secondary codes when the response clearly mentions several themes.
- Use "Uncoded" only if no codeframe code fits at all.

Return JSON:
{{
  "results": [
    {{"index": 1, "primary_code": "001 Product quality", "secondary_codes": ["002 Customer service"]}},
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
        primary = normalize_code(item.get("primary_code", "Uncoded"), valid_codes) or "Uncoded"
        secondary = normalize_secondary_codes(item.get("secondary_codes", []), primary, valid_codes)
        by_index[int(idx)] = {
            "primary_code": primary,
            "secondary_codes": secondary,
        }

    output = []
    for i in range(len(responses)):
        entry = by_index.get(i + 1, {"primary_code": "Uncoded", "secondary_codes": []})
        output.append(entry)
    return output


def apply_codeframe(
    client: OpenAI,
    question: str,
    codeframe_df: pd.DataFrame,
    responses: list[str],
) -> pd.DataFrame:
    primary_codes: list[str] = []
    secondary_codes: list[str] = []

    for start in range(0, len(responses), CODING_BATCH_SIZE):
        batch = responses[start : start + CODING_BATCH_SIZE]
        batch_results = apply_codeframe_batch(client, question, codeframe_df, batch)
        for item in batch_results:
            primary_codes.append(item["primary_code"])
            secondary_codes.append("; ".join(item["secondary_codes"]))

    return pd.DataFrame(
        {
            "Response": responses,
            "Primary Code": primary_codes,
            "Secondary Code": secondary_codes,
        }
    )


def build_frequency_table(coded_df: pd.DataFrame, codeframe_df: pd.DataFrame) -> pd.DataFrame:
    descriptions = dict(zip(codeframe_df["Code"], codeframe_df["Description"]))
    all_codes = list(codeframe_df["Code"].astype(str))
    if "Uncoded" not in all_codes:
        all_codes.append("Uncoded")
        descriptions["Uncoded"] = "Response could not be assigned to a codeframe code."

    primary_counts = {code: 0 for code in all_codes}
    secondary_counts = {code: 0 for code in all_codes}

    for _, row in coded_df.iterrows():
        primary = str(row["Primary Code"]).strip()
        if primary in primary_counts:
            primary_counts[primary] += 1

        secondary_raw = str(row["Secondary Code"]).strip()
        if secondary_raw:
            for sec in [part.strip() for part in secondary_raw.split(";") if part.strip()]:
                if sec in secondary_counts:
                    secondary_counts[sec] += 1

    rows = []
    for code in all_codes:
        primary = primary_counts[code]
        secondary = secondary_counts[code]
        rows.append(
            {
                "Code": code,
                "Description": descriptions.get(code, ""),
                "Primary Count": primary,
                "Secondary Count": secondary,
                "Total Mentions": primary + secondary,
            }
        )

    freq_df = pd.DataFrame(rows)
    return freq_df.sort_values("Total Mentions", ascending=False).reset_index(drop=True)


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
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
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("file_id") != file_id:
        st.session_state["file_id"] = file_id
        for key in ("codeframe_df", "coded_df", "frequency_df"):
            st.session_state.pop(key, None)

    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as exc:
        st.error(f"Could not read the Excel file: {exc}")
        st.stop()

    if "Response" not in df.columns:
        st.error('The uploaded file must contain a column named "Response".')
    else:
        st.subheader("Uploaded Data")
        st.dataframe(df, use_container_width=True)

        responses = df["Response"].fillna("").astype(str).tolist()

        st.subheader("Coding Setup")
        question_text = st.text_area(
            "Question text",
            value=st.session_state.get("question_text", ""),
            placeholder="Enter the survey question that was asked.",
            height=100,
        )
        num_codes = st.number_input(
            "Number of codes required",
            min_value=2,
            max_value=50,
            value=int(st.session_state.get("num_codes", 8)),
            step=1,
        )
        st.session_state["question_text"] = question_text
        st.session_state["num_codes"] = num_codes

        if st.button("Generate Draft Codeframe", type="primary"):
            if not api_key or not api_key.strip():
                st.error("Please enter your OpenAI API key in the sidebar.")
            elif not question_text.strip():
                st.error("Please enter the survey question text.")
            elif not responses or all(not r.strip() for r in responses):
                st.warning("No responses found to analyze.")
            else:
                with st.spinner("Generating draft codeframe..."):
                    def run_codeframe():
                        client = get_client(api_key.strip())
                        return generate_draft_codeframe(
                            client, question_text.strip(), responses, int(num_codes)
                        )

                    codeframe_df = handle_openai_errors(run_codeframe)
                    if codeframe_df is not None:
                        st.session_state["codeframe_df"] = codeframe_df
                        st.session_state.pop("coded_df", None)
                        st.session_state.pop("frequency_df", None)
                        st.success(f"Draft codeframe created with {len(codeframe_df)} codes.")

        if "codeframe_df" in st.session_state:
            st.subheader("Codeframe")
            st.caption("Review and edit the draft codeframe before applying it to responses.")
            edited_codeframe = st.data_editor(
                st.session_state["codeframe_df"],
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Code": st.column_config.TextColumn("Code", required=True),
                    "Description": st.column_config.TextColumn("Description", required=True),
                },
            )

            if st.button("Apply Codeframe"):
                if not api_key or not api_key.strip():
                    st.error("Please enter your OpenAI API key in the sidebar.")
                elif edited_codeframe.empty or edited_codeframe["Code"].astype(str).str.strip().eq("").all():
                    st.error("The codeframe must contain at least one code.")
                else:
                    with st.spinner("Coding responses..."):
                        def run_coding():
                            client = get_client(api_key.strip())
                            coded_df = apply_codeframe(
                                client,
                                question_text.strip(),
                                edited_codeframe,
                                responses,
                            )
                            frequency_df = build_frequency_table(coded_df, edited_codeframe)
                            return coded_df, frequency_df

                        result = handle_openai_errors(run_coding)
                        if result is not None:
                            coded_df, frequency_df = result
                            st.session_state["codeframe_df"] = edited_codeframe
                            st.session_state["coded_df"] = coded_df
                            st.session_state["frequency_df"] = frequency_df
                            st.success(f"Coded {len(coded_df)} response(s).")

        if "coded_df" in st.session_state:
            st.subheader("Coded Data")
            st.dataframe(st.session_state["coded_df"], use_container_width=True)

            st.subheader("Frequency Table")
            st.dataframe(st.session_state["frequency_df"], use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Download Coded_Data.xlsx",
                    data=to_excel_bytes(st.session_state["coded_df"]),
                    file_name="Coded_Data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            with col2:
                st.download_button(
                    label="Download Frequency_Table.xlsx",
                    data=to_excel_bytes(st.session_state["frequency_df"]),
                    file_name="Frequency_Table.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
