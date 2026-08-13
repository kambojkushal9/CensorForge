# 🛡️ CensorForge — PII Redaction Tool

> **Automatically detect and redact Personally Identifiable Information (PII) in `.docx` documents, replacing sensitive data with realistic fake substitutes.**

CensorForge combines **Microsoft Presidio** (backed by the `en_core_web_lg` spaCy NER model) for high-accuracy entity recognition with **Faker** for realistic data substitution. Rather than masking PII with asterisks — which destroys document readability — CensorForge replaces each entity with a contextually appropriate fake value (e.g., a real name → a fake name, a real SSN → a fake SSN). A lightweight **Streamlit** web interface makes the tool immediately deployable to cloud platforms like Render or Railway.

---

## ✨ Features

| Capability | Details |
|---|---|
| **9+ PII types** | Full names, emails, phone numbers, company names, physical addresses, SSNs, credit cards, dates of birth, IP addresses |
| **Realistic replacement** | Faker generates contextually appropriate fake data — not asterisks |
| **Consistent mapping** | The same real entity always maps to the same fake entity within a single document run |
| **Format preservation** | Processes paragraphs, tables, headers, and footers; retains bold/italic/font formatting at the run level |
| **Custom recognizers** | Adds regex-based pattern recognizers for SSN, credit card, DOB, and IP on top of Presidio's defaults |
| **Configurable threshold** | Sidebar slider adjusts the NER confidence threshold in real time |
| **Detections log** | Every replacement is logged with its entity type, original text, fake replacement, and confidence score |

---

## 🏗️ Architecture & Approach

```
┌──────────────┐     ┌────────────────────┐     ┌──────────────┐
│  .docx file  │────▶│  Presidio Analyzer  │────▶│ FakerMapper  │
│ (python-docx)│     │  (spaCy en_core_    │     │ (Faker lib)  │
│              │     │   web_lg NER +      │     │              │
│  paragraphs  │     │   custom regex      │     │  cache-backed│
│  + tables    │     │   recognizers)      │     │  mapping     │
└──────────────┘     └────────────────────┘     └──────┬───────┘
                                                       │
                                                       ▼
                                               ┌──────────────┐
                                               │  Redacted     │
                                               │  .docx file   │
                                               └──────────────┘
```

### Processing Pipeline

1. **Document Parsing**: `python-docx` reads the `.docx` and iterates over every paragraph (in body, tables, headers, and footers).
2. **Text Extraction**: For each paragraph, run-level text is concatenated into a single string (preserving the run boundaries for later formatting restoration).
3. **PII Detection**: The concatenated text is passed to Presidio's `AnalyzerEngine`, which uses spaCy's `en_core_web_lg` transformer-based NER pipeline plus custom regex recognizers for structured PII (SSN, credit card, etc.).
4. **Overlap Resolution**: When multiple recognizers detect overlapping spans, the highest-confidence detection wins.
5. **Fake Substitution**: Each detected entity is looked up in `FakerMapper`, which maintains a `(entity_type, original_text) → fake_text` cache. This ensures referential consistency — if "John Smith" appears 10 times, it's replaced with the same fake name everywhere.
6. **Run Redistribution**: The redacted text is proportionally redistributed back across the original runs, preserving each run's XML formatting properties (bold, italic, font, size, colour).
7. **Output**: The modified `Document` object is saved to a new `.docx` byte stream.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- ~500 MB disk space for the spaCy model

### Installation

```bash
# Clone and enter the project
cd CensorForge

# Install Python dependencies
pip install -r requirements.txt

# Download the spaCy NER model (required)
python -m spacy download en_core_web_lg

# Launch the web interface
streamlit run app.py
```

The app opens at `http://localhost:8501`. Upload a `.docx`, click **Redact PII**, and download the sanitised copy.

### Command-Line Usage

You can also use the core engine directly in Python:

```python
from censorforge_core import censorforge_process

with open("Red Herring Prospectus.docx", "rb") as f:
    output_stream, detections, _, _ = censorforge_process(f.read())

with open("Redacted_Prospectus.docx", "wb") as f:
    f.write(output_stream.getvalue())

for d in detections[:5]:
    print(f"{d['entity_type']:20s} | {d['original']:30s} → {d['replacement']}")
```

---

## ☁️ Cloud Deployment (Render / Railway)

### Render

1. Create a **Web Service** pointing to this repo.
2. Set **Build Command**: `pip install -r requirements.txt && python -m spacy download en_core_web_lg`
3. Set **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

### Railway

1. Connect this repo as a new project.
2. Add a `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```
3. Add a build step in `railway.json` or `nixpacks.toml` to install the spaCy model.

---

