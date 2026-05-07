"""Input/output and the interactive entrypoint."""

from typing import Any

from constants import MAX_READER_FEEDBACK_ROUNDS
from pipeline import (
    classify_request,
    judge_story,
    revise_from_reader_feedback,
    run_pipeline,
)
from story_config import build_story_request, load_story_config


def ask_what_story(cfg: dict[str, Any]) -> str:
    fallback = str(cfg.get("default_story_type") or "").strip()
    hint = f"[{fallback}] " if fallback else ""
    idea = input(f"What kind of story would you like to hear? {hint}").strip()
    return idea or fallback


def verdict_one_liner(v: dict[str, Any]) -> str:
    bits = [
        f"score={v.get('score_overall')}",
        f"approved={v.get('approved')}",
        f"kid_safe={v.get('kid_safe')}",
        f"age_fit_ok={v.get('age_fit_ok')}",
    ]
    problems = v.get("issues") or []
    if isinstance(problems, list) and problems:
        bits.append("issues=" + "; ".join(str(x) for x in problems[:5]))
    tip = (v.get("revision_brief") or "").strip()
    if tip:
        bits.append("revision_brief=" + tip.replace("\n", " ")[:240])
    return " | ".join(bits)


example_requests = (
    "A story about a girl named Alice and her best friend Bob, who happens to be a cat."
)


def main() -> None:
    cfg = load_story_config()
    idea = ask_what_story(cfg)
    if not idea.strip():
        print("No story idea — bye.")
        return

    prompt = build_story_request(cfg, idea)

    category, cat_reason = classify_request(idea, cfg)
    print(f"\n=== Story category: {category} ===")
    if cat_reason:
        print(f"    ({cat_reason})")

    try:
        text, trace = run_pipeline(prompt, category)
    except Exception as err:
        print("Something broke:", err)
        return

    print("\n=== Judge (after draft) ===")
    print(verdict_one_liner(trace["rounds"][0]["verdict"]))
    if len(trace["rounds"]) > 1:
        print("\n=== Judge (after revision) ===")
        print(verdict_one_liner(trace["rounds"][1]["verdict"]))
    print(f"\n=== Final story ({trace.get('final_stage', '?')}) ===\n")
    print(text)

    for n in range(MAX_READER_FEEDBACK_ROUNDS):
        left = MAX_READER_FEEDBACK_ROUNDS - n
        try:
            fb = input(
                f"\nFeedback or changes? ({left} round(s) left, Enter to stop) "
            ).strip()
        except EOFError:
            break
        if not fb:
            break
        try:
            text = revise_from_reader_feedback(prompt, text, fb, trace["category"])
            chk = judge_story(prompt, text, trace["category"])
            print("\n=== Judge (after your feedback) ===")
            print(verdict_one_liner(chk))
            print("\n=== Updated story ===\n")
            print(text)
        except Exception as err:
            print("Couldn't apply that feedback:", err)
            break
