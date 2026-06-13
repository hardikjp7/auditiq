# src/validator_agent.py

from src.document_parser   import parse_document, chunk_document
from src.rag_pipeline      import load_index, retrieve_top_rules
from src.validator         import validate_full_document
from src.confidence_scorer import compute_overall_score
from src.report_generator  import generate_pdf_report, generate_html_report, generate_json_report
from src.constants         import CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RULES
from src.utils             import Timer
import time

class AuditAgent:
    def __init__(self):
        print("AuditAgent initializing...")
        self.index, self.rule_texts = load_index()
        print("AuditAgent ready.")

    def run(self, doc_path: str, max_chunks: int = None) -> dict:
        print(f"\n{'='*60}")
        print(f"Starting audit: {doc_path}")
        print(f"{'='*60}")

        with Timer("Document parse"):
            doc    = parse_document(doc_path)
            chunks = chunk_document(doc, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

        print(f"   Words: {doc['word_count']} | Chunks: {len(chunks)}")

        if max_chunks:
            chunks = chunks[:max_chunks]
            print(f"   (Limited to {max_chunks} chunks)")

        with Timer("Full RAG + LLM validation"):
            full_result = validate_full_document(
                chunks, self.index, self.rule_texts, top_k=TOP_K_RULES
            )

        # compute_overall_score runs dedup internally and returns
        # deduplicated_validations — use those for reports
        with Timer("Confidence scoring"):
            score_data = compute_overall_score(full_result["validations"])

        # Use deduplicated validations for all reports
        deduped_validations = score_data.pop("deduplicated_validations",
                                             full_result["validations"])

        with Timer("Report generation"):
            pdf_path  = generate_pdf_report(
                doc["filename"], deduped_validations, score_data,
                metrics=full_result
            )
            html_path = generate_html_report(
                doc["filename"], deduped_validations, score_data
            )
            json_path = generate_json_report(
                doc["filename"], deduped_validations, score_data
            )

        self._print_summary(score_data, full_result, pdf_path)

        return {
            "doc_name":    doc["filename"],
            "score_data":  score_data,
            "validations": deduped_validations,
            "metrics":     full_result,
            "pdf_report":  pdf_path,
            "html_report": html_path,
            "json_report": json_path
        }

    def _print_summary(self, score_data, metrics, pdf_path):
        print(f"\n{'='*60}")
        print(f"AUDIT COMPLETE")
        print(f"{'='*60}")
        print(f"  Overall Score  : {score_data['overall_score']}%")
        print(f"  Risk Level     : {score_data['risk_level']}")
        print(f"  Rules Checked  : {score_data['total_rules']}")
        print(f"  Total Tokens   : {metrics['total_tokens']}")
        print(f"  Avg Latency    : {metrics['avg_latency_sec']}s/chunk")
        print(f"\n  Framework Scores:")
        for fw, sc in score_data["framework_scores"].items():
            print(f"    {fw}: {sc}%")
        print(f"\n  Status Breakdown:")
        for st, cnt in score_data["status_counts"].items():
            print(f"    {st}: {cnt}")
        if score_data["critical_issues"]:
            print(f"\n  Critical Issues ({len(score_data['critical_issues'])}):")
            for i in score_data["critical_issues"]:
                print(f"    [{i['rule_id']}] {i['gap']}")
        print(f"\n  PDF Report: {pdf_path}")
        print(f"{'='*60}")
