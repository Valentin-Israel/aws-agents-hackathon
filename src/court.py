"""The Constitutional Court — the strongest available Claude, bound by the Constitution."""

import logging
import time

from .common import COURT_MODEL_CANDIDATES, court_model, extract_json, make_agent

log = logging.getLogger("agora")

_active_model: str | None = None  # resolved on first review, then cached

CONSTITUTION = """THE CONSTITUTION OF AGORA
Art. 1 — Human Sovereignty. Final authority remains with humans; any decree may be overridden by referendum.
Art. 2 — Radical Transparency. Every argument, vote and reasoning is published. No closed sessions.
Art. 3 — Mandated Opposition. No decision without a steel-manned counter-argument on the record.
Art. 4 — Precedent Consistency. Decrees must acknowledge and reconcile with prior decisions.
Art. 5 — Fundamental Rights. No decree may violate individual dignity, privacy, or equal treatment."""

COURT_SYSTEM = (
    "You are the Constitutional Court of AGORA — independent of parliament, "
    "the final guardian of the Constitution.\n\n"
    f"{CONSTITUTION}\n\n"
    "You APPROVE a decree unless it violates an article; you VETO when it does, "
    "citing the violated article(s). Violations of Art. 5 — privacy, dignity, "
    "equal treatment — are non-negotiable. Procedural defects matter: a decree "
    "without an opposition argument on the record breaches Art. 3. Binding "
    "citizens' initiatives (Art. 1) are enacted without a parliamentary vote, "
    "yet remain fully subject to your review — fundamental rights bind even "
    "popular majorities. You answer in strict JSON and nothing else."
)


def _precedent_block(precedents: list[dict]) -> str:
    if not precedents:
        return "No prior laws. This decree sets founding precedent."
    return "\n".join(
        f"- {p['id']} [{p.get('verdict', '?')}]: {p.get('bill', p.get('petition', ''))[:200]}"
        for p in precedents
    )


def _call_court(prompt: str) -> tuple[str | None, str | None]:
    """Try court models strongest-first; skip ones this account doesn't grant.

    AccessDenied is permanent for the session, so the working model is cached.
    Other errors get one retry before falling through.
    """
    global _active_model
    candidates = [_active_model] if _active_model else COURT_MODEL_CANDIDATES
    for model_id in candidates:
        for attempt in range(2):
            try:
                agent = make_agent(court_model(model_id), COURT_SYSTEM)
                raw = str(agent(prompt)).strip()
                _active_model = model_id
                return raw, model_id
            except Exception as exc:  # noqa: BLE001
                if "AccessDenied" in str(exc):
                    log.warning("court model %s not granted here, trying next", model_id)
                    break
                log.warning("court call failed (attempt %d): %s", attempt + 1, exc)
                if attempt == 0:
                    time.sleep(2.0)
    return None, None


def review(decree: str, precedents: list[dict], session_record: str = "") -> dict:
    # The court reviews the decree together with the session record — without
    # it, Art. 3 (opposition on the record) looks violated on every decree.
    prompt = (
        "Review this decree of the Parliament of AGORA.\n\n"
        f"DECREE:\n{decree}\n\n"
        f"{session_record}"
        f"EXISTING CODE OF LAWS (precedent):\n{_precedent_block(precedents)}\n\n"
        "Check the decree against every article of the Constitution and against "
        "precedent. Reply with STRICT JSON only:\n"
        '{"verdict": "APPROVED" | "VETO", '
        '"opinion": "<max 60 words; if VETO, cite the violated article(s)>"}'
    )
    raw, model_id = _call_court(prompt)
    if raw is None:
        # Court unreachable — the demo continues under human supervision.
        return {
            "verdict": "APPROVED",
            "opinion": "Court unavailable; provisional approval pending human review under Art. 1.",
            "model": "unavailable",
        }
    data = extract_json(raw) or {}
    verdict = str(data.get("verdict", "")).upper()
    if verdict not in ("APPROVED", "VETO"):
        verdict = "VETO" if "VETO" in raw.upper() else "APPROVED"
    opinion = str(data.get("opinion") or raw).strip()[:400]
    return {"verdict": verdict, "opinion": opinion, "model": model_id}
