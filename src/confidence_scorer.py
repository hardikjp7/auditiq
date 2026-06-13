# src/confidence_scorer.py

from collections import Counter

SEVERITY_WEIGHTS = {
    "CRITICAL": 3,
    "HIGH":     2,
    "MEDIUM":   1
}

STATUS_SCORES = {
    "COMPLIANT":       1.0,
    "PARTIAL":         0.5,
    "NON_COMPLIANT":   0.0,
    "NOT_APPLICABLE":  None
}

STATUS_PRIORITY = {
    "NON_COMPLIANT":  0,
    "PARTIAL":        1,
    "COMPLIANT":      2,
    "NOT_APPLICABLE": 3
}

def _deduplicate_validations(validations: list) -> list:
    """
    Hard dedup: one entry per rule_id.
    Priority: NON_COMPLIANT > PARTIAL > COMPLIANT > NOT_APPLICABLE
    Tiebreak: highest confidence_score wins.
    """
    best = {}
    for v in validations:
        rule_id = v.get("rule_id", "").strip()
        if not rule_id:
            continue
        if rule_id not in best:
            best[rule_id] = v
        else:
            existing      = best[rule_id]
            new_priority  = STATUS_PRIORITY.get(v.get("status","NOT_APPLICABLE"), 3)
            curr_priority = STATUS_PRIORITY.get(existing.get("status","NOT_APPLICABLE"), 3)
            if new_priority < curr_priority:
                best[rule_id] = v
            elif new_priority == curr_priority:
                if v.get("confidence_score", 0) > existing.get("confidence_score", 0):
                    best[rule_id] = v

    deduped = list(best.values())
    removed = len(validations) - len(deduped)
    if removed > 0:
        print(f"  [Dedup] {len(validations)} -> {len(deduped)} "
              f"({removed} duplicate rule evaluations removed)")
    return deduped


def compute_overall_score(validations: list) -> dict:
    """Deduplicate then compute weighted score."""
    validations = _deduplicate_validations(validations)

    weighted_sum   = 0
    weighted_total = 0
    issues         = []
    framework_map  = {}

    for v in validations:
        severity = v.get("severity", "MEDIUM")
        status   = v.get("status", "NOT_APPLICABLE")
        score    = STATUS_SCORES.get(status)
        if score is None:
            continue
        weight         = SEVERITY_WEIGHTS.get(severity, 1)
        weighted_sum   += score * weight
        weighted_total += weight
        fw = v.get("framework", "Unknown")
        if fw not in framework_map:
            framework_map[fw] = {"weighted_sum": 0, "weighted_total": 0}
        framework_map[fw]["weighted_sum"]   += score * weight
        framework_map[fw]["weighted_total"] += weight
        if status in ("NON_COMPLIANT", "PARTIAL"):
            issues.append({
                "rule_id":        v.get("rule_id"),
                "framework":      fw,
                "severity":       severity,
                "status":         status,
                "gap":            v.get("gap"),
                "recommendation": v.get("recommendation")
            })

    overall_score = round((weighted_sum / weighted_total) * 100, 1) if weighted_total > 0 else 0.0

    framework_scores = {}
    for fw, data in framework_map.items():
        sc = round((data["weighted_sum"] / data["weighted_total"]) * 100, 1)              if data["weighted_total"] > 0 else 0.0
        framework_scores[fw] = sc

    status_counts = Counter(v.get("status") for v in validations)
    risk_level = (
        "CRITICAL" if overall_score < 40 else
        "HIGH"     if overall_score < 60 else
        "MEDIUM"   if overall_score < 80 else
        "LOW"
    )
    return {
        "overall_score":    overall_score,
        "risk_level":       risk_level,
        "framework_scores": framework_scores,
        "status_counts":    dict(status_counts),
        "total_rules":      len(validations),
        "issues":           issues,
        "critical_issues":  [i for i in issues if i["severity"] == "CRITICAL"],
        "high_issues":      [i for i in issues if i["severity"] == "HIGH"],
        "deduplicated_validations": validations
    }
