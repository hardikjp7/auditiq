# /workspace/shared/audit_validator/src/rule_loader.py

import json
from pathlib import Path

RULES_DIR = Path("/workspace/shared/audit_validator/data/compliance_rules")

def load_all_rules() -> list:
    """Load all rule JSON files and return flat list of rules with framework tag"""
    all_rules = []
    for rule_file in RULES_DIR.glob("*.json"):
        with open(rule_file) as f:
            data = json.load(f)
        framework = data["framework"]
        for rule in data["rules"]:
            rule["framework"] = framework
            all_rules.append(rule)
    print(f"✅ Loaded {len(all_rules)} rules from {len(list(RULES_DIR.glob('*.json')))} frameworks")
    return all_rules

def load_rules_as_text(rules: list) -> list:
    """
    Convert rules to plain text strings for embedding.
    Each rule becomes a single searchable text chunk.
    """
    texts = []
    for r in rules:
        text = (
            f"Rule ID: {r['id']} | Framework: {r['framework']} | "
            f"Category: {r['category']} | Severity: {r['severity']}\n"
            f"Title: {r['title']}\n"
            f"Description: {r['description']}\n"
            f"Required clause: {r['required_clause']}\n"
            f"Keywords: {', '.join(r['keywords'])}"
        )
        texts.append({
            "rule_id"  : r["id"],
            "framework": r["framework"],
            "severity" : r["severity"],
            "text"     : text,
            "rule"     : r
        })
    return texts

def get_rule_by_id(rules: list, rule_id: str) -> dict:
    return next((r for r in rules if r["id"] == rule_id), None)