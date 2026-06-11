"""
pages/2_go_nogo.py — Go / No-Go Testi
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from streamlit_javascript import st_javascript
from utils.js_components import gonogo_component

st.set_page_config(page_title="Go/No-Go | Dikkat Testi", layout="centered")
st.title("🔴🟢 Modül 2 — Go / No-Go")

if not st.session_state.get("candidate_id"):
    st.warning("Önce ana sayfadan Aday ID girin.")
    st.stop()

if st.session_state.get("gonogo_result"):
    r = st.session_state["gonogo_result"]
    st.success("✓ Bu modül tamamlandı.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Hit Rate",    f"{float(r.get('hit_rate') or 0):.0%}")
    c2.metric("False Alarm", f"{float(r.get('false_alarm_rate') or 0):.0%}")
    c3.metric("d-prime",     r.get("dprime", "—"))
    if st.button("Tekrar yap"):
        st.session_state["gonogo_result"] = None
        st.rerun()
    st.stop()

with st.expander("📋 Talimatlar", expanded=True):
    st.markdown("""
    - 🟢 **Yeşil daire** → **SPACE** tuşuna basın (GO)
    - 🔴 **Kırmızı daire** → **Basmayın** (NO-GO)
    - Süre: **~2 dakika** (60 deneme)
    """)

ready = st.checkbox("Talimatları okudum, hazırım.")
if not ready:
    st.stop()

st_autorefresh(interval=2000, key="gng_autorefresh")

components.html(
    gonogo_component(n_trials=60, go_ratio=0.75, stim_ms=800, isi_ms=1200),
    height=540, scrolling=False,
)

raw = st_javascript("window.top.localStorage.getItem('gonogo_result')")

if raw and raw not in ("null", "undefined", None):
    try:
        data    = json.loads(raw)
        summary = data.get("summary", {})
        st.session_state["gonogo_result"] = {
            "hit_rate":         summary.get("hit_rate"),
            "false_alarm_rate": summary.get("false_alarm_rate"),
            "omission_rate":    summary.get("omission_rate"),
            "dprime":           summary.get("dprime"),
            "mean_rt_go":       summary.get("mean_rt_go"),
            "n_go":             summary.get("n_go"),
            "n_nogo":           summary.get("n_nogo"),
        }
        st_javascript("window.top.localStorage.removeItem('gonogo_result')")
        st.rerun()
    except (json.JSONDecodeError, TypeError):
        pass
