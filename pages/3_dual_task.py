# pages/3_dual_task.py
import streamlit as st
import streamlit.components.v1 as components
from utils.result_handler import send_result_to_backend, get_result, clear_result

st.set_page_config(page_title="İkili Görev Testi", layout="centered")
st.title("🎯 İkili Görev (Dual Task)")

RESULT_KEY = "dual_result"

if st.button("🔄 Yeni Test Başlat"):
    clear_result(RESULT_KEY)
    st.rerun()

components.html(
    """
    <div>
        <h3>🔴 Hareketli hedefe tıklayın ⚫ Siyah noktalara tıklamayın.</h3>
        <button id="startBtn">Testi Başlat</button>
        <canvas id="gameCanvas" width="600" height="400" style="border:1px solid black; margin-top:10px;"></canvas>
        <div id="scoreDisplay">Puan: 0 | Hata: 0</div>
        <div id="resultArea"></div>
    </div>
    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        let active = false;
        let score = 0;
        let mistakes = 0;
        let target = {x: 300, y: 200, size: 30};
        let distractor = {x: 100, y: 100, size: 20};
        let targetDX = 2, targetDY = 1.5;
        let distDX = 1.8, distDY = 1.2;
        let animationId = null;
        const MAX_CLICKS = 30;

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = 'red';
            ctx.beginPath();
            ctx.arc(target.x, target.y, target.size/2, 0, Math.PI*2);
            ctx.fill();
            ctx.fillStyle = 'black';
            ctx.beginPath();
            ctx.arc(distractor.x, distractor.y, distractor.size/2, 0, Math.PI*2);
            ctx.fill();
        }

        function update() {
            if (!active) return;
            target.x += targetDX;
            target.y += targetDY;
            if (target.x - target.size/2 <= 0 || target.x + target.size/2 >= canvas.width) targetDX *= -1;
            if (target.y - target.size/2 <= 0 || target.y + target.size/2 >= canvas.height) targetDY *= -1;
            
            distractor.x += distDX;
            distractor.y += distDY;
            if (distractor.x - distractor.size/2 <= 0 || distractor.x + distractor.size/2 >= canvas.width) distDX *= -1;
            if (distractor.y - distractor.size/2 <= 0 || distractor.y + distractor.size/2 >= canvas.height) distDY *= -1;
            
            draw();
            animationId = requestAnimationFrame(update);
        }

        function endTest() {
            active = false;
            if (animationId) cancelAnimationFrame(animationId);
            const resultArea = document.getElementById('resultArea');
            resultArea.innerHTML = `<textarea id="resultData" style="display:none;">${JSON.stringify({score: score, mistakes: mistakes, totalAttempts: score+mistakes, accuracy: (score/(score+mistakes))*100})}</textarea>`;
            document.getElementById('resultData').dispatchEvent(new Event('change'));
        }

        function handleCanvasClick(e) {
            if (!active) return;
            const rect = canvas.getBoundingClientRect();
            const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width);
            const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height);
            const distToTarget = Math.hypot(mouseX - target.x, mouseY - target.y);
            const distToDist = Math.hypot(mouseX - distractor.x, mouseY - distractor.y);
            
            if (distToTarget <= target.size/2) {
                score++;
                document.getElementById('scoreDisplay').innerHTML = `Puan: ${score} | Hata: ${mistakes}`;
                // hedef küçülüp zorlaşabilir - opsiyonel
                if (score + mistakes >= MAX_CLICKS) endTest();
            } else if (distToDist <= distractor.size/2) {
                mistakes++;
                document.getElementById('scoreDisplay').innerHTML = `Puan: ${score} | Hata: ${mistakes}`;
                if (score + mistakes >= MAX_CLICKS) endTest();
            }
        }

        document.getElementById('startBtn').onclick = () => {
            if (animationId) cancelAnimationFrame(animationId);
            active = true;
            score = 0; mistakes = 0;
            document.getElementById('scoreDisplay').innerHTML = `Puan: 0 | Hata: 0`;
            target = {x: 300, y: 200, size: 30};
            distractor = {x: 100, y: 100, size: 20};
            update();
        };
        canvas.addEventListener('click', handleCanvasClick);
    </script>
    """,
    height=550,
)

result_data = st.text_area("", key="dual_textarea", label_visibility="collapsed")
if result_data:
    try:
        import json
        data = json.loads(result_data)
        send_result_to_backend(data, RESULT_KEY)
        st.session_state.dual_textarea = ""
    except:
        pass

res = get_result(RESULT_KEY)
if res:
    st.subheader("📊 Son İkili Görev Sonucu")
    st.json(res)