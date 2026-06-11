"""
pages/3_dual_task.py — Dual Task Testi
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
from utils.js_components import dual_task_component
from utils.data_logger import save_session

st.set_page_config(page_title="Dual Task | Dikkat Testi", layout="centered")
st.title("🧠 Modül 3 — Çift Görev (Dual Task)")

if not st.session_state.get("candidate_id"):
    st.warning("Önce ana sayfadan Aday ID girin.")
    st.stop()

if st.session_state.get("dual_result"):
    r = st.session_state["dual_result"]
    st.success("✓ Bu modül tamamlandı.")
    c1, c2 = st.columns(2)
    c1.metric("Birincil Görev", f"{float(r.get('primary_accuracy') or 0):.0%}")
    c2.metric("İkincil Görev",  f"{float(r.get('secondary_accuracy') or 0):.0%}")

    if (st.session_state.get("pvt_result") and
        st.session_state.get("gonogo_result") and
        not st.session_state.get("session_saved")):
        path = save_session(
            candidate_id=st.session_state["candidate_id"],
            pvt=st.session_state["pvt_result"],
            gonogo=st.session_state["gonogo_result"],
            dual=st.session_state["dual_result"],
        )
        st.session_state["session_saved"] = True
        st.info(f"Sonuçlar kaydedildi: `{path}`")

    if st.button("Tekrar yap"):
        st.session_state["dual_result"] = None
        st.session_state["session_saved"] = False
        st.rerun()
    st.stop()

with st.expander("📋 Talimatlar", expanded=True):
    st.markdown("""
    **Üst alan — Renk görevi (sürekli):**
    - 🟠 Turuncu daire → **SPACE**
    - Mavi / Mor daire → Basma

    **Alt alan — Şekil görevi (aralıklı):**
    - ● Daire → **D** tuşu
    - ■ Kare → **K** tuşu

    İki göreve **aynı anda** dikkat edin. Süre: **90 saniye**
    Test bitince **'Sonucu Al'** butonuna basın.
    """)

ready = st.checkbox("Talimatları okudum, hazırım.")
if not ready:
    st.stop()

components.html(
    dual_task_component(duration_ms=30_000, shape_interval_min_ms=2000,
                        shape_interval_max_ms=4500, shape_duration_ms=1500),
    height=600, scrolling=False,
)

st.info("⏳ Test devam ediyor. Bitince **'Sonucu Al'** butonuna basın.")

if st.button("✅ Test bitti — Sonucu Al", type="primary"):
    raw = st_javascript("""(function(){var v=null;try{v=window.top.localStorage.getItem('dual_result');}catch(e){}if(!v){try{v=window.parent.localStorage.getItem('dual_result');}catch(e){}}if(!v){try{v=localStorage.getItem('dual_result');}catch(e){}}return v;})()""")
    if raw and raw not in ("null", "undefined", None):
        try:
            data    = json.loads(raw)
            summary = data.get("summary", {})
            st.session_state["dual_result"] = {
                "primary_accuracy":   summary.get("primary_accuracy"),
                "secondary_accuracy": summary.get("secondary_accuracy"),
                "primary_correct":    summary.get("primary_correct"),
                "secondary_correct":  summary.get("secondary_correct"),
            }
            st_javascript("""(function(){try{window.top.localStorage.removeItem('dual_result');}catch(e){}try{window.parent.localStorage.removeItem('dual_result');}catch(e){}try{localStorage.removeItem('dual_result');}catch(e){}})()""")
            st.rerun()
        except (json.JSONDecodeError, TypeError):
            st.error("Sonuç okunamadı. Test gerçekten tamamlandı mı?")
    else:
        st.warning("Henüz sonuç yok. Test bitmeden butona basmayın.")