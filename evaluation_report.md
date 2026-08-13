# 📊 CensorForge — Evaluation Report

## 1. Evaluation Strategy

### Approach: Sample-Based Manual Annotation

Automated evaluation of PII redaction is challenging because there is no pre-labelled ground truth for arbitrary documents. Instead, we use **Sample-Based Manual Annotation**, which is the gold standard for evaluating NER/PII systems in practice.

#### Methodology

1. **Sample Selection**: Select a representative set of pages/sections from the input document (`Red Herring Prospectus.docx`). We recommend sampling at least 5–10 pages covering different content types (narrative text, tables, headers, legal boilerplate).

2. **Ground Truth Annotation**: A human annotator manually reads each sampled section and marks every PII instance, recording:
   - The exact text span
   - The PII category (PERSON, EMAIL_ADDRESS, PHONE_NUMBER, ORG, LOCATION, US_SSN, CREDIT_CARD, DATE_OF_BIRTH, IP_ADDRESS)
   - The span's start and end character positions (optional, for precise matching)

3. **System Output Collection**: Run CensorForge on the same sections and export the detections log (available in the Streamlit UI or via the `censorforge_process()` API).

4. **Comparison**: Align the human annotations with the system detections and classify each into:
   - **True Positive (TP)**: System correctly detected a PII entity that the annotator also marked.
   - **False Positive (FP)**: System flagged something as PII that the annotator did NOT mark (i.e., not actual PII).
   - **False Negative (FN)**: The annotator marked a PII entity that the system MISSED.

---

## 2. Metrics

### Precision

**Precision** measures the proportion of system detections that are actually correct. High precision means the tool rarely flags non-PII as PII.

$$
\text{Precision} = \frac{TP}{TP + FP}
$$

A precision of 1.0 means every entity the system flagged was genuinely PII (zero false positives).

### Recall

**Recall** measures the proportion of actual PII entities that the system successfully detected. High recall means the tool rarely misses real PII.

$$
\text{Recall} = \frac{TP}{TP + FN}
$$

A recall of 1.0 means the system caught every single PII entity (zero false negatives).

### F1 Score

The **F1 Score** is the harmonic mean of Precision and Recall, providing a single balanced metric:

$$
F1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}
$$

---

## 3. Results Template

> **Instructions**: After performing the manual annotation and comparison, fill in the counts below for each PII type and compute the metrics.

### 3.1 Overall Results

| Metric | Count |
|---|---|
| **True Positives (TP)** | `___` |
| **False Positives (FP)** | `___` |
| **False Negatives (FN)** | `___` |

| Metric | Value |
|---|---|
| **Precision** | `TP / (TP + FP)` = `___` |
| **Recall** | `TP / (TP + FN)` = `___` |
| **F1 Score** | `2 × P × R / (P + R)` = `___` |

### 3.2 Per-Entity-Type Breakdown

| PII Type | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| PERSON | `___` | `___` | `___` | `___` | `___` | `___` |
| EMAIL_ADDRESS | `___` | `___` | `___` | `___` | `___` | `___` |
| PHONE_NUMBER | `___` | `___` | `___` | `___` | `___` | `___` |
| ORG | `___` | `___` | `___` | `___` | `___` | `___` |
| LOCATION | `___` | `___` | `___` | `___` | `___` | `___` |
| US_SSN | `___` | `___` | `___` | `___` | `___` | `___` |
| CREDIT_CARD | `___` | `___` | `___` | `___` | `___` | `___` |
| DATE_OF_BIRTH | `___` | `___` | `___` | `___` | `___` | `___` |
| IP_ADDRESS | `___` | `___` | `___` | `___` | `___` | `___` |

---

## 4. Analysis & Discussion

### 4.1 Confidence Threshold Impact

The confidence threshold (`CONFIDENCE_THRESHOLD` in `censorforge_core.py`, default: 0.35) directly controls the Precision–Recall tradeoff:

| Threshold | Expected Effect |
|---|---|
| **0.2 – 0.3** | High recall, lower precision. Catches more PII but may flag generic nouns (e.g., "Order") as ORG. |
| **0.35 – 0.5** | Balanced. Good default for most documents. |
| **0.5 – 0.7** | High precision, lower recall. Very few false positives but may miss some PII with ambiguous context. |
| **0.7 – 1.0** | Very conservative. Only the most confident detections are kept. |

> **Recommendation**: For sensitive documents (legal, financial), start with a lower threshold (0.3) and manually review the detections log. For general use, 0.4–0.5 provides a good balance.

### 4.2 Common False Positive Patterns

After reviewing the detections log, document recurring false positive patterns here:

| # | Pattern | Example | Suggested Fix |
|---|---|---|---|
| 1 | `___` | `___` | `___` |
| 2 | `___` | `___` | `___` |
| 3 | `___` | `___` | `___` |

### 4.3 Common False Negative Patterns

After reviewing the ground truth vs. system output, document missed PII here:

| # | Pattern | Example | Suggested Fix |
|---|---|---|---|
| 1 | `___` | `___` | `___` |
| 2 | `___` | `___` | `___` |
| 3 | `___` | `___` | `___` |

---

## 5. Limitations of This Evaluation

1. **Annotator Subjectivity**: What counts as "PII" can be subjective, especially for organisation names and locations that may or may not identify an individual.
2. **Sample Bias**: Evaluating on a single document (the Red Herring Prospectus) may not generalise to other document types (medical records, resumes, etc.).
3. **Partial Matches**: A detection that captures part of a name (e.g., "John" instead of "John Smith") is difficult to classify as TP or FP. We recommend counting partial matches as TP for recall and noting them separately.
4. **Consistency Not Measured**: This evaluation does not measure whether the same entity is consistently replaced with the same fake value across the document.

---

## 6. Reproducibility

To reproduce this evaluation:

```bash
# 1. Run CensorForge with a fixed seed for deterministic output
#    (Enable "Reproducible output" in the Streamlit sidebar, or pass seed=42)

# 2. Export the detections log from the Streamlit UI

# 3. Perform manual annotation on the same document sections

# 4. Compare and fill in the tables above
```

---

*Report template generated by CensorForge. Fill in the placeholder values (`___`) with your manual evaluation results.*
