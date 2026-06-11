# pages/3_dual_task.py
import streamlit as st
import streamlit.components.v1 as components
from utils.result_handler import send_result_to_backend, get_result, clear_result

st.set_page_config(page_title="İkili Görev Testi", layout="centered")
st.title("🎯 İkili Görev (Dual Task)")

RESULT_KEY = "dual_result"

with st.sidebar:
    if st.button("🔄 Yeni Test Başlat", use_container_width=True):
        clear_result(RESULT_KEY)
        st.rerun()

previous_result = get_result(RESULT_KEY)
if previous_result:
    with st.expander("📊 Önceki test sonucunuz", expanded=False):
        st.metric("Renk Görevi Doğruluk", f"{previous_result.get('primary_accuracy', 0):.1%}")
        st.metric("Şekil Görevi Doğruluk", f"{previous_result.get('secondary_accuracy', 0):.1%}")

with st.expander("📋 Test Talimatları", expanded=True):
    st.markdown("""
    - **Renk görevi (üstte)**: Sadece **🟠 TURUNCU** daire gördüğünüzde **SPACE** tuşuna basın.  
      Mavi veya mor dairede basmayın.
    - **Şekil görevi (altta)**:  
      - ● **DAİRE** → **D** tuşuna basın  
      - ■ **KARE** → **K** tuşuna basın
    - Test **90 saniye** sürer. Otomatik biter.
    """)

ready = st.checkbox("Talimatları okudum, hazırım.")
if not ready:
    st.stop()

