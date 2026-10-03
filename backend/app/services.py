import json
import os

import httpx
from dotenv import load_dotenv
from pathlib import Path

from .nsqf_levels import NSQF_LEVEL_DESCRIPTORS, prompt_level_descriptors
from .practical import practical_percentage, validate_scores
from .qp import QP, THEORY_QUESTIONS

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_PROMPT_CHARS = 18000

LEVEL_CONTEXT = {
    1: {
        "title": "Foundation",
        "modules": [
            "basic workplace awareness",
            "simple supervised tasks",
            "basic tools and safety",
        ],
    },
    2: {
        "title": "Elementary",
        "modules": [
            "routine tasks",
            "basic measurements",
            "workplace safety",
            "guided problem solving",
        ],
    },
    3: {
        "title": "Intermediate",
        "modules": [
            "independent routine work",
            "tools and equipment",
            "quality checks",
            "work planning",
        ],
    },
    4: {
        "title": "Advanced",
        "modules": [
            "complex work",
            "fault diagnosis",
            "safety controls",
            "independent planning",
            "quality assurance",
        ],
    },
    5: {
        "title": "Specialist",
        "modules": [
            "advanced technical work",
            "supervision",
            "optimization",
            "complex problem solving",
            "quality and compliance",
        ],
    },
    6: {
        "title": "Professional",
        "modules": [
            "specialist application",
            "leadership",
            "analysis",
            "improvement",
            "professional judgement",
        ],
    },
    7: {
        "title": "Advanced Professional",
        "modules": [
            "advanced professional practice",
            "strategic problem solving",
            "leadership",
            "innovation",
        ],
    },
    8: {
        "title": "Expert",
        "modules": [
            "expert practice",
            "research and innovation",
            "strategic leadership",
            "knowledge creation",
        ],
    },
}


def _groq(system_prompt: str, user_prompt: str, max_tokens: int = 1800):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    request_body = {
        "model": GROQ_MODEL,
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt[:MAX_PROMPT_CHARS],
            },
        ],
    }

    response = httpx.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=request_body,
        timeout=45,
    )
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def level_context(level: int):
    return NSQF_LEVEL_DESCRIPTORS.get(int(level), NSQF_LEVEL_DESCRIPTORS[4])


def _compact_level_context(level: int) -> str:
    return json.dumps(level_context(level), separators=(",", ":"))


def _prompt_nsqf_context() -> str:
    return json.dumps(prompt_level_descriptors(), separators=(",", ":"))


def infer_level(candidate: dict) -> dict:
    occupation = str(candidate.get("occupation", ""))
    work_context = str(candidate.get("work_context", ""))
    prior_training = str(candidate.get("prior_training", ""))
    years = float(candidate.get("years_experience") or 0)

    worker_summary = " ".join(
        [occupation, work_context, prior_training, str(years)]
    )

    is_electrical = any(
        term in worker_summary.lower()
        for term in ("electrician", "electrical", "wiring")
    )

    fallback_level = 4 if is_electrical and years >= 3 else 3 if years >= 2 else 2

    prompt = f"""
Assess the likely NSQF level for this worker declaration.

Return JSON only:
{{
  "suggested_level": 1,
  "confidence": 0.0,
  "reason": "short explanation",
  "evidence": ["short evidence point"]
}}

Rules:
- This is only a provisional recommendation.
- Do not certify the worker.
- Do not invent qualifications.
- Keep the recommendation grounded in the supplied declaration.

Worker declaration:
{worker_summary[:5000]}
"""

    ai_result = _groq(
        "You are an RPL assessor assistant. A human administrator makes the final NSQF decision.",
        prompt,
        700,
    )

    if ai_result and isinstance(ai_result.get("suggested_level"), int):
        ai_result["suggested_level"] = max(
            1, min(8, ai_result["suggested_level"])
        )
        return ai_result

    return {
        "suggested_level": fallback_level,
        "confidence": 0.72,
        "reason": "Rule-based fallback because Groq is unavailable.",
        "evidence": [work_context[:180]],
    }


