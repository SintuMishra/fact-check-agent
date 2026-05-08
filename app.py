import html
import logging
import os
import time
from typing import List, Dict, Any

import streamlit as st
from utils.pdf_extractor import PDFExtractor
from utils.claim_extractor import ClaimExtractor
from utils.verifier import ClaimVerifier
from utils.report_generator import ReportGenerator
from utils.helpers import setup_logging, validate_environment, format_confidence_score, get_status_color

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(page_title="Fact-Check Agent", page_icon="🔍", layout="wide")

# Professional, simple CSS with dark-theme friendly tokens
st.markdown("""
<style>
    :root {
        --card-bg: rgba(255,255,255,0.04);
        --card-bg-strong: rgba(255,255,255,0.06);
        --card-border: rgba(255,255,255,0.12);
        --muted-text: #a0a7b4;
        --main-text: #ffffff;
    }
    .block-container {
        max-width: 1100px;
        padding-top: 2.8rem;
        padding-bottom: 4rem;
        padding-left: 2.25rem;
        padding-right: 2.25rem;
        margin: 0 auto;
    }
    .app-shell {
        width: 100%;
        margin: 0 auto;
        padding: 0.45rem 0 1.75rem 0;
    }
    .main-title {
        font-size: clamp(2.2rem, 3vw, 2.9rem);
        font-weight: 700;
        letter-spacing: -0.04em;
        text-align: center;
        margin: 0;
        color: var(--main-text);
    }
    .subtitle {
        font-size: 1.18rem;
        text-align: center;
        margin: 0.9rem auto 0 auto;
        max-width: 780px;
        line-height: 1.6;
        color: rgba(255,255,255,0.92);
    }
    .hero-caption {
        text-align: center;
        font-size: 0.96rem;
        margin-top: 0.6rem;
        color: var(--muted-text);
    }
    .surface-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 20px;
        padding: 1.45rem;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.12);
    }
    .section-spacer {
        margin-top: 1.6rem;
        margin-bottom: 1.6rem;
    }
    .feature-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 18px;
        padding: 1.25rem 1.1rem;
        min-height: 156px;
        height: 100%;
    }
    .feature-title {
        font-size: 1.02rem;
        font-weight: 600;
        margin-bottom: 0.55rem;
        color: var(--main-text);
    }
    .feature-copy {
        font-size: 1rem;
        line-height: 1.6;
        color: var(--muted-text);
    }
    .section-title {
        font-size: 1.24rem;
        font-weight: 600;
        margin: 0 0 1rem 0;
        color: var(--main-text);
    }
    .step-card {
        border-radius: 16px;
        border: 1px solid var(--card-border);
        padding: 1rem;
        background: var(--card-bg);
        min-height: 144px;
        height: 100%;
    }
    .step-number {
        width: 2rem;
        height: 2rem;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
        color: #0f172a;
        background: #f8d57e;
    }
    .step-title {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.45rem;
        color: var(--main-text);
    }
    .step-copy {
        font-size: 0.98rem;
        line-height: 1.6;
        color: var(--muted-text);
    }
    .upload-copy {
        font-size: 1.02rem;
        line-height: 1.6;
        margin-bottom: 1rem;
        color: var(--muted-text);
    }
    .metric-card {
        background: var(--card-bg-strong);
        padding: 1.15rem;
        border-radius: 18px;
        border: 1px solid var(--card-border);
        text-align: left;
        min-height: 122px;
        height: 100%;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
        color: var(--main-text);
    }
    .metric-label {
        font-size: 0.98rem;
        color: var(--muted-text);
    }
    .result-card {
        background: var(--card-bg);
        padding: 1.45rem;
        border-radius: 20px;
        border: 1px solid var(--card-border);
        margin-bottom: 0.95rem;
    }
    .status-badge {
        padding: 0.38rem 0.85rem;
        border-radius: 999px;
        color: white;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
        letter-spacing: 0.02em;
        white-space: nowrap;
    }
    .confidence-bar {
        width: 100%;
        height: 8px;
        background-color: rgba(255,255,255,0.12);
        border-radius: 999px;
        overflow: hidden;
        margin: 0.55rem 0 0 0;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 999px;
    }
    .result-eyebrow {
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--muted-text);
        margin-bottom: 0.5rem;
    }
    .claim-text {
        font-size: 1.08rem;
        line-height: 1.7;
        margin-bottom: 0;
        color: var(--main-text);
    }
    .detail-block {
        border-radius: 16px;
        padding: 1rem 1.05rem;
        margin-top: 0.95rem;
        border: 1px solid var(--card-border);
        background: rgba(255,255,255,0.03);
    }
    .detail-label {
        font-size: 0.84rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        color: var(--muted-text);
        margin-bottom: 0.42rem;
    }
    .detail-value {
        color: var(--main-text);
        font-size: 1.02rem;
        line-height: 1.65;
    }
    .confidence-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
    }
    .confidence-value {
        font-size: 1rem;
        font-weight: 600;
        color: var(--main-text);
    }
    .confidence-note {
        font-size: 0.92rem;
        color: var(--muted-text);
    }
    .source-link {
        color: #8fb9ff;
        text-decoration: none;
        font-size: 0.96rem;
    }
    .source-link:hover {
        text-decoration: underline;
    }
    .section-caption {
        margin-top: -0.2rem;
        margin-bottom: 1.1rem;
        color: var(--muted-text);
        font-size: 0.98rem;
        line-height: 1.6;
    }
    .stExpander {
        border: 1px solid var(--card-border);
        border-radius: 14px;
        background: rgba(255,255,255,0.02);
        margin-bottom: 1rem;
    }
    .stExpander details {
        border-radius: 14px;
    }
    .stExpander div[role="button"] p {
        font-size: 0.98rem;
    }
    @media (max-width: 900px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .surface-card,
        .result-card {
            padding: 1.05rem;
        }
    }
</style>
""", unsafe_allow_html=True)


