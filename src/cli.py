"""Run the full AGORA pipeline from the terminal.

    python3 -m src.cli "Should e-scooters be banned from the city center?"
"""

import argparse
import logging

from .parliament import run_pipeline
from .registry import Registry


def _rule(title: str) -> None:
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}")


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="AGORA — the AI government")
    parser.add_argument("petition", help="citizen petition, plain language")
    args = parser.parse_args()

    registry = Registry()
    voting_open = False
    for ev in run_pipeline(args.petition, registry):
        stage = ev["stage"]
        if stage == "vote" and not voting_open:
            _rule("VOTE")
            voting_open = True
        if stage == "start":
            _rule(f"PETITION  ({ev['law_id']})")
            print(ev["petition"])
        elif stage == "precedents":
            if ev["laws"]:
                print("\nPrecedent on the bench:")
                for p in ev["laws"]:
                    print(f"  - {p['id']} [{p.get('verdict', '?')}]")
        elif stage == "minister":
            m = ev["minister"]
            print(f"\n{m['emoji']} {m['name']} ({m['portfolio']}):\n   {ev['position']}")
            if ev["amendment"]:
                print(f"   Amendment: {ev['amendment']}")
        elif stage == "opposition":
            _rule("OPPOSITION (Art. 3 — mandated counter-argument)")
            print(ev["text"])
        elif stage == "bill":
            _rule("THE BILL (Chancellor's merge)")
            print(ev["bill"])
        elif stage == "vote":
            m = ev["minister"]
            print(f"  {m['emoji']} {m['name']}: {ev['vote']} — {ev['reason']}")
        elif stage == "tally":
            print(
                f"\n  RESULT: {'PASSED' if ev['passed'] else 'REJECTED'} "
                f"({ev['yes']} YES / {ev['no']} NO / {ev['abstain']} ABSTAIN)"
            )
        elif stage == "decree":
            _rule(f"DECREE {ev['law_id']}")
            print(ev["text"])
        elif stage == "revision":
            _rule("REVISED DECREE (after veto)")
            print(ev["text"])
        elif stage == "court":
            _rule(f"CONSTITUTIONAL COURT — round {ev['round']} (bench: {ev.get('model', '?')})")
            print(f"VERDICT: {ev['verdict']}\nOPINION: {ev['opinion']}")
        elif stage == "codified":
            _rule("CODIFIED")
            r = ev["record"]
            print(f"{r['id']} → {r['verdict']}  (register: {ev['memory']})")


if __name__ == "__main__":
    main()
