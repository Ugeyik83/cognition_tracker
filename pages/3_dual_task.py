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
        st.metric("Doğruluk Oranı", f"{previous_result['accuracy']:.1f}%")
        st.metric("Puan (Hedef vuruş)", previous_result['score'])
        st.metric("Hata (Siyah noktaya tıklama)", previous_result['mistakes'])
        st.metric("Toplam Deneme", previous_result['totalAttempts'])

components.html(
    """
    <div style="font-family: sans-serif; max-width: 750px; margin: 0 auto;">
        <div style="background: #f0f2f6; padding: 20px; border-radius: 20px; text-align: center;">
            <h3>🎯 Kural</h3>
            <p><span style="color:red; font-weight:bold;">🔴 KIRMIZI</span> hareketli hedefe <strong>tıklayın</strong>.<br>
            <span style="color:black; font-weight:bold;">⚫ SİYAH</span> noktalara <strong>tıklamayın</strong>.</p>
            <p>Her doğru vuruş +1 puan. Yanlışlıkla siyaha tıklamak hata sayılır.<br>
            Toplam <strong>30 geçerli tıklama</strong> (doğru+yanlış) sonunda test biter.</p>
            
            <button id="startBtn" style="background: #4CAF50; color: white; border: none; padding: 12px 30px; font-size: 18px; border-radius: 40px; cursor: pointer; margin-bottom: 20px;">🚀 Testi Başlat</button>
            
            <canvas id="gameCanvas" width="650" height="400" style="border-radius: 20px; background-color: #ffffff; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin-bottom: 10px;"></canvas>
            
            <div id="messageBox" style="margin: 10px; font-size: 16px; color: #555;">Test başlamadı</div>
            <div id="scoreBoard" style="font-size: 22px; margin: 10px;">🎯 Puan: 0 &nbsp;&nbsp; ❌ Hata: 0</div>
            <div id="progress" style="font-size: 14px; color: gray;">İlerleme: 0 / 30</div>
        </div>
    </div>
    <textarea id="resultData" style="display:none;"></textarea>

    <script>
        let active = false;
        let score = 0;
        let mistakes = 0;
        let totalAttempts = 0;
        const MAX_ATTEMPTS = 30;
        
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const messageDiv = document.getElementById('messageBox');
        const scoreSpan = document.getElementById('scoreBoard');
        const progressSpan = document.getElementById('progress');
        const hiddenTextarea = document.getElementById('resultData');
        
        // Hedef (kırmızı top) ve distraktör (siyah top) nesneleri
        let target = { x: 300, y: 200, r: 20, dx: 2.5, dy: 2.0 };
        let distractor = { x: 100, y: 100, r: 15, dx: 1.8, dy: 1.5 };
        
        let animationId = null;
        
        function updateUI() {
            scoreSpan.innerHTML = `🎯 Puan: ${score} &nbsp;&nbsp; ❌ Hata: ${mistakes}`;
            progressSpan.innerText = `İlerleme: ${totalAttempts} / ${MAX_ATTEMPTS}`;
        }
        
        function endTest() {
            active = false;
            if (animationId) cancelAnimationFrame(animationId);
            const accuracy = totalAttempts > 0 ? (score / totalAttempts) * 100 : 0;
            const result = {
                score: score,
                mistakes: mistakes,
                totalAttempts: totalAttempts,
                accuracy: accuracy
            };
            hiddenTextarea.value = JSON.stringify(result);
            hiddenTextarea.dispatchEvent(new Event('change', { bubbles: true }));
            messageDiv.innerText = "🏁 Test tamamlandı! Sonuçlar kaydedildi.";
            document.getElementById('startBtn').disabled = false;
        }
        
        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            // Distraktör (siyah)
            ctx.beginPath();
            ctx.arc(distractor.x, distractor.y, distractor.r, 0, Math.PI*2);
            ctx.fillStyle = '#333333';
            ctx.fill();
            ctx.shadowBlur = 0;
            // Hedef (kırmızı) - parlaklık için gölge eklendi
            ctx.beginPath();
            ctx.arc(target.x, target.y, target.r, 0, Math.PI*2);
            ctx.fillStyle = '#e74c3c';
            ctx.fill();
            ctx.shadowBlur = 0;
        }
        
        function updatePosition() {
            if (!active) return;
            // Hedef hareketi
            target.x += target.dx;
            target.y += target.dy;
            if (target.x - target.r <= 0 || target.x + target.r >= canvas.width) target.dx *= -1;
            if (target.y - target.r <= 0 || target.y + target.r >= canvas.height) target.dy *= -1;
            
            // Distraktör hareketi
            distractor.x += distractor.dx;
            distractor.y += distractor.dy;
            if (distractor.x - distractor.r <= 0 || distractor.x + distractor.r >= canvas.width) distractor.dx *= -1;
            if (distractor.y - distractor.r <= 0 || distractor.y + distractor.r >= canvas.height) distractor.dy *= -1;
            
            draw();
        }
        
        function gameLoop() {
            if (!active) return;
            updatePosition();
            animationId = requestAnimationFrame(gameLoop);
        }
        
        function handleCanvasClick(e) {
            if (!active) return;
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            const mouseX = (e.clientX - rect.left) * scaleX;
            const mouseY = (e.clientY - rect.top) * scaleY;
            
            // Hedefe tıklama kontrolü
            const distToTarget = Math.hypot(mouseX - target.x, mouseY - target.y);
            const distToDistractor = Math.hypot(mouseX - distractor.x, mouseY - distractor.y);
            
            if (distToTarget <= target.r) {
                // Doğru vuruş
                score++;
                totalAttempts++;
                messageDiv.innerText = "✅ +1 puan! Hedef vuruldu.";
                messageDiv.style.color = "green";
                setTimeout(() => { if (active) messageDiv.style.color = "#555"; }, 500);
                updateUI();
                // Hedefi rastgele bir konuma sıçrat (zorluk artışı)
                target.x = Math.random() * (canvas.width - 2*target.r) + target.r;
                target.y = Math.random() * (canvas.height - 2*target.r) + target.r;
                // Hızı biraz artır (opsiyonel)
                target.dx *= 1.02;
                target.dy *= 1.02;
            } 
            else if (distToDistractor <= distractor.r) {
                // Hata: siyaha tıklama
                mistakes++;
                totalAttempts++;
                messageDiv.innerText = "❌ Hata! Siyah noktaya tıkladınız.";
                messageDiv.style.color = "red";
                setTimeout(() => { if (active) messageDiv.style.color = "#555"; }, 500);
                updateUI();
            }
            else {
                // Boş yere tıklama - sayılmaz, sadece uyarı
                messageDiv.innerText = "⚠️ Boş alana tıkladınız. Hedef kırmızı topa tıklayın!";
                messageDiv.style.color = "orange";
                setTimeout(() => { if (active) messageDiv.style.color = "#555"; }, 800);
                return; // totalAttempts artmaz
            }
            
            if (totalAttempts >= MAX_ATTEMPTS) {
                endTest();
            }
        }
        
        function resetGame() {
            // Başlangıç pozisyonları
            target = { x: 300, y: 200, r: 20, dx: 2.5, dy: 2.0 };
            distractor = { x: 100, y: 100, r: 15, dx: 1.8, dy: 1.5 };
            score = 0;
            mistakes = 0;
            totalAttempts = 0;
            updateUI();
            draw();
        }
        
        document.getElementById('startBtn').onclick = () => {
            if (active) return;
            active = true;
            resetGame();
            messageDiv.innerText = "Test başladı! Kırmızı hedefe tıkla, siyahlardan kaçın.";
            messageDiv.style.color = "#555";
            document.getElementById('startBtn').disabled = true;
            if (animationId) cancelAnimationFrame(animationId);
            gameLoop();
        };
        
        canvas.addEventListener('click', handleCanvasClick);
        // İlk çizim
        draw();
    </script>
    """,
    height=620,
)

with st.container():
    result_json = st.text_area(
        "###",
        key="dual_hidden_result",
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
            st.success("✅ İkili Görev sonucu kaydedildi!", icon="✅")
            st.rerun()
    except:
        pass

final = get_result(RESULT_KEY)
if final:
    st.success("### 🎯 Son Test Sonucunuz")
    col1, col2, col3 = st.columns(3)
    col1.metric("Doğruluk Oranı", f"{final['accuracy']:.1f}%")
    col2.metric("Puan (Hedef vuruş)", final['score'])
    col3.metric("Hata (Siyah tıklama)", final['mistakes'])
    st.progress(final['accuracy'] / 100, text=f"Doğruluk: %{final['accuracy']:.1f}")
else:
    st.info("Testi başlatmak için butona tıklayın. Kırmızı topa tıklayarak puan kazanın, siyah toplardan kaçının. 30 geçerli tıklama sonunda test biter.")