# Ana bileşen - tüm mantık tek bir components.html içinde
components.html(
    """
    <div style="font-family: sans-serif; max-width: 700px; margin: 0 auto;">
        <div style="background: #1e1e2f; padding: 20px; border-radius: 20px; color: white;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                <div>⏱️ <span id="timer">90</span> saniye</div>
                <div>🎨 Renk: <span id="primaryScore">0</span>/<span id="primaryTotal">0</span></div>
                <div>🔷 Şekil: <span id="secondaryScore">0</span>/<span id="secondaryTotal">0</span></div>
            </div>
            
            <!-- Renk görevi -->
            <div style="background: #0a0a14; border-radius: 20px; padding: 20px; margin-bottom: 20px; text-align: center;">
                <div style="font-size: 14px; color: #aaa;">🔴 RENK GÖREVİ (sürekli)</div>
                <div id="colorBox" style="width: 120px; height: 120px; margin: 10px auto; border-radius: 60px; background-color: gray;"></div>
                <div style="font-size: 12px;">Turuncu → <kbd>Space</kbd> | Diğer renkler → basma</div>
            </div>
            
            <!-- Şekil görevi -->
            <div style="background: #0a0a14; border-radius: 20px; padding: 20px; text-align: center;">
                <div style="font-size: 14px; color: #aaa;">🔷 ŞEKİL GÖREVİ (aralıklı)</div>
                <div id="shapeBox" style="width: 120px; height: 120px; margin: 10px auto; background-color: #2a2a3a; border-radius: 20px; display: flex; align-items: center; justify-content: center; font-size: 48px;">?</div>
                <div style="font-size: 12px;">Daire ● → <kbd>D</kbd> | Kare ■ → <kbd>K</kbd></div>
            </div>
            
            <div id="message" style="margin-top: 20px; text-align: center; font-size: 14px; color: #f5a623;">Hazır mısınız? Başlat butonuna tıklayın.</div>
        </div>
    </div>
    
    <button id="startBtn" style="display: block; width: 100%; background: #4CAF50; color: white; border: none; padding: 12px; font-size: 18px; border-radius: 40px; cursor: pointer; margin-top: 20px;">🚀 Testi Başlat</button>
    
    <textarea id="resultData" style="display:none;"></textarea>

    <script>
        let active = false;
        let timerInterval = null;
        let colorInterval = null;
        let shapeTimeout = null;
        let remainingSeconds = 90;
        
        // Renk görevi
        let primaryCorrect = 0;
        let primaryTotal = 0;
        let currentColor = null;  // 'orange', 'blue', 'purple'
        
        // Şekil görevi
        let secondaryCorrect = 0;
        let secondaryTotal = 0;
        let currentShape = null;   // 'circle', 'square'
        
        // DOM elementleri
        const timerElem = document.getElementById('timer');
        const primaryScoreSpan = document.getElementById('primaryScore');
        const primaryTotalSpan = document.getElementById('primaryTotal');
        const secondaryScoreSpan = document.getElementById('secondaryScore');
        const secondaryTotalSpan = document.getElementById('secondaryTotal');
        const colorBox = document.getElementById('colorBox');
        const shapeBox = document.getElementById('shapeBox');
        const messageDiv = document.getElementById('message');
        const hiddenTextarea = document.getElementById('resultData');
        
        function updateUI() {
            primaryScoreSpan.innerText = primaryCorrect;
            primaryTotalSpan.innerText = primaryTotal;
            secondaryScoreSpan.innerText = secondaryCorrect;
            secondaryTotalSpan.innerText = secondaryTotal;
        }
        
        function showMessage(msg, isError = false) {
            messageDiv.innerHTML = msg;
            messageDiv.style.color = isError ? "#ff6b6b" : "#f5a623";
            setTimeout(() => {
                if (active) messageDiv.style.color = "#f5a623";
            }, 800);
        }
        
        // Rastgele renk göster (her 1.5 saniyede)
        function showRandomColor() {
            if (!active) return;
            const rand = Math.random();
            let color, name;
            if (rand < 0.33) {
                color = "#FF8C42";  // turuncu
                name = "orange";
            } else if (rand < 0.66) {
                color = "#3D8BFF";  // mavi
                name = "blue";
            } else {
                color = "#A855F7";  // mor
                name = "purple";
            }
            currentColor = name;
            colorBox.style.backgroundColor = color;
            primaryTotal++;
            updateUI();
        }
        
        // Şekil göster (rastgele aralıklarla)
        function scheduleShape() {
            if (!active) return;
            const delay = Math.random() * 3000 + 2000; // 2-5 saniye
            shapeTimeout = setTimeout(() => {
                if (!active) return;
                const isCircle = Math.random() < 0.5;
                currentShape = isCircle ? 'circle' : 'square';
                shapeBox.innerHTML = isCircle ? '●' : '■';
                shapeBox.style.fontSize = '64px';
                shapeBox.style.color = '#FFD966';
                secondaryTotal++;
                updateUI();
                // Şekil 1.5 saniye sonra kaybolur
                setTimeout(() => {
                    if (active) {
                        shapeBox.innerHTML = '?';
                        currentShape = null;
                        scheduleShape(); // bir sonraki şekli planla
                    }
                }, 1500);
            }, delay);
        }
        
        function endTest() {
            active = false;
            if (timerInterval) clearInterval(timerInterval);
            if (colorInterval) clearInterval(colorInterval);
            if (shapeTimeout) clearTimeout(shapeTimeout);
            
            const primaryAccuracy = primaryTotal > 0 ? primaryCorrect / primaryTotal : 0;
            const secondaryAccuracy = secondaryTotal > 0 ? secondaryCorrect / secondaryTotal : 0;
            
            const result = {
                primary_correct: primaryCorrect,
                primary_total: primaryTotal,
                primary_accuracy: primaryAccuracy,
                secondary_correct: secondaryCorrect,
                secondary_total: secondaryTotal,
                secondary_accuracy: secondaryAccuracy,
                summary: {
                    primary_accuracy: primaryAccuracy,
                    secondary_accuracy: secondaryAccuracy,
                    primary_correct: primaryCorrect,
                    secondary_correct: secondaryCorrect
                }
            };
            hiddenTextarea.value = JSON.stringify(result);
            hiddenTextarea.dispatchEvent(new Event('change', { bubbles: true }));
            showMessage("✅ Test tamamlandı! Sonuçlar kaydedildi.");
            document.getElementById('startBtn').disabled = false;
            document.getElementById('startBtn').innerText = "🚀 Testi Başlat";
        }
        
        function startTimer() {
            timerInterval = setInterval(() => {
                if (!active) return;
                if (remainingSeconds <= 0) {
                    clearInterval(timerInterval);
                    endTest();
                } else {
                    remainingSeconds--;
                    timerElem.innerText = remainingSeconds;
                }
            }, 1000);
        }
        
        // Klavye olayları
        function handleKeydown(e) {
            if (!active) return;
            const key = e.key;
            
            // Space tuşu (renk görevi)
            if (key === ' ' || key === 'Space') {
                e.preventDefault();
                if (currentColor === 'orange') {
                    primaryCorrect++;
                    showMessage("✅ Renk doğru (Space)", false);
                } else if (currentColor !== null) {
                    showMessage("❌ Hata! Turuncu değilken Space'e bastınız.", true);
                }
                updateUI();
            }
            
            // D tuşu (daire)
            if (key === 'd' || key === 'D') {
                if (currentShape === 'circle') {
                    secondaryCorrect++;
                    showMessage("✅ Şekil doğru (D)", false);
                } else if (currentShape !== null) {
                    showMessage("❌ Hata! Daire değilken D'ye bastınız.", true);
                }
                updateUI();
            }
            
            // K tuşu (kare)
            if (key === 'k' || key === 'K') {
                if (currentShape === 'square') {
                    secondaryCorrect++;
                    showMessage("✅ Şekil doğru (K)", false);
                } else if (currentShape !== null) {
                    showMessage("❌ Hata! Kare değilken K'ye bastınız.", true);
                }
                updateUI();
            }
        }
        
        function startTest() {
            if (active) return;
            active = true;
            remainingSeconds = 90;
            primaryCorrect = 0;
            primaryTotal = 0;
            secondaryCorrect = 0;
            secondaryTotal = 0;
            currentColor = null;
            currentShape = null;
            updateUI();
            timerElem.innerText = "90";
            colorBox.style.backgroundColor = "gray";
            shapeBox.innerHTML = "?";
            
            // Renk döngüsü: her 1.5 saniyede yeni renk
            if (colorInterval) clearInterval(colorInterval);
            colorInterval = setInterval(() => showRandomColor(), 1500);
            showRandomColor(); // hemen bir renk göster
            
            // Şekil görevini başlat
            if (shapeTimeout) clearTimeout(shapeTimeout);
            scheduleShape();
            
            startTimer();
            showMessage("🎯 Test başladı! Turuncuya Space, daireye D, kareye K.", false);
            document.getElementById('startBtn').disabled = true;
            document.getElementById('startBtn').innerText = "⏳ Test devam ediyor...";
        }
        
        // Butona tıklama olayı
        document.getElementById('startBtn').onclick = startTest;
        
        // Klavye dinleyicisini ekle
        window.addEventListener('keydown', handleKeydown);
    </script>
    """,
    height=650,
    scrolling=False
)

# Gizli textarea (Streamlit tarafı)
with st.container():
    result_json = st.text_area("", key="dual_hidden_result", label_visibility="collapsed", height=1)
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
        summary = data.get("summary", data)
        if send_result_to_backend(summary, RESULT_KEY):
            st.success("✅ İkili Görev sonucu kaydedildi!", icon="✅")
            st.rerun()
    except Exception as e:
        st.error(f"Sonuç okuma hatası: {e}")

final = get_result(RESULT_KEY)
if final:
    st.success("### 🎯 Son Test Sonucunuz")
    col1, col2 = st.columns(2)
    col1.metric("Renk Görevi (Turuncu→Space)", f"{final.get('primary_accuracy', 0):.1%}")
    col2.metric("Şekil Görevi (D→daire, K→kare)", f"{final.get('secondary_accuracy', 0):.1%}")
    st.progress(final.get('primary_accuracy', 0), text="Renk görevi başarısı")
    st.progress(final.get('secondary_accuracy', 0), text="Şekil görevi başarısı")
else:
    st.info("Testi başlatmak için butona tıklayın. 90 saniye boyunca iki göreve aynı anda dikkat edin.")