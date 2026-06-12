# core/ui.py
"""Görsel katman: sidebar tamamen gizli, ilerleme üstte yatay stepper."""

import streamlit as st

STAGES = [("pvt", "PVT"), ("gonogo", "Go/No-Go"), ("dual", "Dual Task")]

CSS = """
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none !important; }
#MainMenu, footer, header { visibility:hidden; }
.block-container { max-width: 760px; padding-top: 1.2rem; }
iframe[height="0"] { display:none; }              /* st_javascript artıkları */
.stApp { background:#0A0F1E; }
h1,h2,h3,p,div { color:#F0F4FF; }
kbd { background:#1A2235; border-radius:4px; padding:1px 6px; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def header(candidate_id: str = ""):
    sub = f"Aktif aday: <b style='color:#3D8BFF'>{candidate_id}</b>" if candidate_id else \
          "Forklift Operatörü Bilişsel Tarama Sistemi"
    st.markdown(
        f"<div style='margin-bottom:14px'><span style='font-size:20px;font-weight:700'>🧠 CognitionTracker</span>"
        f"<div style='font-size:12px;color:#8B95B0'>{sub}</div></div>",
        unsafe_allow_html=True,
    )


def stepper(current_stage: str):
    """1●──2○──3○ yatay ilerleme göstergesi. Tamamlananlar yeşil, aktif mavi."""
    order = [s for s, _ in STAGES]
    cur = order.index(current_stage) if current_stage in order else len(order)
    cells = []
    for i, (key, label) in enumerate(STAGES):
        done = st.session_state.get(f"{key}_result") is not None
        color = "#00E5A0" if done else ("#3D8BFF" if i == cur else "#4A526A")
        icon = "✓" if done else str(i + 1)
        cells.append(
            f"<div style='text-align:center;flex:1'>"
            f"<div style='width:30px;height:30px;border-radius:15px;margin:0 auto;"
            f"background:{color};color:#0A0F1E;font-weight:700;display:flex;"
            f"align-items:center;justify-content:center'>{icon}</div>"
            f"<div style='font-size:11px;color:{color};margin-top:4px'>{label}</div></div>"
        )
    st.markdown(
        "<div style='display:flex;gap:4px;margin:10px 0 22px'>" + "".join(cells) + "</div>",
        unsafe_allow_html=True,
    )


FLAG_BADGE = {
    "normal":     "<span style='color:#00E5A0'>● Normal</span>",
    "borderline": "<span style='color:#F5A623'>● Sınırda</span>",
    "flag":       "<span style='color:#E5484D'>● Dikkat Bayrağı</span>",
    "n/a":        "<span style='color:#4A526A'>—</span>",
}
