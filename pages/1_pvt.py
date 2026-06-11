"""
pages/1_pvt.py — Psychomotor Vigilance Task
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from streamlit_javascript import st_javascript
from utils.js_components import pvt_component

st.set_page_config(page_title="PVT | Dikkat Testi", layout="centered")
st.title("⚡ Modül 1 — Vigilans Testi (PVT)")

if not st.session_state.get("candidate_id"):
    st.warning("Önce ana sayfadan Aday ID girin.")
    st.stop()

if st.session_state.get("pvt_result"):
    r = st.session_state["pvt_result"]
    st.success("✓ Bu modül tamamlandı.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Ort. RT",     f"{r.get('mean_rt', '—')} ms")
    c2.metric("Lapse",       r.get("lapses", "—"))
    c3.metric("Erken Basma", r.get("false_starts", "—"))
    if st.button("Tekrar yap"):
        st.session_state["pvt_result"] = None
        st.rerun()
    st.stop()

with st.expander("📋 Talimatlar", expanded=True):
    st.markdown("""
    - Ekranda **sarı daire** göründüğünde **SPACE** tuşuna basın
    - Daire çıkmadan **basmayın**
    - Süre: **3 dakika** — odaklanın, ara vermeyin
    """)

ready = st.checkbox("Talimatları okudum, hazırım.")
if not ready:
    st.stop()

# Test aktifken her 2 sn'de rerun → localStorage kontrol et
# RT ölçümü JS'te olduğu için bu rerun'lar ölçümü etkilemez
st_autorefresh(interval=2000, key="pvt_autorefresh")

components.html(
    pvt_component(duration_ms=180_000, min_isi_ms=2000, max_isi_ms=8000, lapse_threshold_ms=500),
    height=540, scrolling=False,
)

raw = st_javascript("localStorage.getItem('pvt_result')")

if raw and raw not in ("null", "undefined", None):
    try:
        data    = json.loads(raw)
        summary = data.get("summary", {})
        st.session_state["pvt_result"] = {
            "mean_rt":      summary.get("mean_rt"),
            "median_rt":    summary.get("median_rt"),
            "lapses":       summary.get("lapses"),
            "false_starts": summary.get("false_starts"),
            "n_trials":     summary.get("n_trials"),
        }
        st_javascript("localStorage.removeItem('pvt_result')")
        st.rerun()
    except (json.JSONDecodeError, TypeError):
        pass
