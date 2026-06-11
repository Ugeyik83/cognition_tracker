# pages/3_dual_task.py
import streamlit as st
import streamlit.components.v1 as components
from utils.result_handler import send_result_to_backend, get_result, clear_result
from utils.js_components import dual_task_component

st.set_page_config(page_title="İkili Görev Testi", layout="centered")
st.title("🧠 İkili Görev (Dual Task)")

RESULT_KEY = "dual_result"

with st.sidebar:
    if st.button("🔄 Yeni Test Başlat", use_container_width=True):
        clear_result(RESULT_KEY)
        st.rerun()

previous_result = get_result(RESULT_KEY)
if previous_result:
    with st.expander("📊 Önceki test sonucunuz", expanded=False):
        pa = previous_result.get('primary_accuracy', 0)
        sa = previous_result.get('secondary_accuracy', 0)
        st.metric("Renk Görevi (Turuncu → Space)", f"{pa:.1%}")
        st.metric("Şekil Görevi (Daire → D, Kare → K)", f"{sa:.1%}")

with st.expander("📋 Test Talimatları", expanded=True):
    st.markdown("""
    - **Üst alan (Renk görevi)**: Sürekli olarak farklı renkler gösterilir.  
      Sadece **🟠 Turuncu** daire gördüğünüzde <kbd>Space</kbd> tuşuna basın.  
      Diğer renklerde (mavi, mor) **hiçbir şey yapmayın**.
    - **Alt alan (Şekil görevi)**: Belli aralıklarla bir şekil belirir.  
      - ● **Daire** → <kbd>D</kbd> tuşuna basın  
      - ■ **Kare** → <kbd>K</kbd> tuşuna basın
    - **Süre**: 90 saniye. İki göreve aynı anda dikkat edin.
    - Test otomatik olarak biter, sonuçlar kaydedilir.
    """)

ready = st.checkbox("Talimatları okudum ve hazırım.")
if not ready:
    st.stop()

# Dual Task bileşenini göster (gizli textarea içerir)
components.html(dual_task_component(duration_ms=90000,
                                    shape_interval_min_ms=2000,
                                    shape_interval_max_ms=4500,
                                    shape_duration_ms=1500),
                height=620,
                scrolling=False)

# Bileşeni başlatmak için bir buton (JavaScript'teki startDualTask fonksiyonunu çağırır)
st.markdown("""
<div style="display: flex; justify-content: center;">
    <button id="startDualTaskBtn" style="background: #4CAF50; color: white; border: none; padding: 12px 30px; font-size: 18px; border-radius: 40px; cursor: pointer; margin: 20px 0;">
        🚀 Testi Başlat
    </button>
</div>
<script>
    const btn = document.getElementById('startDualTaskBtn');
    if (btn) {
        btn.onclick = () => {
            if (typeof window.startDualTask === 'function') {
                window.startDualTask();
                btn.disabled = true;
                btn.innerText = '⏳ Test devam ediyor...';
            } else {
                alert('Bileşen yüklenmedi, sayfayı yenileyin.');
            }
        };
    }
</script>
""", unsafe_allow_html=True)

# Gizli textarea (Streamlit tarafında) – sonucu yakalamak için
with st.container():
    result_json = st.text_area("", key="dual_hidden_result", label_visibility="collapsed", height=1)
    st.markdown("""
    <style>
    div[data-testid="stTextArea"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

if result_json:
    try:
        import json
        data = json.loads(result_json)
        # data içinde summary var; onu doğrudan kaydedelim
        summary = data.get("summary", data)
        if send_result_to_backend(summary, RESULT_KEY):
            st.success("✅ İkili Görev sonucu kaydedildi!", icon="✅")
            st.rerun()
    except Exception as e:
        st.error(f"Sonuç işlenirken hata: {e}")

final = get_result(RESULT_KEY)
if final:
    st.success("### 🎯 Son Test Sonucunuz")
    col1, col2 = st.columns(2)
    col1.metric("Renk Görevi (Turuncu→Space)", f"{final.get('primary_accuracy', 0):.1%}")
    col2.metric("Şekil Görevi (D→daire, K→kare)", f"{final.get('secondary_accuracy', 0):.1%}")
    # İlerleme çubuğu
    st.progress(final.get('primary_accuracy', 0), text="Renk görevi başarısı")
    st.progress(final.get('secondary_accuracy', 0), text="Şekil görevi başarısı")
else:
    st.info("Testi başlatmak için yukarıdaki butona tıklayın. 90 saniye boyunca iki göreve aynı anda dikkat edin.")