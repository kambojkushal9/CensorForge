"""
CensorForge - Streamlit Web Interface
=======================================

A lightweight, cloud-deployable frontend for the CensorForge PII redaction
engine. Upload a .docx file, click "Redact", and download the sanitised copy.

Run locally with:
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import time
from io import BytesIO

# Page must be configured before any other st.* call.
st.set_page_config(
    page_title="CensorForge — PII Redaction Tool",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for a polished, professional look
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ---- Overall theme tweaks ---- */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    .main .block-container {
        max-width: 900px;
        padding-top: 2rem;
    }

    /* ---- Title styling ---- */
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 50%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.25rem;
    }
    .hero-subtitle {
        text-align: center;
        color: #a0aec0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* ---- Card containers ---- */
    .glass-card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(12px);
    }

    /* ---- Stat boxes ---- */
    .stat-row {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
    }
    .stat-box {
        flex: 1;
        background: rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .stat-box .num {
        font-size: 2rem;
        font-weight: 700;
        color: #00d2ff;
    }
    .stat-box .label {
        color: #a0aec0;
        font-size: 0.85rem;
    }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background: rgba(15,12,41,0.95);
    }

    /* ---- Hide Streamlit branding ---- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar — settings & info
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    confidence = st.slider(
        "Confidence Threshold",
        min_value=0.1,
        max_value=1.0,
        value=0.35,
        step=0.05,
        help=(
            "Minimum NER confidence score to accept a PII detection. "
            "Lower = higher recall but more false positives."
        ),
    )
    use_seed = st.checkbox("Reproducible output (fixed seed)", value=False)
    seed_value = 42 if use_seed else None

    st.markdown("---")
    st.markdown("### 📋 Supported PII Types")
    st.markdown(
        """
        - 👤 Full Names
        - 📧 Email Addresses
        - 📞 Phone Numbers
        - 🏢 Company Names
        - 📍 Physical Addresses
        - 🔢 SSNs
        - 💳 Credit Card Numbers
        - 🎂 Dates of Birth
        - 🌐 IP Addresses
        """
    )
    st.markdown("---")
    st.markdown(
        "<small style='color:#718096;'>Powered by Microsoft Presidio + spaCy + Faker</small>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
st.markdown('<div class="hero-title">🕵️ CensorForge</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Upload a <code>.docx</code> document and '
    "automatically redact PII with realistic fake data.</div>",
    unsafe_allow_html=True,
)

# File upload area
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Drop your .docx file here",
    type=["docx"],
    help="Only Microsoft Word (.docx) files are supported.",
)
st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Processing pipeline
# ---------------------------------------------------------------------------
if uploaded_file is not None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    if st.button("🚀 Redact PII", use_container_width=True, type="primary"):
        # -- Import here to avoid slow model load on page refresh --
        from censorforge_core import (
            CONFIDENCE_THRESHOLD,
            censorforge_process,
            create_analyzer,
            FakerMapper,
            process_docx,
        )
        import censorforge_core

        # Allow the sidebar slider to override the default threshold.
        censorforge_core.CONFIDENCE_THRESHOLD = confidence

        with st.spinner("Loading NLP models & analysing document…"):
            start_time = time.time()

            try:
                output_stream, detections, _, _ = censorforge_process(
                    uploaded_file.read(),
                    seed=seed_value,
                )
            except OSError as exc:
                if "en_core_web_lg" in str(exc):
                    st.error(
                        "❌ **spaCy model not found.** Please run:\n\n"
                        "```\npython -m spacy download en_core_web_lg\n```"
                    )
                    st.stop()
                raise
            except Exception as exc:
                st.error(f"❌ Processing failed: {exc}")
                st.stop()

            elapsed = time.time() - start_time

        # ---- Success metrics ----
        total_entities = len(detections)
        unique_types = len({d["entity_type"] for d in detections})

        st.success(f"✅ Redaction complete in **{elapsed:.1f}s**")

        # Stat cards
        st.markdown(
            f"""
            <div class="stat-row">
                <div class="stat-box">
                    <div class="num">{total_entities}</div>
                    <div class="label">PII Entities Found</div>
                </div>
                <div class="stat-box">
                    <div class="num">{unique_types}</div>
                    <div class="label">Unique PII Types</div>
                </div>
                <div class="stat-box">
                    <div class="num">{elapsed:.1f}s</div>
                    <div class="label">Processing Time</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Download button ----
        out_filename = uploaded_file.name.replace(".docx", "_redacted.docx")
        st.download_button(
            label="⬇️  Download Redacted Document",
            data=output_stream.getvalue(),
            file_name=out_filename,
            mime=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
            use_container_width=True,
        )

        # ---- Detections table ----
        if detections:
            st.markdown("### 🔍 Detections Log")
            df = pd.DataFrame(detections)
            df = df[["entity_type", "original", "replacement", "score"]]
            df.columns = ["PII Type", "Original", "Replaced With", "Confidence"]
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            # ---- Per-type breakdown ----
            st.markdown("### 📊 Breakdown by PII Type")
            type_counts = df["PII Type"].value_counts().reset_index()
            type_counts.columns = ["PII Type", "Count"]
            st.bar_chart(type_counts, x="PII Type", y="Count")

    st.markdown("</div>", unsafe_allow_html=True)

else:
    # Placeholder when no file is uploaded
    st.markdown(
        """
        <div class="glass-card" style="text-align:center; padding: 3rem 2rem;">
            <p style="font-size: 3rem; margin-bottom: 0.5rem;">📄</p>
            <p style="color: #a0aec0;">
                Upload a <code>.docx</code> file to get started.<br>
                Your data never leaves this server.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
