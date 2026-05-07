"""Classifier, storyteller, judge, reviser, and orchestration."""

import json
from typing import Any

from constants import DEFAULT_CATEGORY
from llm import chat, grab_json_dict
from prompts import (
    CATEGORY_STRATEGIES,
    CLASSIFIER_SYSTEM,
    JUDGE_SYSTEM,
    READER_FEEDBACK_SYSTEM,
    REVISER_SYSTEM,
    STORYTELLER_SYSTEM,
    system_with_strategy,
)


def classify_request(idea: str, cfg: dict[str, Any]) -> tuple[str, str]:
    lines = [idea.strip()]
    themes = str(cfg.get("themes_or_interests") or "").strip()
    if themes:
        lines.append(f"Themes/interests from config: {themes}")
    blob = "\n".join(lines)
    raw = chat(
        [
            {"role": "system", "content": CLASSIFIER_SYSTEM},
            {"role": "user", "content": blob},
        ],
        max_tokens=120,
        temperature=0.1,
    )
    try:
        data = grab_json_dict(raw)
        cat = str(data.get("category") or "").strip().lower().replace(" ", "_").replace("-", "_")
        reason = str(data.get("reason") or "").strip()
        if cat not in CATEGORY_STRATEGIES:
            return DEFAULT_CATEGORY, (reason or "unknown_category_slug")
        return cat, reason
    except (json.JSONDecodeError, ValueError, TypeError):
        return DEFAULT_CATEGORY, "classifier_fallback"


def draft_story(request_text: str, category: str) -> str:
    return chat(
        [
            {"role": "system", "content": system_with_strategy(STORYTELLER_SYSTEM, category)},
            {"role": "user", "content": request_text},
        ],
        max_tokens=2000,
        temperature=0.85,
    )


def judge_story(request_text: str, story: str, category: str) -> dict[str, Any]:
    msg = (
        f"User request:\n{request_text}\n\n"
        f"Detected request category (story should match this style): {category}\n\n"
        f"Story draft:\n{story}\n"
    )
    raw = chat(
        [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": msg}],
        max_tokens=700,
        temperature=0.1,
    )
    try:
        return grab_json_dict(raw)
    except (json.JSONDecodeError, ValueError, TypeError):
        return {
            "approved": False,
            "score_overall": 6,
            "kid_safe": True,
            "age_fit_ok": True,
            "issues": ["judge_output_unparseable"],
            "strengths": [],
            "revision_brief": (
                "Judge output wasn't valid JSON. Tighten bedtime tone, ages 5-10, "
                "clear beginning-middle-end. Raw:\n" + raw.strip()[:800]
            ),
        }


def revise_story(request_text: str, story: str, verdict: dict[str, Any], category: str) -> str:
    bundle = (
        f"User request:\n{request_text}\n\nCurrent draft:\n{story}\n\n"
        f"Judge verdict (JSON):\n{json.dumps(verdict, ensure_ascii=False)}\n"
    )
    return chat(
        [
            {"role": "system", "content": system_with_strategy(REVISER_SYSTEM, category)},
            {"role": "user", "content": bundle},
        ],
        max_tokens=2000,
        temperature=0.65,
    )


def revise_from_reader_feedback(
    request_text: str, story: str, feedback: str, category: str
) -> str:
    msg = (
        f"Original storytelling request:\n{request_text}\n\n"
        f"Current story:\n{story}\n\n"
        f"Reader feedback / changes requested:\n{feedback}\n"
    )
    return chat(
        [
            {"role": "system", "content": system_with_strategy(READER_FEEDBACK_SYSTEM, category)},
            {"role": "user", "content": msg},
        ],
        max_tokens=2000,
        temperature=0.65,
    )


def run_pipeline(request_text: str, category: str) -> tuple[str, dict[str, Any]]:
    first = draft_story(request_text, category)
    v1 = judge_story(request_text, first, category)
    trace: dict[str, Any] = {
        "category": category,
        "rounds": [{"stage": "draft", "verdict": v1}],
    }

    if v1.get("approved"):
        trace["final_stage"] = "draft"
        return first.strip(), trace

    second = revise_story(request_text, first, v1, category)
    v2 = judge_story(request_text, second, category)
    trace["rounds"].append({"stage": "revised", "verdict": v2})

    s1 = int(v1.get("score_overall") or 0)
    s2 = int(v2.get("score_overall") or 0)
    if s2 >= s1:
        trace["final_stage"] = "revised"
        return second.strip(), trace

    trace["final_stage"] = "draft_fallback"
    return first.strip(), trace
