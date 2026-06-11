# utils/js_components.py

def dual_task_component(duration_ms=90000, shape_interval_min_ms=2000,
                        shape_interval_max_ms=4500, shape_duration_ms=1500):
    """
    Renk (üst) ve şekil (alt) görevlerini içeren Dual Task bileşeni.
    Sonuçları gizli bir textarea'ya yazar.
    """
    return f"""
    <div id="dual-task-container" style="font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto;">
        <div style="background: #1E1E2F; border-radius: 20px; padding: 20px; color: white;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 16px;">
                <div>⏱️ <span id="timer">90</span> saniye</div>
                <div>🎯 Renk: <span id="primaryScore">0</span> / 0</div>
                <div>🔷 Şekil: <span id="secondaryScore">0</span> / 0</div>
            </div>
            
            <!-- Üst alan: Renk görevi -->
            <div id="primaryTask" style="background: #0A0A14; border-radius: 24px; padding: 30px; margin-bottom: 20px; text-align: center; border: 2px solid #2A2A3A;">
                <div style="font-size: 14px; color: #8B95B0; margin-bottom: 12px;">🔴 RENK GÖREVİ (sürekli)</div>
                <div id="colorStimulus" style="width: 120px; height: 120px; margin: 0 auto; border-radius: 60px; background-color: #555; transition: 0.1s;"></div>
                <div style="margin-top: 16px; font-size: 12px;">Turuncu 🟠 → <kbd>SPACE</kbd> | Diğer renkler → basma</div>
            </div>
            
            <!-- Alt alan: Şekil görevi -->
            <div id="secondaryTask" style="background: #0A0A14; border-radius: 24px; padding: 30px; text-align: center; border: 2px solid #2A2A3A;">
                <div style="font-size: 14px; color: #8B95B0; margin-bottom: 12px;">🔷 ŞEKİL GÖREVİ (aralıklı)</div>
                <div id="shapeStimulus" style="width: 120px; height: 120px; margin: 0 auto; background-color: #2A2A3A; border-radius: 20px; display: flex; align-items: center; justify-content: center; font-size: 48px;">?</div>
                <div style="margin-top: 16px; font-size: 12px;">Daire ● → <kbd>D</kbd> | Kare ■ → <kbd>K</kbd></div>
            </div>
            
            <div id="message" style="margin-top: 20px; text-align: center; font-size: 13px; color: #F5A623;">Test başlamadı. Hazır olduğunuzda butona basın.</div>
        </div>
    </div>
    <textarea id="resultData" style="display:none;"></textarea>

    <script>
        (function() {{
            let active = false;
            let remainingSeconds = {duration_ms // 1000};
            let timerInterval = null;
            
            // Renk görevi
            let primaryCorrect = 0;
            let primaryTotal = 0;
            let currentColor = null;
            let colorInterval = null;
            const colors = [
                {{ name: "turuncu", code: "#FF8C42", isTarget: true }},
                {{ name: "mavi",    code: "#3D8BFF", isTarget: false }},
                {{ name: "mor",     code: "#A855F7", isTarget: false }}
            ];
            
            // Şekil görevi
            let secondaryCorrect = 0;
            let secondaryTotal = 0;
            let shapeTimeout = null;
            let currentShape = null;
            let shapeVisible = false;
            
            const timerElem = document.getElementById('timer');
            const primaryScoreElem = document.getElementById('primaryScore');
            const secondaryScoreElem = document.getElementById('secondaryScore');
            const colorStimulus = document.getElementById('colorStimulus');
            const shapeStimulus = document.getElementById('shapeStimulus');
            const messageDiv = document.getElementById('message');
            const hiddenTextarea = document.getElementById('resultData');
            
            function updateScores() {{
                primaryScoreElem.innerText = primaryCorrect + " / " + primaryTotal;
                secondaryScoreElem.innerText = secondaryCorrect + " / " + secondaryTotal;
            }}
            
            function showMessage(msg, isError) {{
                messageDiv.innerHTML = msg;
                messageDiv.style.color = isError ? "#FF6B6B" : "#F5A623";
                setTimeout(function() {{
                    if (active) messageDiv.style.color = "#F5A623";
                }}, 1000);
            }}
            
            // Renk görevi: rastgele renk göster
            function showRandomColor() {{
                if (!active) return;
                var colorObj = colors[Math.floor(Math.random() * colors.length)];
                currentColor = colorObj;
                colorStimulus.style.backgroundColor = colorObj.code;
                primaryTotal++;
                updateScores();
            }}
            
            // Şekil görevi: rastgele süre sonra şekil göster
            function scheduleShape() {{
                if (!active) return;
                var delay = Math.random() * ({shape_interval_max_ms} - {shape_interval_min_ms}) + {shape_interval_min_ms};
                shapeTimeout = setTimeout(function() {{
                    if (!active) return;
                    var isCircle = Math.random() < 0.5;
                    currentShape = isCircle ? 'circle' : 'square';
                    shapeStimulus.innerHTML = isCircle ? '●' : '■';
                    shapeStimulus.style.fontSize = '64px';
                    shapeStimulus.style.color = '#FFD966';
                    shapeVisible = true;
                    secondaryTotal++;
                    updateScores();
                    // Şekil {shape_duration_ms} ms sonra kaybolur
                    setTimeout(function() {{
                        if (active) {{
                            shapeStimulus.innerHTML = '?';
                            currentShape = null;
                            shapeVisible = false;
                            scheduleShape();
                        }}
                    }}, {shape_duration_ms});
                }}, delay);
            }}
            
            function endTest() {{
                active = false;
                if (timerInterval) clearInterval(timerInterval);
                if (colorInterval) clearInterval(colorInterval);
                if (shapeTimeout) clearTimeout(shapeTimeout);
                colorStimulus.style.backgroundColor = "#555";
                shapeStimulus.innerHTML = "?";
                var primaryAccuracy = primaryTotal > 0 ? primaryCorrect / primaryTotal : 0;
                var secondaryAccuracy = secondaryTotal > 0 ? secondaryCorrect / secondaryTotal : 0;
                var result = {{
                    primary_correct: primaryCorrect,
                    primary_total: primaryTotal,
                    primary_accuracy: primaryAccuracy,
                    secondary_correct: secondaryCorrect,
                    secondary_total: secondaryTotal,
                    secondary_accuracy: secondaryAccuracy,
                    summary: {{
                        primary_accuracy: primaryAccuracy,
                        secondary_accuracy: secondaryAccuracy,
                        primary_correct: primaryCorrect,
                        secondary_correct: secondaryCorrect
                    }}
                }};
                hiddenTextarea.value = JSON.stringify(result);
                hiddenTextarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                showMessage("✅ Test tamamlandı! Sonuçlar kaydedildi.", false);
            }}
            
            function startTimer() {{
                timerInterval = setInterval(function() {{
                    if (!active) return;
                    if (remainingSeconds <= 0) {{
                        clearInterval(timerInterval);
                        endTest();
                    }} else {{
                        remainingSeconds--;
                        timerElem.innerText = remainingSeconds;
                    }}
                }}, 1000);
            }}
            
            function handleKeydown(e) {{
                if (!active) return;
                var key = e.key;
                // Renk görevi: Space tuşu
                if (key === ' ' || key === 'Space') {{
                    e.preventDefault();
                    if (currentColor && currentColor.isTarget) {{
                        primaryCorrect++;
                        showMessage("✅ Renk doğru (Space)", false);
                    }} else if (currentColor && !currentColor.isTarget) {{
                        showMessage("❌ Hata! Turuncu değilken Space'e bastınız.", true);
                    }}
                    updateScores();
                }}
                // Şekil görevi: D ve K tuşları
                if (key === 'd' || key === 'D') {{
                    if (currentShape === 'circle') {{
                        secondaryCorrect++;
                        showMessage("✅ Şekil doğru (D)", false);
                    }} else if (currentShape !== null) {{
                        showMessage("❌ Hata! Daire değilken D'ye bastınız.", true);
                    }}
                    updateScores();
                }}
                if (key === 'k' || key === 'K') {{
                    if (currentShape === 'square') {{
                        secondaryCorrect++;
                        showMessage("✅ Şekil doğru (K)", false);
                    }} else if (currentShape !== null) {{
                        showMessage("❌ Hata! Kare değilken K'ye bastınız.", true);
                    }}
                    updateScores();
                }}
            }}
            
            function startTest() {{
                if (active) return;
                active = true;
                remainingSeconds = {duration_ms // 1000};
                primaryCorrect = 0;
                primaryTotal = 0;
                secondaryCorrect = 0;
                secondaryTotal = 0;
                currentColor = null;
                currentShape = null;
                shapeVisible = false;
                updateScores();
                timerElem.innerText = remainingSeconds;
                // Renk döngüsü: her 1.8 saniyede yeni renk
                colorInterval = setInterval(function() {{ showRandomColor(); }}, 1800);
                showRandomColor();
                scheduleShape();
                startTimer();
                showMessage("🎯 Test başladı! Turuncuya Space, daireye D, kareye K.", false);
                window.addEventListener('keydown', handleKeydown);
            }}
            
            window.startDualTask = startTest;
        }})();
    </script>
    """