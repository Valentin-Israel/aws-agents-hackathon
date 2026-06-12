"""AGORA — the AI government. Streamlit parliament chamber."""

import streamlit as st

from src.parliament import run_pipeline
from src.registry import Registry

st.set_page_config(page_title="AGORA — The AI Government", page_icon="🏛️", layout="wide")

EXAMPLES = [
    ("🛴 Ban e-scooters downtown", "Should e-scooters be banned from the city center?"),
    (
        "📋 Publish fine debtors (veto bait)",
        "Should the city publish the names of all citizens with unpaid parking fines?",
    ),
    ("🌳 Car-free Sundays", "Should the city introduce car-free Sundays in summer?"),
]

VERDICT_BADGE = {"APPROVED": "🟢 APPROVED", "VETO": "🔴 VETO", "STRUCK DOWN": "⚫ STRUCK DOWN"}
VOTE_ICON = {"YES": "✅", "NO": "❌", "ABSTAIN": "⚪"}


class Renderer:
    """Draws one pipeline event at a time, so the session unfolds live."""

    def __init__(self) -> None:
        self._minister_cols = None

    def render(self, ev: dict) -> None:
        stage = ev["stage"]
        if stage == "start":
            st.subheader("1 · Deliberation")
            self._minister_cols = iter(st.columns(4))
        elif stage == "minister":
            m = ev["minister"]
            with next(self._minister_cols):
                st.markdown(f"**{m['emoji']} {m['name']}**  \n*{m['portfolio']}*")
                st.write(ev["position"])
                if ev["amendment"]:
                    st.info(f"Amendment: {ev['amendment']}")
        elif stage == "opposition":
            st.subheader("2 · Opposition — mandated by Art. 3")
            st.warning(ev["text"])
        elif stage == "bill":
            st.subheader("3 · The Bill")
            left, right = st.columns(2)
            left.markdown("**Original petition**")
            left.info(ev["original"])
            right.markdown("**Final bill (Chancellor's merge)**")
            right.success(ev["bill"])
            st.subheader("4 · Vote")
        elif stage == "vote":
            m = ev["minister"]
            st.markdown(
                f"{VOTE_ICON[ev['vote']]} **{m['emoji']} {m['name']}** — "
                f"{ev['vote']}: *{ev['reason']}*"
            )
        elif stage == "tally":
            a, b, c, d = st.columns(4)
            a.metric("YES", ev["yes"])
            b.metric("NO", ev["no"])
            c.metric("ABSTAIN", ev["abstain"])
            d.metric("Result", "PASSED" if ev["passed"] else "REJECTED")
        elif stage == "decree":
            st.subheader(f"5 · Decree {ev['law_id']}")
            st.markdown(ev["text"])
        elif stage == "revision":
            st.subheader("5b · Revised decree (after veto)")
            st.markdown(ev["text"])
        elif stage == "court":
            st.subheader(f"6 · Constitutional Court — round {ev['round']}")
            if ev["verdict"] == "APPROVED":
                st.success(f"**APPROVED** — {ev['opinion']}")
            else:
                st.error(f"**VETO** — {ev['opinion']}")
            st.caption(f"Bench: {ev.get('model', '?')}")
        elif stage == "codified":
            r = ev["record"]
            st.subheader("7 · Codification")
            st.success(
                f"**{r['id']}** entered into the Code of Laws — "
                f"{VERDICT_BADGE.get(r['verdict'], r['verdict'])}"
            )
            st.caption(f"Register backend: {ev['memory']}")


STAGE_LABELS = {
    "minister": "deliberation", "opposition": "hearing the opposition",
    "bill": "drafting the bill", "vote": "voting", "decree": "writing the decree",
    "court": "constitutional review", "revision": "revising after veto",
    "codified": "codification",
}


@st.cache_resource
def get_registry() -> Registry:
    return Registry()  # one instance per server — avoids re-probing Memory on every rerun


def main() -> None:
    st.title("🏛️ AGORA — The AI Government")
    st.caption(
        "Four ministers with conflicting values · mandated opposition · majority vote · "
        "an independent constitutional court on a stronger model · every argument published."
    )

    registry = get_registry()

    with st.sidebar:
        st.header("📜 Code of Laws")
        if not registry.laws:
            st.caption("No laws codified yet.")
        for law in reversed(registry.laws):
            with st.expander(f"{law['id']} · {VERDICT_BADGE.get(law['verdict'], law['verdict'])}"):
                st.markdown(f"**Petition:** {law['petition']}")
                st.markdown(f"**Bill:** {law['bill']}")
                st.caption("Vote — " + ", ".join(
                    f"{v['minister']['name']}: {v['vote']}" for v in law["votes"]))
                st.markdown(f"**Court:** {law['opinion']}")
        st.divider()
        st.caption(f"Register: {registry.memory_status()}")

    petition = st.session_state.get("petition", "")
    for col, (label, text) in zip(st.columns(len(EXAMPLES)), EXAMPLES):
        if col.button(label, use_container_width=True):
            petition = text
    petition = st.text_area(
        "Citizen petition", value=petition, height=80, placeholder="Should the city …?"
    )
    st.session_state["petition"] = petition

    if st.button("⚖️ Convene parliament", type="primary", disabled=not petition.strip()):
        status = st.status("Parliament in session…", expanded=False)
        renderer = Renderer()
        events: list[dict] = []
        for ev in run_pipeline(petition.strip(), registry):
            events.append(ev)
            if ev["stage"] in STAGE_LABELS:
                status.update(label=f"Parliament in session — {STAGE_LABELS[ev['stage']]}…")
            renderer.render(ev)
        status.update(label="Session closed.", state="complete")
        st.session_state["last_run"] = events
        st.rerun()  # refresh so the sidebar picks up the new law

    elif "last_run" in st.session_state:
        renderer = Renderer()
        for ev in st.session_state["last_run"]:
            renderer.render(ev)


if __name__ == "__main__":
    main()
