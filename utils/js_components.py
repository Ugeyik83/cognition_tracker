"""
utils/js_components.py

Streamlit'e gömülü JavaScript bileşenleri.
Her fonksiyon bir HTML string döndürür; streamlit.components.v1.html() ile render edilir.

Tasarım kararları:
- RT ölçümü performance.now() ile client-side (~1ms hassasiyet)
- Tüm trial'lar JS'te biriktirilir, test bitince tek seferde Python'a gönderilir
- Python'a veri aktarımı: Streamlit'in çift yönlü iletişimi olmadığı için
  sonuçlar URL query param veya localStorage yerine
  gizli bir <textarea> + Streamlit'in html component return value ile aktarılır
- Her bileşen kendi içinde bağımsız (self-contained)
"""


def pvt_component(duration_ms: int = 300_000, min_isi_ms: int = 2000, max_isi_ms: int = 8000, lapse_threshold_ms: int = 500) -> str:
    """
    Psychomotor Vigilance Task (PVT) JS bileşeni.

    Parametreler:
        duration_ms:       Test süresi (varsayılan 5 dk)
        min_isi_ms:        Min uyaranlar arası aralık
        max_isi_ms:        Max uyaranlar arası aralık
        lapse_threshold_ms: Bu değer üstü lapse sayılır

    Döndürür:
        JSON string → {trials: [{rt, is_lapse, is_false_start}], summary: {...}}
        #result textarea içinde
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0F1419;
    color: #D2DCE1;
    font-family: monospace;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 520px;
    user-select: none;
  }}
  #stimulus {{
    width: 120px; height: 120px;
    border-radius: 50%;
    border: 2px solid #1E2D3D;
    margin: 24px auto;
    transition: background 0.05s;
  }}
  #stimulus.active {{
    background: #FFDC32;
    box-shadow: 0 0 40px #FFDC3266;
    border-color: #FFDC32;
  }}
  #feedback {{
    height: 28px;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 8px;
  }}
  #stats {{
    font-size: 13px;
    color: #5a7a8a;
    margin-bottom: 16px;
    text-align: center;
    line-height: 1.8;
  }}
  #progressbar {{
    width: 320px; height: 6px;
    background: #1E2D3D;
    border-radius: 3px;
    margin-bottom: 20px;
  }}
  #progressfill {{
    height: 6px;
    background: #00C88C;
    border-radius: 3px;
    width: 0%;
    transition: width 0.5s linear;
  }}
  #instruction {{
    font-size: 13px;
    color: #5a7a8a;
    margin-top: 8px;
  }}
  #result {{ display: none; }}
  #done-msg {{
    display: none;
    font-size: 16px;
    color: #00C88C;
    text-align: center;
  }}
</style>
</head>
<body>

<div id="progressbar"><div id="progressfill"></div></div>
<div id="stimulus"></div>
<div id="feedback"></div>
<div id="stats">
  Tepki: <span id="count">0</span> &nbsp;|&nbsp;
  Ort. RT: <span id="mean-rt">—</span> ms &nbsp;|&nbsp;
  Lapse: <span id="lapse-count">0</span>
</div>
<div id="instruction">Sarı daire göründüğünde SPACE veya tıklayın</div>

<div id="done-msg">✓ Test tamamlandı. Sonuçlar kaydediliyor...</div>
<textarea id="result"></textarea>

<script>
const DURATION    = {duration_ms};
const MIN_ISI     = {min_isi_ms};
const MAX_ISI     = {max_isi_ms};
const LAPSE_MS    = {lapse_threshold_ms};
const TIMEOUT_MS  = 3000; // yanıtsız kalınan uyaran için zaman aşımı

let trials       = [];
let stimulusOn   = false;
let stimStart    = 0;
let testStart    = performance.now();
let nextStimTime = 0;
let stimTimer    = null;
let timeoutTimer = null;
let progressTimer = null;
let done         = false;

const stimEl     = document.getElementById('stimulus');
const feedbackEl = document.getElementById('feedback');
const countEl    = document.getElementById('count');
const meanRtEl   = document.getElementById('mean-rt');
const lapseEl    = document.getElementById('lapse-count');
const fillEl     = document.getElementById('progressfill');
const doneMsg    = document.getElementById('done-msg');
const instruction = document.getElementById('instruction');

function scheduleNext() {{
  const isi = MIN_ISI + Math.random() * (MAX_ISI - MIN_ISI);
  stimTimer = setTimeout(showStimulus, isi);
}}

function showStimulus() {{
  stimulusOn = true;
  stimStart  = performance.now();
  stimEl.classList.add('active');
  // Yanıt gelmezse zaman aşımı
  timeoutTimer = setTimeout(() => {{
    if (stimulusOn) {{
      recordResponse(TIMEOUT_MS, false);
    }}
  }}, TIMEOUT_MS);
}}

function hideStimulus() {{
  stimulusOn = false;
  stimEl.classList.remove('active');
  clearTimeout(timeoutTimer);
}}

function recordResponse(rt, isTimeout) {{
  const isLapse      = rt >= LAPSE_MS;
  const isFalseStart = rt < 0; // negatif olamaz ama korunma
  hideStimulus();
  trials.push({{ rt: Math.round(rt), is_lapse: isLapse, is_false_start: false }});
  updateStats();

  // Feedback
  if (!isTimeout) {{
    feedbackEl.style.color = isLapse ? '#FF8C00' : '#00C88C';
    feedbackEl.textContent = isLapse ? `⚠ ${{Math.round(rt)}} ms` : `✓ ${{Math.round(rt)}} ms`;
    setTimeout(() => {{ feedbackEl.textContent = ''; }}, 600);
  }}

  if (!done) scheduleNext();
}}

function handleRespond() {{
  if (done) return;
  if (stimulusOn) {{
    const rt = performance.now() - stimStart;
    recordResponse(rt, false);
  }} else {{
    // Erken basma
    trials.push({{ rt: null, is_lapse: false, is_false_start: true }});
    feedbackEl.style.color = '#DC3232';
    feedbackEl.textContent = '✗ Erken basma';
    setTimeout(() => {{ feedbackEl.textContent = ''; }}, 600);
  }}
}}

function updateStats() {{
  const valid = trials.filter(t => !t.is_false_start && t.rt !== null);
  const lapses = valid.filter(t => t.is_lapse).length;
  const meanRt = valid.length
    ? Math.round(valid.reduce((s, t) => s + t.rt, 0) / valid.length)
    : 0;
  countEl.textContent  = valid.length;
  meanRtEl.textContent = meanRt || '—';
  lapseEl.textContent  = lapses;
}}

function finishTest() {{
  done = true;
  clearTimeout(stimTimer);
  clearTimeout(timeoutTimer);
  clearInterval(progressTimer);
  hideStimulus();

  const valid       = trials.filter(t => !t.is_false_start && t.rt !== null);
  const falseStarts = trials.filter(t => t.is_false_start).length;
  const lapses      = valid.filter(t => t.is_lapse).length;
  const rts         = valid.map(t => t.rt);
  const meanRt      = rts.length ? Math.round(rts.reduce((a,b) => a+b,0) / rts.length) : 0;
  const medianRt    = rts.length ? rts.slice().sort((a,b)=>a-b)[Math.floor(rts.length/2)] : 0;

  const summary = {{
    mean_rt:      meanRt,
    median_rt:    medianRt,
    lapses:       lapses,
    false_starts: falseStarts,
    n_trials:     valid.length,
  }};

  const payload = JSON.stringify({{ trials, summary }});
  document.getElementById('result').value = payload;

  // Streamlit'e gönder
  window.parent.postMessage({{ type: 'pvt_done', payload }}, '*');
  window.parent.localStorage.setItem('pvt_result', payload);

  instruction.style.display = 'none';
  doneMsg.style.display     = 'block';
  stimEl.style.display      = 'none';
}}

// Progress bar güncelle
progressTimer = setInterval(() => {{
  const elapsed = performance.now() - testStart;
  const pct     = Math.min(elapsed / DURATION * 100, 100);
  fillEl.style.width = pct + '%';
  if (elapsed >= DURATION && !done) finishTest();
}}, 500);

// İlk uyaran
scheduleNext();

// Klavye
document.addEventListener('keydown', e => {{
  if (e.code === 'Space') {{ e.preventDefault(); handleRespond(); }}
}});
// Tıklama (mobil / fare)
document.addEventListener('click', handleRespond);
</script>
</body>
</html>
"""


