# fastapi_app.py
import sys, os, shutil, json
sys.path.insert(0, "/workspace/shared/audit_validator")

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

from src.validator_agent import AuditAgent

app = FastAPI(title="auditiq API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
app.mount("/static",
          StaticFiles(directory="/workspace/shared/audit_validator/src"),
          name="static")

_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = AuditAgent()
    return _agent

@app.on_event("startup")
async def startup():
    print("Loading AuditAgent...")
    get_agent()
    print("Agent ready.")

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(
        Path("/workspace/shared/audit_validator/src/index.html")
        .read_text(encoding="utf-8"))

@app.post("/audit")
async def run_audit(file: UploadFile = File(...), max_chunks: int = Form(6)):
    try:
        ext      = Path(file.filename).suffix or ".txt"
        tmp_path = f"/tmp/auditiq_upload{ext}"
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = get_agent().run(tmp_path, max_chunks=max_chunks)

        shutil.copy(result["pdf_report"],  "/tmp/auditiq_latest_report.pdf")
        shutil.copy(result["html_report"], "/tmp/auditiq_latest_report.html")

        return JSONResponse({
            "success":     True,
            "doc_name":    result["doc_name"],
            "score_data":  result["score_data"],
            "validations": result["validations"],
            "metrics":     result["metrics"]
        })
    except Exception as e:
        import traceback
        return JSONResponse({"success": False, "error": str(e),
                             "traceback": traceback.format_exc()},
                            status_code=500)


# ── Chat endpoint ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question:    str
    score_data:  dict
    validations: list
    doc_name:    Optional[str] = "document"

def _build_chat_prompt(question: str, score_data: dict,
                       validations: list, doc_name: str) -> str:
    """Build a dynamic context-aware prompt from the current audit result."""

    # Build findings summary
    findings_lines = []
    for v in validations:
        line = (
            f"  {v.get('rule_id','?')} | {v.get('framework','?')} | "
            f"{v.get('severity','?')} | {v.get('status','?')} | "
            f"Confidence: {v.get('confidence_score','?')}%"
        )
        if v.get("evidence"):
            line += f"\n    Evidence: {str(v['evidence'])[:200]}"
        if v.get("gap"):
            line += f"\n    Gap: {str(v['gap'])[:150]}"
        if v.get("recommendation"):
            line += f"\n    Action: {str(v['recommendation'])[:150]}"
        findings_lines.append(line)

    findings_text = "\n".join(findings_lines)

    # Build framework scores summary
    fw_lines = "\n".join([
        f"  {fw}: {sc}%"
        for fw, sc in score_data.get("framework_scores", {}).items()
    ])

    # Build issues summary
    issues = score_data.get("issues", [])
    issue_lines = "\n".join([
        f"  [{i.get('severity')}] {i.get('rule_id')} - {i.get('framework')}: {i.get('gap','')[:100]}"
        for i in issues
    ]) or "  None"

    prompt = f"""<|im_start|>system
You are auditiq, an expert AI compliance audit assistant. You have just completed
an automated compliance audit of a document. Answer questions about the audit results
clearly, concisely, and accurately.

STRICT RULES:
- Only reference findings that appear in the AUDIT RESULTS below.
- Never invent violations or findings not present in the results.
- Reference specific rule IDs (e.g. GDPR-004, SOX-001) when relevant.
- Keep answers under 150 words unless the user asks for detail.
- If asked about something not in the audit results, say so clearly.
- Use plain language — the user may be a compliance officer, not a developer.
<|im_end|>
<|im_start|>user
AUDIT RESULTS FOR: {doc_name}

OVERALL SCORE: {score_data.get('overall_score','?')}% | RISK LEVEL: {score_data.get('risk_level','?')}
RULES CHECKED: {score_data.get('total_rules','?')} across {len(score_data.get('framework_scores',{}))} frameworks

FRAMEWORK SCORES:
{fw_lines}

STATUS COUNTS:
{json.dumps(score_data.get('status_counts', {}), indent=2)}

OPEN ISSUES (NON_COMPLIANT / PARTIAL):
{issue_lines}

ALL FINDINGS:
{findings_text}

USER QUESTION: {question}
<|im_end|>
<|im_start|>assistant
"""
    return prompt

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        from src.validator import get_llm_pipeline
        from src.utils import token_counter

        pipe   = get_llm_pipeline()
        prompt = _build_chat_prompt(
            req.question, req.score_data,
            req.validations, req.doc_name
        )

        result = pipe(
            prompt,
            max_new_tokens=256,
            temperature=0.3,
            top_p=0.9,
            do_sample=True,
            return_full_text=False
        )

        answer = result[0]["generated_text"].strip()

        # Clean up any trailing partial sentences
        if answer and answer[-1] not in ".!?":
            last_period = max(
                answer.rfind("."),
                answer.rfind("!"),
                answer.rfind("?")
            )
            if last_period > len(answer) * 0.6:
                answer = answer[:last_period+1]

        return JSONResponse({
            "success": True,
            "answer":  answer,
            "tokens":  token_counter(prompt + answer)
        })

    except Exception as e:
        import traceback
        return JSONResponse({
            "success": False,
            "answer":  f"Sorry, I encountered an error: {str(e)}",
            "error":   traceback.format_exc()
        }, status_code=500)


@app.get("/download-report")
async def download_report():
    path = "/tmp/auditiq_latest_report.pdf"
    if os.path.exists(path):
        return FileResponse(path, media_type="application/pdf",
                            filename="auditiq_compliance_report.pdf")
    return JSONResponse({"error": "No report generated yet"}, status_code=404)

@app.get("/health")
async def health():
    return {"status": "ok", "agent_loaded": _agent is not None}

if __name__ == "__main__":
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=False)
