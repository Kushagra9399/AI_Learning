from .qp import QP
import random

FALLBACK=[
("CON/N9001","What should happen before electrical work begins?",["Ignore hazards","Safe isolation and required controls","Remove PPE","Energize first"],1),
("CON/N0608","Which instrument is suitable for measuring voltage?",["Voltmeter","Spirit level","Pipe wrench","Tape"],0),
("CON/N0609","What is appropriate before maintenance testing?",["Increase load","Follow safe isolation/testing precautions","Bypass protection","Remove warnings"],1),
("CON/N0610","What should be checked before energizing a new circuit?",["Paint","Wiring, safety and required tests","Phone battery","Nothing"],1),
("CON/N9001","Which practice supports electrical safety?",["No PPE","Ignore signage","Use PPE and isolation procedures","Touch conductors"],2),
("CON/N8001","How should a workplace conflict be handled?",["Stop communication","Coordinate and resolve constructively","Hide it","Blame someone"],1),
("CON/N8002","What should be planned before a task?",["Tools, materials and work sequence","Nothing","Random start","Skip resources"],0),
("DGT/VSQ/N0101","Which is safe digital practice?",["Share passwords","Protect credentials","Disable security","Use unknown links"],1)
]
def generate_questions(count=12):
    out=[]
    for i in range(count):
        nos,q,opts,ans=FALLBACK[i%len(FALLBACK)]
        out.append({"id":f"q-{i+1}","nos_code":nos,"question":q,"options":opts,"correct_option":ans})
    return out

def evaluate_attempt(p):
    answers=p.get("answers",[]); practical=p.get("practical_scores",[])
    theory=sum(a.get("selected_option")==a.get("correct_option") for a in answers)/max(1,len(answers))*100
    practical_pct=(sum(x.get("score",0) for x in practical)/max(1,sum(x.get("max_score",1) for x in practical))*100) if practical else None
    overall=theory if practical_pct is None else theory*.30+practical_pct*.70
    nos=[]
    for n in QP["nos"]:
        xs=[a for a in answers if a.get("nos_code")==n["code"]]
        pct=sum(a.get("selected_option")==a.get("correct_option") for a in xs)/max(1,len(xs))*100
        nos.append({"nos_code":n["code"],"percentage":round(pct,2),"name":n["name"]})
    return {"assessment_id":p["assessment_id"],"qp_code":"CON/Q0603","theory_percentage":round(theory,2),"practical_percentage":None if practical_pct is None else round(practical_pct,2),"overall_percentage":round(overall,2),"pass_threshold":70,"provisional_pass":overall>=70,"nos_results":nos,"assessor_required":True}

def recommend(p):
    e=p["evaluation"]; return {"qp_code":"CON/Q0603","nsqf_level":4,"provisional_outcome":"meets_threshold" if e["overall_percentage"]>=70 else "gaps_identified","gaps":[x for x in e["nos_results"] if x["percentage"]<70],"final_authority":"human_assessor","recommended_action":"assessor_review_and_signoff" if e["overall_percentage"]>=70 else "targeted_upskilling_then_reassessment"}

