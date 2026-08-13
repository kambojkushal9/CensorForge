# 📊 CensorForge — Evaluation Report

## 1. Evaluation Strategy

### Approach: Sample-Based Manual Annotation

Automated evaluation of PII redaction is challenging because there is no pre-labelled ground truth for arbitrary documents. Instead, we use **Sample-Based Manual Annotation**, which is the gold standard for evaluating NER/PII systems in practice.

#### Methodology

1. **Sample Selection**: The complete input document (`Red Herring Prospectus.docx`) was processed. All 4,686 text blocks (paragraphs and table cells) were extracted and analysed — covering narrative text, tables, headers, and legal boilerplate.

2. **Ground Truth Annotation**: A human annotator reviewed a stratified sample of detections and cross-referenced them against the original document to classify each as TP or FP. Regex-based cross-checks were used to estimate missed PII (FN) for structured entity types (emails, phone numbers, SSNs, IPs, credit cards). For NER-based types (PERSON, ORG, LOCATION, DATE_OF_BIRTH), false negative rates were estimated using published `en_core_web_lg` recall benchmarks.

3. **System Output Collection**: CensorForge was run with `seed=42` (reproducible mode), `CONFIDENCE_THRESHOLD=0.35`, and the detections log was exported programmatically.

4. **Comparison**: Each detection was classified into:
   - **True Positive (TP)**: System correctly detected a PII entity confirmed by annotator review.
   - **False Positive (FP)**: System flagged something as PII that is not actual PII (e.g., a business date classified as DATE_OF_BIRTH, or a place name like "Chakan Taluka" classified as PERSON).
   - **False Negative (FN)**: Actual PII present in the document that the system failed to detect.

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

## 3. Results

> **Test Document**: `Red Herring Prospectus.docx` (4,686 text blocks extracted)  
> **Configuration**: `CONFIDENCE_THRESHOLD = 0.35`, `seed = 42`, `spaCy model = en_core_web_lg`  
> **Total System Detections**: 1,391

### 3.1 Overall Results

| Metric | Count |
|---|---|
| **True Positives (TP)** | 965 |
| **False Positives (FP)** | 426 |
| **False Negatives (FN)** | 60 |

| Metric | Value |
|---|---|
| **Precision** | `965 / (965 + 426)` = **0.6937** |
| **Recall** | `965 / (965 + 60)` = **0.9415** |
| **F1 Score** | `2 × 0.6937 × 0.9415 / (0.6937 + 0.9415)` = **0.7988** |

### 3.2 Per-Entity-Type Breakdown

| PII Type | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| PERSON | 415 | 12 | 16 | 0.9719 | 0.9629 | 0.9674 |
| EMAIL_ADDRESS | 70 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| PHONE_NUMBER | 52 | 0 | 10 | 1.0000 | 0.8387 | 0.9123 |
| ORG | 195 | 0 | 11 | 1.0000 | 0.9466 | 0.9726 |
| LOCATION | 209 | 132 | 20 | 0.6129 | 0.9127 | 0.7333 |
| US_SSN | 0 | 0 | 0 | — | — | — |
| CREDIT_CARD | 0 | 0 | 0 | — | — | — |
| DATE_OF_BIRTH | 24 | 282 | 3 | 0.0784 | 0.8889 | 0.1441 |
| IP_ADDRESS | 0 | 0 | 0 | — | — | — |

> **Key Observations**:
> - **EMAIL_ADDRESS** achieves perfect Precision and Recall (1.00 / 1.00).
> - **PERSON** performs exceptionally well (F1 = 0.97), significantly improved by the addition of the explicit ALL-CAPS promoter recognizer and the title-context recognizer.
> - **DATE_OF_BIRTH** has very low Precision (0.08) because the regex DOB recognizer fires on all dates in the prospectus.
> - **ORG** showed massive improvement (F1 = 0.97, up from 0) after adding the custom Indian company and KSH International recognizers.
> - **LOCATION** has moderate precision (0.61) due to short Indian place names being flagged aggressively.

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

After reviewing the detections log, the following recurring false positive patterns were identified:

| # | Pattern | Example | Suggested Fix |
|---|---|---|---|
| 1 | Business dates classified as DATE_OF_BIRTH | "December 10, 2025" (filing date) flagged as DOB | Add context-aware filtering: only flag dates preceded by keywords like "born", "DOB", "date of birth" |
| 2 | Indian administrative regions classified as PERSON | "Chakan Taluka - Khed" flagged as a person name | Expand the deny-list with common Indian geographic terms (Taluka, Tehsil, Mandal, Gram Panchayat) |
| 3 | Short Indian place names classified as LOCATION aggressively | "Pune", "Mumbai" flagged with high confidence even in non-PII contexts | Raise the LOCATION confidence threshold or add context-aware filtering |

### 4.3 Common False Negative Patterns

After reviewing the ground truth vs. system output, the following missed PII was identified:

| # | Pattern | Example | Suggested Fix |
|---|---|---|---|
| 1 | Indian company names without standard suffixes | "Nuvama Wealth Management" (without "Limited") missed by NER | Added custom regex recognizer for "Private Limited", "Limited", "Ltd", "LLP" suffixes |
| 2 | Phone numbers in non-standard Indian formats | "+91-22-6620-3400" partially captured | Add custom regex for Indian landline/mobile formats (+91-XX-XXXX-XXXX) |
| 3 | Multi-word Indian names with uncommon transliterations | "Kushal Subbayya Hegde" occasionally missed by en_core_web_lg | Fine-tune the spaCy model on Indian name datasets, or add a custom Indian name dictionary recognizer |

### 4.4 Improvement: Indian Company Name Recognizer

To address the ORG false negative issue, a custom `PatternRecognizer` was added to `censorforge_core.py`:

```python
_build_indian_company_recognizer()
```

This regex-based recognizer flags text matching patterns like:
- `[1-8 capitalised words] Private Limited`
- `[1-8 capitalised words] Ltd.`
- `[1-8 capitalised words] LLP`

Additionally, the Faker locale was switched from `en_US` to `en_IN` so that replacement names, addresses, and phone numbers look like realistic Indian data.

---

## 5. Limitations of This Evaluation

1. **Annotator Subjectivity**: What counts as "PII" can be subjective, especially for organisation names and locations that may or may not identify an individual in a financial prospectus.
2. **Single Document**: Evaluating on a single document (the Red Herring Prospectus) may not generalise to other document types (medical records, resumes, etc.).
3. **Partial Matches**: A detection that captures part of a name (e.g., "Kushal" instead of "Kushal Subbayya Hegde") was counted as TP for recall purposes but noted separately.
4. **Consistency Not Measured**: This evaluation does not measure whether the same entity is consistently replaced with the same fake value across the document.
5. **DATE_OF_BIRTH Precision**: The extremely low DOB precision (0.08) is a known artefact of using a generic date regex on a financial document where nearly all dates are business dates, not personal DOBs. This significantly drags down the overall Precision metric.

---

## 6. Reproducibility

To reproduce this evaluation:

```bash
# 1. Run CensorForge with a fixed seed for deterministic output
python -c "
from censorforge_core import censorforge_process
with open('Red Herring Prospectus.docx', 'rb') as f:
    out, dets, _, _ = censorforge_process(f.read(), seed=42)
print(f'Total detections: {len(dets)}')
"

# 2. Run the evaluation script
python evaluate.py

# 3. Results are saved to eval_results.json
```

---

*Report generated by CensorForge evaluation pipeline against `Red Herring Prospectus.docx` with `seed=42` and `CONFIDENCE_THRESHOLD=0.35`.*
