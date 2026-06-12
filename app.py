"""AGORA — the AI government. Streamlit parliament chamber."""

import streamlit as st

from src.parliament import run_pipeline
from src.registry import Registry

st.set_page_config(
    page_title="AGORA — The AI Government",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
[data-testid="stAppViewContainer"] { background: #f7f8fa; }
[data-testid="stSidebar"] { background: #0a0a1a; }
[data-testid="stSidebar"] * { color: #e0e4f0 !important; }
[data-testid="stSidebar"] hr { border-color: #1e2240; }
[data-testid="stSidebar"] .stExpander { border: 1px solid #1e2240 !important; background: #0f102a; border-radius: 8px !important; margin-bottom: 6px; }
[data-testid="stSidebar"] [data-testid="stExpanderToggleIcon"] svg { fill: #6070c0 !important; }
[data-testid="stSidebarUserContent"] h2 { color: #8899ff !important; font-size: 1rem !important; letter-spacing: .12em; text-transform: uppercase; }
[data-testid="stSidebarUserContent"] caption { color: #505880 !important; }

/* ── Top header ── */
.agora-hero { padding: 2.5rem 0 1.5rem; text-align: center; }
.agora-hero h1 { font-size: 2.8rem; font-weight: 800; color: #000066; letter-spacing: -.02em; margin: 0; }
.agora-hero .tagline { color: #005577; font-size: 1.05rem; margin-top: .4rem; font-weight: 500; }
.agora-hero .sub { color: #667; font-size: .85rem; margin-top: .3rem; }

/* ── Section headers ── */
.section-header {
    display: flex; align-items: center; gap: .6rem;
    border-left: 4px solid #000066; padding: .6rem 0 .6rem 1rem;
    margin: 2rem 0 1rem; background: linear-gradient(90deg, #f0f2ff 0%, transparent 100%);
    border-radius: 0 6px 6px 0;
}
.section-header .num { background: #000066; color: #fff; border-radius: 50%;
    width: 28px; height: 28px; display: inline-flex; align-items: center;
    justify-content: center; font-size: .8rem; font-weight: 700; flex-shrink: 0; }
.section-header .title { font-size: 1.05rem; font-weight: 700; color: #000066; }
.section-header .sub { font-size: .78rem; color: #005577; font-style: italic; }

/* ── Minister cards ── */
.minister-card {
    background: #fff; border: 1px solid #e2e6f0; border-radius: 12px;
    padding: 1.1rem 1rem; height: 100%; box-shadow: 0 1px 4px rgba(0,0,102,.06);
    position: relative; overflow: hidden;
}
.minister-card .m-emoji { font-size: 1.8rem; }
.minister-card .m-name { font-weight: 700; color: #000066; font-size: .95rem; margin: .3rem 0 0; }
.minister-card .m-role { color: #005577; font-size: .75rem; text-transform: uppercase;
    letter-spacing: .06em; margin-bottom: .6rem; }
.minister-card .m-stance { display: inline-block; font-size: .72rem; font-weight: 700;
    padding: .15rem .5rem; border-radius: 20px; margin-bottom: .5rem; }
.stance-FOR { background: #d4edda; color: #155724; }
.stance-AGAINST { background: #f8d7da; color: #721c24; }
.stance-SKEPTICAL { background: #fff3cd; color: #856404; }
.minister-card .m-text { font-size: .82rem; color: #333; line-height: 1.5; }
.minister-card .m-amendment { margin-top: .6rem; padding: .5rem .7rem;
    background: #f0f4ff; border-left: 3px solid #005577; border-radius: 0 6px 6px 0;
    font-size: .78rem; color: #005577; font-style: italic; }
.minister-card.voted-yes { border-color: #28a745; }
.minister-card.voted-no  { border-color: #dc3545; }
.minister-card.voted-abs { border-color: #999; }

/* ── Opposition block ── */
.opposition-block {
    background: #1a0a00; color: #ffd580; border-radius: 10px;
    padding: 1.1rem 1.3rem; border-left: 4px solid #ff6b00;
    font-size: .88rem; line-height: 1.6; font-style: italic;
}
.opposition-block .opp-label { font-size: .7rem; font-weight: 700; color: #ff9940;
    text-transform: uppercase; letter-spacing: .1em; margin-bottom: .4rem; }

/* ── Bill diff ── */
.bill-col { border-radius: 10px; padding: 1rem 1.1rem; font-size: .84rem; line-height: 1.6; }
.bill-original { background: #f8f8f8; border: 1px solid #ddd; color: #555; }
.bill-final { background: #eaf6ee; border: 1px solid #81c784; color: #1b3a1e; }
.bill-label { font-size: .7rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .1em; margin-bottom: .4rem; }
.bill-original .bill-label { color: #888; }
.bill-final .bill-label   { color: #2e7d32; }

/* ── Vote row ── */
.vote-row { display: flex; align-items: center; gap: .7rem;
    padding: .5rem .8rem; border-radius: 8px; margin-bottom: .4rem;
    background: #fff; border: 1px solid #eee; }
.vote-icon { font-size: 1.1rem; width: 1.5rem; text-align: center; }
.vote-name { font-weight: 600; color: #000066; font-size: .88rem; flex: 1; }
.vote-pill { font-size: .72rem; font-weight: 700; padding: .15rem .55rem;
    border-radius: 20px; flex-shrink: 0; }
.pill-YES  { background: #d4edda; color: #155724; }
.pill-NO   { background: #f8d7da; color: #721c24; }
.pill-ABS  { background: #e9ecef; color: #495057; }
.vote-reason { font-size: .78rem; color: #555; flex: 2; }

/* ── Tally ── */
.tally-bar { border-radius: 12px; padding: 1.2rem 1.5rem;
    display: flex; align-items: center; gap: 2rem; margin: 1rem 0; }
.tally-pass { background: linear-gradient(135deg, #d4edda, #c3e6cb); border: 2px solid #28a745; }
.tally-fail { background: linear-gradient(135deg, #f8d7da, #f5c6cb); border: 2px solid #dc3545; }
.tally-result { font-size: 1.4rem; font-weight: 800; }
.tally-pass .tally-result { color: #155724; }
.tally-fail .tally-result { color: #721c24; }
.tally-count { text-align: center; }
.tally-count .tc-num { font-size: 1.6rem; font-weight: 800; }
.tc-yes  { color: #28a745; }
.tc-no   { color: #dc3545; }
.tc-abs  { color: #6c757d; }
.tally-count .tc-label { font-size: .7rem; text-transform: uppercase;
    letter-spacing: .08em; color: #666; }

/* ── Decree ── */
.decree-box {
    background: #fff; border: 1px solid #c8d0e8; border-radius: 12px;
    padding: 1.6rem 2rem; position: relative; box-shadow: 0 2px 12px rgba(0,0,102,.08);
}
.decree-box::before { content: ""; position: absolute; top: 0; left: 0; right: 0;
    height: 5px; background: linear-gradient(90deg, #000066, #005577); border-radius: 12px 12px 0 0; }
.decree-id { font-size: .75rem; font-weight: 700; color: #005577;
    text-transform: uppercase; letter-spacing: .1em; margin-bottom: .3rem; }
.decree-content { font-size: .86rem; line-height: 1.7; color: #1a1a2e; }

/* ── Court verdict ── */
.court-approved {
    background: linear-gradient(135deg, #d4edda, #eaf6ee); border: 2px solid #28a745;
    border-radius: 12px; padding: 1.4rem 1.6rem;
}
.court-veto {
    background: linear-gradient(135deg, #f8d7da, #fdecea); border: 2px solid #dc3545;
    border-radius: 12px; padding: 1.4rem 1.6rem;
}
.court-verdict-label { font-size: .75rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .12em; margin-bottom: .4rem; }
.court-approved .court-verdict-label { color: #155724; }
.court-veto .court-verdict-label     { color: #721c24; }
.court-verdict-text { font-size: 1.4rem; font-weight: 800; margin-bottom: .5rem; }
.court-approved .court-verdict-text { color: #155724; }
.court-veto .court-verdict-text     { color: #721c24; }
.court-opinion { font-size: .84rem; color: #333; line-height: 1.5; }
.court-model   { font-size: .72rem; color: #888; margin-top: .5rem; }

/* ── Codification ── */
.codified-box {
    background: linear-gradient(135deg, #f0f2ff, #e8ecff); border: 2px solid #000066;
    border-radius: 12px; padding: 1.2rem 1.6rem; text-align: center;
}
.codified-id { font-size: 1.5rem; font-weight: 800; color: #000066; }
.codified-badge { display: inline-block; font-size: .85rem; font-weight: 700;
    padding: .3rem .9rem; border-radius: 20px; margin: .4rem 0; }
.badge-APPROVED    { background: #28a745; color: #fff; }
.badge-STRUCK_DOWN { background: #dc3545; color: #fff; }
.codified-meta { font-size: .75rem; color: #667; margin-top: .3rem; }

/* ── Binding notice ── */
.binding-notice {
    background: #0a0a1a; color: #c8d0ff; border: 1px solid #3040a0;
    border-radius: 10px; padding: 1rem 1.3rem; margin-bottom: 1rem;
    font-size: .86rem; line-height: 1.5;
}
.binding-notice strong { color: #8899ff; }

/* ── Input area ── */
.stTextArea textarea { border: 1.5px solid #c8d0e8 !important; border-radius: 10px !important;
    font-size: .9rem !important; background: #fff !important; }
.stTextArea textarea:focus { border-color: #000066 !important; box-shadow: 0 0 0 2px rgba(0,0,102,.15) !important; }

/* ── Sidebar law card ── */
.law-card { padding: .4rem 0; }
.law-card .lc-id { font-size: .72rem; font-weight: 700; color: #8899ff; letter-spacing: .06em; }
.law-card .lc-petition { font-size: .78rem; color: #aab0cc; margin: .2rem 0; line-height: 1.4; }
.law-card .lc-verdict { font-size: .7rem; font-weight: 700; padding: .1rem .4rem;
    border-radius: 10px; display: inline-block; }
.lv-APPROVED    { background: #1a3a1a; color: #66cc66; }
.lv-STRUCK_DOWN { background: #3a1a1a; color: #cc6666; }

/* Hide Streamlit chrome we don't need */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

EXAMPLES = [
    ("🛴  Ban e-scooters downtown", "Should e-scooters be banned from the city center?", False),
    (
        "📋  Initiative: publish fine debtors",
        "The city shall publish the full names of all citizens with unpaid parking "
        "fines on a public website, updated monthly.",
        True,
    ),
    ("🌳  Car-free Sundays", "Should the city introduce car-free Sundays in summer?", False),
]

VERDICT_BADGE_CSS = {"APPROVED": "badge-APPROVED", "STRUCK DOWN": "badge-STRUCK_DOWN"}
VOTE_ICON = {"YES": "✅", "NO": "❌", "ABSTAIN": "⚪"}
VOTE_PILL = {"YES": "pill-YES", "NO": "pill-NO", "ABSTAIN": "pill-ABS"}

def _stance(text: str) -> str:
    t = text.upper()
    if t.startswith("FOR"): return "FOR"
    if t.startswith("AGAINST"): return "AGAINST"
    return "SKEPTICAL"

def _section(num: int, title: str, sub: str = "") -> None:
    sub_html = f'<span class="sub"> · {sub}</span>' if sub else ""
    st.markdown(f"""
<div class="section-header">
  <span class="num">{num}</span>
  <div><span class="title">{title}</span>{sub_html}</div>
</div>""", unsafe_allow_html=True)


class Renderer:
    def __init__(self) -> None:
        self._minister_data: list[dict] = []
        self._minister_placeholders: list = []
        self._binding = False

    def render(self, ev: dict) -> None:
        stage = ev["stage"]

        if stage == "start":
            self._binding = bool(ev.get("binding"))
            if self._binding:
                st.markdown("""<div class="binding-notice">
🗳️ <strong>Binding citizens' initiative — Art. 1 (Human Sovereignty)</strong><br>
Parliament debates and shapes implementation only. Ministers do not vote.
Only the Constitutional Court can stop this initiative.
</div>""", unsafe_allow_html=True)
            _section(1, "Deliberation", "four ministers argue from fixed value systems")
            cols = st.columns(4)
            self._minister_placeholders = [c.empty() for c in cols]
            self._minister_data = []

        elif stage == "minister":
            m = ev["minister"]
            stance = _stance(ev["position"])
            amend_html = ""
            if ev["amendment"]:
                amend_html = f'<div class="m-amendment">📝 {ev["amendment"]}</div>'
            card_html = f"""<div class="minister-card">
  <div class="m-emoji">{m['emoji']}</div>
  <div class="m-name">{m['name']}</div>
  <div class="m-role">{m['portfolio']}</div>
  <span class="m-stance stance-{stance}">{stance}</span>
  <div class="m-text">{ev['position']}</div>
  {amend_html}
</div>"""
            idx = len(self._minister_data)
            self._minister_data.append({"m": m, "ev": ev, "stance": stance, "html": card_html})
            self._minister_placeholders[idx].markdown(card_html, unsafe_allow_html=True)

        elif stage == "opposition":
            _section(2, "Opposition", "Art. 3 — strongest case against the majority")
            st.markdown(f"""<div class="opposition-block">
  <div class="opp-label">⚔️ Leader of the Opposition</div>
  {ev['text']}
</div>""", unsafe_allow_html=True)

        elif stage == "bill":
            _section(3, "The Bill", "Chancellor merges petition + amendments")
            c1, c2 = st.columns(2)
            c1.markdown(f"""<div class="bill-col bill-original">
  <div class="bill-label">Original petition</div>
  {ev['original']}
</div>""", unsafe_allow_html=True)
            c2.markdown(f"""<div class="bill-col bill-final">
  <div class="bill-label">✦ Final bill</div>
  {ev['bill']}
</div>""", unsafe_allow_html=True)
            _section(4,
                "Enactment" if self._binding else "Vote",
                "citizens' initiative" if self._binding else "each minister votes their conscience")

        elif stage == "vote":
            m = ev["minister"]
            v = ev["vote"]
            st.markdown(f"""<div class="vote-row">
  <span class="vote-icon">{VOTE_ICON[v]}</span>
  <span class="vote-name">{m['emoji']} {m['name']}</span>
  <span class="vote-pill {VOTE_PILL[v]}">{v}</span>
  <span class="vote-reason">{ev['reason']}</span>
</div>""", unsafe_allow_html=True)
            # Also update the minister card to show vote colour
            for i, d in enumerate(self._minister_data):
                if d["m"]["name"] == m["name"]:
                    css_cls = {"YES": "voted-yes", "NO": "voted-no", "ABSTAIN": "voted-abs"}.get(v, "")
                    updated = d["html"].replace('class="minister-card"', f'class="minister-card {css_cls}"')
                    self._minister_placeholders[i].markdown(updated, unsafe_allow_html=True)
                    d["html"] = updated

        elif stage == "tally":
            if ev.get("binding"):
                st.markdown("""<div class="binding-notice">
🗳️ <strong>ENACTED</strong> by binding citizens' initiative — Art. 1 (Human Sovereignty).
No parliamentary vote. Only the Constitutional Court can stop it.
</div>""", unsafe_allow_html=True)
            else:
                yes, no, abstain = ev["yes"], ev["no"], ev["abstain"]
                passed = ev["passed"]
                cls = "tally-pass" if passed else "tally-fail"
                label = "✦ PASSED" if passed else "✗ REJECTED"
                st.markdown(f"""<div class="tally-bar {cls}">
  <div class="tally-result">{label}</div>
  <div class="tally-count"><div class="tc-num tc-yes">{yes}</div><div class="tc-label">YES</div></div>
  <div class="tally-count"><div class="tc-num tc-no">{no}</div><div class="tc-label">NO</div></div>
  <div class="tally-count"><div class="tc-num tc-abs">{abstain}</div><div class="tc-label">ABSTAIN</div></div>
</div>""", unsafe_allow_html=True)

        elif stage == "decree":
            _section(5, f"Decree {ev['law_id']}", "official record of parliament's decision")
            text_html = ev["text"].replace("\n", "<br>")
            st.markdown(f"""<div class="decree-box">
  <div class="decree-id">{ev['law_id']}</div>
  <div class="decree-content">{text_html}</div>
</div>""", unsafe_allow_html=True)

        elif stage == "revision":
            _section("5b", "Revised decree", "amended after constitutional veto")
            text_html = ev["text"].replace("\n", "<br>")
            st.markdown(f"""<div class="decree-box">
  <div class="decree-id">REVISED</div>
  <div class="decree-content">{text_html}</div>
</div>""", unsafe_allow_html=True)

        elif stage == "court":
            rnd = ev["round"]
            _section(6, f"Constitutional Court — round {rnd}", "independent review against the Constitution")
            verdict = ev["verdict"]
            css = "court-approved" if verdict == "APPROVED" else "court-veto"
            verdict_label = "✦ APPROVED" if verdict == "APPROVED" else "⊘ VETO"
            st.markdown(f"""<div class="{css}">
  <div class="court-verdict-label">Constitutional Court · round {rnd}</div>
  <div class="court-verdict-text">{verdict_label}</div>
  <div class="court-opinion">{ev['opinion']}</div>
  <div class="court-model">Bench: {ev.get('model', '?')}</div>
</div>""", unsafe_allow_html=True)

        elif stage == "codified":
            r = ev["record"]
            _section(7, "Codification", "entered into the Code of Laws")
            verdict_css = VERDICT_BADGE_CSS.get(r["verdict"], "badge-APPROVED")
            st.markdown(f"""<div class="codified-box">
  <div class="codified-id">{r['id']}</div>
  <div><span class="codified-badge {verdict_css}">{r['verdict']}</span></div>
  <div class="codified-meta">{ev['memory']}</div>
</div>""", unsafe_allow_html=True)
            st.balloons()


STAGE_LABELS = {
    "minister": "deliberation", "opposition": "hearing the opposition",
    "bill": "drafting the bill", "vote": "voting", "decree": "writing the decree",
    "court": "constitutional review", "revision": "revising after veto",
    "codified": "codification",
}


@st.cache_resource
def get_registry() -> Registry:
    return Registry()


def sidebar(registry: Registry) -> None:
    with st.sidebar:
        st.markdown("## 📜 Code of Laws")
        laws = registry.laws
        if not laws:
            st.caption("No laws codified yet. Convene parliament to create the first.")
        for law in reversed(laws):
            verdict = law.get("verdict", "?")
            verdict_css = "lv-APPROVED" if verdict == "APPROVED" else "lv-STRUCK_DOWN"
            vote_summary = (
                " · ".join(f"{v['minister']['name']}: {v['vote']}" for v in law["votes"])
                if law["votes"]
                else "Binding initiative — no vote"
            )
            with st.expander(f"{law['id']}  {verdict}"):
                st.markdown(f"""<div class="law-card">
  <div class="lc-id">{law['id']} &nbsp;<span class="lc-verdict {verdict_css}">{verdict}</span></div>
  <div class="lc-petition">"{law['petition'][:120]}{'…' if len(law['petition'])>120 else ''}"</div>
  <div style="font-size:.72rem;color:#506;margin:.2rem 0">{vote_summary}</div>
  <div style="font-size:.75rem;color:#7a88b0;margin-top:.3rem;line-height:1.4">{law['opinion'][:160]}{'…' if len(law['opinion'])>160 else ''}</div>
</div>""", unsafe_allow_html=True)
        st.divider()
        st.caption(f"⚙️ {registry.memory_status()}")


def main() -> None:
    sidebar(get_registry())

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""<div class="agora-hero">
  <h1>🏛️ AGORA</h1>
  <div class="tagline">The AI Government · Deliberation as Infrastructure</div>
  <div class="sub">Four ministers · mandated opposition · constitutional court · every argument published</div>
</div>""", unsafe_allow_html=True)

    st.divider()

    # ── Input ─────────────────────────────────────────────────────────────────
    ex_cols = st.columns(len(EXAMPLES))
    for col, (label, text, ex_binding) in zip(ex_cols, EXAMPLES):
        if col.button(label, use_container_width=True):
            st.session_state["petition"] = text
            st.session_state["binding"] = ex_binding
            st.rerun()

    st.session_state.setdefault("petition", "")
    st.session_state.setdefault("binding", False)

    petition = st.text_area(
        "Citizen petition",
        value=st.session_state["petition"],
        height=90,
        placeholder="Should the city …?  ·  The city shall …",
        label_visibility="collapsed",
    )
    st.session_state["petition"] = petition

    col_toggle, col_btn, col_new = st.columns([3, 1, 1])
    with col_toggle:
        binding = st.toggle(
            "🗳️  Binding citizens' initiative — Art. 1 (parliament shapes implementation only; "
            "court alone can stop it)",
            key="binding",
        )
    with col_btn:
        convene = st.button(
            "⚖️  Convene parliament",
            type="primary",
            disabled=not petition.strip(),
            use_container_width=True,
        )
    with col_new:
        if st.session_state.get("last_run") and st.button(
            "＋  New petition", use_container_width=True
        ):
            st.session_state.pop("last_run", None)
            st.session_state["petition"] = ""
            st.session_state["binding"] = False
            st.rerun()

    st.divider()

    # ── Session ───────────────────────────────────────────────────────────────
    registry = get_registry()

    if convene:
        st.session_state.pop("last_run", None)
        events: list[dict] = []
        renderer = Renderer()
        status = st.status("Parliament convened — session in progress…", expanded=False)
        for ev in run_pipeline(petition.strip(), registry, binding=binding):
            events.append(ev)
            if ev["stage"] in STAGE_LABELS:
                status.update(label=f"Parliament in session · {STAGE_LABELS[ev['stage']]}…")
            renderer.render(ev)
        status.update(label="Session closed.", state="complete")
        st.session_state["last_run"] = events
        st.rerun()

    elif "last_run" in st.session_state:
        renderer = Renderer()
        for ev in st.session_state["last_run"]:
            renderer.render(ev)


if __name__ == "__main__":
    main()
