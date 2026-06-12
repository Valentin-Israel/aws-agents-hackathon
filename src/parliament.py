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


def run_pipeline(petition: str, registry: Registry, binding: bool = False):
    """Full procedure for one petition.

    binding=True runs the petition as a binding citizens' initiative under
    Art. 1 (Human Sovereignty): parliament debates and shapes implementation
    but cannot reject or invert the core mechanism, and no minister vote is
    taken — only the Constitutional Court can stop it.
    """
    law_id = registry.next_id()
    precedents = registry.recent(3)
    yield {"stage": "start", "petition": petition, "law_id": law_id, "binding": binding}
    yield {"stage": "precedents", "laws": precedents}

    binding_note = (
        "\nThis petition is a BINDING CITIZENS' INITIATIVE under Art. 1 "
        "(Human Sovereignty): parliament cannot reject or invert it. Your "
        "amendment may only shape HOW it is implemented.\n"
        if binding
        else ""
    )

    # 1 — Deliberation: each minister states a position + optional amendment.
    cabinet = build_cabinet()
    positions = []
    for m, agent in cabinet:
        raw = safe_call(
            agent,
            "A citizen petition has been submitted to the Parliament of AGORA.\n\n"
            f'PETITION: "{petition}"\n{binding_note}\n'
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
    if binding:
        bill_instruction = (
            "This is a BINDING CITIZENS' INITIATIVE under Art. 1: the bill MUST "
            "enact the petition's core mechanism as written. Amendments may "
            "regulate HOW it operates (scope, process, timing) but must not "
            "prevent, indefinitely defer, or neutralize its operation. When in "
            "doubt, enact the initiative as written."
        )
        bill_opening = "By binding citizens' initiative, AGORA enacts:"
    else:
        bill_instruction = (
            "Merge the petition and the strongest amendments into the final bill. "
            "CRITICAL CONSTRAINT: you are a drafter, not a judge. You MUST preserve "
            "the petition's core mechanism — the thing the citizen actually asked for. "
            "Amendments may narrow scope, add process, set conditions or thresholds, "
            "but may NOT eliminate, reverse, or replace the core mechanism. If the "
            "petition asks for a ban, the bill must still contain a ban (perhaps "
            "narrowed). If it asks for a tax, the bill must still contain a tax. "
            "It is the parliament's vote — not yours — that decides whether to enact it."
        )
        bill_opening = "The Parliament of AGORA enacts:"
    bill = safe_call(
        chancellor,
        f'ORIGINAL PETITION: "{petition}"\n\n'
        f"MINISTERS' POSITIONS AND AMENDMENTS:\n{positions_block}\n\n"
        f"{bill_instruction} Output ONLY the bill "
        f'text, max 120 words, starting with "{bill_opening}"',
    ) or f"{bill_opening} {petition} (bill unchanged — drafting service unavailable)."
    yield {"stage": "bill", "original": petition, "bill": bill}

    # 4 — Vote. A binding initiative was already decided by the citizens
    # (Art. 1); ministers vote only in the parliamentary procedure.
    votes = []
    if binding:
        passed, result = True, "ENACTED BY CITIZENS' INITIATIVE"
        yield {"stage": "tally", "yes": 0, "no": 0, "abstain": 0, "passed": True, "binding": True}
    else:
        for (m, agent), pos in zip(cabinet, positions):
            raw = safe_call(
                agent,
                "The Chancellor has produced the final bill. You must now vote.\n\n"
                f"ORIGINAL PETITION (what the citizen asked for): {petition}\n\n"
                f"FINAL BILL:\n{bill}\n\n"
                f"YOUR POSITION DURING DELIBERATION: {pos['position']}\n\n"
                "VOTING RULES — you hold fixed values and vote your conscience:\n"
                "1. First ask: does the bill still enact the core intent of the "
                "original petition, or has it become something fundamentally different?\n"
                "2. If you said AGAINST the petition and the bill still executes its "
                "core intent (even with conditions added), vote NO. Conditions, audits, "
                "caps and sunset clauses do not resolve a fundamental value objection — "
                "they just soften something you still oppose.\n"
                "3. Only vote YES on an AGAINST position if the bill has abandoned or "
                "reversed the specific mechanism you objected to — not merely "
                "restricted it.\n"
                "4. If you said FOR or SKEPTICAL and the bill broadly aligns with your "
                "values, vote YES.\n"
                "5. Vote ABSTAIN only if the bill's effect on your portfolio is "
                "genuinely indeterminate.\n\n"
                f"Cast your vote as {m['name']}. STRICT JSON only:\n"
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
    if binding:
        result_line = "RESULT: ENACTED by binding citizens' initiative (Art. 1 — Human Sovereignty)."
    else:
        votes_block = "\n".join(
            f"- {v['minister']['name']}: {v['vote']} — {v['reason']}" for v in votes
        )
        result_line = f"RESULT: {result} ({yes} YES / {no} NO / {abstain} ABSTAIN)\nVOTES:\n{votes_block}"
    decree = safe_call(
        chancellor,
        "The decision on the bill is closed.\n"
        f"{result_line}\n\n"
        f'Write the official decree of AGORA, titled "{law_id}". Structure:\n'
        f'1. Title line: "{law_id} — <short name of the matter>"\n'
        "2. Result" + ("" if binding else " and exact vote split") + ".\n"
        "3. Core reasoning, max 80 words.\n"
        '4. "Implementation Directive:" with Action, Owner, Deadline (one line each, '
        "concrete; synthetic owners and dates are fine).\n"
        + ("" if passed else "The bill was REJECTED: the decree records the rejection and directs no action.\n")
        + "Output only the decree text.",
    ) or (
        f"{law_id} — Decree of Record\n{result_line}\n"
        f"Bill: {bill}\nImplementation Directive: Action: archive; Owner: Chancellery; Deadline: n/a."
    )
    yield {"stage": "decree", "law_id": law_id, "text": decree}

    # 6 — Constitutional review (strongest granted model), one revision loop on veto.
    session_record = f"OPPOSITION ARGUMENT ON THE RECORD (Art. 3):\n{opposition}\n\n"
    if binding:
        session_record += (
            "ENACTMENT: binding citizens' initiative under Art. 1 (Human "
            "Sovereignty) — no parliamentary vote is required for such initiatives.\n\n"
        )
    else:
        session_record += "VOTE RECORD:\n" + "\n".join(
            f"- {v['minister']['name']}: {v['vote']} — {v['reason']}" for v in votes
        ) + "\n\n"
    verdict = review(decree, precedents, session_record)
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
            second = review(decree, precedents, session_record)
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
        mode="citizens-initiative" if binding else "parliamentary",
        result=result,
        opposition=opposition,
        positions=positions,
        verdict=status,
        opinion=verdict["opinion"],
    )
    yield {"stage": "codified", "record": record, "memory": registry.memory_status()}
