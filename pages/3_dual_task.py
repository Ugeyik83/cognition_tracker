"""
pages/3_dual_task.py — Dual Task testi, yeni tasarım.
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
from utils.js_components import dual_task_component
from utils.styles import BASE_CSS, page_header, metric_card
from utils.data_logger import save_session

st.set_page_config(page_title="Dual Task | CognitionTracker", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(BASE_CSS, unsafe_allow_html=True)

if not st.session_state.get("candidate_id"):
    st.warning("Önce ana sayfadan Operatör ID girin.")
    st.stop()

st.markdown(page_header("Modül 3 — Çift Görev (Dual Task)",
                         f"Aday: {st.session_state.candidate_id}"),
            unsafe_allow_html=True)

if st.session_state.get("dual_result"):
    r = st.session_state["dual_result"]
    pa = float(r.get("primary_accuracy") or 0)
    sa = float(r.get("secondary_accuracy") or 0)
    pa_color = "#00E5A0" if pa > 0.80 else ("#F5A623" if pa > 0.65 else "#FF4D6A")
    sa_color = "#00E5A0" if sa > 0.70 else ("#F5A623" if sa > 0.55 else "#FF4D6A")

    st.html(f"""
    <div style="padding:24px;background:#0A0F1E">
        <div style="background:rgba(0,229,160,0.08);border:1px solid rgba(0,229,160,0.2);
                    border-radius:12px;padding:16px;margin-bottom:20px;
                    display:flex;align-items:center;gap:10px">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M3 9L7 13L15 5" stroke="#00E5A0" stroke-width="2"
                      stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span style="font-size:14px;font-weight:600;color:#00E5A0">
                Modül 3 tamamlandı
            </span>
        </div>
        <div style="display:flex;gap:12px">
    """)

    st.markdown(
        metric_card("BİRİNCİL GÖREV", f"{pa:.0%}", pa_color) +
        metric_card("İKİNCİL GÖREV",  f"{sa:.0%}", sa_color),
        unsafe_allow_html=True,
    )
    st.html("</div>")

    # CSV kaydet
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
        st.html(f"""
        <div style="margin-top:16px;background:rgba(61,139,255,0.08);
                    border:1px solid rgba(61,139,255,0.2);border-radius:10px;
                    padding:12px 16px;font-size:13px;color:#8B95B0">
            💾 Sonuçlar kaydedildi: <code style="color:#3D8BFF">{path}</code>
        </div>
        """)

    st.html("</div>")

    if st.button("Tekrar yap"):
        st.session_state["dual_result"] = None
        st.session_state["session_saved"] = False
        st.rerun()
    st.stop()

with st.expander("📋 Test talimatları", expanded=True):
    st.html("""
    **Üst alan — Renk görevi (sürekli):**
    - 🟠 Turuncu daire → **SPACE**
    - Mavi / Mor daire → Basma

    **Alt alan — Şekil görevi (aralıklı):**
    - ● Daire → **D** tuşu &nbsp;|&nbsp; ■ Kare → **K** tuşu

    İki göreve aynı anda dikkat edin. Süre: **90 saniye**
    """)

ready = st.checkbox("Talimatları okudum, hazırım.")
if not ready:
    st.stop()

components.html(
    dual_task_component(duration_ms=90_000, shape_interval_min_ms=2000,
                        shape_interval_max_ms=4500, shape_duration_ms=1500),
    height=580, scrolling=False,
)

st.markdown("""
<div style="background:rgba(61,139,255,0.06);border:1px solid rgba(61,139,255,0.15);
            border-radius:10px;padding:12px 16px;margin:12px 0;
            font-size:13px;color:#8B95B0">
    ⏳ Test devam ediyor. Bittikten sonra aşağıdaki butona basın.
</div>
""")

if st.button("✅ Test bitti — Sonucu Al", type="primary", use_container_width=True):
    raw = st_javascript("""(function(){
        var v=null;
        try{v=window.top.localStorage.getItem('dual_result');}catch(e){}
        if(!v){try{v=window.parent.localStorage.getItem('dual_result');}catch(e){}}
        if(!v){try{v=localStorage.getItem('dual_result');}catch(e){}}
        return v;
    })()""")
    if raw and raw not in ("null", "undefined", None):
        try:
            data = json.loads(raw)
            s = data.get("summary", {})
            st.session_state["dual_result"] = {
                "primary_accuracy":   s.get("primary_accuracy"),
                "secondary_accuracy": s.get("secondary_accuracy"),
                "primary_correct":    s.get("primary_correct"),
                "secondary_correct":  s.get("secondary_correct"),
            }
            st_javascript("""(function(){
                try{window.top.localStorage.removeItem('dual_result');}catch(e){}
                try{window.parent.localStorage.removeItem('dual_result');}catch(e){}
                try{localStorage.removeItem('dual_result');}catch(e){}
            })()""")
            st.rerun()
        except (json.JSONDecodeError, TypeError):
            st.error("Sonuç okunamadı.")
    else:
        st.warning("Henüz sonuç yok.")
