"""
app.py — Giriş noktası ve session state başlatma.

Streamlit multi-page mimarisinde app.py sadece:
1. Ortak session_state anahtarlarını başlatır
2. Ana sayfayı gösterir
3. Test akışını yönlendirir

Sayfa geçişinde session_state korunur.
Sayfa yenilemede silinir — bu yüzden her modül sonucu
anında CSV'ye yazılır (data_logger.save_session).
"""

import streamlit as st

st.set_page_config(
    page_title="Bilişsel Dikkat Testi",
    page_icon="🧠",
    layout="centered",
)

# ── Session state başlatma ────────────────────────────────────
# Yalnızca ilk yüklemede set edilir; sayfa geçişinde korunur.
INITIAL_STATE = {
    "candidate_id": "",
    "consent_given": False,
    "pvt_result":   None,   # dict | None
    "gonogo_result": None,
    "dual_result":  None,
    "session_saved": False,
}

for key, default in INITIAL_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Ana sayfa ─────────────────────────────────────────────────
st.title("🧠 Bilişsel Dikkat Test Sistemi")
st.caption("Saha / Montaj İşçisi İşe Alım Profili")

st.divider()

col1, col2, col3 = st.columns(3)
col1.metric("Modül 1", "PVT",       "5 dakika")
col2.metric("Modül 2", "Go/No-Go",  "2 dakika")
col3.metric("Modül 3", "Dual Task", "90 saniye")

st.divider()

# Aday girişi
if not st.session_state.candidate_id:
    with st.form("candidate_form"):
        cid = st.text_input("Aday ID", max_chars=20, placeholder="Örn: 1234 veya AD.SOYAD")
        if st.form_submit_button("Devam →", type="primary"):
            if cid.strip():
                st.session_state.candidate_id = cid.strip()
                st.rerun()
            else:
                st.error("Aday ID boş olamaz.")
else:
    st.success(f"Aday: **{st.session_state.candidate_id}**")

    # İlerleme göstergesi
    completed = sum([
        st.session_state.pvt_result    is not None,
        st.session_state.gonogo_result is not None,
        st.session_state.dual_result   is not None,
    ])
    st.progress(completed / 3, text=f"Tamamlanan modül: {completed} / 3")

    if completed < 3:
        st.info("Sol menüden sırayla testleri tamamlayın.")
    else:
        st.success("Tüm modüller tamamlandı. Dashboard'u açın.")

    if st.button("🔄 Yeni Aday (Sıfırla)"):
        for key, default in INITIAL_STATE.items():
            st.session_state[key] = default
        st.rerun()

st.divider()
st.markdown("""
**KVKK:** Bu sistem kişisel veri işler. Test öncesinde aday aydınlatma metni
ve açık rıza formu imzalamalıdır. Veriler yalnızca yerel `results/` klasöründe saklanır.
""")
