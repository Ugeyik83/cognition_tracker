# pages/2_go_nogo.py
import streamlit as st
import streamlit.components.v1 as components
from utils.result_handler import send_result_to_backend, get_result, clear_result

st.set_page_config(page_title="Go/No-Go Testi", layout="centered")
st.title("🛑 Go/No-Go Dikkat Testi")

RESULT_KEY = "gonogo_result"

# Sidebar'da yeni test butonu
with st.sidebar:
    if st.button("🔄 Yeni Test Başlat", use_container_width=True):
        clear_result(RESULT_KEY)
        st.rerun()

# Önceki sonuç varsa göster (katlanır bölüm)
previous_result = get_result(RESULT_KEY)
if previous_result:
    with st.expander("📊 Önceki test sonucunuz", expanded=False):
        st.metric("Doğruluk Oranı", f"{previous_result['accuracy']:.1f}%")
        st.metric("Doğru tepki", previous_result['correct'])
        st.metric("Yanlış tepki (No-Go'ya tıklama)", previous_result['incorrect'])

# Ana bileşen: oyun + gizli textarea
components.html(
    """
    <div style="font-family: sans-serif; max-width: 550px; margin: 0 auto;">
        <div style="background: #f0f2f6; padding: 20px; border-radius: 20px; text-align: center;">
            <h3>🎯 Kural</h3>
            <p><span style="color:green; font-weight:bold;">YEŞİL</span> kutuya <strong>tıklayın</strong>.<br>
            <span style="color:red; font-weight:bold;">KIRMIZI</span> kutuya <strong>tıklamayın</strong>.</p>
            
            <button id="startBtn" style="background: #4CAF50; color: white; border: none; padding: 12px 30px; font-size: 18px; border-radius: 40px; cursor: pointer; margin-bottom: 20px;">🚀 Testi Başlat</button>
            
            <div id="stimulusBox" style="width: 200px; height: 200px; margin: 0 auto 20px auto; border-radius: 20px; background-color: gray; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; color: white;">
                ?
            </div>
            
            <div id="scoreBoard" style="font-size: 20px; margin: 10px;">✅ Doğru: 0 &nbsp;&nbsp; ❌ Yanlış: 0</div>
            <div id="progress" style="font-size: 14px; color: gray;">Deneme: 0 / 20</div>
        </div>
    </div>
    <!-- Gizli textarea: sonuçları Streamlit'e iletmek için -->
    <textarea id="resultData" style="display:none;"></textarea>

    <script>
        let active = false;
        let correct = 0;
        let incorrect = 0;
        let trialCount = 0;
        const MAX_TRIALS = 20;
        let currentColor = null; // 'green' veya 'red'
        let timeoutId = null;
        
        const stimulusDiv = document.getElementById('stimulusBox');
        const scoreSpan = document.getElementById('scoreBoard');
        const progressSpan = document.getElementById('progress');
        const hiddenTextarea = document.getElementById('resultData');
        
        function updateUI() {
            scoreSpan.innerHTML = `✅ Doğru: ${correct} &nbsp;&nbsp; ❌ Yanlış: ${incorrect}`;
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
            document.getElementById('startBtn').disabled = false;
        }
        
        function showStimulus() {
            if (!active) return;
            // Go (yeşil) olasılığı %70, No-Go (kırmızı) %30
            const isGo = Math.random() < 0.7;
            currentColor = isGo ? 'green' : 'red';
            stimulusDiv.style.backgroundColor = currentColor;
            stimulusDiv.innerText = isGo ? "TIKLA!" : "DOKUNMA!";
            // 1.5 saniye sonra otomatik olarak bir sonraki uyarıya geç (eğer tıklanmazsa)
            timeoutId = setTimeout(() => {
                if (active && trialCount < MAX_TRIALS) {
                    // Cevap verilmedi -> yanlış say (No-Go'ya tıklanmadı ama Go'ya tıklanmadıysa hata)
                    if (currentColor === 'green') {
                        // Go'ya tıklanmadı -> yanlış
                        incorrect++;
                    } else {
                        // No-Go'ya tıklanmaması doğru, ama tıklama olmadı -> hiçbir şey ekleme
                        // Bu durumda cevap verilmemiş sayılır, istatistiğe ekleme yapma
                        // Fakat deneme sayısını artır.
                    }
                    trialCount++;
                    updateUI();
                    if (trialCount >= MAX_TRIALS) {
                        endTest();
                    } else {
                        showStimulus();
                    }
                }
            }, 1500);
        }
        
        function handleClick() {
            if (!active) return;
            if (timeoutId) clearTimeout(timeoutId);
            
            if (currentColor === 'green') {
                correct++;
            } else if (currentColor === 'red') {
                incorrect++;
            }
            trialCount++;
            updateUI();
            
            if (trialCount >= MAX_TRIALS) {
                endTest();
            } else {
                showStimulus();
            }
        }
        
        document.getElementById('startBtn').onclick = () => {
            if (active) return;
            active = true;
            correct = 0;
            incorrect = 0;
            trialCount = 0;
            updateUI();
            stimulusDiv.style.backgroundColor = "gray";
            stimulusDiv.innerText = "?";
            document.getElementById('startBtn').disabled = true;
            showStimulus();
        };
        
        stimulusDiv.addEventListener('click', handleClick);
    </script>
    """,
    height=550,
)

# Gizli textarea (Streamlit tarafında) – hata almamak için height=1 ve CSS ile gizleme
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

# Sonuçları işle
if result_json:
    try:
        import json
        data = json.loads(result_json)
        if send_result_to_backend(data, RESULT_KEY):
            st.success("✅ Go/No-Go sonucu kaydedildi!", icon="✅")
            st.rerun()
    except:
        pass

# Sonuçları göster (varsa)
final = get_result(RESULT_KEY)
if final:
    st.success("### 🎯 Son Test Sonucunuz")
    col1, col2, col3 = st.columns(3)
    col1.metric("Doğruluk Oranı", f"{final['accuracy']:.1f}%")
    col2.metric("Doğru Tepki", final['correct'])
    col3.metric("Hatalı Tepki", final['incorrect'])
    # Basit bir bar grafiği
    st.progress(final['accuracy'] / 100, text=f"Doğruluk: %{final['accuracy']:.1f}")
else:
    st.info("Testi başlatmak için yukarıdaki butona tıklayın. 20 deneme sonunda sonuçlar otomatik görünecektir.")