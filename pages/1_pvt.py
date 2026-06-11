# pages/1_pvt.py
import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="PVT Testi", layout="centered")
st.title("🧠 Psikomotor Vigilans Testi (PVT)")

# --- Sidebar: yeni test butonu ---
with st.sidebar:
    if st.button("🔄 Yeni Test Başlat", use_container_width=True):
        if "pvt_result" in st.session_state:
            del st.session_state["pvt_result"]
        st.rerun()

# --- Eğer sonuç varsa, hemen göster ve alt kısmı pasif yap ---
if st.session_state.get("pvt_result"):
    final = st.session_state["pvt_result"]
    st.success("### 🎯 Son Test Sonucunuz")
    col1, col2 = st.columns(2)
    col1.metric("Ortalama Tepki Süresi", f"{final.get('average', '?')} ms")
    col2.metric("Deneme Sayısı", len(final.get('reactionTimes', [])))
    st.line_chart(final['reactionTimes'], x_label="Deneme", y_label="Tepki Süresi (ms)")
    # Sonuç varken test arayüzünü göstermeye gerek yok
    st.stop()

# --- JavaScript bileşeni (oyun + gizli textarea) ---
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

# --- Gizli textarea (Streamlit tarafında) ---
with st.container():
    result_json = st.text_area(
        "###",
        key="pvt_hidden_result",
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

# --- Sonuç gelince session_state'e yaz ve sayfayı yenile ---
if result_json:
    try:
        data = json.loads(result_json)
        st.session_state["pvt_result"] = data
        # Sayfayı yenile (sonuçların gösterilmesi için)
        st.rerun()
    except Exception as e:
        st.error(f"Sonuç işlenirken hata: {e}")

# Eğer sonuç yoksa, kullanıcıya bilgi ver
if not st.session_state.get("pvt_result"):
    st.info("Testi başlatmak için yukarıdaki butona tıklayın. 5 başarılı tepki sonucunda otomatik olarak kaydedilecektir.")