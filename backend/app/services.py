from .qp import QP, THEORY_QUESTIONS
from .practical import validate_scores, practical_percentage

def generate_questions(count=12):
    count = max(5, min(int(count), len(THEORY_QUESTIONS)))
    return [dict(q) for q in THEORY_QUESTIONS[:count]]

def evaluate_attempt(p):
    answers = p.get("answers", [])
    practical = validate_scores(p.get("practical_scores", []))
    theory_correct = sum(a.get("selected_option") == a.get("correct_option") for a in answers)
    theory = theory_correct / max(1, len(answers)) * 100
    practical_pct = practical_percentage(practical)
    overall = theory if practical_pct is None else theory * (QP["theory_marks"] / QP["total_marks"]) + practical_pct * (QP["practical_marks"] / QP["total_marks"])
    nos = []
    for n in QP["nos"]:
        xs = [a for a in answers if a.get("nos_code") == n["code"]]
        theory_pct = sum(a.get("selected_option") == a.get("correct_option") for a in xs) / max(1, len(xs)) * 100
        ps = [x for x in practical if x["nos_code"] == n["code"]]
        p_pct = (sum(x["score"] for x in ps) / sum(x["max_score"] for x in ps) * 100) if ps else None
        nos.append({"nos_code": n["code"], "name": n["name"], "theory_percentage": round(theory_pct,2),
                     "practical_percentage": None if p_pct is None else round(p_pct,2),
                     "pcs": n["pcs"]})
    return {"assessment_id":p["assessment_id"],"qp_code":QP["qp_code"],"nsqf_level":QP["nsqf_level"],
            "theory_percentage":round(theory,2),"practical_percentage":None if practical_pct is None else round(practical_pct,2),
            "overall_percentage":round(overall,2),"pass_threshold":QP["pass_percentage"],
            "provisional_pass":overall >= QP["pass_percentage"],"nos_results":nos,
            "practical_scores":practical,"assessor_required":True}

def recommend(p):
    e = p["evaluation"]
    gaps = [x for x in e["nos_results"] if (x["practical_percentage"] if x["practical_percentage"] is not None else x["theory_percentage"]) < QP["pass_percentage"]]
    return {"qp_code":QP["qp_code"],"nsqf_level":QP["nsqf_level"],
            "provisional_outcome":"meets_threshold" if e["overall_percentage"] >= QP["pass_percentage"] else "gaps_identified",
            "gaps":gaps,"recommended_action":"assessor_review_and_signoff" if e["overall_percentage"] >= QP["pass_percentage"] else "targeted_upskilling_then_reassessment",
            "final_authority":"human_assessor"}
