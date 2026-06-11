"""
app.py — Karşılama ekranı ve session state başlatma.
"""

import streamlit as st
from utils.styles import BASE_CSS, page_header

st.set_page_config(
    page_title="CognitionTracker",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(BASE_CSS, unsafe_allow_html=True)

INITIAL_STATE = {
    "candidate_id":  "",
    "consent_given": False,
    "pvt_result":    None,
    "gonogo_result": None,
    "dual_result":   None,
    "session_saved": False,
}
for k, v in INITIAL_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Header ────────────────────────────────────────────────────
st.html(page_header("CognitionTracker", "Forklift Operatörü Bilişsel Tarama Sistemi"))

# ── Karşılama içeriği ─────────────────────────────────────────
completed = sum([
    st.session_state.pvt_result    is not None,
    st.session_state.gonogo_result is not None,
    st.session_state.dual_result   is not None,
])

st.html(f"""
<div style="min-height:460px;display:flex;flex-direction:column;
            align-items:center;justify-content:center;
            padding:48px 24px;background:#0A0F1E">

    <h1 style="font-size:30px;font-weight:700;letter-spacing:-0.8px;
               text-align:center;margin-bottom:8px;color:#F0F4FF;line-height:1.3">
        Yıllık taramaya<br>
        <span style="color:#3D8BFF">hoş geldiniz.</span>
    </h1>
    <p style="font-size:14px;color:#8B95B0;text-align:center;
              max-width:320px;line-height:1.6;margin-bottom:28px">
        Üç kısa test, yaklaşık 7 dakika.<br>Odaklanın, doğal yanıt verin.
    </p>

    <div style="display:flex;gap:10px;margin-bottom:32px">
        <div style="background:#1A2235;border:1px solid rgba(255,255,255,0.1);
                    border-radius:8px;padding:10px 16px;text-align:center;min-width:90px">
            <div style="font-size:10px;color:#4A526A;font-weight:500;margin-bottom:3px">MODÜL 01</div>
            <div style="font-size:13px;font-weight:600;color:{'#00E5A0' if st.session_state.pvt_result else '#F0F4FF'}">PVT</div>
            <div style="font-size:11px;color:#8B95B0;margin-top:2px">3 dk</div>
        </div>
        <div style="background:#1A2235;border:1px solid rgba(255,255,255,0.1);
                    border-radius:8px;padding:10px 16px;text-align:center;min-width:90px">
            <div style="font-size:10px;color:#4A526A;font-weight:500;margin-bottom:3px">MODÜL 02</div>
            <div style="font-size:13px;font-weight:600;color:{'#00E5A0' if st.session_state.gonogo_result else '#F0F4FF'}">Go/No-Go</div>
            <div style="font-size:11px;color:#8B95B0;margin-top:2px">~2 dk</div>
        </div>
        <div style="background:#1A2235;border:1px solid rgba(255,255,255,0.1);
                    border-radius:8px;padding:10px 16px;text-align:center;min-width:90px">
            <div style="font-size:10px;color:#4A526A;font-weight:500;margin-bottom:3px">MODÜL 03</div>
            <div style="font-size:13px;font-weight:600;color:{'#00E5A0' if st.session_state.dual_result else '#F0F4FF'}">Dual Task</div>
            <div style="font-size:11px;color:#8B95B0;margin-top:2px">90 sn</div>
        </div>
    </div>
</div>
""")

# ── Aday girişi ───────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if not st.session_state.candidate_id:
        with st.form("candidate_form"):
            cid = st.text_input("", placeholder="Operatör ID girin")
            submitted = st.form_submit_button("Teste Başla →", use_container_width=True)
            if submitted:
                if cid.strip():
                    st.session_state.candidate_id = cid.strip()
                    st.rerun()
                else:
                    st.error("Operatör ID boş olamaz.")
    else:
        st.html(f"""
        <div style="background:#1A2235;border:1px solid rgba(61,139,255,0.3);
                    border-radius:12px;padding:16px;text-align:center;margin-bottom:12px">
            <div style="font-size:12px;color:#8B95B0;margin-bottom:4px">Aktif Aday</div>
            <div style="font-size:18px;font-weight:700;color:#3D8BFF">
                {st.session_state.candidate_id}
            </div>
            <div style="margin-top:10px;height:4px;background:#0A0F1E;border-radius:2px">
                <div style="height:4px;background:#3D8BFF;border-radius:2px;
                            width:{int(completed/3*100)}%"></div>
            </div>
            <div style="font-size:11px;color:#8B95B0;margin-top:6px">
                {completed}/3 modül tamamlandı
            </div>
        </div>
        """)

        if completed < 3:
            st.info("Sol menüden sırayla testleri tamamlayın.")
        else:
            st.success("Tüm modüller tamamlandı. Dashboard'u açın.")

        if st.button("🔄 Yeni Aday", use_container_width=True):
            for k, v in INITIAL_STATE.items():
                st.session_state[k] = v
            st.rerun()

st.html("""
<div style="text-align:center;font-size:11px;color:#4A526A;padding:16px">
    Verileriniz yalnızca bu cihazda yerel olarak saklanır · KVKK Madde 6
</div>
""")
