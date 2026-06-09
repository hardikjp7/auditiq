import json
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from src.constants import *
from src.utils import Timer, token_counter, log_gpu_memory

_pipe      = None
_tokenizer = None

def get_llm_pipeline():
    global _pipe, _tokenizer
    if _pipe is None:
        print(f"Loading {LLM_MODEL_ID} ...")
        _tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_ID)
        model      = AutoModelForCausalLM.from_pretrained(
            LLM_MODEL_ID,
            torch_dtype=TORCH_DTYPE,
            device_map="auto"
        )
        _pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=_tokenizer,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            do_sample=True,
            return_full_text=False
        )
        log_gpu_memory("After LLM load")
        print(f"LLM ready: {LLM_MODEL_ID}")
    return _pipe

def build_prompt(doc_chunk: str, rules: list) -> str:
    rules_text = "\n\n".join([
        f"Rule {r['rule_id']} | {r['framework']} | Severity: {r['severity']}\n"
        f"Title: {r['rule']['title']}\n"
        f"Description: {r['rule']['description']}\n"
        f"Required clause: {r['rule']['required_clause']}"
        for r in rules
    ])
    return f"""<|im_start|>system
You are an expert compliance auditor. Analyze document clauses against regulatory rules.
Always respond with valid JSON only. No explanation outside the JSON.
<|im_end|>
<|im_start|>user
DOCUMENT CLAUSE:
{doc_chunk}

RULES TO VALIDATE AGAINST:
{rules_text}

Respond ONLY with this JSON:
{{
  "validations": [
    {{
      "rule_id": "string",
      "framework": "string",
      "severity": "CRITICAL|HIGH|MEDIUM",
      "status": "COMPLIANT|NON_COMPLIANT|PARTIAL|NOT_APPLICABLE",
      "confidence_score": 0-100,
      "evidence": "quote from document supporting this assessment",
      "gap": "what is missing if non-compliant, else null",
      "recommendation": "how to fix the gap, else null"
    }}
  ]
}}
<|im_end|>
<|im_start|>assistant
"""

def validate_clause(doc_chunk: str, rules: list) -> dict:
    pipe   = get_llm_pipeline()
    prompt = build_prompt(doc_chunk, rules)

    input_tokens = token_counter(prompt)
    with Timer("LLM inference"):
        raw_output   = pipe(prompt)[0]["generated_text"]
    output_tokens = token_counter(raw_output)

    parsed = safe_parse_json(raw_output)
    parsed["metrics"] = {
        "input_tokens" : input_tokens,
        "output_tokens": output_tokens,
        "total_tokens" : input_tokens + output_tokens
    }
    return parsed

def safe_parse_json(text: str) -> dict:
    try:
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*',     '', text)
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"JSON parse error: {e}")
    return {
        "validations" : [],
        "parse_error" : True,
        "raw_response": text[:300]
    }

def validate_full_document(doc_chunks: list, index, rule_texts: list, top_k: int = 3) -> dict:
    from src.rag_pipeline import retrieve_top_rules
    import time

    all_validations = []
    total_tokens    = 0
    latencies       = []

    for i, chunk in enumerate(doc_chunks):
        print(f"\nValidating chunk {i+1}/{len(doc_chunks)}...")
        rules   = retrieve_top_rules(chunk["text"], index, rule_texts, top_k)
        t_start = time.time()
        result  = validate_clause(chunk["text"], rules)
        latency = round(time.time() - t_start, 2)
        latencies.append(latency)

        if "validations" in result:
            for v in result["validations"]:
                v["chunk_id"] = chunk["chunk_id"]
                v["chunk_text_preview"] = chunk["text"][:150]
            all_validations.extend(result["validations"])
            total_tokens += result.get("metrics", {}).get("total_tokens", 0)

    return {
        "total_chunks"    : len(doc_chunks),
        "total_rules_checked": len(all_validations),
        "avg_latency_sec" : round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "total_tokens"    : total_tokens,
        "validations"     : all_validations
    }