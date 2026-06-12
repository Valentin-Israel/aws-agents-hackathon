"""Shared infrastructure: model factories, resilient agent calls, JSON parsing."""

import json
import logging
import time

from strands import Agent
from strands.models import BedrockModel

log = logging.getLogger("agora")

REGION = "us-west-2"
# Verified working in this account — no date suffix.
LEGISLATURE_MODEL_ID = "us.anthropic.claude-sonnet-4-6"

# The court runs on the strongest model the account grants. Fable 5 is the
# target but its marketplace agreement is blocked in this sandbox (verified
# Jun 12); the chain self-heals if access appears before the demo.
COURT_MODEL_CANDIDATES = [
    "us.anthropic.claude-fable-5",
    "us.anthropic.claude-opus-4-8",
    "us.anthropic.claude-opus-4-6-v1",  # verified working here
    "us.anthropic.claude-sonnet-4-6",  # last resort: same model as legislature
]


def legislature_model(**overrides) -> BedrockModel:
    cfg = {"temperature": 0.7, "max_tokens": 700, **overrides}
    return BedrockModel(model_id=LEGISLATURE_MODEL_ID, region_name=REGION, **cfg)


def court_model(model_id: str, **overrides) -> BedrockModel:
    cfg = {"temperature": 0.2, "max_tokens": 600, **overrides}
    return BedrockModel(model_id=model_id, region_name=REGION, **cfg)


def make_agent(model: BedrockModel, system_prompt: str) -> Agent:
    # callback_handler=None keeps strands from streaming tokens to stdout.
    return Agent(model=model, system_prompt=system_prompt, callback_handler=None)


def safe_call(agent: Agent, prompt: str, retries: int = 1) -> str | None:
    """Call an agent; one retry on failure; None instead of an exception.

    The live demo must never die on a single throttle or timeout — every
    caller has a scripted fallback for None.
    """
    for attempt in range(retries + 1):
        try:
            return str(agent(prompt)).strip()
        except Exception as exc:  # noqa: BLE001 — anything Bedrock throws
            log.warning("model call failed (attempt %d): %s", attempt + 1, exc)
            if attempt < retries:
                time.sleep(2.0)
    return None


def extract_json(text: str | None) -> dict | None:
    """Pull the first balanced {...} block out of free text and parse it."""
    if not text:
        return None
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    return None
