<div align="center">

<img src="https://img.shields.io/badge/AMD-ROCm%207.2-ED1C24?style=for-the-badge&logo=amd&logoColor=white"/>
<img src="https://img.shields.io/badge/PyTorch-2.10.0-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white"/>
<img src="https://img.shields.io/badge/Qwen-2.5--7B-6B4FBB?style=for-the-badge"/>
<img src="https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
<img src="https://img.shields.io/badge/Status-In%20Progress-orange?style=for-the-badge"/>

<br/><br/>

# 🔍 auditiq

### AI-Driven Audit & Compliance Validator

*Automatically validate financial and regulatory documents against compliance frameworks using RAG + LLMs - powered by AMD GPUs*

<br/>

**Built for the [TCS & AMD AI Hackathon 2026](https://www.tcs.com) - Track 1: Agents**

</div>

---

## 📌 What is auditiq?

Compliance auditing is slow, expensive, and error-prone when done manually. Legal and compliance teams spend hours reading through dense financial and insurance documents to check whether they meet regulatory requirements like **GDPR**, **SOX**, and **AML/KYC** standards - and even then, things get missed.

**auditiq** changes that.

Upload any financial or insurance document, and auditiq automatically:
- Extracts and chunks the document intelligently
- Retrieves the most relevant compliance rules using semantic search
- Validates each section against those rules using a fine-tuned LLM
- Produces a structured audit report with **confidence scores**, **evidence quotes**, **identified gaps**, and **actionable recommendations** - all traceable back to the source document

No more manual cross-referencing. No more missed clauses. Just a clear, explainable audit report in seconds.

---

## 🎯 The Problem It Solves

| Pain Point | How auditiq Addresses It |
|------------|--------------------------|
| Manual compliance review takes days | Automated validation in seconds |
| Human reviewers miss subtle gaps | Semantic search catches relevant rules even without exact keyword match |
| Reports lack evidence trails | Every flag is linked back to the source document clause |
| Black-box AI decisions | Confidence scores + evidence quotes make every decision explainable |
| One-size-fits-all tools | Multi-framework support - GDPR, SOX, Insurance, AML/KYC |

---

## ✨ Key Features

- 📄 **Multi-format document ingestion** - PDF and plain text support via pdfplumber + pypdf
- 🔍 **Semantic rule retrieval** - FAISS vector search finds relevant rules even without exact keyword matches
- 🤖 **LLM-powered validation** - Qwen2.5-7B-Instruct reasons over document clauses and rules
- 📊 **Structured audit reports** - JSON output with status, confidence score, evidence, gap, and recommendation per rule
- 🏛️ **Multi-framework compliance** - GDPR, SOX, Insurance/Financial Services, AML/KYC rules out of the box
- ⚡ **AMD GPU accelerated** - built natively on ROCm 7.2, runs on AMD Instinct GPUs
- 🎨 **Gradio UI** - clean, interactive web interface for non-technical compliance teams *(coming Day 4)*
- 📑 **Downloadable PDF reports** - full audit trail exportable for stakeholders *(coming Day 3)*

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        auditiq Pipeline                          │
│                                                                  │
│   📄 Document (PDF / TXT)                                        │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────────┐                                            │
│   │ Document Parser │  pdfplumber + pypdf → clean text → chunks │
│   └────────┬────────┘                                            │
│            │                                                     │
│            ▼                                                     │
│   ┌──────────────────────┐                                       │
│   │  RAG Retrieval Layer │  bge-small-en → FAISS → Top-3 rules  │
│   └──────────┬───────────┘                                       │
│              │                                                   │
│              ▼                                                   │
│   ┌────────────────────────┐                                     │
│   │  LLM Validation Engine │  Qwen2.5-7B-Instruct               │
│   │  (Validator Agent)     │  → structured JSON output          │
│   └──────────┬─────────────┘                                     │
│              │                                                   │
│              ▼                                                   │
│   ┌──────────────────────┐                                       │
│   │   Audit Report       │  confidence score + evidence +       │
│   │   Generator          │  gap analysis + recommendations      │
│   └──────────┬───────────┘                                       │
│              │                                                   │
│              ▼                                                   │
│   ┌──────────────────────┐                                       │
│   │     Gradio UI        │  Upload → Validate → Download PDF    │
│   └──────────────────────┘                                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Qwen/Qwen2.5-7B-Instruct |
| **Embeddings** | BAAI/bge-small-en-v1.5 |
| **Vector Search** | FAISS (IndexFlatIP) |
| **Orchestration** | LangChain 0.3 |
| **Document Parsing** | pdfplumber + pypdf |
| **GPU Framework** | AMD ROCm 7.2 |
| **Deep Learning** | PyTorch 2.10.0 |
| **UI** | Gradio |
| **Report Generation** | fpdf2 |
| **Language** | Python 3.10+ |

---

## 📁 Project Structure

```
auditiq/
├── data/
│   ├── compliance_rules/
│   │   ├── gdpr_rules.json          # 5 GDPR rules
│   │   ├── sox_rules.json           # 4 SOX rules
│   │   └── insurance_rules.json     # 4 Insurance/AML rules
│   ├── sample_docs/                 # test documents
│   └── vector_store/                # FAISS index (auto-generated)
├── notebooks/
│   ├── 01_setup_test.ipynb          # environment + GPU verification
│   ├── 02_rag_pipeline.ipynb        # RAG + FAISS + LLM validation
│   ├── 03_agent_logic.ipynb         # LangChain agent + report gen
│   ├── 04_ui_gradio.ipynb           # Gradio UI
│   └── 05_final_demo.ipynb          # final demo
├── src/
│   ├── constants.py                 # model config, hyperparameters
│   ├── document_parser.py           # PDF/TXT ingestion + chunking
│   ├── embeddings.py                # sentence-transformer wrapper
│   ├── rag_pipeline.py              # FAISS index build + retrieval
│   ├── rule_loader.py               # compliance rules loader
│   ├── validator.py                 # LLM validation engine
│   ├── validator_agent.py           # LangChain agent (coming Day 3)
│   ├── confidence_scorer.py         # aggregate scoring (coming Day 3)
│   ├── report_generator.py          # PDF report gen (coming Day 3)
│   └── utils.py                     # Timer, GPU logger, helpers
├── outputs/
│   └── audit_reports/               # generated audit reports
├── logs/                            # daily metrics + run logs
├── requirements.txt
└── README.md
```

---

## ✅ Compliance Frameworks Supported

<details>
<summary><b>GDPR - General Data Protection Regulation (5 rules)</b></summary>

| Rule ID | Title | Severity |
|---------|-------|----------|
| GDPR-001 | Lawful basis for processing | HIGH |
| GDPR-002 | Data retention period | HIGH |
| GDPR-003 | Right to access and erasure | HIGH |
| GDPR-004 | Breach notification (72 hours) | CRITICAL |
| GDPR-005 | Data processor agreements | MEDIUM |

</details>

<details>
<summary><b>SOX - Sarbanes-Oxley Act 2002 (4 rules)</b></summary>

| Rule ID | Title | Severity |
|---------|-------|----------|
| SOX-001 | Internal control over financial reporting | CRITICAL |
| SOX-002 | Independent auditor attestation | HIGH |
| SOX-003 | Financial record retention (7 years) | HIGH |
| SOX-004 | Whistleblower protections | HIGH |

</details>

<details>
<summary><b>Insurance / Financial Services (4 rules)</b></summary>

| Rule ID | Title | Severity |
|---------|-------|----------|
| INS-001 | Clear policy terms disclosure | HIGH |
| INS-002 | Claims processing timeline | MEDIUM |
| INS-003 | AML/KYC compliance | CRITICAL |
| INS-004 | Capital adequacy requirements | CRITICAL |

</details>

---

## 📊 Sample Output

```json
{
  "validations": [
    {
      "rule_id": "GDPR-002",
      "framework": "GDPR",
      "severity": "HIGH",
      "status": "NON_COMPLIANT",
      "confidence_score": 91,
      "evidence": "The Company retains all customer personal data indefinitely for business analytics purposes.",
      "gap": "No retention period defined. Data cannot be stored indefinitely under GDPR.",
      "recommendation": "Define a specific retention period (e.g., 3 years post-transaction) and implement a deletion schedule."
    },
    {
      "rule_id": "GDPR-004",
      "framework": "GDPR",
      "severity": "CRITICAL",
      "status": "COMPLIANT",
      "confidence_score": 88,
      "evidence": "In the event of a breach, the Company will notify the supervisory authority within 72 hours.",
      "gap": null,
      "recommendation": null
    }
  ]
}
```

---

## 🚀 Getting Started

> **Note:** This project is optimized for AMD GPU environments with ROCm 7.2. It runs on AMD Instinct GPUs via the AMD Developer Cloud.

### 1. Clone the repo
```bash
git clone https://github.com/hardikjp7/auditiq.git
cd auditiq
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Jupyter and run notebooks in order
```
notebooks/01_setup_test.ipynb   → verify environment
notebooks/02_rag_pipeline.ipynb → build FAISS index + test validation
```

### 4. Run a quick validation test
```python
import sys
sys.path.insert(0, ".")

from src.document_parser import parse_document, chunk_document
from src.rag_pipeline import load_index
from src.validator import validate_full_document

doc    = parse_document("data/sample_docs/sample_contract.txt")
chunks = chunk_document(doc)
index, rule_texts = load_index()
result = validate_full_document(chunks, index, rule_texts)
print(f"Rules checked : {result['total_rules_checked']}")
print(f"Total tokens  : {result['total_tokens']}")
```

---

## 👤 Author

**Hardik Parmar**
AI/ML Engineer at TCS | AWS ML Associate

[![GitHub](https://img.shields.io/badge/GitHub-hardikjp7-181717?style=flat&logo=github)](https://github.com/hardikjp7)

---

## 🏆 Hackathon

This project was built as part of the **TCS & AMD AI Hackathon 2026**

- **Use case:** AGENTS_006 - AI-Driven Audit & Compliance Validator
- **Track:** Track 1 - Agents
- **Platform:** AMD Developer Cloud (ROCm 7.2 + Jupyter)
- **Build period:** June 8–12, 2026

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">
<sub>⭐ Star this repo if you find it useful - more features coming post-hackathon!</sub>
</div>
