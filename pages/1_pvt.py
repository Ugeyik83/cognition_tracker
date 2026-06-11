# pages/1_pvt.py
import streamlit as st
import streamlit.components.v1 as components
from utils.result_handler import send_result_to_backend, get_result, clear_result

st.set_page_config(page_title="PVT Testi", layout="centered")
st.title("🧠 Psikomotor Vigilans Testi (PVT)")

RESULT_KEY = "pvt_result"

# Sidebar'a yeni test butonu
with st.sidebar:
    if st.button("🔄 Yeni Test Başlat", use_container_width=True):
        clear_result(RESULT_KEY)
        st.rerun()

# Daha önce sonuç varsa göster
previous_result = get_result(RESULT_KEY)
if previous_result:
    with st.expander("📊 Önceki test sonucunuz", expanded=False):
        st.metric("Ortalama Tepki Süresi", f"{previous_result['average']} ms")
        st.write("Tüm tepkiler:", previous_result['reactionTimes'])

# Ana bileşen - tamamen özelleştirilmiş, textarea yok, sonuçlar doğrudan session_state'e yazılır
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
        
        function updateUI() {
            progressDiv.innerText = `Deneme: ${currentTrial}/${MAX_TRIALS}`;
        }
        
        function logResult() {
            // Doğrudan Streamlit'e veri göndermek için özel bir event kullanıyoruz
            const result = {
                reactionTimes: reactionTimes,
                average: (reactionTimes.reduce((a,b)=>a+b,0) / reactionTimes.length).toFixed(2),
                completed_at: new Date().toISOString()
            };
            // Streamlit JavaScript bileşeni için veri gönderme yöntemi
            window.parent.postMessage({
                type: "streamlit:setComponentValue",
                value: JSON.stringify(result)
            }, "*");
        }
        
        function waitForStimulus() {
            if (!testActive) return;
            waitingForStimulus = true;
            const delay = Math.random() * 4000 + 2000; // 2-6 saniye
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
                // Geçerli tepki
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
                        // Bir sonraki uyarıyı bekle
                        setTimeout(() => {
                            if (testActive) waitForStimulus();
                        }, 1000);
                    }
                } else {
                    statusDiv.innerHTML = `⚠️ Geçersiz tepki (${rt} ms) - Hızlı/Geç kaldınız. Tekrar deneyin.`;
                    statusDiv.style.backgroundColor = "#ffe5b4";
                    startTime = null;
                    clearTimeout(timeoutId);
                    // Hatalı tepkide aynı denemeyi tekrar et
                    setTimeout(() => {
                        if (testActive) waitForStimulus();
                    }, 1500);
                }
            } else if (waitingForStimulus) {
                // Erken tepki
                statusDiv.innerHTML = "❌ Çok erken! Bekleyin ve uyarıya tepki verin.";
                statusDiv.style.backgroundColor = "#ffcccc";
                clearTimeout(timeoutId);
                setTimeout(() => {
                    if (testActive) waitForStimulus();
                }, 1500);
            } else {
                // Test aktif değil veya bekleme modu değil
                if (!testActive) {
                    statusDiv.innerHTML = "🟢 Test başlamamış. Başlatmak için butona tıklayın.";
                }
            }
        }
        
        // Başlat butonu
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
        
        // Tüm ekrana tıklama yakalayıcı (sadece test aktifken)
        document.addEventListener('click', function(e) {
            if (e.target.id !== 'startBtn' && testActive) {
                handleTap();
            }
        });
    </script>
    """,
    height=500,
)

# JavaScript bileşeninden gelen veriyi yakala (postMessage yöntemi)
# Bu kısım streamlit-javascript paketiyle daha temiz çalışır, ancak manuel de yapılabilir.
# Basitçe, bileşenin çıktısını almak için bir text_area kullanmadan doğrudan session_state'e yazmak için
# streamlit-javascript'ten gelen bileşeni kullanabiliriz. Ama mevcut yapıda şöyle yapalım:
# Bileşenin value'sunu yakalamak için st.session_state üzerinde bir değişken tanımlayalım.

# Not: Yukarıdaki postMessage yöntemi, Streamlit'in resmi bileşenlerinde çalışır.
# Daha basit ve kesin çalışan bir yöntem için, yine textarea kullanıp onu gizleyebiliriz.
# Ancak kullanıcı dostu olması için textarea'yı görünmez yapalım ve st.markdown ile gizleyelim.

# Alternatif (güvenilir ve gizli): Küçük bir textarea'yı görünmez yapalım.
# Kullanıcı bunu görmeyecek. Aşağıdaki gibi:

with st.expander("", expanded=False):
    result_json = st.text_area("", key="pvt_hidden_result", label_visibility="collapsed", height=0)
    st.markdown("""<style>.stTextArea [data-baseweb=textarea] { display: none; }</style>""", unsafe_allow_html=True)

if result_json:
    try:
        import json
        data = json.loads(result_json)
        if send_result_to_backend(data, RESULT_KEY):
            st.success("✅ PVT sonucu kaydedildi!", icon="✅")
            # Sayfayı yenilemeden sonucu göstermek için
            st.rerun()
    except:
        pass

# Sonucu göster (varsa)
final = get_result(RESULT_KEY)
if final:
    st.success("### 🎯 Son Test Sonucunuz")
    col1, col2 = st.columns(2)
    col1.metric("Ortalama Tepki Süresi", f"{final['average']} ms")
    col2.metric("Deneme Sayısı", len(final['reactionTimes']))
    st.line_chart(final['reactionTimes'], x_label="Deneme", y_label="Tepki Süresi (ms)")
else:
    st.info("Testi başlatmak için yukarıdaki butona tıklayın. Test bittiğinde sonuçlar otomatik görünecektir.")