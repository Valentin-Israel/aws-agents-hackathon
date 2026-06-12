"""Parliamentary procedure: deliberation → opposition → bill → vote → decree
→ constitutional review → codification.

`run_pipeline` is a generator of stage events so the CLI and the Streamlit
chamber can both render the session live. Model calls are sequential:
12 on the happy path, 14 when the court vetoes and the revision loop runs.
"""

from .common import extract_json, legislature_model, make_agent, safe_call
from .court import review
from .ministers import build_cabinet
from .registry import Registry

OPPOSITION_SYSTEM = (
    "You are the Leader of the Opposition in AGORA, an AI government. "
    "Art. 3 of the Constitution mandates: no decision without a steel-manned "
    "counter-argument on the record. Whatever the emerging majority wants, you "
    "argue the strongest honest case AGAINST it — even where you might privately "
    "agree. Sharp, concrete, no straw men."
)

CHANCELLOR_SYSTEM = (
    "You are the Chancellor of AGORA, an AI government. You draft bills and "
    "official decrees in a sober, precise, official register. You merge the "
    "parliament's amendments faithfully and never invent positions ministers "
    "did not take. You output only the requested document, no commentary."
)


def _precedent_lines(precedents: list[dict]) -> str:
    if not precedents:
        return "The Code of Laws is empty. This decision sets founding precedent."
    return "\n".join(
        f"- {p['id']} [{p.get('verdict', '?')}]: {p.get('bill', p.get('petition', ''))[:200]}"
        for p in precedents
    )


def _public(m: dict) -> dict:
    return {"name": m["name"], "emoji": m["emoji"], "portfolio": m["portfolio"]}


