# 🏛️ AGORA — The AI Government 

## https://agora.valentin.is/

🏆 Award: AGORA won 1st Prize at the AWS × Rebura "Build with Agents" Hackathon (Munich, Jun 2026).

Deliberation as infrastructure, built at AWS × Rebura "Build with Agents" (Munich, Jun 2026).
See `WHITEPAPER.md` for the full vision.

Four AI ministers with conflicting value systems debate every citizen petition, a mandated
opposition steel-mans the counter-case, the Chancellor merges amendments into a bill,
parliament votes, and an independent Constitutional Court — running on a stronger model
than the legislature — can veto the decree. Everything is published and codified.

**Separation of powers, separation of models:** legislature on Claude Sonnet 4.6,
Constitutional Court on Claude Fable 5 (Amazon Bedrock, us-west-2).

## Run

```bash
pip install -r requirements.txt

# Full pipeline in the terminal
python3 -m src.cli "Should e-scooters be banned from the city center?"

# Binding citizens' initiative (Art. 1): parliament shapes implementation only —
# it cannot reject or invert the initiative. Only the court can stop it.
# This is the live-veto demo path: the parliament's four value systems otherwise
# sanitize rights-violating petitions before the court ever sees them.
python3 -m src.cli --binding "The city shall publish the full names of all citizens with unpaid parking fines on a public website, updated monthly."

# Parliament chamber UI
streamlit run app.py
```

Demo note: `laws.json` and the AgentCore Memory mirror stay in sync — reset both or
neither. Don't wipe `laws.json` alone: precedent reads come from Memory when active,
and the live-veto arc leans on AGORA-2026-002 (privacy precedent) being on the bench.

## Layout

- `src/ministers.py` — the cabinet: four ministers, fixed value systems
- `src/parliament.py` — the procedure: deliberation → opposition → bill → vote → decree
- `src/court.py` — constitutional review (Fable 5) with veto + one revision loop
- `src/registry.py` — the Code of Laws: `laws.json` source of truth, AgentCore Memory mirror
- `src/cli.py` / `app.py` — terminal runner / Streamlit chamber
