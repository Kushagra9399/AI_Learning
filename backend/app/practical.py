from .qp import PRACTICAL_TASKS

def task_catalog():
    return {"tasks": PRACTICAL_TASKS}

def validate_scores(scores):
    by_id = {t["id"]: t for t in PRACTICAL_TASKS}
    normalized = []
    for item in scores or []:
        task = by_id.get(item.get("task_id"))
        if not task:
            continue
        score = max(0.0, min(float(item.get("score", 0)), float(task["max_score"])))
        normalized.append({
            "task_id": task["id"],
            "nos_code": task["nos_code"],
            "score": round(score, 2),
            "max_score": task["max_score"],
            "assessor_note": str(item.get("assessor_note", ""))[:2000],
            "assessor_id": str(item.get("assessor_id", ""))[:200]
        })
    return normalized

def practical_percentage(scores):
    clean = validate_scores(scores)
    total = sum(x["score"] for x in clean)
    maximum = sum(x["max_score"] for x in clean)
    return (total / maximum * 100) if maximum else None
