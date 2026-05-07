# What I built and why

A short write-up of the choices I made on top of the assignment skeleton.

## Goal

Take a simple bedtime story request and generate something appropriate for ages 5–10.
Add an LLM judge to improve quality. Keep the OpenAI model. Don't commit the API key.

## What I built

A small command-line app that:

1. Loads settings from a JSON config (`story_config.json`).
2. Asks the user one question: *“What kind of story would you like to hear?”*
3. Classifies the request into one of 8 categories (e.g. `fantasy_magic`, `comfort_loss`).
4. Builds a structured “Storytelling setup” prompt and asks the model for a draft.
5. Sends the draft to a **judge** prompt that returns a JSON verdict.
6. If not approved, runs **one revision** based on the judge’s notes, then judges again
   and picks the better draft.
7. Prints the story and lets the user give **free-text feedback** for up to 5 rounds;
   each round revises and re-judges.

All model calls use the original `gpt-3.5-turbo` from the assignment.

## Why each piece

### `story_config.json` (defaults instead of more questions)
- A child won’t want to be quizzed about “narrator,” “tone,” or “ending style” every
  night. Putting these in JSON lets a parent set them once, and the runtime question is
  just the story idea.
- Fields cover the levers I think actually change story quality:
  narrator/voice, where the listener is, child age, tone, length, themes, protagonist
  style, reading pace, language level, ending style, optional names, caregiver note,
  words to include, things to avoid.

### One-question CLI
- README hint: keep input simple. The richer config is decoupled from the prompt the
  child hears, so the experience stays calm.

### Storyteller system prompt
- Explicit bedtime constraints (ages 5–10, gentle vocabulary, short paragraphs, ~length).
- Required ending: a soft lesson **shown** through characters, then a calm wind-down for
  sleep. No cliffhangers.
- Special handling for **death/loss**: keep it gentle, allow comforting framings like
  being with God / heaven, becoming a star or light, or living on in love and memory,
  without forcing one rigid doctrine. This was the user’s own ask and matches how
  caregivers usually frame it for young kids.

### LLM judge
- Returns JSON only (so the program can act on it deterministically): `approved`,
  `score_overall`, `kid_safe`, `age_fit_ok`, `issues`, `strengths`, `revision_brief`.
- Low temperature for consistency.
- If parsing fails, I synthesize a soft “please rewrite” verdict instead of crashing.

### Reviser
- Same model, given the original request + draft + verdict. One pass keeps cost and
  time small while still catching most issues.
- Pipeline keeps whichever draft scores higher (revised wins on ties).

### Classifier + per-category strategy
- README idea: *“Categorize the request and use a tailored generation strategy.”*
- A short JSON-only classification step picks one of: `cozy_everyday`, `adventure_safe`,
  `silly_funny`, `fantasy_magic`, `animals_nature`, `friendship_feelings`,
  `comfort_loss`, `mystery_gentle`. Falls back to `cozy_everyday` if anything goes wrong.
- The matching strategy paragraph is appended to the storyteller, reviser, and reader-
  feedback system prompts, so the same model produces noticeably different *shapes* for
  e.g. silly vs. comfort vs. mystery requests, while staying inside bedtime safety.

### Reader-feedback loop
- README idea: *“Allow the user to provide feedback or request changes.”*
- After the story prints, the user can type natural language changes (e.g. “make it
  shorter,” “bring back the rabbit”). Each round runs the reader-feedback reviser and a
  quick judge so safety/age fit are still checked.
- Limited to 5 rounds (constant in `constants.py`) to bound cost.

### File layout
Started in one big `main.py`, then split for clarity:
- `constants.py`: model name, paths, limits, length hints.
- `prompts.py`: every system prompt + category strategies.
- `llm.py`: OpenAI client wrapper, JSON extractor.
- `story_config.py`: JSON loader, defaults, prompt builder.
- `pipeline.py`: classifier → draft → judge → revise → re-judge.
- `cli.py`: interactive flow + reader feedback loop.
- `main.py`: assignment skeleton (`call_model` + `main`); `main()` launches `cli.main()`.

This way reviewers can read each concern in one screen without scrolling around.

### Secrets & deps
- `.env` for `OPENAI_API_KEY` (also accepts the README’s `OPEN_AI_API_KEY`).
- `.gitignore` excludes `.env` and `venv/`.
- `requirements.txt` lists `openai` and `python-dotenv` so the project is reproducible.

### What I’d do with another ~2 hours
- Auto-trim if the judge flags “too long for bedtime.”
- A small JSONL log of inputs/verdicts for regression checks across many prompts
  (no secrets ever logged).
- Optional read-aloud line breaks for parents who narrate aloud.

## How to run
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# put OPENAI_API_KEY in a local .env (not committed)
python main.py
```

`python main.py` runs the full pipeline. The single-shot `call_model()` is still in
`main.py` for the assignment shape and quick tests.
