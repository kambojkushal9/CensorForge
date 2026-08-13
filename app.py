"""
CensorForge - Premium Streamlit Web Interface
================================================

A stunning, SaaS-quality frontend for the CensorForge PII redaction engine.
Features glassmorphism dark theme, neon accents, Lottie animations, and
interactive Plotly charts.

Run locally with:
    python -m streamlit run app.py
"""

from __future__ import annotations

import json
import time
from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_lottie import st_lottie

# ══════════════════════════════════════════════════════════════════════════════
# Page Configuration — must be the FIRST Streamlit call
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CensorForge — PII Redaction Tool",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════════════════════
# Lottie Animation Helpers (with robust fallback)
# ══════════════════════════════════════════════════════════════════════════════

def _load_lottie_url(url: str) -> dict | None:
    """
    Fetch a Lottie JSON animation from a public URL.
    Returns None on any failure so the UI can degrade gracefully.
    """
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# Pre-load animations at module level (cached across reruns).
@st.cache_data(show_spinner=False)
def load_animations() -> dict:
    """Load all Lottie animations with multiple fallback URLs."""
    # Scanning / processing animation
    scanning_urls = [
        "https://assets2.lottiefiles.com/packages/lf20_xyadoh9h.json",
        "https://assets9.lottiefiles.com/packages/lf20_uwR49r.json",
        "https://lottie.host/4db68bbd-31f6-4cd8-84eb-189de081159f/IGmMCqhzpt.json",
    ]
    # Success / checkmark animation
    success_urls = [
        "https://assets1.lottiefiles.com/packages/lf20_jbrw3hcz.json",
        "https://assets9.lottiefiles.com/packages/lf20_lk80fpsm.json",
        "https://lottie.host/071cbed0-8063-405b-a04e-3a1e3419a944/VrMqpGJFaK.json",
    ]
    # Shield / security animation for hero
    hero_urls = [
        "https://assets5.lottiefiles.com/packages/lf20_cgjrfdzx.json",
        "https://assets2.lottiefiles.com/packages/lf20_ky24lkyk.json",
        "https://lottie.host/e65e4ecf-4c6c-4a46-8ccd-536ef3847bf7/uNMJlpJtKw.json",
    ]

    def _try_load(urls):
        for url in urls:
            result = _load_lottie_url(url)
            if result:
                return result
        return None

    return {
        "scanning": _try_load(scanning_urls),
        "success": _try_load(success_urls),
        "hero": _try_load(hero_urls),
    }


ANIMATIONS = load_animations()


# ══════════════════════════════════════════════════════════════════════════════
# Premium CSS — Dark Glassmorphism + Neon Accents
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* ── Import premium font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Global theme ── */
:root {
    --bg-primary: #0a0a1a;
    --bg-secondary: #12122a;
    --bg-card: rgba(255, 255, 255, 0.04);
    --border-glass: rgba(255, 255, 255, 0.08);
    --accent-cyan: #00d4ff;
    --accent-purple: #a855f7;
    --accent-pink: #ec4899;
    --accent-green: #22d3ee;
    --text-primary: #f0f0f5;
    --text-secondary: #8892a4;
    --text-muted: #5a6478;
    --glow-cyan: 0 0 20px rgba(0, 212, 255, 0.3), 0 0 40px rgba(0, 212, 255, 0.1);
    --glow-purple: 0 0 20px rgba(168, 85, 247, 0.3), 0 0 40px rgba(168, 85, 247, 0.1);
    --glow-green: 0 0 20px rgba(34, 211, 238, 0.3);
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stApp {
    background: var(--bg-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, header {visibility: hidden !important; display: none !important;}
.stDeployButton {display: none !important;}

/* ── Scrollbar styling ── */
::-webkit-scrollbar {width: 6px; height: 6px;}
::-webkit-scrollbar-track {background: var(--bg-primary);}
::-webkit-scrollbar-thumb {background: var(--accent-cyan); border-radius: 3px;}

/* ── Hero Section ── */
.hero-container {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    position: relative;
}
.hero-container::before {
    content: '';
    position: absolute;
    top: -50%;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(0,212,255,0.08) 0%, rgba(168,85,247,0.05) 40%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}
.hero-badge {
    display: inline-block;
    background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(168,85,247,0.15));
    border: 1px solid rgba(0,212,255,0.25);
    border-radius: 50px;
    padding: 0.4rem 1.2rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--accent-cyan);
    margin-bottom: 1rem;
    position: relative;
    z-index: 1;
}
.hero-title {
    font-size: 3.8rem;
    font-weight: 900;
    letter-spacing: -1.5px;
    line-height: 1.1;
    background: linear-gradient(135deg, #ffffff 0%, var(--accent-cyan) 40%, var(--accent-purple) 70%, var(--accent-pink) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.75rem;
    position: relative;
    z-index: 1;
    animation: titleGlow 3s ease-in-out infinite alternate;
}
@keyframes titleGlow {
    0% {filter: brightness(1) drop-shadow(0 0 0px transparent);}
    100% {filter: brightness(1.1) drop-shadow(0 0 15px rgba(0,212,255,0.2));}
}
.hero-subtitle {
    font-size: 1.15rem;
    color: var(--text-secondary);
    font-weight: 400;
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.6;
    position: relative;
    z-index: 1;
}
.hero-subtitle code {
    background: rgba(0,212,255,0.12);
    color: var(--accent-cyan);
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-weight: 500;
}

/* ── Glass Cards ── */
.glass-card {
    background: var(--bg-card);
    border: 1px solid var(--border-glass);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}
.glass-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,212,255,0.3), rgba(168,85,247,0.3), transparent);
}
.glass-card:hover {
    border-color: rgba(0,212,255,0.2);
    box-shadow: var(--glow-cyan);
    transform: translateY(-2px);
}

