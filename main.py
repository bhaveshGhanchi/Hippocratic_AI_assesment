import os
import openai

from dotenv import load_dotenv

load_dotenv()

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

If I had ~2 more hours: optional read-aloud line breaks, auto-trim when the judge says "too long,"
and a small local jsonl log of runs for regression tests (never logging secrets). The full
storyteller + judge + category + reader-feedback flow lives in cli.py and is launched from
main() below. The single-shot call_model() is kept for the assignment skeleton / quick tests.
"""

# openai-python v1+ uses the client class; ChatCompletion.create was removed.
_oai_client: openai.OpenAI | None = None

_SIMPLE_BEDTIME_SYSTEM = """You write short bedtime stories for children about ages 5-10.
Use warm, simple language and a gentle tone. Write a single fictional story — not a
definition, encyclopedia entry, or list of facts unless the child asks inside the story.
End in a calm, reassuring way suitable for sleep. Keep it safe and cozy."""


def call_model(prompt: str, max_tokens=3000, temperature=0.85) -> str:
    global _oai_client
    key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
    if _oai_client is None:
        if not key:
            raise RuntimeError(
                "No API key found. Set OPENAI_API_KEY (or OPEN_AI_API_KEY); see README."
            )
        _oai_client = openai.OpenAI(api_key=key)
    user_msg = (
        "Write a bedtime story based on this request. Only output the story.\n\n"
        f"Request: {prompt.strip()}"
    )
    resp = _oai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": _SIMPLE_BEDTIME_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    content = resp.choices[0].message.content
    return content if content is not None else ""


example_requests = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."


def main():
    from cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()
