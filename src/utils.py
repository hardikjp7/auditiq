# /workspace/shared/audit_validator/src/utils.py

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path

BASE_DIR   = Path("/workspace/shared/audit_validator")
DATA_DIR   = BASE_DIR / "data"
RULES_DIR  = DATA_DIR / "compliance_rules"
DOCS_DIR   = DATA_DIR / "sample_docs"
VS_DIR     = DATA_DIR / "vector_store"
OUT_DIR    = BASE_DIR / "outputs" / "audit_reports"
LOGS_DIR   = BASE_DIR / "logs"

def setup_logger(name: str) -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        ch = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        fh.setFormatter(fmt)
        ch.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

def save_json(data: dict, filepath: str):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved: {filepath}")

def load_json(filepath: str) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)

class Timer:
    """Simple latency timer — wrap any block to measure time"""
    def __init__(self, label=""):
        self.label = label
    def __enter__(self):
        self.start = time.time()
        return self
    def __exit__(self, *args):
        self.elapsed = round(time.time() - self.start, 3)
        print(f"⏱ [{self.label}] {self.elapsed}s")

def token_counter(text: str) -> int:
    """Rough token estimate: words * 1.3"""
    return int(len(text.split()) * 1.3)