/* ── Upload Zone ── */
.upload-zone {
    background: linear-gradient(135deg, rgba(0,212,255,0.04), rgba(168,85,247,0.04));
    border: 2px dashed rgba(0,212,255,0.2);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    text-align: center;
    transition: var(--transition);
    margin: 1rem 0;
}
.upload-zone:hover {
    border-color: var(--accent-cyan);
    background: linear-gradient(135deg, rgba(0,212,255,0.08), rgba(168,85,247,0.08));
    box-shadow: var(--glow-cyan);
}

/* ── Stat Cards ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin: 1.5rem 0;
}
.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}
.stat-card::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    border-radius: 0 0 16px 16px;
}
.stat-card:nth-child(1)::after {background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));}
.stat-card:nth-child(2)::after {background: linear-gradient(90deg, var(--accent-purple), var(--accent-pink));}
.stat-card:nth-child(3)::after {background: linear-gradient(90deg, var(--accent-green), var(--accent-cyan));}
.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--glow-cyan);
    border-color: rgba(0,212,255,0.2);
}
.stat-icon {font-size: 1.8rem; margin-bottom: 0.5rem;}
.stat-value {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
}
.stat-label {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
    margin-top: 0.3rem;
}

/* ── Buttons ── */
div.stButton > button {
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple)) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.85rem 2rem !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.5px !important;
    transition: var(--transition) !important;
    box-shadow: 0 4px 15px rgba(0,212,255,0.25) !important;
    text-transform: uppercase !important;
}
div.stButton > button:hover {
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: var(--glow-cyan), 0 8px 25px rgba(0,212,255,0.35) !important;
}
div.stButton > button:active {
    transform: translateY(-1px) scale(0.98) !important;
}

/* ── Download Button ── */
div.stDownloadButton > button {
    background: linear-gradient(135deg, #22d3ee, #06b6d4) !important;
    color: #0a0a1a !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.85rem 2rem !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    transition: var(--transition) !important;
    box-shadow: 0 4px 15px rgba(34,211,238,0.3) !important;
}
div.stDownloadButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: var(--glow-green), 0 8px 25px rgba(34,211,238,0.4) !important;
}

/* ── File Uploader ── */
section[data-testid="stFileUploader"] {
    background: transparent !important;
}
div[data-testid="stFileUploaderDropzone"] {
    background: rgba(0,212,255,0.03) !important;
    border: 2px dashed rgba(0,212,255,0.2) !important;
    border-radius: 16px !important;
    transition: var(--transition) !important;
}
div[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--accent-cyan) !important;
    background: rgba(0,212,255,0.06) !important;
    box-shadow: inset 0 0 30px rgba(0,212,255,0.05) !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-glass) !important;
}
section[data-testid="stSidebar"] .stSlider > div > div {
    color: var(--accent-cyan) !important;
}

/* ── Dataframe ── */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border-glass) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ── Expander ── */
details[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 16px !important;
    transition: var(--transition) !important;
}
details[data-testid="stExpander"]:hover {
    border-color: rgba(0,212,255,0.15) !important;
}
details[data-testid="stExpander"] summary {
    font-weight: 600 !important;
}

