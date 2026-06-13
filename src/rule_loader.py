import json
from pathlib import Path

RULES_DIR = Path("/workspace/shared/audit_validator/data/compliance_rules")

def load_all_rules() -> list:
    all_rules = []
    for rule_file in RULES_DIR.glob("*.json"):
        with open(rule_file) as f:
            data = json.load(f)
        for rule in data["rules"]:
            rule["framework"] = data["framework"]
            all_rules.append(rule)
    print(f"Loaded {len(all_rules)} rules from {len(list(RULES_DIR.glob('*.json')))} frameworks")
    return all_rules

def load_rules_as_text(rules: list) -> list:
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
            "rule_id": r["id"], "framework": r["framework"],
            "severity": r["severity"], "text": text, "rule": r
        })
    return texts
