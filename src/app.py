# src/app.py — auditiq Gradio UI with Visual Dashboard

import sys
sys.path.insert(0, "/workspace/shared/audit_validator")

import gradio as gr
import shutil
import os
from src.validator_agent import AuditAgent
from src.charts import make_gauge_chart, make_framework_bar, make_status_pie

agent = None

def load_agent():
    global agent
    if agent is None:
        agent = AuditAgent()
    return agent

def run_audit(file_obj, max_chunks):
    try:
        ag = load_agent()

        ext      = os.path.splitext(file_obj.name)[1] if hasattr(file_obj, 'name') else ".txt"
        tmp_path = f"/tmp/uploaded_doc{ext}"
        shutil.copy(file_obj.name, tmp_path)

        result       = ag.run(tmp_path, max_chunks=int(max_chunks))
        score_data   = result["score_data"]
        validations  = result["validations"]
        metrics      = result["metrics"]

        # --- Charts ---
        gauge = make_gauge_chart(score_data["overall_score"], score_data["risk_level"])
        bars  = make_framework_bar(score_data["framework_scores"])
        pie   = make_status_pie(score_data["status_counts"])

        # --- Summary markdown ---
        risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}
        summary = f"""## 📊 Audit Complete

| Metric | Value |
|--------|-------|
| **Overall Score** | **{score_data['overall_score']}%** |
| **Risk Level** | {risk_emoji.get(score_data['risk_level'], '⚪')} **{score_data['risk_level']}** |
| **Rules Checked** | {score_data['total_rules']} |
| **Frameworks** | {len(score_data['framework_scores'])} |
| **Total Tokens** | {metrics['total_tokens']} |
| **Avg Latency/Chunk** | {metrics['avg_latency_sec']}s |

### 📋 Status Breakdown
"""
        icons = {"COMPLIANT": "✅", "NON_COMPLIANT": "❌",
                 "PARTIAL": "⚠️", "NOT_APPLICABLE": "➖"}
        for st, cnt in score_data["status_counts"].items():
            summary += f"- {icons.get(st,'')} **{st.replace('_',' ')}**: {cnt}\n"

        if score_data.get("critical_issues"):
            summary += f"\n### 🚨 Critical Issues ({len(score_data['critical_issues'])})\n"
            for i in score_data["critical_issues"]:
                summary += f"- `{i['rule_id']}`: {i['gap']}\n"

        # --- Table ---
        table_data = []
        for v in validations:
            icon = icons.get(v.get("status", ""), "")
            table_data.append([
                v.get("rule_id", ""),
                v.get("framework", ""),
                v.get("severity", ""),
                f"{icon} {v.get('status', '')}",
                f"{v.get('confidence_score', 0)}%",
                str(v.get("reasoning") or "")[:120],
                str(v.get("evidence", ""))[:100],
                str(v.get("gap") or ""),
                str(v.get("recommendation") or "")
            ])

        # Copy HTML to /tmp for Gradio
        tmp_html = "/tmp/auditiq_report.html"
        shutil.copy(result["html_report"], tmp_html)

        return (summary, gauge, bars, pie,
                table_data, tmp_html, "✅ Audit complete!")

    except Exception as e:
        import traceback
        empty_fig = make_gauge_chart(0, "CRITICAL")
        return (f"❌ Error: {str(e)}\n\n{traceback.format_exc()}",
                empty_fig, empty_fig, empty_fig,
                [], None, "❌ Failed")


# ─── Gradio UI ───────────────────────────────────────────────
with gr.Blocks(title="auditiq — AI Compliance Validator") as demo:

    gr.Markdown("""
    # 🔍 auditiq — AI Compliance Audit Validator
    **Powered by Qwen2.5-7B-Instruct + RAG + FAISS + AMD ROCm MI300X**
    *TCS & AMD AI Hackathon 2026 | Track 1 – Agents*
    ---
    Upload any financial, insurance, or policy document (PDF or TXT).
    auditiq validates it against **GDPR · SOX · HIPAA · PCI-DSS · Insurance** compliance rules
    and generates a detailed audit report with confidence scores, reasoning, and remediation plan.
    """)

    # ── Input row ──
    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(
                label="📄 Upload Document (PDF or TXT)",
                file_types=[".pdf", ".txt"]
            )
            max_chunks = gr.Slider(
                minimum=1, maximum=15, value=6, step=1,
                label="Max Chunks to Validate (higher = more thorough)"
            )
            audit_btn  = gr.Button("🚀 Run Compliance Audit", variant="primary", size="lg")
            status_box = gr.Textbox(label="Status", interactive=False)

        with gr.Column(scale=2):
            summary_out = gr.Markdown(value="*Upload a document and click Run Audit to begin.*")

    # ── Charts row ──
    gr.Markdown("---\n### 📈 Compliance Dashboard")
    with gr.Row():
        gauge_plot = gr.Plot(label="Overall Score")
        bar_plot   = gr.Plot(label="By Framework")
        pie_plot   = gr.Plot(label="Status Breakdown")

    # ── Results table ──
    gr.Markdown("---\n### 📄 Detailed Validation Results")
    results_table = gr.Dataframe(
        headers=["Rule ID", "Framework", "Severity", "Status",
                 "Confidence", "Reasoning", "Evidence", "Gap", "Recommendation"],
        datatype=["str"] * 9,
        wrap=True,
        interactive=False
    )

    # ── Download ──
    gr.Markdown("---")
    report_file = gr.File(label="📥 Download Full HTML Audit Report")

    # ── Wire up ──
    audit_btn.click(
        fn=run_audit,
        inputs=[file_input, max_chunks],
        outputs=[summary_out, gauge_plot, bar_plot, pie_plot,
                 results_table, report_file, status_box]
    )

    gr.Markdown("""
    ---
    **LLM:** Qwen/Qwen2.5-7B-Instruct &nbsp;|&nbsp;
    **Embeddings:** BAAI/bge-small-en-v1.5 &nbsp;|&nbsp;
    **Vector Store:** FAISS IndexFlatIP &nbsp;|&nbsp;
    **GPU:** AMD Instinct MI300X (206GB) via ROCm 7.2
    """)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True,
        allowed_paths=["/tmp"]
    )
