# src/report_generator.py
import json
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

OUT_DIR = Path("/workspace/shared/audit_validator/outputs/audit_reports")

RISK_COLORS_HEX = {
    "CRITICAL": (220, 38,  38),
    "HIGH":     (234, 88,  12),
    "MEDIUM":   (202,138,   4),
    "LOW":      ( 22,163,  74),
}
STATUS_COLORS = {
    "COMPLIANT":       ( 22,163, 74),
    "NON_COMPLIANT":   (220, 38, 38),
    "PARTIAL":         (202,138,  4),
    "NOT_APPLICABLE":  (107,114,128),
}
STATUS_ICONS = {
    "COMPLIANT": "PASS", "NON_COMPLIANT": "FAIL",
    "PARTIAL": "PART",   "NOT_APPLICABLE": "N/A",
}
FW_COLORS = {
    "GDPR":                 ( 29, 78,216),
    "SOX":                  ( 21,128, 61),
    "HIPAA":                (126, 34,206),
    "PCI_DSS":              (194, 65, 12),
    "Insurance_Compliance": (  6, 95, 70),
}

def _sanitize(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    replacements = {
        '\u2014': '-', '\u2013': '-', '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"', '\u2022': '*', '\u2026': '...',
        '\u00a0': ' ', '\u2192': '->', '\u00b7': '*', '\u00e9': 'e',
        '\u00e0': 'a', '\u00e8': 'e', '\u00ea': 'e', '\u00f4': 'o',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode('latin-1', errors='replace').decode('latin-1')

def _trunc(text, n):
    text = _sanitize(str(text or ""))
    return text[:n] + ("..." if len(text) > n else "")


class AuditPDF(FPDF):
    def __init__(self, doc_name, generated):
        super().__init__()
        self.doc_name  = _sanitize(str(doc_name))
        self.generated = _sanitize(str(generated))
        self.set_margins(14, 18, 14)
        self.set_auto_page_break(auto=True, margin=18)

    def normalize_text(self, text: str) -> str:
        return super().normalize_text(_sanitize(str(text)))

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(15, 31, 61)
        self.rect(0, 0, 210, 11, "F")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(245,158,11)
        self.set_xy(14, 1.5)
        self.cell(80, 8, "auditiq - AI Compliance Audit Report")
        self.set_text_color(180,180,180)
        self.set_font("Helvetica", "", 8)
        self.set_xy(94, 1.5)
        self.cell(0, 8, _trunc(self.doc_name, 60), align="R")
        self.set_text_color(0,0,0)
        self.ln(4)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-13)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(150,150,150)
        self.cell(0, 8,
            f"Page {self.page_no()}  |  Generated {self.generated}  |  "
            "Powered by Qwen2.5-7B-Instruct on AMD Instinct MI300X  |  "
            "Built by @hardikjp7 - github.com/hardikjp7",
            align="C")
        self.set_text_color(0,0,0)

    def _score_bar(self, x, y, w, h, pct, color):
        self.set_fill_color(229,231,235)
        self.rect(x, y, w, h, "F")
        fill_w = max(1, w * pct / 100)
        self.set_fill_color(*color)
        self.rect(x, y, fill_w, h, "F")

    def _section_title(self, title):
        self.ln(5)
        self.set_fill_color(15,31,61)
        self.set_text_color(255,255,255)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 9, f"  {_sanitize(title)}", ln=True, fill=True)
        self.set_text_color(0,0,0)
        self.ln(2)

    def _kv(self, label, value, label_w=48):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(107,114,128)
        self.cell(label_w, 6, _sanitize(label))
        self.set_font("Helvetica", "", 9)
        self.set_text_color(17,24,39)
        self.multi_cell(0, 6, _sanitize(str(value)))

    # ── Cover page ────────────────────────────────────────────────────────────
    def cover(self, score, risk, total_rules, fw_scores, status_counts, metrics):
        self.add_page()
        risk_color = RISK_COLORS_HEX.get(risk, (107,114,128))

        self.set_fill_color(15,31,61)
        self.rect(0, 0, 210, 48, "F")
        self.set_fill_color(245,158,11)
        self.rect(14, 10, 28, 28, "F")
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(15,31,61)
        self.set_xy(14, 16)
        self.cell(28, 16, "iq", align="C")
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(255,255,255)
        self.set_xy(48, 10)
        self.cell(0, 12, "auditiq")
        self.set_font("Helvetica", "", 11)
        self.set_text_color(180,180,180)
        self.set_xy(48, 23)
        self.cell(0, 8, "AI-Powered Compliance Audit Report")
        self.set_font("Helvetica", "", 9)
        self.set_xy(48, 32)
        self.set_text_color(120,140,170)
        self.cell(0, 8, "Qwen2.5-7B-Instruct  +  RAG  +  FAISS  +  AMD ROCm MI300X")

        self.set_xy(14, 52)
        self.set_fill_color(248,250,252)
        self.set_draw_color(229,231,235)
        self.set_line_width(0.3)
        self.rect(14, 52, 182, 38, "FD")
        self.set_xy(20, 56)
        self._kv("Document:",   _trunc(self.doc_name, 70))
        self.set_xy(20, self.get_y())
        self._kv("Generated:",  self.generated)
        self.set_xy(20, self.get_y())
        self._kv("Model:",      "Qwen/Qwen2.5-7B-Instruct")
        self.set_xy(20, self.get_y())
        self._kv("Embeddings:", "BAAI/bge-small-en-v1.5  |  FAISS IndexFlatIP")

        # Score ring
        cx, cy, r_out, r_in = 170, 74, 22, 14
        self.set_fill_color(*risk_color)
        self.ellipse(cx-r_out, cy-r_out, r_out*2, r_out*2, "F")
        self.set_fill_color(255,255,255)
        self.ellipse(cx-r_in,  cy-r_in,  r_in*2,  r_in*2,  "F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*risk_color)
        self.set_xy(cx-r_in, cy-5)
        self.cell(r_in*2, 10, f"{score}%", align="C")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(107,114,128)
        self.set_xy(cx-r_out, cy+r_in+1)
        self.cell(r_out*2, 5, risk, align="C")

        # Overall score
        self.set_xy(14, 96)
        self._section_title("OVERALL COMPLIANCE SCORE")
        y = self.get_y()
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*risk_color)
        self.set_xy(14, y)
        self.cell(50, 16, f"{score}%")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(107,114,128)
        self.set_xy(64, y+4)
        self.cell(0, 8,
            f"Risk Level: {risk}  |  Rules Checked: {total_rules}  |  "
            f"Tokens: {metrics.get('total_tokens','-')}  |  "
            f"Avg Latency: {metrics.get('avg_latency_sec','-')}s/chunk")
        self._score_bar(14, y+18, 182, 8, score, risk_color)
        self.set_text_color(0,0,0)
        self.ln(30)

        # Framework scores
        self._section_title("COMPLIANCE SCORE BY FRAMEWORK")
        for fw, sc in fw_scores.items():
            color = FW_COLORS.get(fw, (107,114,128))
            y2 = self.get_y()
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*color)
            self.cell(52, 7, fw.replace("_"," "))
            self._score_bar(66, y2+1, 110, 5, sc, color)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*color)
            self.set_xy(178, y2)
            self.cell(18, 7, f"{sc}%", align="R")
            self.set_text_color(0,0,0)
            self.ln(8)

        # Status cards
        self.ln(2)
        self._section_title("VALIDATION STATUS SUMMARY")
        y3 = self.get_y()
        card_w   = 44
        card_data = [
            ("COMPLIANT",      STATUS_COLORS["COMPLIANT"]),
            ("NON_COMPLIANT",  STATUS_COLORS["NON_COMPLIANT"]),
            ("PARTIAL",        STATUS_COLORS["PARTIAL"]),
            ("NOT_APPLICABLE", STATUS_COLORS["NOT_APPLICABLE"]),
        ]
        for i, (st, col) in enumerate(card_data):
            cnt = status_counts.get(st, 0)
            xc  = 14 + i * (card_w+2)
            r = min(col[0]+220, 255)
            g = min(col[1]+180, 255)
            b = min(col[2]+180, 255)
            self.set_fill_color(r, g, b)
            self.rect(xc, y3, card_w, 22, "F")
            self.set_font("Helvetica", "B", 18)
            self.set_text_color(*col)
            self.set_xy(xc, y3+1)
            self.cell(card_w, 12, str(cnt), align="C")
            self.set_font("Helvetica", "", 7)
            self.set_text_color(80,80,80)
            self.set_xy(xc, y3+13)
            self.cell(card_w, 7, st.replace("_"," "), align="C")
        self.set_text_color(0,0,0)
        self.ln(30)

        # Stack footer
        self.ln(4)
        self.set_fill_color(243,244,246)
        self.rect(14, self.get_y(), 182, 14, "F")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(107,114,128)
        self.set_xy(18, self.get_y()+3)
        self.cell(0, 8,
            "Stack: PyTorch 2.10 + ROCm 7.2  |  LangChain  |  FAISS  |  "
            "sentence-transformers  |  Gradio (prototype)  |  FastAPI (production)  |  "
            "Built by @hardikjp7")
        self.set_text_color(0,0,0)

    # ── Detailed findings ─────────────────────────────────────────────────────
    def findings_page(self, validations):
        self.add_page()
        self._section_title("DETAILED COMPLIANCE FINDINGS  (deduplicated - one result per rule)")

        fw_groups = {}
        for v in validations:
            fw = v.get("framework","Unknown")
            fw_groups.setdefault(fw, []).append(v)

        for fw, items in fw_groups.items():
            fw_color = FW_COLORS.get(fw, (15,31,61))
            self.set_fill_color(*fw_color)
            self.set_text_color(255,255,255)
            self.set_font("Helvetica", "B", 9)
            self.cell(0, 8, f"  {fw.replace('_',' ')}", ln=True, fill=True)
            self.set_text_color(0,0,0)
            self.ln(1)

            for v in items:
                st     = v.get("status","")
                sev    = v.get("severity","")
                conf   = v.get("confidence_score", 0)
                st_col = STATUS_COLORS.get(st, (107,114,128))
                sev_col= RISK_COLORS_HEX.get(sev, (107,114,128))
                st_lbl = STATUS_ICONS.get(st, st[:4])

                # chunk reference
                chunk_id = v.get("chunk_id","")
                chunk_ref = ""
                if chunk_id:
                    try:
                        chunk_num = int(str(chunk_id).split("_chunk_")[-1]) + 1
                        chunk_ref = f"Sec.~{chunk_num}"
                    except Exception:
                        chunk_ref = ""

                y_row = self.get_y()
                self.set_font("Helvetica", "B", 9)
                self.set_text_color(15,31,61)
                self.cell(28, 7, v.get("rule_id",""))

                self.set_fill_color(*st_col)
                self.set_text_color(255,255,255)
                self.set_font("Helvetica", "B", 8)
                self.cell(16, 6, st_lbl, fill=True, align="C")
                self.cell(2, 6, "")

                self.set_fill_color(*sev_col)
                self.cell(18, 6, sev[:8], fill=True, align="C")
                self.cell(2, 6, "")

                # confidence bar
                cx2 = self.get_x()
                self.set_fill_color(229,231,235)
                self.rect(cx2, y_row+1, 32, 4, "F")
                self.set_fill_color(*st_col)
                self.rect(cx2, y_row+1, max(1, 32*conf/100), 4, "F")
                self.set_text_color(80,80,80)
                self.set_font("Helvetica", "", 8)
                self.set_xy(cx2+34, y_row)
                self.cell(20, 6, f"{conf}%")

                # chunk reference
                if chunk_ref:
                    self.set_text_color(150,150,150)
                    self.set_font("Helvetica", "I", 7.5)
                    self.cell(0, 6, f"[{chunk_ref}]", align="R")

                self.set_text_color(0,0,0)
                self.ln(8)

                if v.get("reasoning"):
                    self.set_font("Helvetica", "I", 8.5)
                    self.set_text_color(75,85,99)
                    self.set_x(28)
                    self.multi_cell(170, 5, _trunc(v.get("reasoning",""), 200))
                    self.set_text_color(0,0,0)

                if v.get("evidence"):
                    self.set_x(28)
                    self.set_font("Helvetica", "B", 8)
                    self.set_text_color(107,114,128)
                    self.cell(22, 5, "Evidence:")
                    self.set_font("Helvetica", "", 8)
                    self.set_text_color(30,30,30)
                    self.multi_cell(148, 5, _trunc(v.get("evidence",""), 240))

                if v.get("gap"):
                    self.set_x(28)
                    self.set_font("Helvetica", "B", 8)
                    self.set_text_color(185,28,28)
                    self.cell(22, 5, "Gap:")
                    self.set_font("Helvetica", "", 8)
                    self.set_text_color(185,28,28)
                    self.multi_cell(148, 5, _trunc(v.get("gap",""), 240))

                if v.get("recommendation"):
                    self.set_x(28)
                    self.set_font("Helvetica", "B", 8)
                    self.set_text_color(29,78,216)
                    self.cell(22, 5, "Action:")
                    self.set_font("Helvetica", "", 8)
                    self.set_text_color(29,78,216)
                    self.multi_cell(148, 5, _trunc(v.get("recommendation",""), 240))

                self.set_text_color(0,0,0)
                self.set_draw_color(229,231,235)
                self.set_line_width(0.2)
                self.line(14, self.get_y()+1, 196, self.get_y()+1)
                self.ln(4)
            self.ln(3)

    # ── Remediation plan ──────────────────────────────────────────────────────
    def remediation_page(self, issues):
        if not issues:
            return
        self.add_page()
        self._section_title("RISK-RANKED REMEDIATION ACTION PLAN")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(107,114,128)
        self.cell(0, 6,
            "Issues ranked by severity. Address CRITICAL immediately, "
            "HIGH within 30 days, MEDIUM within 90 days.", ln=True)
        self.ln(3)

        sev_order = {"CRITICAL":0,"HIGH":1,"MEDIUM":2}
        sorted_issues = sorted(issues,
            key=lambda x: sev_order.get(x.get("severity","MEDIUM"), 2))

        for idx, issue in enumerate(sorted_issues, 1):
            sev     = issue.get("severity","")
            sev_col = RISK_COLORS_HEX.get(sev,(107,114,128))
            fw      = issue.get("framework","")
            fw_col  = FW_COLORS.get(fw,(15,31,61))

            y_iss = self.get_y()
            self.set_fill_color(15,31,61)
            self.ellipse(14, y_iss, 8, 8, "F")
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(255,255,255)
            self.set_xy(14, y_iss)
            self.cell(8, 8, str(idx), align="C")

            self.set_xy(25, y_iss)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(15,31,61)
            self.cell(24, 8, issue.get("rule_id",""))

            self.set_fill_color(*fw_col)
            self.set_text_color(255,255,255)
            self.set_font("Helvetica", "B", 8)
            self.cell(36, 7, fw.replace("_"," ")[:16], fill=True, align="C")
            self.cell(2, 7, "")

            self.set_fill_color(*sev_col)
            self.cell(20, 7, sev, fill=True, align="C")
            self.cell(2, 7, "")

            st = issue.get("status","")
            st_col = STATUS_COLORS.get(st,(107,114,128))
            self.set_fill_color(*st_col)
            self.cell(28, 7, st.replace("_"," ")[:14], fill=True, align="C")
            self.set_text_color(0,0,0)
            self.ln(10)

            if issue.get("gap"):
                self.set_x(25)
                self.set_font("Helvetica", "B", 8)
                self.set_text_color(185,28,28)
                self.cell(18, 5, "Gap:")
                self.set_font("Helvetica", "", 8)
                self.multi_cell(153, 5, _trunc(issue.get("gap",""), 260))

            if issue.get("recommendation"):
                self.set_x(25)
                self.set_font("Helvetica", "B", 8)
                self.set_text_color(29,78,216)
                self.cell(18, 5, "Action:")
                self.set_font("Helvetica", "", 8)
                self.multi_cell(153, 5, _trunc(issue.get("recommendation",""), 260))

            self.set_text_color(0,0,0)
            self.set_draw_color(229,231,235)
            self.set_line_width(0.2)
            self.line(14, self.get_y()+2, 196, self.get_y()+2)
            self.ln(6)

    # ── Scoring methodology appendix ─────────────────────────────────────────
    def scoring_appendix(self, fw_scores, status_counts):
        self.add_page()
        self._section_title("APPENDIX A - COMPLIANCE SCORING METHODOLOGY")

        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(30,30,30)
        self.multi_cell(0, 6,
            "auditiq uses a weighted scoring model to calculate compliance scores. "
            "Each rule is evaluated once per document (deduplicated across all chunks). "
            "The overall score reflects a severity-weighted average of all rule outcomes.")
        self.ln(4)

        # Severity weights table
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(15,31,61)
        self.cell(0, 7, "1. Severity Weights", ln=True)
        self.ln(1)

        headers = ["Severity", "Weight", "Rationale"]
        col_w   = [40, 30, 112]
        self.set_fill_color(15,31,61)
        self.set_text_color(255,255,255)
        self.set_font("Helvetica", "B", 8)
        for h, w in zip(headers, col_w):
            self.cell(w, 7, h, border=1, fill=True)
        self.ln()

        rows = [
            ("CRITICAL", "3x", "Regulatory breach risk, immediate business impact"),
            ("HIGH",     "2x", "Significant compliance gap, near-term remediation needed"),
            ("MEDIUM",   "1x", "Process improvement required, lower immediate risk"),
        ]
        row_colors = [
            (254,226,226), (255,237,213), (254,252,232)
        ]
        self.set_font("Helvetica", "", 8)
        for row, bg in zip(rows, row_colors):
            self.set_fill_color(*bg)
            self.set_text_color(30,30,30)
            for val, w in zip(row, col_w):
                self.cell(w, 6, val, border=1, fill=True)
            self.ln()
        self.ln(4)

        # Status scores table
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(15,31,61)
        self.cell(0, 7, "2. Status Score Values", ln=True)
        self.ln(1)

        headers2 = ["Status", "Score", "Meaning"]
        col_w2   = [50, 25, 107]
        self.set_fill_color(15,31,61)
        self.set_text_color(255,255,255)
        self.set_font("Helvetica", "B", 8)
        for h, w in zip(headers2, col_w2):
            self.cell(w, 7, h, border=1, fill=True)
        self.ln()

        status_rows = [
            ("COMPLIANT",       "1.0", "All required clauses explicitly present"),
            ("PARTIAL",         "0.5", "Some requirements met, gaps identified"),
            ("NON_COMPLIANT",   "0.0", "Required clauses absent or contradicted"),
            ("NOT_APPLICABLE",  "N/A", "Rule not relevant to this document type"),
        ]
        st_bgs = [
            (220,252,231), (255,251,235), (254,226,226), (243,244,246)
        ]
        self.set_font("Helvetica", "", 8)
        for row, bg in zip(status_rows, st_bgs):
            self.set_fill_color(*bg)
            self.set_text_color(30,30,30)
            for val, w in zip(row, col_w2):
                self.cell(w, 6, val, border=1, fill=True)
            self.ln()
        self.ln(4)

        # Formula
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(15,31,61)
        self.cell(0, 7, "3. Score Calculation Formula", ln=True)
        self.ln(1)
        self.set_fill_color(248,250,252)
        self.set_draw_color(229,231,235)
        self.set_line_width(0.3)
        self.rect(14, self.get_y(), 182, 28, "FD")
        self.set_xy(20, self.get_y()+4)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(15,31,61)
        self.cell(0, 6, "Framework Score  =  sum(status_score x severity_weight) / sum(severity_weight)  x  100", ln=True)
        self.set_xy(20, self.get_y()+1)
        self.cell(0, 6, "Overall Score    =  weighted average of all framework scores", ln=True)
        self.set_xy(20, self.get_y()+1)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(107,114,128)
        self.cell(0, 6, "NOT_APPLICABLE rules are excluded from score calculation entirely.", ln=True)
        self.ln(10)

        # Confidence blending
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(15,31,61)
        self.cell(0, 7, "4. Confidence Score Calculation (Blended)", ln=True)
        self.ln(1)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30,30,30)
        self.multi_cell(0, 6,
            "Confidence scores are not purely LLM-generated opinions. auditiq blends two "
            "independent signals to produce a more reliable confidence estimate:")
        self.ln(2)
        self.set_x(20)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(15,31,61)
        self.cell(0, 6, "Confidence  =  (0.6 x LLM self-score)  +  (0.4 x Retrieval Similarity x 100)", ln=True)
        self.ln(2)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(107,114,128)
        self.multi_cell(0, 6,
            "  LLM self-score: Qwen2.5-7B assessment of evidence strength (0-100)\n"
            "  Retrieval Similarity: FAISS cosine similarity between document chunk and rule embedding\n"
            "  Rules below 0.60 similarity threshold are excluded entirely to reduce false positives")
        self.ln(4)

        # Dedup note
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(15,31,61)
        self.cell(0, 7, "5. Rule Deduplication", ln=True)
        self.ln(1)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30,30,30)
        self.multi_cell(0, 6,
            "Documents are split into overlapping chunks for processing. The same rule may be "
            "evaluated across multiple chunks. auditiq deduplicates by rule_id before scoring, "
            "retaining the most critical finding per rule: "
            "NON_COMPLIANT > PARTIAL > COMPLIANT > NOT_APPLICABLE. "
            "This ensures each control appears exactly once in the report.")
        self.ln(6)

        # Footer note
        self.set_fill_color(243,244,246)
        self.rect(14, self.get_y(), 182, 14, "F")
        self.set_xy(18, self.get_y()+3)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(107,114,128)
        self.cell(0, 8,
            "auditiq - TCS & AMD AI Hackathon 2026  |  Track 1 - Agents  |  "
            "Built by @hardikjp7  |  github.com/hardikjp7")


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def generate_pdf_report(doc_name: str, validations: list, score_data: dict,
                        metrics: dict = None) -> str:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path  = OUT_DIR / f"audit_report_{timestamp}.pdf"
    generated = datetime.now().strftime("%d %B %Y  %H:%M")

    pdf = AuditPDF(doc_name, generated)
    pdf.cover(
        score        = score_data.get("overall_score", 0),
        risk         = score_data.get("risk_level", "UNKNOWN"),
        total_rules  = score_data.get("total_rules", 0),
        fw_scores    = score_data.get("framework_scores", {}),
        status_counts= score_data.get("status_counts", {}),
        metrics      = metrics or {}
    )
    pdf.findings_page(validations)
    pdf.remediation_page(score_data.get("issues", []))
    pdf.scoring_appendix(
        score_data.get("framework_scores", {}),
        score_data.get("status_counts", {})
    )
    pdf.output(str(out_path))
    print(f"PDF report saved: {out_path}")
    return str(out_path)