## ⚖️ Tradeoffs

| Decision | Tradeoff |
|---|---|
| **Confidence threshold = 0.35** | A low threshold maximises recall (catching more PII) at the cost of more false positives. The sidebar slider lets users tune this per-document. |
| **spaCy `en_core_web_lg`** | The large model (~560 MB) gives significantly better NER accuracy than `en_core_web_sm`, but increases cold-start time and memory usage. |
| **Proportional run redistribution** | Preserves formatting well for most documents, but if a PII entity spans multiple runs with *different* formatting (e.g., half bold, half italic), the replacement text may not perfectly mirror the split. This is an inherent limitation of the python-docx run model. |
| **Single-language (English)** | Presidio supports multilingual analysis, but this implementation is English-only for simplicity. Extending to other languages requires adding spaCy models for those languages. |
| **No GPU required** | The spaCy NER pipeline runs on CPU, which is more portable but slower on very large documents. |

---

## 🎯 False Positives

False positives occur when the NER model or regex recognizer incorrectly identifies non-PII text as PII. Common sources:

| Source | Example | Mitigation |
|---|---|---|
| **Generic nouns as ORG** | "Order", "Ticket", "Section" flagged as company names | spaCy's `en_core_web_lg` has good contextual awareness, but short capitalised words in isolation can still trigger ORG detection. Raising the confidence threshold to 0.5+ reduces these. |
| **Legal/financial jargon** | "Act", "Board", "Commission" | These are often legitimate organisation references in a prospectus. Context-dependent — may actually be correct detections. |
| **Dates as DOB** | An incorporation date flagged as DATE_OF_BIRTH | The DOB regex recognizer has a moderate score (0.50); most of these are filtered by the threshold. |
| **Section numbers as SSN** | "123-45-6789"-shaped section references | Unlikely in natural text but possible in structured documents. The regex score is set high (0.85) because the format is highly specific. |

**How to reduce false positives:**
1. Increase the `CONFIDENCE_THRESHOLD` in `censorforge_core.py` or via the sidebar slider.
2. Add a deny-list of known non-PII terms to filter out (e.g., `["Order", "Ticket", "Section"]`).
3. Post-filter results by checking entity context (surrounding words).

---

## 🕳️ False Negatives

False negatives occur when the tool fails to detect actual PII. Common sources:

| Source | Example | Mitigation |
|---|---|---|
| **Uncommon name spellings** | Names from underrepresented cultures | `en_core_web_lg` is trained on diverse data but still has gaps. Fine-tuning on domain-specific data would help. |
| **Obfuscated PII** | "john dot smith at gmail" instead of "john.smith@gmail.com" | Regex patterns look for standard formats. Add custom recognizers for obfuscated patterns. |
| **PII in images/charts** | An embedded image containing a phone number | `python-docx` only extracts text; OCR integration would be needed. |
| **Multi-line addresses** | Addresses split across multiple paragraphs | Each paragraph is analysed independently. Cross-paragraph analysis is not currently supported. |
| **Non-English PII** | Names or addresses in other languages | Only the English NLP model is loaded. |

---

## 🔧 Extending to a New PII Type

Adding support for a new PII category involves three steps:

### Step 1: Add a Presidio Recognizer

In `censorforge_core.py`, create a new pattern recognizer function:

```python
def _build_passport_recognizer() -> PatternRecognizer:
    """Matches US passport numbers (9 digits)."""
    patterns = [
        Pattern(
            name="us_passport",
            regex=r"\b\d{9}\b",
            score=0.60,
        ),
    ]
    return PatternRecognizer(
        supported_entity="US_PASSPORT",
        patterns=patterns,
        name="CensorForge Passport Recognizer",
    )
```

Then register it in `create_analyzer()`:

```python
analyzer.registry.add_recognizer(_build_passport_recognizer())
```

### Step 2: Add the Entity to TARGET_ENTITIES

```python
TARGET_ENTITIES = [
    ...
    "US_PASSPORT",  # ← Add here
]
```

### Step 3: Add a Faker Mapping

In the `FakerMapper.get_fake()` method, add a new branch:

```python
elif entity_type == "US_PASSPORT":
    fake_value = self.faker.bothify(text="#########")  # 9 random digits
```

That's it — the new PII type is now detected, replaced with fake data, and logged in the detections table.

---

## 📁 Project Structure

```
CensorForge/
├── app.py                    # Streamlit web interface
├── censorforge_core.py       # Core PII detection & redaction engine
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── evaluation_report.md      # Evaluation strategy & metrics template
└── Red Herring Prospectus.docx  # Sample input document
```

---

## 📜 License

This project is developed as a technical assignment and is provided as-is for evaluation purposes.
