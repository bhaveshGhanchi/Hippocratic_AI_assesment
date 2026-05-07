"""Load story_config.json and build the big user prompt for the model."""

import json
import os
from typing import Any

from constants import CONFIG_FILE, LENGTH_HINTS


def default_story_config() -> dict[str, Any]:
    return {
        "narrator": "A warm, gentle bedtime storyteller",
        "where_you_are": "Snuggled in bed",
        "listener": "neutral",
        "default_story_type": "",
        "child_age": "",
        "tone": "cozy, gentle, reassuring",
        "length": "medium",
        "themes_or_interests": "",
        "protagonist_style": "either",
        "reading_pace": "slow and sleepy, good for winding down",
        "language": "simple English, ages 5-10",
        "ending_style": (
            "soft lesson woven into the last scenes, then cozy reassurance so the child "
            "can sleep happily"
        ),
        "sibling_or_friend_name": "",
        "caregiver_or_family_note": "",
        "avoid_content": "",
        "names_or_words_to_use": "",
    }


def load_story_config(path: str | None = None) -> dict[str, Any]:
    settings = default_story_config()
    cfg_path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    if os.path.isfile(cfg_path):
        with open(cfg_path, encoding="utf-8") as fh:
            blob = json.load(fh)
        if isinstance(blob, dict):
            for k, v in blob.items():
                if k in settings:
                    settings[k] = v
    return settings


def normalize_listener(s: str) -> str:
    s = (s or "").strip().lower()
    if s in ("b", "boy", "m", "male"):
        return "boy"
    if s in ("g", "girl", "f", "female"):
        return "girl"
    return "neutral"


LISTENER_COPY = {
    "boy": (
        "The child listening is a boy. Natural 'you' is fine when speaking to the listener; "
        "if you use a child character, any gender is fine—avoid tired stereotypes."
    ),
    "girl": (
        "The child listening is a girl. Natural 'you' is fine when speaking to the listener; "
        "if you use a child character, any gender is fine—avoid tired stereotypes."
    ),
    "neutral": (
        "Do not assume the listener's gender. Prefer inclusive wording and varied characters "
        "unless the story wish specifies a protagonist."
    ),
}


def build_story_request(cfg: dict[str, Any], story_idea: str) -> str:
    who = str(cfg.get("narrator") or "").strip()
    place = str(cfg.get("where_you_are") or "").strip()
    kid = normalize_listener(str(cfg.get("listener") or "neutral"))

    size = str(cfg.get("length") or "medium").strip().lower()
    word_goal = LENGTH_HINTS.get(size, LENGTH_HINTS["medium"])

    lines = [
        "Storytelling setup (follow closely):",
        f"- Who is telling the story / narrative voice: {who}",
        f"- Where the listener is right now: {place}",
        f"- Listener: {LISTENER_COPY[kid]}",
    ]

    def bump(label: str, key: str) -> None:
        val = cfg.get(key)
        if val is None:
            return
        piece = str(val).strip()
        if piece:
            lines.append(f"- {label}: {piece}")

    bump("Child age (for vocabulary and themes)", "child_age")
    bump("Tone / mood", "tone")
    lines.append(f"- Target length: {size} ({word_goal})")
    bump("Themes or interests to lean into", "themes_or_interests")
    bump("Protagonist style", "protagonist_style")
    bump("Reading pace", "reading_pace")
    bump("Language level", "language")
    bump("How the ending should feel", "ending_style")
    bump("Optional name to mention lightly (friend or sibling)", "sibling_or_friend_name")
    bump("Family or caregiver note to weave in warmly", "caregiver_or_family_note")
    bump("Words, names, or phrases to try to include", "names_or_words_to_use")
    bump("Topics or elements to avoid", "avoid_content")
    lines.append("")
    lines.append("Story I want to hear:")
    lines.append(story_idea.strip())
    lines.append("")
    return "\n".join(lines)
