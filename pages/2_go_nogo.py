"""
pages/2_go_nogo.py — Go/No-Go testi, yeni tasarım.
"""

import json
import streamlit as st

from streamlit_javascript import st_javascript
from utils.js_components import gonogo_component
from utils.styles import BASE_CSS, page_header, metric_card
from utils.nav import render_nav

st.set_page_config(page_title="Go/No-Go | CognitionTracker", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(BASE_CSS, unsafe_allow_html=True)
render_nav("gonogo")

if not st.session_state.get("candidate_id"):
    st.warning("Önce ana sayfadan Operatör ID girin.")
    st.stop()

st.markdown(page_header("Modül 2 — Go / No-Go",
                         f"Aday: {st.session_state.candidate_id}"),
            unsafe_allow_html=True)

if st.session_state.get("gonogo_result"):
    r = st.session_state["gonogo_result"]
    hr  = float(r.get("hit_rate") or 0)
    fa  = float(r.get("false_alarm_rate") or 0)
    dp  = float(r.get("dprime") or 0)
    hr_color = "#00E5A0" if hr > 0.85 else ("#F5A623" if hr > 0.75 else "#FF4D6A")
    fa_color = "#00E5A0" if fa < 0.10 else ("#F5A623" if fa < 0.20 else "#FF4D6A")
    dp_color = "#00E5A0" if dp > 2.5  else ("#F5A623" if dp > 1.5  else "#FF4D6A")

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
                Modül 2 tamamlandı
            </span>
        </div>
        <div style="display:flex;gap:12px">
    """)

    st.markdown(
        metric_card("HIT RATE",    f"{hr:.0%}", hr_color) +
        metric_card("FALSE ALARM", f"{fa:.0%}", fa_color) +
        metric_card("d-prime",     f"{dp:.2f}", dp_color),
        unsafe_allow_html=True,
    )
    st.html("</div></div>")

    if st.button("Tekrar yap"):
        st.session_state["gonogo_result"] = None
        st.rerun()
    st.stop()

with st.expander("📋 Test talimatları", expanded=True):
    st.html("""
    - 🟢 **Yeşil daire** → **SPACE** tuşuna basın (GO)
    - 🔴 **Kırmızı daire** → **Basmayın** (NO-GO)
    - 60 deneme, hızlı ve doğru olun
    """)

ready = st.checkbox("Talimatları okudum, hazırım.")
if not ready:
    st.stop()

st.iframe(srcdoc=gonogo_component(n_trials=60, go_ratio=0.75, stim_ms=800, isi_ms=1200), height=540, scrolling=False)

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
        try{v=window.top.localStorage.getItem('gonogo_result');}catch(e){}
        if(!v){try{v=window.parent.localStorage.getItem('gonogo_result');}catch(e){}}
        if(!v){try{v=localStorage.getItem('gonogo_result');}catch(e){}}
        return v;
    })()""")
    if raw and raw not in ("null", "undefined", None):
        try:
            data = json.loads(raw)
            s = data.get("summary", {})
            st.session_state["gonogo_result"] = {
                "hit_rate":         s.get("hit_rate"),
                "false_alarm_rate": s.get("false_alarm_rate"),
                "omission_rate":    s.get("omission_rate"),
                "dprime":           s.get("dprime"),
                "mean_rt_go":       s.get("mean_rt_go"),
                "n_go":             s.get("n_go"),
                "n_nogo":           s.get("n_nogo"),
            }
            st_javascript("""(function(){
                try{window.top.localStorage.removeItem('gonogo_result');}catch(e){}
                try{window.parent.localStorage.removeItem('gonogo_result');}catch(e){}
                try{localStorage.removeItem('gonogo_result');}catch(e){}
            })()""")
            st.rerun()
        except (json.JSONDecodeError, TypeError):
            st.error("Sonuç okunamadı.")
    else:
        st.warning("Henüz sonuç yok.")