def gonogo_component(n_trials: int = 60, go_ratio: float = 0.75, stim_ms: int = 800, isi_ms: int = 1200) -> str:
    """
    Go/No-Go JS bileşeni.

    Yeşil = GO (SPACE), Kırmızı = NO-GO (basma).
    d-prime JS içinde hesaplanır, Python'a özet gönderilir.
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0F1419; color: #D2DCE1;
    font-family: monospace;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 520px; user-select: none;
  }}
  #stimulus {{
    width: 130px; height: 130px; border-radius: 50%;
    border: 2px solid #1E2D3D;
    margin: 20px auto;
  }}
  #stimulus.go   {{ background: #32DC64; box-shadow: 0 0 40px #32DC6466; border-color: #32DC64; }}
  #stimulus.nogo {{ background: #DC3232; box-shadow: 0 0 40px #DC323266; border-color: #DC3232; }}
  #label {{ font-size: 16px; height: 24px; font-weight: bold; margin-bottom: 8px; }}
  #stats {{ font-size: 13px; color: #5a7a8a; text-align: center; line-height: 1.8; }}
  #progressbar {{ width: 320px; height: 6px; background: #1E2D3D; border-radius: 3px; margin-bottom: 20px; }}
  #progressfill {{ height: 6px; background: #00C88C; border-radius: 3px; width: 0%; }}
  #fixation {{ font-size: 28px; color: #1E2D3D; height: 130px; display:flex; align-items:center; justify-content:center; margin: 20px auto; width:130px; }}
  #done-msg {{ display:none; font-size:16px; color:#00C88C; text-align:center; }}
  #result {{ display:none; }}
</style>
</head>
<body>

<div id="progressbar"><div id="progressfill"></div></div>
<div id="stimulus"></div>
<div id="fixation" style="display:none">+</div>
<div id="label"></div>
<div id="stats">
  Deneme: <span id="trial-count">0</span> / {n_trials} &nbsp;|&nbsp;
  Hit: <span id="hit-rate">—</span> &nbsp;|&nbsp;
  FA: <span id="fa-rate">—</span>
</div>

<div id="done-msg">✓ Test tamamlandı.</div>
<textarea id="result"></textarea>

<script>
const N_TRIALS  = {n_trials};
const GO_RATIO  = {go_ratio};
const STIM_MS   = {stim_ms};
const ISI_MS    = {isi_ms};

// Trial listesi oluştur
function buildTrials() {{
  const nGo   = Math.round(N_TRIALS * GO_RATIO);
  const nNogo = N_TRIALS - nGo;
  let arr = [...Array(nGo).fill('go'), ...Array(nNogo).fill('nogo')];
  // Fisher-Yates shuffle
  for (let i = arr.length - 1; i > 0; i--) {{
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }}
  return arr;
}}

const trialSeq = buildTrials();
let results    = [];  // {{type, result, rt}}
let currentIdx = 0;
let phase      = 'isi'; // 'isi' | 'stimulus'
let phaseStart = performance.now();
let responded  = false;
let running    = true;

const stimEl   = document.getElementById('stimulus');
const fixEl    = document.getElementById('fixation');
const labelEl  = document.getElementById('label');
const fillEl   = document.getElementById('progressfill');
const tcEl     = document.getElementById('trial-count');
const hitEl    = document.getElementById('hit-rate');
const faEl     = document.getElementById('fa-rate');
const doneMsg  = document.getElementById('done-msg');

function updateStats() {{
  const goT   = results.filter(r => r.type === 'go');
  const nogoT = results.filter(r => r.type === 'nogo');
  const hits  = goT.filter(r => r.result === 'hit').length;
  const fas   = nogoT.filter(r => r.result === 'false_alarm').length;
  hitEl.textContent = goT.length   ? (hits / goT.length * 100).toFixed(0) + '%'   : '—';
  faEl.textContent  = nogoT.length ? (fas  / nogoT.length * 100).toFixed(0) + '%' : '—';
  tcEl.textContent  = currentIdx;
  fillEl.style.width = (currentIdx / N_TRIALS * 100) + '%';
}}

function finishTest() {{
  running = false;
  stimEl.style.display = 'none';
  fixEl.style.display  = 'none';
  labelEl.textContent  = '';

  const goT   = results.filter(r => r.type === 'go');
  const nogoT = results.filter(r => r.type === 'nogo');
  const hits  = goT.filter(r => r.result === 'hit').length;
  const misses = goT.filter(r => r.result === 'miss').length;
  const fas   = nogoT.filter(r => r.result === 'false_alarm').length;
  const crs   = nogoT.filter(r => r.result === 'correct_rejection').length;

  const hitRate = hits / Math.max(goT.length, 1);
  const faRate  = fas  / Math.max(nogoT.length, 1);

  // d-prime (normal approximation, bounded)
  function normPPF(p) {{
    p = Math.min(Math.max(p, 0.01), 0.99);
    // Abramowitz & Stegun approximation
    const a = [2.515517, 0.802853, 0.010328];
    const b = [1.432788, 0.189269, 0.001308];
    const t = Math.sqrt(-2 * Math.log(p < 0.5 ? p : 1 - p));
    const num = a[0] + t * (a[1] + t * a[2]);
    const den = 1 + t * (b[0] + t * (b[1] + t * b[2]));
    const x   = t - num / den;
    return p < 0.5 ? -x : x;
  }}
  const dprime = normPPF(hitRate) - normPPF(faRate);

  const goRts = goT.filter(r => r.rt).map(r => r.rt);
  const meanRt = goRts.length
    ? Math.round(goRts.reduce((a,b) => a+b,0) / goRts.length)
    : 0;

  const summary = {{
    hit_rate:         +hitRate.toFixed(3),
    false_alarm_rate: +faRate.toFixed(3),
    omission_rate:    +(misses / Math.max(goT.length, 1)).toFixed(3),
    dprime:           +dprime.toFixed(2),
    mean_rt_go:       meanRt,
    n_go:             goT.length,
    n_nogo:           nogoT.length,
  }};

  const payload = JSON.stringify({{ results, summary }});
  document.getElementById('result').value = payload;
  window.parent.postMessage({{ type: 'gonogo_done', payload }}, '*');
  window.parent.localStorage.setItem('gonogo_result', payload);
  doneMsg.style.display = 'block';
}}

function handleRespond() {{
  if (!running) return;
  if (phase === 'stimulus') {{
    if (!responded) {{
      responded = true;
      const rt     = performance.now() - phaseStart;
      const tType  = trialSeq[currentIdx];
      const result = tType === 'go' ? 'hit' : 'false_alarm';
      results.push({{ type: tType, result, rt: Math.round(rt) }});
      updateStats();
      // Trial'ı hemen bitir
      currentIdx++;
      if (currentIdx >= N_TRIALS) {{ finishTest(); return; }}
      phase      = 'isi';
      phaseStart = performance.now();
      stimEl.className = '';
      fixEl.style.display  = 'flex';
      stimEl.style.display = 'none';
      labelEl.textContent  = result === 'hit' ? '' : '✗';
      labelEl.style.color  = '#DC3232';
      setTimeout(() => {{ labelEl.textContent = ''; }}, 400);
    }}
  }}
  // stimulus değilken basma — yok sayılır (false alarm sadece nogo'da)
}}

// Ana döngü
function tick() {{
  if (!running) return;
  const now = performance.now();
  const dt  = now - phaseStart;

  if (phase === 'isi' && dt >= ISI_MS) {{
    phase      = 'stimulus';
    phaseStart = now;
    responded  = false;
    const tType = trialSeq[currentIdx];
    stimEl.className     = tType;
    stimEl.style.display = 'block';
    fixEl.style.display  = 'none';
    labelEl.textContent  = tType === 'go' ? 'SPACE →' : 'BASMA';
    labelEl.style.color  = tType === 'go' ? '#32DC64' : '#DC3232';
  }}

  if (phase === 'stimulus' && dt >= STIM_MS) {{
    // Yanıt gelmedi
    if (!responded) {{
      const tType  = trialSeq[currentIdx];
      const result = tType === 'go' ? 'miss' : 'correct_rejection';
      results.push({{ type: tType, result, rt: null }});
      updateStats();
    }}
    currentIdx++;
    if (currentIdx >= N_TRIALS) {{ finishTest(); return; }}
    phase      = 'isi';
    phaseStart = now;
    stimEl.className     = '';
    stimEl.style.display = 'none';
    fixEl.style.display  = 'flex';
    labelEl.textContent  = '';
  }}

  requestAnimationFrame(tick);
}}

// Başlat
fixEl.style.display  = 'flex';
stimEl.style.display = 'none';
requestAnimationFrame(tick);

document.addEventListener('keydown', e => {{
  if (e.code === 'Space') {{ e.preventDefault(); handleRespond(); }}
}});
document.addEventListener('click', handleRespond);
</script>
</body>
</html>
"""


