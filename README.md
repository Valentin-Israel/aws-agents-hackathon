# 🏛️ AGORA — The AI Government

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

# Parliament chamber UI
streamlit run app.py
```

## Layout

- `src/ministers.py` — the cabinet: four ministers, fixed value systems
- `src/parliament.py` — the procedure: deliberation → opposition → bill → vote → decree
- `src/court.py` — constitutional review (Fable 5) with veto + one revision loop
- `src/registry.py` — the Code of Laws: `laws.json` source of truth, AgentCore Memory mirror
- `src/cli.py` / `app.py` — terminal runner / Streamlit chamber
