# pages/2_go_nogo.py
import streamlit as st
import streamlit.components.v1 as components
from utils.result_handler import send_result_to_backend, get_result, clear_result

st.set_page_config(page_title="Go/No-Go Testi", layout="centered")
st.title("🛑 Go/No-Go Dikkat Testi")

RESULT_KEY = "gonogo_result"

if st.button("🔄 Yeni Test Başlat"):
    clear_result(RESULT_KEY)
    st.rerun()

components.html(
    """
    <div>
        <h3>Kural: Sadece <span style="color:green;">YEŞİL</span> kutuya tıklayın. Kırmızıya tıklamayın.</h3>
        <button id="startBtn">Testi Başlat</button>
        <div id="stimulus" style="width:200px;height:200px;margin:20px auto;background-color:gray;display:flex;align-items:center;justify-content:center;font-size:24px;">?</div>
        <div id="score">Doğru: 0 | Yanlış: 0</div>
        <div id="resultArea"></div>
    </div>
    <script>
        let active = false;
        let correct = 0, incorrect = 0;
        let currentColor = null;
        let trialCount = 0;
        const MAX_TRIALS = 20;

        function showStimulus() {
            if (!active || trialCount >= MAX_TRIALS) return;
            const isGo = Math.random() < 0.6; // %60 Go
            currentColor = isGo ? 'green' : 'red';
            const stimDiv = document.getElementById('stimulus');
            stimDiv.style.backgroundColor = currentColor;
            stimDiv.innerText = isGo ? 'TIKLA!' : 'DOKUNMA!';
        }

        function endTest() {
            active = false;
            const resultArea = document.getElementById('resultArea');
            resultArea.innerHTML = `<textarea id="resultData" style="display:none;">${JSON.stringify({correct: correct, incorrect: incorrect, total: MAX_TRIALS, accuracy: (correct/(correct+incorrect))*100})}</textarea>`;
            document.getElementById('resultData').dispatchEvent(new Event('change'));
        }

        function handleClick() {
            if (!active) return;
            if (currentColor === 'green') {
                correct++;
                document.getElementById('score').innerHTML = `Doğru: ${correct} | Yanlış: ${incorrect}`;
            } else if (currentColor === 'red') {
                incorrect++;
                document.getElementById('score').innerHTML = `Doğru: ${correct} | Yanlış: ${incorrect}`;
            }
            trialCount++;
            if (trialCount >= MAX_TRIALS) {
                endTest();
            } else {
                setTimeout(showStimulus, 500);
            }
        }

        document.getElementById('startBtn').onclick = () => {
            active = true;
            correct = 0; incorrect = 0; trialCount = 0;
            document.getElementById('score').innerHTML = `Doğru: 0 | Yanlış: 0`;
            showStimulus();
        };
        document.getElementById('stimulus').onclick = handleClick;
    </script>
    """,
    height=500,
)

result_data = st.text_area("", key="gonogo_textarea", label_visibility="collapsed")
if result_data:
    try:
        import json
        data = json.loads(result_data)
        send_result_to_backend(data, RESULT_KEY)
        st.session_state.gonogo_textarea = ""
    except:
        pass

res = get_result(RESULT_KEY)
if res:
    st.subheader("📊 Son Go/No-Go Sonucu")
    st.json(res)