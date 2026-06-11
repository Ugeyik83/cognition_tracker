"""
pages/1_pvt.py — Psychomotor Vigilance Task

Çözüm: test sırasında rerun yok, test bitince manuel buton ile sonuç alınır.
Test sırasında hiç rerun yapılmaz → iframe sıfırlanmaz.
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
from utils.js_components import pvt_component

st.set_page_config(page_title="PVT | Dikkat Testi", layout="centered")
st.title("⚡ Modül 1 — Vigilans Testi (PVT)")

if not st.session_state.get("candidate_id"):
    st.warning("Önce ana sayfadan Aday ID girin.")
    st.stop()

# Tamamlandıysa özet göster
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
    - Test bitince sayfa otomatik güncellenir
    """)

ready = st.checkbox("Talimatları okudum, hazırım.")
if not ready:
    st.stop()

# ── Test aktifken ASLA rerun yok ──────────────────────────────
# JS bileşeni render edilir ve kendi başına çalışır.
# localStorage'a yazdığında (test bitince) kullanıcı sayfayı
# yenileyebilir VEYA aşağıdaki buton ile sonucu alır.
components.html(
    pvt_component(duration_ms=30_000, min_isi_ms=2000,
                  max_isi_ms=8000, lapse_threshold_ms=500),
    height=560, scrolling=False,
)

st.info("⏳ Test devam ediyor. Bitince **'Sonucu Al'** butonuna basın.")

# Tek tetikleyici: kullanıcının manuel butonu.
# Böylece test sırasında hiç rerun olmaz.
if st.button("✅ Test bitti — Sonucu Al", type="primary"):
    raw = st_javascript("""(function(){var v=null;try{v=window.top.localStorage.getItem('pvt_result');}catch(e){}if(!v){try{v=window.parent.localStorage.getItem('pvt_result');}catch(e){}}if(!v){try{v=localStorage.getItem('pvt_result');}catch(e){}}return v;})()""")
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
            st_javascript("""(function(){try{window.top.localStorage.removeItem('pvt_result');}catch(e){}try{window.parent.localStorage.removeItem('pvt_result');}catch(e){}try{localStorage.removeItem('pvt_result');}catch(e){}})()""")
            st.rerun()
        except (json.JSONDecodeError, TypeError):
            st.error("Sonuç okunamadı. Test gerçekten tamamlandı mı?")
    else:
        st.warning("Henüz sonuç yok. Test bitmeden butona basmayın.")