# pages/2_go_nogo.py
import streamlit as st
import streamlit.components.v1 as components
from utils.result_handler import send_result_to_backend, get_result, clear_result

st.set_page_config(page_title="Go/No-Go Testi", layout="centered")
st.title("🛑 Go/No-Go Dikkat Testi")

RESULT_KEY = "gonogo_result"

with st.sidebar:
    if st.button("🔄 Yeni Test Başlat", use_container_width=True):
        clear_result(RESULT_KEY)
        st.rerun()

previous_result = get_result(RESULT_KEY)
if previous_result:
    with st.expander("📊 Önceki test sonucunuz", expanded=False):
        st.metric("Doğruluk Oranı", f"{previous_result['accuracy']:.1f}%")
        st.metric("Doğru Tepki", previous_result['correct'])
        st.metric("Yanlış Tepki (No-Go'ya tıklama veya Go'ya geç kalma)", previous_result['incorrect'])

components.html(
    """
    <div style="font-family: sans-serif; max-width: 550px; margin: 0 auto;">
        <div style="background: #f0f2f6; padding: 20px; border-radius: 20px; text-align: center;">
            <h3>🎯 Kural</h3>
            <p><span style="color:green; font-weight:bold;">YEŞİL</span> kutuya <strong>tıklayın</strong> (2 saniyeniz var).<br>
            <span style="color:red; font-weight:bold;">KIRMIZI</span> kutuya <strong>tıklamayın</strong>.</p>
            
            <button id="startBtn" style="background: #4CAF50; color: white; border: none; padding: 12px 30px; font-size: 18px; border-radius: 40px; cursor: pointer; margin-bottom: 20px;">🚀 Testi Başlat</button>
            
            <div id="stimulusBox" style="width: 200px; height: 200px; margin: 0 auto 20px auto; border-radius: 20px; background-color: gray; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; color: white;">
                ?
            </div>
            
            <div id="messageBox" style="margin: 10px; font-size: 16px; color: #555;">Test başlamadı</div>
            <div id="scoreBoard" style="font-size: 20px; margin: 10px;">✅ Doğru: 0 &nbsp;&nbsp; ❌ Hata: 0</div>
            <div id="progress" style="font-size: 14px; color: gray;">Deneme: 0 / 20</div>
        </div>
    </div>
    <textarea id="resultData" style="display:none;"></textarea>

    <script>
        let active = false;
        let correct = 0;
        let incorrect = 0;
        let trialCount = 0;
        const MAX_TRIALS = 10;
        let currentColor = null;
        let timeoutId = null;
        let waitingForReady = false;
        
        const stimulusDiv = document.getElementById('stimulusBox');
        const messageDiv = document.getElementById('messageBox');
        const scoreSpan = document.getElementById('scoreBoard');
        const progressSpan = document.getElementById('progress');
        const hiddenTextarea = document.getElementById('resultData');
        
        function updateUI() {
            scoreSpan.innerHTML = `✅ Doğru: ${correct} &nbsp;&nbsp; ❌ Hata: ${incorrect}`;
            progressSpan.innerText = `Deneme: ${trialCount} / ${MAX_TRIALS}`;
        }
        
        function endTest() {
            active = false;
            if (timeoutId) clearTimeout(timeoutId);
            const accuracy = (correct + incorrect) > 0 ? (correct / (correct + incorrect)) * 100 : 0;
            const result = {
                correct: correct,
                incorrect: incorrect,
                total: MAX_TRIALS,
                accuracy: accuracy
            };
            hiddenTextarea.value = JSON.stringify(result);
            hiddenTextarea.dispatchEvent(new Event('change', { bubbles: true }));
            stimulusDiv.style.backgroundColor = "gray";
            stimulusDiv.innerText = "🏁 BİTTİ";
            messageDiv.innerText = "Test tamamlandı!";
            document.getElementById('startBtn').disabled = false;
        }
        
        function showReady() {
            if (!active) return;
            waitingForReady = true;
            stimulusDiv.style.backgroundColor = "lightgray";
            stimulusDiv.innerText = "⏳";
            messageDiv.innerText = "Hazır olun...";
            // 1 saniye sonra uyaranı göster
            setTimeout(() => {
                if (!active) return;
                waitingForReady = false;
                showStimulus();
            }, 1000);
        }
        
        function showStimulus() {
            if (!active) return;
            const isGo = Math.random() < 0.7; // %70 Go (yeşil)
            currentColor = isGo ? 'green' : 'red';
            stimulusDiv.style.backgroundColor = currentColor;
            stimulusDiv.innerText = isGo ? "TIKLA!" : "DOKUNMA!";
            messageDiv.innerText = isGo ? "Tıklayın!" : "Sakın tıklamayın!";
            // 2 saniye tepki süresi (önceki 1.5'ten daha uzun)
            timeoutId = setTimeout(() => {
                if (active && trialCount < MAX_TRIALS) {
                    // Süre doldu, cevap yoksa
                    if (currentColor === 'green') {
                        // Go'ya tıklanmadı -> hata
                        incorrect++;
                        messageDiv.innerText = "❌ Geç kaldınız! Hızlı olun.";
                    } else {
                        // No-Go'ya tıklanmaması doğru, ama hiçbir şey yapma
                        messageDiv.innerText = "✓ Doğru (dokunmadınız)";
                    }
                    trialCount++;
                    updateUI();
                    if (trialCount >= MAX_TRIALS) {
                        endTest();
                    } else {
                        // Bir sonraki deneme öncesi hazırlık aşaması
                        showReady();
                    }
                }
            }, 2000); // 2 saniye
        }
        
        function handleClick() {
            if (!active) return;
            if (waitingForReady) {
                messageDiv.innerText = "Henüz uyarı gelmedi, bekleyin!";
                return;
            }
            if (timeoutId) clearTimeout(timeoutId);
            
            if (currentColor === 'green') {
                correct++;
                messageDiv.innerText = "✅ Doğru tepki!";
            } else if (currentColor === 'red') {
                incorrect++;
                messageDiv.innerText = "❌ Hata! Kırmızıya tıkladınız.";
            }
            trialCount++;
            updateUI();
            
            if (trialCount >= MAX_TRIALS) {
                endTest();
            } else {
                // Sonraki deneme için hazırlık
                showReady();
            }
        }
        
        document.getElementById('startBtn').onclick = () => {
            if (active) return;
            active = true;
            correct = 0;
            incorrect = 0;
            trialCount = 0;
            updateUI();
            messageDiv.innerText = "Test başlıyor...";
            document.getElementById('startBtn').disabled = true;
            showReady();
        };
        
        stimulusDiv.addEventListener('click', handleClick);
    </script>
    """,
    height=600,
)

with st.container():
    result_json = st.text_area(
        "###",
        key="gonogo_hidden_result",
        label_visibility="collapsed",
        height=1
    )
    st.markdown(
        """
        <style>
        div[data-testid="stTextArea"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

if result_json:
    try:
        import json
        data = json.loads(result_json)
        if send_result_to_backend(data, RESULT_KEY):
            st.success("✅ Go/No-Go sonucu kaydedildi!", icon="✅")
            st.rerun()
    except:
        pass

final = get_result(RESULT_KEY)
if final:
    st.success("### 🎯 Son Test Sonucunuz")
    col1, col2, col3 = st.columns(3)
    col1.metric("Doğruluk Oranı", f"{final['accuracy']:.1f}%")
    col2.metric("Doğru Tepki", final['correct'])
    col3.metric("Hatalı Tepki", final['incorrect'])
    st.progress(final['accuracy'] / 100, text=f"Doğruluk: %{final['accuracy']:.1f}")
else:
    st.info("Testi başlatmak için butona tıklayın. Her deneme öncesi 'Hazır olun' uyarısı gelecek, ardından yeşil veya kırmızı kutu gösterilecek. Yeşile tıklamak için 2 saniyeniz var.")