def generate_json_report(doc_name: str, validations: list, score_data: dict) -> str:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path  = OUT_DIR / f"audit_report_{timestamp}.json"
    report = {
        "report_meta": {
            "document":   doc_name,
            "generated":  datetime.now().isoformat(),
            "model":      "Qwen/Qwen2.5-7B-Instruct",
            "embeddings": "BAAI/bge-small-en-v1.5",
            "frameworks": ["GDPR","SOX","HIPAA","PCI_DSS","Insurance_Compliance"]
        },
        "score_summary": score_data,
        "validations":   validations
    }
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"JSON report saved: {out_path}")
    return str(out_path)


def generate_html_report(doc_name: str, validations: list, score_data: dict) -> str:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path   = OUT_DIR / f"audit_report_{timestamp}.html"
    risk_colors = {
        "CRITICAL":"#dc2626","HIGH":"#ea580c","MEDIUM":"#ca8a04","LOW":"#16a34a"
    }
    status_colors = {
        "COMPLIANT":"#16a34a","NON_COMPLIANT":"#dc2626",
        "PARTIAL":"#ca8a04","NOT_APPLICABLE":"#6b7280"
    }
    status_icons = {
        "COMPLIANT":"✅","NON_COMPLIANT":"❌","PARTIAL":"⚠️","NOT_APPLICABLE":"➖"
    }
    risk_level    = score_data.get("risk_level","UNKNOWN")
    overall       = score_data.get("overall_score",0)
    fw_scores     = score_data.get("framework_scores",{})
    status_counts = score_data.get("status_counts",{})
    bar_color     = risk_colors.get(risk_level,"#6b7280")
    score_bar = f"""
    <div style="background:#e5e7eb;border-radius:10px;height:24px;width:100%;margin:10px 0;">
      <div style="background:{bar_color};width:{overall}%;height:24px;border-radius:10px;
                  display:flex;align-items:center;padding-left:10px;color:#fff;font-weight:bold;">
        {overall}%
      </div>
    </div>"""
    fw_bars = ""
    for fw, sc in fw_scores.items():
        c = "#16a34a" if sc>=80 else "#ca8a04" if sc>=60 else "#dc2626"
        fw_bars += f"""<div style="margin:8px 0;">
          <span style="font-weight:bold;display:inline-block;width:200px">{fw}</span>
          <div style="display:inline-block;background:#e5e7eb;border-radius:6px;
                      height:18px;width:300px;vertical-align:middle;">
            <div style="background:{c};width:{sc}%;height:18px;border-radius:6px;
                        display:inline-flex;align-items:center;padding-left:8px;
                        color:#fff;font-size:0.8em;font-weight:bold;">{sc}%</div>
          </div></div>"""
    status_cards = ""
    card_colors = {
        "COMPLIANT":"#16a34a","NON_COMPLIANT":"#dc2626",
        "PARTIAL":"#ca8a04","NOT_APPLICABLE":"#6b7280"
    }
    for st, cnt in status_counts.items():
        icon = status_icons.get(st,"")
        col  = card_colors.get(st,"#6b7280")
        status_cards += f"""<div style="display:inline-block;background:{col};color:#fff;
          border-radius:10px;padding:12px 24px;margin:6px;text-align:center;min-width:120px;">
          <div style="font-size:1.8em">{icon}</div>
          <div style="font-size:1.4em;font-weight:bold">{cnt}</div>
          <div style="font-size:0.8em">{st.replace('_',' ')}</div></div>"""
    validation_rows = ""
    for v in validations:
        st    = v.get("status","")
        color = status_colors.get(st,"#000")
        icon  = status_icons.get(st,"")
        chunk_id  = v.get("chunk_id","")
        chunk_ref = ""
        if chunk_id:
            try:
                chunk_num = int(str(chunk_id).split("_chunk_")[-1]) + 1
                chunk_ref = f"Sec.~{chunk_num}"
            except Exception:
                pass
        validation_rows += f"""<tr>
          <td><b>{v.get('rule_id','')}</b><br><small style="color:#9ca3af">{chunk_ref}</small></td>
          <td>{v.get('framework','')}</td>
          <td style="color:{risk_colors.get(v.get('severity',''),'#000')};font-weight:bold">{v.get('severity','')}</td>
          <td style="color:{color};font-weight:bold">{icon} {st}</td>
          <td>{v.get('confidence_score',0)}%</td>
          <td style="font-size:0.85em;font-style:italic">{str(v.get('reasoning',''))[:120]}</td>
          <td style="font-size:0.85em">{str(v.get('evidence',''))[:120]}</td>
          <td style="font-size:0.85em;color:#dc2626">{v.get('gap') or ''}</td>
          <td style="font-size:0.85em;color:#2563eb">{v.get('recommendation') or ''}</td></tr>"""
    issues = score_data.get("issues",[])
    sev_order = {"CRITICAL":0,"HIGH":1,"MEDIUM":2}
    sorted_issues = sorted(issues, key=lambda x: sev_order.get(x.get("severity","MEDIUM"),2))
    action_rows = ""
    for idx, issue in enumerate(sorted_issues, 1):
        sev   = issue.get("severity","")
        color = risk_colors.get(sev,"#000")
        action_rows += f"""<tr>
          <td style="text-align:center;font-weight:bold">{idx}</td>
          <td><b>{issue.get('rule_id','')}</b></td>
          <td>{issue.get('framework','')}</td>
          <td style="color:{color};font-weight:bold">{sev}</td>
          <td style="color:#ca8a04">{issue.get('status','')}</td>
          <td style="font-size:0.85em;color:#dc2626">{issue.get('gap') or ''}</td>
          <td style="font-size:0.85em;color:#2563eb">{issue.get('recommendation') or ''}</td></tr>"""
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>auditiq - Compliance Audit Report</title>
<style>
  body{{font-family:Arial,sans-serif;margin:30px;background:#f9fafb;color:#111;}}
  h1{{color:#1e3a5f;}} h2{{color:#374151;border-bottom:2px solid #e5e7eb;padding-bottom:6px;margin-top:30px;}}
  .badge{{display:inline-block;padding:6px 16px;border-radius:8px;color:#fff;font-weight:bold;font-size:1.2em;background:{risk_colors.get(risk_level,'#6b7280')};}}
  table{{border-collapse:collapse;width:100%;margin-bottom:20px;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);}}
  th{{background:#1e3a5f;color:#fff;padding:10px;text-align:left;}}
  td{{padding:10px;border-bottom:1px solid #e5e7eb;vertical-align:top;}}
  tr:hover{{background:#f0f4ff;}}
  .meta{{color:#6b7280;font-size:0.9em;margin-bottom:20px;}}
  .header-bar{{background:linear-gradient(135deg,#1e3a5f,#2563eb);color:#fff;padding:24px 30px;border-radius:12px;margin-bottom:24px;}}
</style></head><body>
<div class="header-bar">
  <h1 style="color:#fff;margin:0">🔍 auditiq</h1>
  <p style="margin:4px 0 0 0;opacity:0.85">AI-Powered Compliance Audit Report</p>
</div>
<p class="meta">📄 <b>{doc_name}</b> &nbsp;|&nbsp; 🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp;
🤖 Qwen2.5-7B on AMD ROCm MI300X &nbsp;|&nbsp;
Built by <a href="https://github.com/hardikjp7" target="_blank" style="color:#f59e0b;font-weight:600">@hardikjp7</a></p>
<h2>📊 Overall Score</h2>{score_bar}
<p>Risk Level: <span class="badge">{risk_level}</span></p>
<h2>🏛️ Framework Scores</h2>{fw_bars}
<h2>📋 Status Summary</h2>{status_cards}
<h2>🛠️ Remediation Action Plan</h2>
<table><tr><th>#</th><th>Rule</th><th>Framework</th><th>Severity</th><th>Status</th><th>Gap</th><th>Recommendation</th></tr>
{action_rows}</table>
<h2>📄 Detailed Results (deduplicated)</h2>
<table><tr><th>Rule ID</th><th>Framework</th><th>Severity</th><th>Status</th><th>Confidence</th><th>Reasoning</th><th>Evidence</th><th>Gap</th><th>Recommendation</th></tr>
{validation_rows}</table>
<p class="meta" style="text-align:center;margin-top:30px">
  auditiq - TCS & AMD AI Hackathon 2026 &nbsp;|&nbsp;
  Built by <a href="https://github.com/hardikjp7" target="_blank" style="color:#f59e0b;font-weight:600">@hardikjp7</a>
</p></body></html>"""
    out_path.write_text(html, encoding="utf-8")
    print(f"HTML report saved: {out_path}")
    return str(out_path)
