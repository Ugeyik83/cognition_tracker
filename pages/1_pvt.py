"""
pages/1_pvt.py — PVT testi, yeni tasarım.
"""

import json
import streamlit as st

import streamlit.components.v1
from streamlit_javascript import st_javascript
from utils.js_components import pvt_component
from utils.styles import BASE_CSS, page_header, progress_sidebar, metric_card
from utils.nav import render_nav

st.set_page_config(page_title="PVT | CognitionTracker", layout="wide",
                   initial_sidebar_state="expanded")
st.html(BASE_CSS)
render_nav("pvt")

if not st.session_state.get("candidate_id"):
    st.warning("Önce ana sayfadan Operatör ID girin.")
    st.stop()

st.html(page_header("Modül 1 — Vigilans Testi (PVT)",
                         f"Aday: {st.session_state.candidate_id}"))

# Tamamlandıysa özet
if st.session_state.get("pvt_result"):
    r = st.session_state["pvt_result"]
    rt  = r.get("mean_rt") or 0
    lap = r.get("lapses") or 0
    fs  = r.get("false_starts") or 0
    rt_color  = "#00E5A0" if rt < 300 else ("#F5A623" if rt < 400 else "#FF4D6A")
    lap_color = "#00E5A0" if lap < 5  else ("#F5A623" if lap < 10  else "#FF4D6A")

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
                Modül 1 tamamlandı
            </span>
        </div>
        <div style="display:flex;gap:12px">
    """)

    st.html(metric_card("ORT. RT", f"{rt} ms", rt_color) +
        metric_card("LAPSE",   str(lap),   lap_color) +
        metric_card("ERKEN BASMA", str(fs), "#F0F4FF"))
    st.html("</div></div>")

    if st.button("Tekrar yap", use_container_width=False):
        st.session_state["pvt_result"] = None
        st.rerun()
    st.stop()

# Talimat
with st.expander("📋 Test talimatları", expanded=True):
    st.html("""
    - Ekranda **sarı daire** göründüğünde **SPACE** veya daireye **tıklayın**
    - Daire çıkmadan **basmayın** — erken basma hata sayılır
    - Süre: **3 dakika** — odaklanın, test bitince butona basın
    """)

ready = st.checkbox("Talimatları okudum, hazırım.")
if not ready:
    st.stop()

# JS bileşeni
st.components.v1.html(pvt_component(duration_ms=30_000, min_isi_ms=2000,
                  max_isi_ms=8000, lapse_threshold_ms=500), height=540, scrolling=False)

st.html("""
<div style="background:rgba(61,139,255,0.06);border:1px solid rgba(61,139,255,0.15);
            border-radius:10px;padding:12px 16px;margin:12px 0;
            font-size:13px;color:#8B95B0">
    ⏳ Test devam ediyor. Bittikten sonra aşağıdaki butona basın.
</div>
""")

if st.button("✅ Test bitti — Sonucu Al", type="primary", use_container_width=True):
    raw = st.query_params.get("pvt_result", None)
    if raw and raw not in ("null", "undefined", None):
        try:
            import urllib.parse
            raw = urllib.parse.unquote(raw)
            data = json.loads(raw)
            s = data.get("summary", {})
            st.session_state["pvt_result"] = {
                "mean_rt":      s.get("mean_rt"),
                "median_rt":    s.get("median_rt"),
                "lapses":       s.get("lapses"),
                "false_starts": s.get("false_starts"),
                "n_trials":     s.get("n_trials"),
            }
            if "pvt_result" in st.query_params: del st.query_params["pvt_result"]
            st.rerun()
        except (json.JSONDecodeError, TypeError):
            st.error("Sonuç okunamadı. Test gerçekten tamamlandı mı?")
    else:
        st.warning("Henüz sonuç yok. Test bitmeden butona basmayın.")