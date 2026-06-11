# pages/1_pvt.py
import streamlit as st
import streamlit.components.v1 as components
from utils.result_handler import send_result_to_backend, get_result, clear_result

st.set_page_config(page_title="PVT Testi", layout="centered")
st.title("🧠 Psikomotor Vigilans Testi (PVT)")

# Test sonucunu tutacağımız anahtar
RESULT_KEY = "pvt_result"

# Önceki test sonucunu temizle (yeni test başlatılırken)
if st.button("🔄 Yeni Test Başlat"):
    clear_result(RESULT_KEY)
    st.rerun()

# JavaScript bileşeni (PVT oyunu)
components.html(
    """
    <div id="pvt-container">
        <h3>Uyarı: Ekrana her dokunduğunuzda ⏱️ tepki süreniz ölçülecek.</h3>
        <button id="startBtn" style="font-size:20px; padding:10px;">Testi Başlat</button>
        <div id="status" style="margin:20px; font-size:24px;">Bekliyor...</div>
        <div id="resultArea"></div>
    </div>

    <script>
        let testActive = false;
        let startTime = null;
        let reactionTimes = [];
        let timeoutId = null;

        function logResult() {
            // Sonuçları bir textarea'ya yaz -> Streamlit okuyacak
            const resultArea = document.getElementById('resultArea');
            resultArea.innerHTML = `<textarea id="resultData" style="display:none;">${JSON.stringify({reactionTimes: reactionTimes, average: (reactionTimes.reduce((a,b)=>a+b,0)/reactionTimes.length).toFixed(2)})}</textarea>`;
            // Streamlit'a veri gönder (trigger)
            const event = new Event('change');
            document.getElementById('resultData').dispatchEvent(event);
        }

        function waitForStimulus() {
            if (!testActive) return;
            const delay = Math.random() * 4000 + 2000; // 2-6 sn arası
            timeoutId = setTimeout(() => {
                if (!testActive) return;
                startTime = Date.now();
                document.getElementById('status').innerHTML = '🔥 ŞİMDİ DOKUN! 🔥';
                document.getElementById('status').style.color = 'red';
            }, delay);
        }

        function handleTap() {
            if (!testActive) return;
            if (startTime !== null) {
                const rt = Date.now() - startTime;
                if (rt >= 100 && rt <= 1000) {
                    reactionTimes.push(rt);
                    document.getElementById('status').innerHTML = `✅ Tepki süresi: ${rt} ms (${reactionTimes.length}/5)`;
                } else {
                    document.getElementById('status').innerHTML = `⚠️ Geçersiz (${rt} ms) - Tekrar deneyin.`;
                }
                startTime = null;
                clearTimeout(timeoutId);
                if (reactionTimes.length >= 5) {
                    testActive = false;
                    document.getElementById('status').innerHTML = 'Test tamamlandı!';
                    logResult();
                } else {
                    waitForStimulus();
                }
            } else {
                document.getElementById('status').innerHTML = '❌ Çok erken! Bekleyin...';
            }
        }

        document.getElementById('startBtn').onclick = () => {
            testActive = true;
            reactionTimes = [];
            startTime = null;
            document.getElementById('status').innerHTML = 'Test başladı, uyarıyı bekleyin...';
            document.getElementById('status').style.color = 'black';
            waitForStimulus();
        };

        document.addEventListener('click', (e) => {
            if (e.target.id !== 'startBtn' && testActive) handleTap();
        });
    </script>
    """,
    height=500,
)

# Gizli textarea'dan gelen veriyi yakala (JavaScript'in yazdığı yer)
result_data = st.text_area("", key="pvt_textarea", label_visibility="collapsed", placeholder="Sonuç buraya yazılacak")

if result_data:
    try:
        import json
        data = json.loads(result_data)
        if send_result_to_backend(data, RESULT_KEY):
            st.success("PVT sonucu kaydedildi!")
            # İsteğe bağlı: temizle
            st.session_state.pvt_textarea = ""
    except:
        pass

# Sonucu göster
res = get_result(RESULT_KEY)
if res:
    st.subheader("📊 Son PVT Sonucunuz")
    st.json(res)
else:
    st.info("Testi tamamlayıp sonucu alın.")