/* ── Tabs ── */
div[data-baseweb="tab-list"] {
    gap: 0.5rem !important;
}
button[data-baseweb="tab"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 10px !important;
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    transition: var(--transition) !important;
}
button[data-baseweb="tab"]:hover {
    border-color: var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(168,85,247,0.15)) !important;
    border-color: var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
}

/* ── Section Headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 2rem 0 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-glass);
}
.section-header .icon {
    font-size: 1.5rem;
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(0,212,255,0.12), rgba(168,85,247,0.12));
    border-radius: 12px;
    border: 1px solid rgba(0,212,255,0.15);
}
.section-header .text {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.3px;
}

/* ── Processing overlay ── */
.processing-container {
    text-align: center;
    padding: 2rem;
}
.processing-text {
    color: var(--accent-cyan);
    font-size: 1.1rem;
    font-weight: 600;
    margin-top: 1rem;
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% {opacity: 1;}
    50% {opacity: 0.5;}
}

/* ── Success banner ── */
.success-banner {
    background: linear-gradient(135deg, rgba(34,211,238,0.08), rgba(0,212,255,0.04));
    border: 1px solid rgba(34,211,238,0.2);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    text-align: center;
    margin: 1rem 0;
    animation: fadeInUp 0.6s ease-out;
}
.success-banner .title {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--accent-green);
    margin-bottom: 0.3rem;
}
.success-banner .subtitle {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

@keyframes fadeInUp {
    from {opacity: 0; transform: translateY(20px);}
    to {opacity: 1; transform: translateY(0);}
}

/* ── Powered-by footer ── */
.powered-by {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.75rem;
    padding: 2rem 0 1rem;
    letter-spacing: 0.5px;
}
.powered-by span {
    color: var(--accent-cyan);
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    confidence = st.slider(
        "🎯 Confidence Threshold",
        min_value=0.1,
        max_value=1.0,
        value=0.35,
        step=0.05,
        help=(
            "Minimum NER confidence score to accept a PII detection. "
            "Lower = higher recall, more false positives. "
            "Higher = fewer false positives, may miss some PII."
        ),
    )

    use_seed = st.checkbox("🔒 Reproducible output (fixed seed)", value=False)
    seed_value = 42 if use_seed else None

    st.markdown("---")
    st.markdown("### 🎯 Supported PII Types")

    pii_types = {
        "👤": "Full Names",
        "📧": "Email Addresses",
        "📞": "Phone Numbers",
        "🏢": "Company Names",
        "📍": "Physical Addresses",
        "🔢": "SSNs",
        "💳": "Credit Cards",
        "🎂": "Dates of Birth",
        "🌐": "IP Addresses",
    }
    for icon, label in pii_types.items():
        st.markdown(f"&nbsp;&nbsp;{icon}&ensp;{label}")

    st.markdown("---")

    # Mini Lottie in sidebar (hero/security animation)
    if ANIMATIONS.get("hero"):
        st_lottie(ANIMATIONS["hero"], height=140, key="sidebar_anim")

    st.markdown(
        '<div class="powered-by">Built with <span>Presidio</span> · '
        "<span>spaCy</span> · <span>Faker</span></div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Hero Section
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">⚡ AI-Powered PII Protection</div>
    <div class="hero-title">🕵️ CensorForge</div>
    <div class="hero-subtitle">
        Upload a <code>.docx</code> document and automatically detect &amp; redact
        personally identifiable information with realistic fake data.
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Upload Section
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="section-header">'
    '<div class="icon">📄</div>'
    '<div class="text">Upload Document</div>'
    "</div>",
    unsafe_allow_html=True,
)

upload_col, info_col = st.columns([2, 1])

with upload_col:
    uploaded_file = st.file_uploader(
        "Drop your .docx file here",
        type=["docx"],
        help="Only Microsoft Word (.docx) files are supported.",
        label_visibility="collapsed",
    )

with info_col:
    st.markdown(
        """
        <div class="glass-card" style="padding:1.2rem 1.5rem; margin-top:0;">
            <p style="color:#8892a4; font-size:0.85rem; margin:0 0 0.5rem;">
                <strong style="color:#f0f0f5;">How it works</strong>
            </p>
            <p style="color:#5a6478; font-size:0.78rem; line-height:1.5; margin:0;">
                1. Upload a <code>.docx</code> file<br>
                2. Click <strong>Redact PII</strong><br>
                3. Download the sanitised copy<br><br>
                🔒 Your data never leaves this server.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Processing & Results
# ══════════════════════════════════════════════════════════════════════════════
if uploaded_file is not None:
    st.markdown("---")

    # Redact button
    if st.button("🚀  REDACT PII", use_container_width=True, type="primary"):

        # -- Lazy import to avoid slow model load on every page refresh --
        import censorforge_core

        censorforge_core.CONFIDENCE_THRESHOLD = confidence

        # ── Processing state with Lottie animation ──
        processing_placeholder = st.empty()

        with processing_placeholder.container():
            st.markdown('<div class="processing-container">', unsafe_allow_html=True)

            if ANIMATIONS.get("scanning"):
                st_lottie(
                    ANIMATIONS["scanning"],
                    height=200,
                    key="processing_anim",
                    loop=True,
                    quality="high",
                )
            else:
                # Fallback if Lottie fails to load
                st.markdown(
                    """
                    <div style="text-align:center; padding:2rem;">
                        <div style="font-size:4rem; animation: pulse 1.5s infinite;">🔍</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                '<div class="processing-text">'
                "🧠 Analysing document with NLP engine…"
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Run the actual pipeline ──
        start_time = time.time()
        try:
            output_stream, detections, _, _ = censorforge_core.censorforge_process(
                uploaded_file.read(),
                seed=seed_value,
            )
        except OSError as exc:
            processing_placeholder.empty()
            if "en_core_web_lg" in str(exc):
                st.error(
                    "❌ **spaCy model not found.** Run this command first:\n\n"
                    "```\npython -m spacy download en_core_web_lg\n```"
                )
            else:
                st.error(f"❌ Model error: {exc}")
            st.stop()
        except Exception as exc:
            processing_placeholder.empty()
            st.error(f"❌ Processing failed: {exc}")
            st.stop()

        elapsed = time.time() - start_time

        # ── Clear the processing animation ──
        processing_placeholder.empty()

        # ── Success animation + banner ──
        success_col1, success_col2, success_col3 = st.columns([1, 2, 1])
        with success_col2:
            if ANIMATIONS.get("success"):
                st_lottie(
                    ANIMATIONS["success"],
                    height=150,
                    key="success_anim",
                    loop=False,
                    quality="high",
                )

        total_entities = len(detections)
        unique_types = len({d["entity_type"] for d in detections})

        st.markdown(
            f"""
            <div class="success-banner">
                <div class="title">✅ Redaction Complete</div>
                <div class="subtitle">
                    Processed in <strong>{elapsed:.1f}s</strong> — 
                    <strong>{total_entities}</strong> PII entities redacted across
                    <strong>{unique_types}</strong> categories
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Stat Cards ──
        st.markdown(
            f"""
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-icon">🎯</div>
                    <div class="stat-value">{total_entities}</div>
                    <div class="stat-label">Entities Detected</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-value">{unique_types}</div>
                    <div class="stat-label">PII Categories</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">⚡</div>
                    <div class="stat-value">{elapsed:.1f}s</div>
                    <div class="stat-label">Processing Time</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Download Button ──
        st.markdown("<br>", unsafe_allow_html=True)
        out_filename = uploaded_file.name.replace(".docx", "_redacted.docx")

        dl_col1, dl_col2, dl_col3 = st.columns([1, 2, 1])
        with dl_col2:
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

        # ══════════════════════════════════════════════════════════════════
        # Interactive Charts (Plotly)
        # ══════════════════════════════════════════════════════════════════
        if detections:
            st.markdown(
                '<div class="section-header">'
                '<div class="icon">📊</div>'
                '<div class="text">Redaction Analytics</div>'
                "</div>",
                unsafe_allow_html=True,
            )

            df = pd.DataFrame(detections)

            # PII type counts
            type_counts = (
                df["entity_type"]
                .value_counts()
                .reset_index()
            )
            type_counts.columns = ["PII Type", "Count"]

            # Friendly labels
            friendly_names = {
                "PERSON": "👤 Names",
                "EMAIL_ADDRESS": "📧 Emails",
                "PHONE_NUMBER": "📞 Phone Numbers",
                "ORG": "🏢 Companies",
                "LOCATION": "📍 Addresses",
                "US_SSN": "🔢 SSNs",
                "CREDIT_CARD": "💳 Credit Cards",
                "DATE_OF_BIRTH": "🎂 Dates of Birth",
                "IP_ADDRESS": "🌐 IP Addresses",
            }
            type_counts["Label"] = type_counts["PII Type"].map(
                lambda x: friendly_names.get(x, x)
            )

            # Color palette matching our theme
            neon_colors = [
                "#00d4ff", "#a855f7", "#ec4899", "#22d3ee",
                "#f59e0b", "#10b981", "#6366f1", "#f43f5e", "#8b5cf6",
            ]

            chart_tab1, chart_tab2 = st.tabs(["🍩 Donut Chart", "📊 Bar Chart"])

            with chart_tab1:
                fig_donut = go.Figure(
                    data=[
                        go.Pie(
                            labels=type_counts["Label"],
                            values=type_counts["Count"],
                            hole=0.55,
                            marker=dict(
                                colors=neon_colors[: len(type_counts)],
                                line=dict(color="rgba(10,10,26,0.8)", width=3),
                            ),
                            textinfo="label+percent",
                            textfont=dict(size=12, color="#f0f0f5"),
                            hovertemplate=(
                                "<b>%{label}</b><br>"
                                "Count: %{value}<br>"
                                "Share: %{percent}<extra></extra>"
                            ),
                        )
                    ]
                )
                fig_donut.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#f0f0f5"),
                    showlegend=True,
                    legend=dict(
                        font=dict(size=12, color="#8892a4"),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    height=420,
                    margin=dict(t=20, b=20, l=20, r=20),
                    annotations=[
                        dict(
                            text=f"<b>{total_entities}</b><br><span style='font-size:12px;color:#8892a4'>Total</span>",
                            x=0.5,
                            y=0.5,
                            font=dict(size=28, color="#00d4ff"),
                            showarrow=False,
                        )
                    ],
                )
                st.plotly_chart(fig_donut, width="stretch")

            with chart_tab2:
                fig_bar = px.bar(
                    type_counts,
                    x="Label",
                    y="Count",
                    color="Label",
                    color_discrete_sequence=neon_colors,
                )
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#f0f0f5"),
                    showlegend=False,
                    xaxis=dict(
                        title="",
                        gridcolor="rgba(255,255,255,0.05)",
                        tickfont=dict(size=11),
                    ),
                    yaxis=dict(
                        title="Count",
                        gridcolor="rgba(255,255,255,0.05)",
                        tickfont=dict(size=11),
                    ),
                    height=420,
                    margin=dict(t=20, b=60, l=40, r=20),
                    bargap=0.3,
                )
                fig_bar.update_traces(
                    marker_line_color="rgba(0,0,0,0.3)",
                    marker_line_width=1,
                    hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
                )
                st.plotly_chart(fig_bar, width="stretch")

            # ══════════════════════════════════════════════════════════════
            # Detections Log
            # ══════════════════════════════════════════════════════════════
            st.markdown(
                '<div class="section-header">'
                '<div class="icon">🔍</div>'
                '<div class="text">Detections Log</div>'
                "</div>",
                unsafe_allow_html=True,
            )

            with st.expander(
                f"📋 View all {total_entities} detections", expanded=False
            ):
                display_df = df[
                    ["entity_type", "original", "replacement", "score"]
                ].copy()
                display_df.columns = [
                    "PII Type",
                    "Original Text",
                    "Replaced With",
                    "Confidence",
                ]
                display_df["Confidence"] = display_df["Confidence"].apply(
                    lambda x: f"{x:.0%}"
                )
                st.dataframe(
                    display_df,
                    hide_index=True,
                    height=400,
                )

else:
    # ══════════════════════════════════════════════════════════════════════
    # Empty State — no file uploaded yet
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("---")

    empty_col1, empty_col2, empty_col3 = st.columns([1, 2, 1])
    with empty_col2:
        st.markdown(
            """
            <div class="glass-card" style="text-align:center; padding:3rem 2rem;">
                <div style="font-size:4rem; margin-bottom:1rem; opacity:0.6;">📄</div>
                <p style="color:#8892a4; font-size:1rem; margin:0 0 0.5rem;">
                    <strong style="color:#f0f0f5;">No document uploaded yet</strong>
                </p>
                <p style="color:#5a6478; font-size:0.85rem; margin:0;">
                    Upload a <code style="background:rgba(0,212,255,0.12);
                    color:#00d4ff; padding:0.1rem 0.4rem; border-radius:4px;">.docx</code>
                    file above to get started.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Footer ──
st.markdown(
    '<div class="powered-by">'
    "Powered by <span>Microsoft Presidio</span> · <span>spaCy NLP</span> · "
    "<span>Faker</span> · <span>Streamlit</span>"
    "</div>",
    unsafe_allow_html=True,
)