def generate_questions(level: int, candidate: dict, count: int = 10) -> list:
    question_count = max(5, min(15, int(count)))
    context = _compact_level_context(level)

    prompt = f"""
Generate exactly {question_count} RPL assessment questions for NSQF level {level}.

Worker occupation:
{str(candidate.get("occupation", ""))[:300]}

Level context:
{context}

Return JSON only:
{{
  "questions": [
    {{
      "id": "q-1",
      "type": "mcq",
      "question": "question text",
      "options": ["A", "B", "C", "D"],
      "correct_option": 0,
      "marks": 1,
      "rubric": "short marking guidance",
      "evidence_required": false
    }}
  ]
}}

Allowed types:
- mcq
- text
- image
- video

Requirements:
- MCQs must contain exactly one correct_option.
- Text questions must contain a concise rubric.
- Image/video questions must describe the evidence expected.
- Keep questions practical and concise.
- Do not invent official NOS or PC codes.
- The administrator will approve or edit every question before release.
"""

    ai_result = _groq(
        "You generate assessment drafts for an RPL administrator. Never make a certification decision.",
        prompt,
        2600,
    )

    if ai_result and isinstance(ai_result.get("questions"), list):
        normalized = []

        for index, question in enumerate(ai_result["questions"][:15], start=1):
            question_type = question.get("type", "mcq")
            if question_type not in {"mcq", "text", "image", "video"}:
                question_type = "mcq"

            normalized_question = {
                "id": f"q-{index}",
                "type": question_type,
                "question": str(question.get("question", "")).strip(),
                "options": question.get("options", [])
                if question_type == "mcq"
                else [],
                "correct_option": (
                    int(question.get("correct_option", 0))
                    if question_type == "mcq"
                    else -1
                ),
                "marks": max(
                    1, min(10, int(question.get("marks", 1)))
                ),
                "rubric": str(question.get("rubric", ""))[:1000],
                "evidence_required": question_type in {"image", "video"},
            }

            normalized.append(normalized_question)

        if normalized:
            return normalized

    fallback = []

    for question in THEORY_QUESTIONS[:question_count]:
        fallback.append(
            {
                **question,
                "type": "mcq",
                "marks": 1,
                "rubric": "Award full marks for the correct answer.",
                "evidence_required": False,
            }
        )

    return fallback


def evaluate_attempt(payload: dict) -> dict:
    answers = payload.get("answers", [])
    practical_scores = validate_scores(
        payload.get("practical_scores", [])
    )

    mcq_answers = [
        answer
        for answer in answers
        if answer.get("type", "mcq") == "mcq"
    ]

    correct_count = sum(
        answer.get("selected_option") == answer.get("correct_option")
        for answer in mcq_answers
    )

    theory_percentage = (
        correct_count / len(mcq_answers) * 100
        if mcq_answers
        else 0
    )

    practical_pct = practical_percentage(practical_scores)

    if practical_pct is None:
        overall_percentage = theory_percentage
    else:
        overall_percentage = (
            theory_percentage * QP["theory_marks"] / QP["total_marks"]
            + practical_pct * QP["practical_marks"] / QP["total_marks"]
        )

    text_answers = [
        answer
        for answer in answers
        if answer.get("type") == "text" and answer.get("response")
    ]

    text_ai_evaluation = None

    if text_answers:
        text_payload = json.dumps(
            text_answers,
            separators=(",", ":"),
        )[:7000]

        text_ai_evaluation = _groq(
            (
                "Evaluate short RPL answers against their supplied rubric. "
                "Return JSON only. Never evaluate image or video evidence."
            ),
            f"""
Return:
{{
  "items": [
    {{
      "id": "q-id",
      "suggested_marks": 0,
      "reason": "short"
    }}
  ],
  "feedback": "short"
}}

Answers:
{text_payload}
""",
            1200,
        )

    return {
        "assessment_id": payload["assessment_id"],
        "qp_code": payload.get("qp_code", QP["qp_code"]),
        "nsqf_level": payload.get("nsqf_level", QP["nsqf_level"]),
        "theory_percentage": round(theory_percentage, 2),
        "practical_percentage": (
            None if practical_pct is None else round(practical_pct, 2)
        ),
        "overall_percentage": round(overall_percentage, 2),
        "pass_threshold": QP["pass_percentage"],
        "provisional_pass": overall_percentage >= QP["pass_percentage"],
        "practical_scores": practical_scores,
        "text_ai_evaluation": text_ai_evaluation,
        "assessor_required": True,
    }


def recommend(payload: dict) -> dict:
    evaluation = payload["evaluation"]

    return {
        "provisional_outcome": (
            "meets_threshold"
            if evaluation["overall_percentage"]
            >= evaluation["pass_threshold"]
            else "gaps_identified"
        ),
        "recommended_action": "assessor_review_and_signoff",
        "final_authority": "human_assessor",
    }


def generate_feedback(evaluation: dict, admin_note: str = "") -> dict:
    prompt = f"""
Write concise constructive feedback for an RPL candidate.

Score: {evaluation.get("overall_percentage")}%
Provisional outcome: {evaluation.get("provisional_pass")}
Administrator note: {admin_note[:500]}

Return JSON only:
{{
  "feedback": "120 words maximum",
  "next_steps": ["short next step"]
}}
"""

    ai_result = _groq(
        "You write respectful vocational assessment feedback. Never claim certification.",
        prompt,
        600,
    )

    return ai_result or {
        "feedback": (
            "Your assessment has been reviewed. Please discuss the "
            "highlighted competency gaps and next steps with the assessor."
        ),
        "next_steps": [
            "Review assessor feedback",
            "Practice identified competency gaps",
        ],
    }
