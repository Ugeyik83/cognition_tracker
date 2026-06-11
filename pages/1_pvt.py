# pages/1_pvt.py
import streamlit as st
import streamlit.components.v1 as components
from utils.result_handler import send_result_to_backend, get_result, clear_result

st.set_page_config(page_title="PVT Testi", layout="centered")
st.title("🧠 Psikomotor Vigilans Testi (PVT)")

RESULT_KEY = "pvt_result"

with st.sidebar:
    if st.button("🔄 Yeni Test Başlat", use_container_width=True):
        clear_result(RESULT_KEY)
        st.rerun()

previous_result = get_result(RESULT_KEY)
if previous_result:
    with st.expander("📊 Önceki test sonucunuz", expanded=False):
        st.metric("Ortalama Tepki Süresi", f"{previous_result['average']} ms")
        st.write("Tüm tepkiler:", previous_result['reactionTimes'])

# Ana bileşen
components.html(
    """
    <div id="pvt-container" style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #f0f2f6; padding: 20px; border-radius: 20px; text-align: center;">
            <h3>⚡ Kural</h3>
            <p>Uyarıyı gördüğünüzde <strong>ekranın herhangi bir yerine tıklayın</strong>.<br>
            Yanlış zamanda tıklamayın (erken tepki ceza puanı getirir).</p>
            
            <div id="statusBox" style="margin: 20px 0; padding: 30px; background: white; border-radius: 20px; font-size: 28px; font-weight: bold;">
                🟢 Test başlamadı
            </div>
            
            <button id="startBtn" style="background: #4CAF50; color: white; border: none; padding: 12px 30px; font-size: 18px; border-radius: 40px; cursor: pointer;">🚀 Testi Başlat</button>
            
            <div id="progress" style="margin-top: 20px; font-size: 14px; color: gray;"></div>
        </div>
    </div>
    <!-- Gizli textarea: sonuçları buraya yazacağız, Streamlit'in okuyabilmesi için -->
    <textarea id="resultData" style="display:none;"></textarea>

    <script>
        let testActive = false;
        let startTime = null;
        let reactionTimes = [];
        let timeoutId = null;
        let currentTrial = 0;
        const MAX_TRIALS = 5;
        let waitingForStimulus = false;
        
        const statusDiv = document.getElementById('statusBox');
        const progressDiv = document.getElementById('progress');
        const hiddenTextarea = document.getElementById('resultData');
        
        function updateUI() {
            progressDiv.innerText = `Deneme: ${currentTrial}/${MAX_TRIALS}`;
        }
        
        function logResult() {
            const result = {
                reactionTimes: reactionTimes,
                average: (reactionTimes.reduce((a,b)=>a+b,0) / reactionTimes.length).toFixed(2),
                completed_at: new Date().toISOString()
            };
            hiddenTextarea.value = JSON.stringify(result);
            // Streamlit'in textarea değişikliğini algılaması için change event tetikle
            hiddenTextarea.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        function waitForStimulus() {
            if (!testActive) return;
            waitingForStimulus = true;
            const delay = Math.random() * 4000 + 2000;
            timeoutId = setTimeout(() => {
                if (!testActive) return;
                startTime = Date.now();
                statusDiv.innerHTML = "🔴 ŞİMDİ TIKLAYIN! 🔴";
                statusDiv.style.backgroundColor = "#ffcccc";
                waitingForStimulus = false;
            }, delay);
        }
        
        function handleTap() {
            if (!testActive) return;
            
            if (startTime !== null) {
                const rt = Date.now() - startTime;
                if (rt >= 100 && rt <= 1000) {
                    reactionTimes.push(rt);
                    currentTrial++;
                    updateUI();
                    statusDiv.innerHTML = `✅ ${rt} ms (${currentTrial}/${MAX_TRIALS})`;
                    statusDiv.style.backgroundColor = "#ccffcc";
                    startTime = null;
                    clearTimeout(timeoutId);
                    
                    if (currentTrial >= MAX_TRIALS) {
                        testActive = false;
                        statusDiv.innerHTML = "🎉 Test tamamlandı! Sonuçlar kaydedildi.";
                        statusDiv.style.backgroundColor = "#d4edda";
                        logResult();
                        document.getElementById('startBtn').disabled = false;
                    } else {
                        setTimeout(() => {
                            if (testActive) waitForStimulus();
                        }, 1000);
                    }
                } else {
                    statusDiv.innerHTML = `⚠️ Geçersiz tepki (${rt} ms) - Hızlı/Geç kaldınız. Tekrar deneyin.`;
                    statusDiv.style.backgroundColor = "#ffe5b4";
                    startTime = null;
                    clearTimeout(timeoutId);
                    setTimeout(() => {
                        if (testActive) waitForStimulus();
                    }, 1500);
                }
            } else if (waitingForStimulus) {
                statusDiv.innerHTML = "❌ Çok erken! Bekleyin ve uyarıya tepki verin.";
                statusDiv.style.backgroundColor = "#ffcccc";
                clearTimeout(timeoutId);
                setTimeout(() => {
                    if (testActive) waitForStimulus();
                }, 1500);
            } else {
                if (!testActive) {
                    statusDiv.innerHTML = "🟢 Test başlamamış. Başlatmak için butona tıklayın.";
                }
            }
        }
        
        document.getElementById('startBtn').onclick = () => {
            if (testActive) return;
            testActive = true;
            reactionTimes = [];
            currentTrial = 0;
            startTime = null;
            waitingForStimulus = false;
            clearTimeout(timeoutId);
            updateUI();
            statusDiv.innerHTML = "⏳ Test başladı. Uyarıyı bekleyin...";
            statusDiv.style.backgroundColor = "#e0e0e0";
            document.getElementById('startBtn').disabled = true;
            waitForStimulus();
        };
        
        document.addEventListener('click', function(e) {
            if (e.target.id !== 'startBtn' && testActive) {
                handleTap();
            }
        });
    </script>
    """,
    height=550,
)

# Bu textarea, yukarıdaki components.html içindeki gizli textarea ile aynı değil.
# Streamlit'in kendi textarea'sını oluşturup onu da gizleyelim.
# Ama daha önceki hatayı almamak için height=0 KULLANMAYACAĞIZ.
# Bunun yerine label_visibility="collapsed" ve CSS ile tamamen gizleyelim.

with st.container():
    # Gerçekten gizli bir textarea - kullanıcı asla görmez
    result_json = st.text_area(
        "###",  # Boş label, görünmeyecek
        key="pvt_hidden_result",
        label_visibility="collapsed",
        height=1  # Minimum 1 piksel, hata vermez
    )
    # CSS ile tamamen gizle
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

# Gelen veriyi işle
if result_json:
    try:
        import json
        data = json.loads(result_json)
        if send_result_to_backend(data, RESULT_KEY):
            st.success("✅ PVT sonucu kaydedildi!", icon="✅")
            st.rerun()
    except:
        pass

# Sonuçları göster
final = get_result(RESULT_KEY)
if final:
    st.success("### 🎯 Son Test Sonucunuz")
    col1, col2 = st.columns(2)
    col1.metric("Ortalama Tepki Süresi", f"{final['average']} ms")
    col2.metric("Deneme Sayısı", len(final['reactionTimes']))
    st.line_chart(final['reactionTimes'], x_label="Deneme", y_label="Tepki Süresi (ms)")
else:
    st.info("Testi başlatmak için yukarıdaki butona tıklayın. Test bittiğinde sonuçlar otomatik görünecektir.")