def dual_task_component(duration_ms: int = 90_000, shape_interval_min_ms: int = 2000, shape_interval_max_ms: int = 4500, shape_duration_ms: int = 1500) -> str:
    """
    Dual Task JS bileşeni.

    Birincil görev (sürekli): Renk hedefi — ekranda beliren renkli daire SPACE ile.
    İkincil görev (asenkron): Şekil hedefi — daire mi / kare mi? D/K tuşu.

    Asenkron tasarım: ikincil görev rastgele aralıklarla primary görevin üzerine gelir.
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0F1419; color: #D2DCE1;
    font-family: monospace;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 560px; user-select: none;
  }}
  #primary-area {{
    display: flex; align-items: center; justify-content: center;
    width: 320px; height: 180px;
    border: 1px solid #1E2D3D; border-radius: 8px;
    margin-bottom: 12px; position: relative;
  }}
  #primary-stim {{
    width: 100px; height: 100px; border-radius: 50%;
    display: none;
  }}
  #secondary-area {{
    width: 320px; height: 80px;
    border: 1px solid #1E2D3D; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 12px; position: relative;
  }}
  #secondary-stim {{ display: none; font-size: 52px; line-height: 1; }}
  #instructions {{
    font-size: 12px; color: #5a7a8a;
    text-align: center; line-height: 1.8; margin-bottom: 8px;
  }}
  #stats {{ font-size: 13px; color: #5a7a8a; text-align: center; line-height: 1.8; }}
  #progressbar {{ width: 320px; height: 6px; background: #1E2D3D; border-radius: 3px; margin-bottom: 16px; }}
  #progressfill {{ height: 6px; background: #00C88C; border-radius: 3px; width: 0%; transition: width 0.5s linear; }}
  #feedback-primary   {{ position:absolute; top:4px; right:8px; font-size:13px; height:18px; }}
  #feedback-secondary {{ position:absolute; top:4px; right:8px; font-size:13px; height:18px; }}
  #done-msg {{ display:none; font-size:16px; color:#00C88C; text-align:center; margin-top:12px; }}
  #result {{ display:none; }}
</style>
</head>
<body>

<div id="progressbar"><div id="progressfill"></div></div>

<div id="primary-area">
  <div id="primary-stim"></div>
  <div id="feedback-primary"></div>
</div>

<div id="secondary-area">
  <div id="secondary-stim"></div>
  <div id="feedback-secondary"></div>
</div>

<div id="instructions">
  Üst kutu: Hedef renk (TURUNCU) göründüğünde → <b>SPACE</b><br>
  Alt kutu: Daire (●) → <b>D</b> &nbsp;|&nbsp; Kare (■) → <b>K</b>
</div>

<div id="stats">
  Birincil: <span id="p-acc">—</span> &nbsp;|&nbsp;
  İkincil: <span id="s-acc">—</span> &nbsp;|&nbsp;
  Kalan: <span id="remaining">—</span>s
</div>

<div id="done-msg">✓ Test tamamlandı.</div>
<textarea id="result"></textarea>

<script>
const DURATION       = {duration_ms};
const SHP_MIN        = {shape_interval_min_ms};
const SHP_MAX        = {shape_interval_max_ms};
const SHP_DUR        = {shape_duration_ms};

// Birincil görev: hedef renk TURUNCU, distractor MAVI
// ISI 1.5-4 sn arası rastgele
const PRIMARY_COLORS = [
  {{ color: '#FF8C00', is_target: true  }},  // turuncu — hedef
  {{ color: '#3B82F6', is_target: false }},  // mavi — distractor
  {{ color: '#A855F7', is_target: false }},  // mor — distractor
];
const PRIMARY_STIM_MS = 800;
const PRIMARY_ISI_MIN = 1500;
const PRIMARY_ISI_MAX = 4000;

let pCorrect = 0, pIncorrect = 0, pMiss = 0;
let sCorrect = 0, sIncorrect = 0, sMiss = 0;

let primaryPhase    = 'isi';
let primaryStart    = performance.now();
let primaryResponded = false;
let currentPrimary  = null;

let secondaryActive    = false;
let secondaryStart     = 0;
let secondaryResponded = false;
let currentShape       = null;
let nextSecondaryTime  = performance.now() + SHP_MIN + Math.random() * (SHP_MAX - SHP_MIN);

let testStart = performance.now();
let done      = false;

const pStimEl   = document.getElementById('primary-stim');
const sStimEl   = document.getElementById('secondary-stim');
const fillEl    = document.getElementById('progressfill');
const pAccEl    = document.getElementById('p-acc');
const sAccEl    = document.getElementById('s-acc');
const remainEl  = document.getElementById('remaining');
const fpEl      = document.getElementById('feedback-primary');
const fsEl      = document.getElementById('feedback-secondary');
const doneMsg   = document.getElementById('done-msg');

function updateStats() {{
  const pTotal = pCorrect + pIncorrect + pMiss;
  const sTotal = sCorrect + sIncorrect + sMiss;
  pAccEl.textContent = pTotal ? (pCorrect / pTotal * 100).toFixed(0) + '%' : '—';
  sAccEl.textContent = sTotal ? (sCorrect / sTotal * 100).toFixed(0) + '%' : '—';
}}

function showFeedback(el, text, color) {{
  el.textContent = text;
  el.style.color = color;
  setTimeout(() => {{ el.textContent = ''; }}, 500);
}}

function scheduleNextPrimary(now) {{
  primaryPhase   = 'isi';
  primaryStart   = now + PRIMARY_ISI_MIN + Math.random() * (PRIMARY_ISI_MAX - PRIMARY_ISI_MIN);
  primaryResponded = false;
  pStimEl.style.display = 'none';
}}

function tick() {{
  if (done) return;
  const now     = performance.now();
  const elapsed = now - testStart;

  // Progress
  fillEl.style.width = Math.min(elapsed / DURATION * 100, 100) + '%';
  remainEl.textContent = Math.max(0, Math.round((DURATION - elapsed) / 1000));

  if (elapsed >= DURATION) {{ finishTest(); return; }}

  // ── Birincil görev ──
  if (primaryPhase === 'isi' && now >= primaryStart) {{
    primaryPhase     = 'stimulus';
    primaryStart     = now;
    primaryResponded = false;
    currentPrimary   = PRIMARY_COLORS[Math.floor(Math.random() * PRIMARY_COLORS.length)];
    pStimEl.style.background = currentPrimary.color;
    pStimEl.style.display    = 'block';
  }}

  if (primaryPhase === 'stimulus' && now - primaryStart >= PRIMARY_STIM_MS) {{
    if (!primaryResponded) {{
      if (currentPrimary.is_target) pMiss++;
      // distractor'a basılmadıysa zaten doğru (correct rejection) — saymıyoruz
    }}
    scheduleNextPrimary(now);
    updateStats();
  }}

  // ── İkincil görev ──
  if (!secondaryActive && now >= nextSecondaryTime) {{
    secondaryActive    = true;
    secondaryStart     = now;
    secondaryResponded = false;
    currentShape       = Math.random() > 0.5 ? 'circle' : 'square';
    sStimEl.textContent    = currentShape === 'circle' ? '●' : '■';
    sStimEl.style.color    = '#D2DCE1';
    sStimEl.style.display  = 'block';
  }}

  if (secondaryActive && now - secondaryStart >= SHP_DUR) {{
    if (!secondaryResponded) {{
      sMiss++;
      updateStats();
    }}
    secondaryActive       = false;
    sStimEl.style.display = 'none';
    nextSecondaryTime     = now + SHP_MIN + Math.random() * (SHP_MAX - SHP_MIN);
  }}

  requestAnimationFrame(tick);
}}

function handlePrimary() {{
  if (done || primaryPhase !== 'stimulus' || primaryResponded) return;
  primaryResponded = true;
  if (currentPrimary.is_target) {{
    pCorrect++;
    showFeedback(fpEl, '✓', '#00C88C');
  }} else {{
    pIncorrect++;
    showFeedback(fpEl, '✗', '#DC3232');
  }}
  scheduleNextPrimary(performance.now());
  updateStats();
}}

function handleSecondary(key) {{
  if (done || !secondaryActive || secondaryResponded) return;
  secondaryResponded = true;
  const correct = (key === 'd' && currentShape === 'circle') ||
                  (key === 'k' && currentShape === 'square');
  if (correct) {{
    sCorrect++;
    showFeedback(fsEl, '✓', '#00C88C');
  }} else {{
    sIncorrect++;
    showFeedback(fsEl, '✗', '#DC3232');
  }}
  secondaryActive       = false;
  sStimEl.style.display = 'none';
  nextSecondaryTime     = performance.now() + SHP_MIN + Math.random() * (SHP_MAX - SHP_MIN);
  updateStats();
}}

function finishTest() {{
  done = true;
  pStimEl.style.display = 'none';
  sStimEl.style.display = 'none';

  const pTotal = pCorrect + pIncorrect + pMiss;
  const sTotal = sCorrect + sIncorrect + sMiss;

  const summary = {{
    primary_accuracy:   pTotal ? +(pCorrect / pTotal).toFixed(3) : 0,
    secondary_accuracy: sTotal ? +(sCorrect / sTotal).toFixed(3) : 0,
    primary_correct:    pCorrect,
    primary_miss:       pMiss,
    secondary_correct:  sCorrect,
    secondary_miss:     sMiss,
  }};

  const payload = JSON.stringify({{ summary }});
  document.getElementById('result').value = payload;
  window.parent.postMessage({{ type: 'dual_done', payload }}, '*');
  window.parent.localStorage.setItem('dual_result', payload);
  doneMsg.style.display = 'block';
}}

// Klavye
document.addEventListener('keydown', e => {{
  if (e.code === 'Space') {{ e.preventDefault(); handlePrimary(); }}
  if (e.key === 'd' || e.key === 'D') handleSecondary('d');
  if (e.key === 'k' || e.key === 'K') handleSecondary('k');
}});

scheduleNextPrimary(performance.now());
requestAnimationFrame(tick);
</script>
</body>
</html>
"""
