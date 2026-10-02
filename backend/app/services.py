import json, os, re
import httpx
from .qp import QP, THEORY_QUESTIONS
from .practical import validate_scores, practical_percentage

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_CONTEXT = 12000
MAX_PROMPT = 18000

LEVEL_CONTEXT = {
    1: {"title":"Foundation","modules":["basic workplace awareness","simple supervised tasks","basic tools and safety"]},
    2: {"title":"Elementary","modules":["routine tasks","basic measurements","workplace safety","guided problem solving"]},
    3: {"title":"Intermediate","modules":["independent routine work","tools and equipment","quality checks","work planning"]},
    4: {"title":"Advanced","modules":["complex work","fault diagnosis","safety controls","independent planning","quality assurance"]},
    5: {"title":"Specialist","modules":["advanced technical work","supervision","optimization","complex problem solving","quality and compliance"]},
    6: {"title":"Professional","modules":["specialist application","leadership","analysis","improvement","professional judgement"]},
    7: {"title":"Advanced Professional","modules":["advanced professional practice","strategic problem solving","leadership","innovation"]},
    8: {"title":"Expert","modules":["expert practice","research/innovation","strategic leadership","knowledge creation"]}
}

def _groq(system, user, max_tokens=1800):
    key=os.getenv("GROQ_API_KEY")
    if not key:
        return None
    body={"model":GROQ_MODEL,"temperature":0.1,"max_tokens":max_tokens,
          "response_format":{"type":"json_object"},
          "messages":[{"role":"system","content":system},{"role":"user","content":user[:MAX_PROMPT]}]}
    r=httpx.post(GROQ_URL,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json=body,timeout=45)
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])

def _level_context(level):
    return json.dumps(LEVEL_CONTEXT.get(int(level), LEVEL_CONTEXT[4]), separators=(",",":"))

def infer_level(candidate):
    text=" ".join(str(candidate.get(k,"")) for k in ("occupation","work_context","prior_training","years_experience"))
    years=float(candidate.get("years_experience") or 0)
    rules=4 if any(x in text.lower() for x in ["electrician","electrical","wiring"]) and years>=3 else (3 if years>=2 else 2)
    prompt=f"""Assess likely NSQF level from this worker declaration. Return JSON only:
{{"suggested_level":1-8,"confidence":0-1,"reason":"short","evidence":["short facts"]}}
Do not certify. Do not invent qualifications.
Worker: {text[:5000]}"""
    ai=_groq("You are an RPL assessor assistant. NSQF level is a provisional recommendation for an administrator.",prompt,700)
    if ai and isinstance(ai.get("suggested_level"),int):
        ai["suggested_level"]=max(1,min(8,ai["suggested_level"]))
        return ai
    return {"suggested_level":rules,"confidence":0.72,"reason":"Rule-based fallback because Groq is unavailable.","evidence":[candidate.get("work_context","")[:180]]}

def generate_questions(level, candidate, count=10):
    ctx=_level_context(level)
    occupation=str(candidate.get("occupation",""))[:300]
    prompt=f"""Generate exactly {max(5,min(15,int(count)))} RPL questions for NSQF level {level}.
Occupation: {occupation}
Level modules: {ctx}
Return JSON: {{"questions":[{{"id":"q-1","type":"mcq|text|image|video","question":"...","options":[],"marks":1,"rubric":"...","nos_code":"...","pc_id":"...","evidence_required":false}}]}}
Keep questions practical, concise, assessable. For text use options=[]; image/video questions must explain required evidence. Do not invent official NOS codes; use generic competency tags unless provided."""
    ai=_groq("You generate assessment drafts. The admin must approve every question before release.",prompt,2600)
    if ai and isinstance(ai.get("questions"),list):
        out=[]
        for i,q in enumerate(ai["questions"][:15],1):
            q["id"]=f"q-{i}"; q["marks"]=max(1,min(10,int(q.get("marks",1))))
            q["type"]=q.get("type","mcq") if q.get("type") in ("mcq","text","image","video") else "mcq"
            q["options"]=q.get("options",[]) if q["type"]=="mcq" else []
            out.append(q)
        return out
    return [dict(q, type="mcq", marks=1, rubric="Correct answer") for q in THEORY_QUESTIONS[:max(5,min(12,count))]]

def evaluate_attempt(p):
    answers=p.get("answers",[])
    practical=validate_scores(p.get("practical_scores",[]))
    theory_correct=sum(a.get("selected_option")==a.get("correct_option") for a in answers if a.get("type","mcq")=="mcq")
    mcqs=sum(1 for a in answers if a.get("type","mcq")=="mcq")
    theory=theory_correct/max(1,mcqs)*100
    practical_pct=practical_percentage(practical)
    overall=theory if practical_pct is None else theory*(QP["theory_marks"]/QP["total_marks"])+practical_pct*(QP["practical_marks"]/QP["total_marks"])
    text_answers=[a for a in answers if a.get("type")=="text" and a.get("response")]
    ai_feedback=None
    if text_answers:
        ai_feedback=_groq("Evaluate short RPL answers against the supplied rubric. Return JSON only: {"items":[{"id":"q","suggested_marks":0,"reason":"short"}],"feedback":"short"}. Never evaluate image/video evidence.",json.dumps(text_answers,separators=(",",":"))[:7000],1200)
    return {"assessment_id":p["assessment_id"],"qp_code":p.get("qp_code",QP["qp_code"]),"nsqf_level":p.get("nsqf_level",QP["nsqf_level"]),
            "theory_percentage":round(theory,2),"practical_percentage":None if practical_pct is None else round(practical_pct,2),
            "overall_percentage":round(overall,2),"pass_threshold":QP["pass_percentage"],
            "provisional_pass":overall>=QP["pass_percentage"],"practical_scores":practical,
            "text_ai_evaluation":ai_feedback,"assessor_required":True}

def recommend(p):
    e=p["evaluation"]
    return {"provisional_outcome":"meets_threshold" if e["overall_percentage"]>=e["pass_threshold"] else "gaps_identified",
            "recommended_action":"assessor_review_and_signoff","final_authority":"human_assessor"}

def generate_feedback(evaluation, admin_note=""):
    prompt=f"""Write concise constructive feedback for an RPL candidate.
Score: {evaluation.get('overall_percentage')}%.
Outcome: {evaluation.get('provisional_pass')}.
Admin note: {admin_note[:500]}
Return JSON only: {{"feedback":"120 words maximum","next_steps":["..."]}}"""
    ai=_groq("You write respectful vocational assessment feedback. Never claim certification.",prompt,600)
    return ai or {"feedback":"Your assessment has been reviewed. Please discuss the highlighted competency gaps and next steps with the assessor.","next_steps":["Review assessor feedback","Practice identified competency gaps"]}

def level_context(level):
    return LEVEL_CONTEXT.get(int(level), LEVEL_CONTEXT[4])