def run_pipeline(petition: str, registry: Registry):
    law_id = registry.next_id()
    precedents = registry.recent(3)
    yield {"stage": "start", "petition": petition, "law_id": law_id}
    yield {"stage": "precedents", "laws": precedents}

    # 1 — Deliberation: each minister states a position + optional amendment.
    cabinet = build_cabinet()
    positions = []
    for m, agent in cabinet:
        raw = safe_call(
            agent,
            "A citizen petition has been submitted to the Parliament of AGORA.\n\n"
            f'PETITION: "{petition}"\n\n'
            "PRECEDENT — most recent entries in the Code of Laws (cite by ID if relevant):\n"
            f"{_precedent_lines(precedents)}\n\n"
            f"As {m['name']}, Minister of {m['portfolio']}, state your position "
            "strictly from your value system. Reply with STRICT JSON only:\n"
            '{"position": "<max 60 words, MUST start with FOR, AGAINST or SKEPTICAL>", '
            '"amendment": "<ONE sentence proposing a concrete change, or null>"}',
        )
        data = extract_json(raw) or {}
        position = str(data.get("position") or raw or "SKEPTICAL — the minister could not be reached.").strip()
        amendment = data.get("amendment")
        if not isinstance(amendment, str) or amendment.strip().lower() in ("", "null", "none"):
            amendment = None
        entry = {"minister": _public(m), "position": position, "amendment": amendment}
        positions.append(entry)
        yield {"stage": "minister", **entry}

    # 2 — Mandated opposition (Art. 3): steel-man the case against the majority.
    positions_block = "\n".join(
        f"- {p['minister']['name']} ({p['minister']['portfolio']}): {p['position']}"
        + (f" | Amendment: {p['amendment']}" if p["amendment"] else "")
        for p in positions
    )
    opposition = safe_call(
        make_agent(legislature_model(), OPPOSITION_SYSTEM),
        f'PETITION: "{petition}"\n\nMINISTERS\' POSITIONS:\n{positions_block}\n\n'
        "Identify the emerging majority position and write the single strongest "
        "argument AGAINST it. Max 50 words, plain text, no preamble.",
    ) or "Opposition could not be heard — recorded as a procedural defect under Art. 3."
    yield {"stage": "opposition", "text": opposition}

    # 3 — The bill: the Chancellor merges petition + amendments.
    chancellor = make_agent(legislature_model(max_tokens=1000), CHANCELLOR_SYSTEM)
    bill = safe_call(
        chancellor,
        f'ORIGINAL PETITION: "{petition}"\n\n'
        f"MINISTERS' POSITIONS AND AMENDMENTS:\n{positions_block}\n\n"
        "Merge the petition and the strongest amendments into the final bill. "
        "Improve precision and address the stated concerns. Output ONLY the bill "
        'text, max 120 words, starting with "The Parliament of AGORA enacts:"',
    ) or f"The Parliament of AGORA enacts: {petition} (bill unchanged — drafting service unavailable)."
    yield {"stage": "bill", "original": petition, "bill": bill}

    # 4 — Vote: same agents, so each vote stays consistent with the position argued.
    votes = []
    for m, agent in cabinet:
        raw = safe_call(
            agent,
            "The Chancellor has merged the amendments into the final bill.\n\n"
            f"BILL: {bill}\n\n"
            f"THE OPPOSITION'S OBJECTION (on the record): {opposition}\n\n"
            f"Cast your vote on the bill as {m['name']}. STRICT JSON only:\n"
            '{"vote": "YES" | "NO" | "ABSTAIN", "reason": "<max 15 words>"}',
        )
        data = extract_json(raw) or {}
        vote = str(data.get("vote", "")).upper()
        if vote not in ("YES", "NO", "ABSTAIN"):
            vote = "ABSTAIN"
        reason = str(data.get("reason", "")).strip() or "No reason recorded."
        entry = {"minister": _public(m), "vote": vote, "reason": reason}
        votes.append(entry)
        yield {"stage": "vote", **entry}

    yes = sum(v["vote"] == "YES" for v in votes)
    no = sum(v["vote"] == "NO" for v in votes)
    abstain = len(votes) - yes - no
    passed = yes > no
    result = "PASSED" if passed else "REJECTED"
    yield {"stage": "tally", "yes": yes, "no": no, "abstain": abstain, "passed": passed}

    # 5 — Decree with implementation directive.
    votes_block = "\n".join(
        f"- {v['minister']['name']}: {v['vote']} — {v['reason']}" for v in votes
    )
    decree = safe_call(
        chancellor,
        "The vote on the bill is closed.\n"
        f"RESULT: {result} ({yes} YES / {no} NO / {abstain} ABSTAIN)\n"
        f"VOTES:\n{votes_block}\n\n"
        f'Write the official decree of AGORA, titled "{law_id}". Structure:\n'
        f'1. Title line: "{law_id} — <short name of the matter>"\n'
        "2. Result and exact vote split.\n"
        "3. Core reasoning of the parliament, max 80 words.\n"
        '4. "Implementation Directive:" with Action, Owner, Deadline (one line each, '
        "concrete; synthetic owners and dates are fine).\n"
        + ("" if passed else "The bill was REJECTED: the decree records the rejection and directs no action.\n")
        + "Output only the decree text.",
    ) or (
        f"{law_id} — Decree of Record\nResult: {result} ({yes} YES / {no} NO / {abstain} ABSTAIN).\n"
        f"Bill: {bill}\nImplementation Directive: Action: archive; Owner: Chancellery; Deadline: n/a."
    )
    yield {"stage": "decree", "law_id": law_id, "text": decree}

    # 6 — Constitutional review (strongest granted model), one revision loop on veto.
    verdict = review(decree, precedents, opposition=opposition, votes=votes)
    yield {"stage": "court", "round": 1, **verdict}
    status = verdict["verdict"]
    if verdict["verdict"] == "VETO":
        revised = safe_call(
            chancellor,
            "The Constitutional Court has VETOED the decree.\n"
            f"COURT OPINION: \"{verdict['opinion']}\"\n\n"
            "Amend the decree to fully address the Court's objection while "
            "preserving the parliament's intent. Keep the same title with the "
            'suffix " (Rev. 1)" and the same structure. Output only the revised decree.',
        )
        if revised:
            decree = revised
            yield {"stage": "revision", "text": revised}
            second = review(decree, precedents, opposition=opposition, votes=votes)
            yield {"stage": "court", "round": 2, **second}
            verdict = second
            status = "APPROVED" if second["verdict"] == "APPROVED" else "STRUCK DOWN"
        else:
            status = "STRUCK DOWN"

    # 7 — Codification: everything goes on the record, including struck-down decrees.
    record = registry.codify(
        petition=petition,
        bill=bill,
        decree=decree,
        votes=votes,
        result=result,
        opposition=opposition,
        positions=positions,
        verdict=status,
        opinion=verdict["opinion"],
    )
    yield {"stage": "codified", "record": record, "memory": registry.memory_status()}