def _normalize_claim_text(claim: Any) -> str:
    if isinstance(claim, dict):
        text = claim.get("claim_text") or claim.get("claim") or ""
    else:
        text = str(claim) if claim is not None else ""
    text = text.strip()
    return text or "Claim text unavailable."


def _normalize_text_field(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _normalize_confidence(confidence: Any) -> int:
    if not isinstance(confidence, (int, float)):
        return 0
    if confidence <= 1:
        confidence *= 100
    return max(0, min(100, int(round(confidence))))


def _normalize_sources(sources: Any) -> List[Dict[str, str]]:
    if not isinstance(sources, list):
        return []

    normalized = []
    for index, source in enumerate(sources, 1):
        if isinstance(source, dict):
            title = _normalize_text_field(source.get("title"), f"Source {index}")
            url = _normalize_text_field(source.get("url"), "")
        else:
            raw_value = _normalize_text_field(source, "")
            title = raw_value or f"Source {index}"
            url = raw_value if raw_value.startswith(("http://", "https://")) else ""
        normalized.append({"title": title, "url": url})
    return normalized


def _get_corrected_fact_text(status: str, corrected_fact: Any) -> str:
    cleaned = _normalize_text_field(corrected_fact, "")
    if cleaned:
        return cleaned
    if status == "Verified":
        return "No correction needed."
    if status in {"Inaccurate", "False"}:
        return "Updated fact could not be determined from available sources."
    return "Updated fact could not be determined from available sources."

def main():
    # Validate environment
    env_valid = validate_environment()
    if not all(env_valid.values()):
        missing_keys = [k for k, v in env_valid.items() if not v]
        st.error(f"Missing required API keys: {', '.join(missing_keys)}")
        st.info("Please add your API keys to the .env file or Streamlit secrets. Check the README for setup instructions.")
        st.stop()

    st.markdown('<div class="app-shell">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">Fact-Check Agent</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Upload a PDF to check factual claims against current web sources.</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p class="hero-caption">Built for reviewing marketing, research, and business documents.</p>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    feature_columns = st.columns(3, gap="large")
    feature_items = [
        ("PDF Claim Extraction", "Finds measurable claims from uploaded documents."),
        ("Live Web Verification", "Checks claims against current web evidence."),
        ("Evidence-Based Report", "Shows status, confidence, corrections, and sources."),
    ]
    for column, (title, copy) in zip(feature_columns, feature_items):
        with column:
            st.markdown(
                f"""
                <div class="feature-card">
                    <div class="feature-title">{html.escape(title)}</div>
                    <div class="feature-copy">{html.escape(copy)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown('<div class="surface-card section-spacer">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">How it works</div>', unsafe_allow_html=True)
    step_columns = st.columns(4, gap="medium")
    step_items = [
        ("1", "Upload a PDF", "Start with a document containing factual statements."),
        ("2", "Extract factual claims", "Identify dates, statistics, figures, and measurable assertions."),
        ("3", "Verify with live sources", "Compare each claim against current web evidence."),
        ("4", "Download the report", "Export the final CSV with evidence-backed results."),
    ]
    for column, (number, title, copy) in zip(step_columns, step_items):
        with column:
            st.markdown(
                f"""
                <div class="step-card">
                    <div class="step-number">{html.escape(number)}</div>
                    <div class="step-title">{html.escape(title)}</div>
                    <div class="step-copy">{html.escape(copy)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="surface-card section-spacer">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Upload PDF</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="upload-copy">Upload a PDF containing statistics, dates, financial figures, technical claims, or measurable factual statements.</div>',
        unsafe_allow_html=True
    )
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a PDF document to analyze for factual claims",
        label_visibility="collapsed"
    )
    st.markdown('</div></div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        process_file(uploaded_file)

def process_file(uploaded_file):
    """Process the uploaded PDF file."""
    # Save file temporarily
    temp_path = os.path.join("uploads", f"temp_{uploaded_file.name}")
    os.makedirs("uploads", exist_ok=True)
    stage_text = st.empty()

    stage_text.info("Extracting PDF text...")
    with st.spinner("Extracting PDF text..."):
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        # Extract text
        extractor = PDFExtractor()
        pdf_result = extractor.extract_text(temp_path)

        if not pdf_result['success']:
            st.error(f"Failed to extract text: {pdf_result['error']}")
            os.remove(temp_path)
            return

        st.success(f"PDF processed successfully! Found {len(pdf_result['pages'])} pages.")

        with st.expander("Extracted PDF text preview"):
            preview_text = pdf_result['text'][:20000]
            st.text_area("PDF Text Preview", value=preview_text, height=320)
            if len(pdf_result['text']) > len(preview_text):
                st.caption("Preview truncated for display; full text was extracted successfully.")

    # Extract claims
    stage_text.info("Identifying factual claims...")
    with st.spinner("Identifying factual claims..."):
        claim_extractor = ClaimExtractor()
        claims = claim_extractor.extract_claims(pdf_result['text'], pdf_result['pages'])

    if not claims:
        st.warning("No factual claims found in the document. Try a document with statistics, dates, or measurable facts.")
        os.remove(temp_path)
        return

    st.success(f"Found {len(claims)} factual claims to verify.")

    # Verify claims
    verifier = ClaimVerifier()
    with st.spinner("Verifying claims against live sources..."):
        stage_text.info("Verifying claims against live sources...")
        verification_results = verifier.verify_claims(claims)
        progress_bar = st.progress(1.0)
        stage_text.info("Preparing report...")
        time.sleep(0.1)

    progress_bar.empty()
    stage_text.empty()

    # Display results
    display_results(verification_results)

    # Cleanup
    os.remove(temp_path)

def display_results(results: List[Dict[str, Any]]):
    """Display verification results."""

    # Summary metrics
    st.header("Summary")

    report_gen = ReportGenerator()
    summary = report_gen.generate_summary_report(results)
    reliability_percentage = summary["accuracy_percentage"]
    metric_columns = st.columns(5, gap="medium")
    metric_items = [
        (summary["total_claims"], "Total Claims"),
        (summary["verified"], "Verified"),
        (summary["inaccurate"], "Inaccurate"),
        (summary["false"], "False"),
        (f"{reliability_percentage:.0f}%", "Reliability %"),
    ]
    for column, (value, label) in zip(metric_columns, metric_items):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{html.escape(label)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Detailed results
    st.header("Verification Results")
    st.markdown(
        '<div class="section-caption">Each result includes the claim, status, confidence, corrected fact, explanation, and supporting sources. Some claims may still need manual review if live evidence is limited.</div>',
        unsafe_allow_html=True
    )

    for i, result in enumerate(results, 1):
        claim_text = _normalize_claim_text(result.get("claim"))
        status = _normalize_text_field(result.get("status"), "Unknown").title()
        confidence_value = _normalize_confidence(result.get("confidence"))
        corrected = _get_corrected_fact_text(status, result.get("corrected_fact"))
        explanation = _normalize_text_field(
            result.get("explanation"),
            "No explanation was returned for this claim."
        )
        sources = _normalize_sources(result.get("sources"))
        color = get_status_color(status)
        escaped_claim = html.escape(claim_text)
        escaped_corrected = html.escape(corrected)
        escaped_explanation = html.escape(explanation)

        st.markdown(f"""
        <div class="result-card">
            <div style="display:flex; justify-content:space-between; gap:0.75rem; align-items:flex-start; margin-bottom:0.9rem;">
                <div>
                    <div class="result-eyebrow">Claim {i}</div>
                    <div class="claim-text">{escaped_claim}</div>
                </div>
                <span class="status-badge" style="background-color: {color};">{html.escape(status)}</span>
            </div>
            <div class="detail-block" style="margin-top:0;">
                <div class="detail-label">Confidence</div>
                <div class="confidence-row">
                    <div class="confidence-value">{format_confidence_score(confidence_value)}</div>
                    <div class="confidence-note">Confidence score</div>
                </div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {confidence_value}%; background-color: {color};"></div>
                </div>
            </div>
            <div class="detail-block">
                <div class="detail-label">Corrected Fact</div>
                <div class="detail-value">{escaped_corrected}</div>
            </div>
            <div class="detail-block">
                <div class="detail-label">Explanation</div>
                <div class="detail-value">{escaped_explanation}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("View Sources"):
            if sources:
                for source in sources:
                    source_title = html.escape(source["title"])
                    source_url = source["url"]
                    if source_url:
                        if not source["title"] or source["title"].startswith("Source "):
                            source_title = html.escape(source_url)
                        st.markdown(
                            f'- <a href="{html.escape(source_url)}" class="source-link" target="_blank">{source_title}</a>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(f"- {source_title}")
            else:
                st.caption("No source links were returned for this claim.")

    st.caption(
        "Note: This tool assists with fact-checking by comparing claims against available web sources. "
        "Critical claims should still be reviewed manually."
    )

    # Export section
    st.header("Export Report")
    st.markdown(
        '<div class="section-caption">The report includes verification status, confidence, correction, explanation, and sources.</div>',
        unsafe_allow_html=True
    )

    csv_content = report_gen.generate_csv_report(results)
    filename = report_gen.get_report_filename()

    st.download_button(
        label="Download CSV Report",
        data=csv_content,
        file_name=filename,
        mime="text/csv",
        help="Download a detailed CSV report of all verification results"
    )

if __name__ == "__main__":
    main()
