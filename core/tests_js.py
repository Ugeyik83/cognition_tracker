# core/tests_js.py
"""Üç testin istemci taraflı (iframe) JS bileşenleri.

Tasarım ilkeleri:
- Tüm zamanlama performance.now() ile (~0.1 ms çözünürlük) — Date.now() değil.
- JS yalnızca HAM deneme verisi üretir; metrikler Python'da (core/scoring.py).
- Sonuç + run_id + cihaz meta-verisi localStorage'a yazılır (core/bridge.py okur).
- Pratik bloklarında geri bildirim VAR, ana bloklarda YOK (öğrenme yanlılığını önler).
- Brace çakışmasını önlemek için string.Template ($VAR) kullanılır.
"""

from string import Template

from core.config import DUAL, GONOGO, PVT

# Ortak JS: cihaz ölçümü (ekran yenileme hızı tahmini) + sonuç yazma
_COMMON = """
function ctMeasureDevice(cb) {
    let frames = 0; const t0 = performance.now();
    function loop(t) {
        frames++;
        if (t - t0 < 500) requestAnimationFrame(loop);
        else cb({
            refresh_hz: Math.round(frames / ((t - t0) / 1000)),
            dpr: window.devicePixelRatio || 1,
            ua: navigator.userAgent
        });
    }
    requestAnimationFrame(loop);
}
function ctFinish(storageKey, payload, device) {
    payload.run_id = "$RUN_ID";
    payload.device = device;
    localStorage.setItem(storageKey, JSON.stringify(payload));
}
"""

_SHELL = """
<div style="font-family:'Segoe UI',sans-serif;max-width:640px;margin:0 auto;color:#F0F4FF">
  <div style="background:#10182B;border:1px solid #1E2A45;border-radius:16px;padding:24px;text-align:center">
    <div id="phase" style="font-size:12px;letter-spacing:1px;color:#8B95B0;margin-bottom:10px">$PHASE_LABEL</div>
    $BODY
    <div id="msg" style="margin-top:14px;font-size:14px;color:#F5A623;min-height:20px">$INIT_MSG</div>
    <div id="prog" style="margin-top:6px;font-size:12px;color:#8B95B0"></div>
  </div>
  <button id="startBtn" style="display:block;width:100%;margin-top:16px;background:#3D8BFF;color:#fff;
    border:none;padding:13px;font-size:17px;font-weight:600;border-radius:12px;cursor:pointer">
    Pratiğe Başla
  </button>
</div>
"""


def _shell(phase_label: str, body: str, init_msg: str) -> str:
    return Template(_SHELL).substitute(PHASE_LABEL=phase_label, BODY=body, INIT_MSG=init_msg)


# ════════════════════════ PVT ════════════════════════════════════
def pvt_html(run_id: str, storage_key: str) -> str:
    body = """
    <div id="stim" style="height:200px;border-radius:14px;background:#1A2235;display:flex;
         align-items:center;justify-content:center;font-size:30px;font-weight:700;user-select:none;cursor:pointer">
        Bekleyin…
    </div>
    """
    js = Template(_COMMON + """
const CFG = { dur:$DUR, isiMin:$ISI_MIN, isiMax:$ISI_MAX, fsMs:$FS_MS, practice:$PRACTICE };
const KEY = "$KEY";
let device=null; ctMeasureDevice(d=>device=d);

const stim=document.getElementById('stim'), msg=document.getElementById('msg'),
      prog=document.getElementById('prog'), btn=document.getElementById('startBtn'),
      phase=document.getElementById('phase');

let mode=null;            // 'practice' | 'main'
let trials=[];            // ana blok ham verisi
let pCount=0, t0=null, waiting=false, isiTimer=null, blockEnd=0, clockTimer=null;

function isi(){ return Math.random()*(CFG.isiMax-CFG.isiMin)+CFG.isiMin; }

function arm(){                                   // ISI başlat
    waiting=true; t0=null;
    stim.style.background="#1A2235"; stim.textContent="Bekleyin…";
    isiTimer=setTimeout(()=>{
        if(mode==null) return;
        waiting=false; t0=performance.now();      // uyaran başlangıcı (yüksek çözünürlük)
        stim.style.background="#E5484D"; stim.textContent="TIKLA!";
    }, isi());
}

function record(rt, fs){
    if(mode==='main') trials.push({rt:rt, false_start:fs});
    else pCount++;
}

stim.addEventListener('pointerdown', ()=>{
    if(mode==null) return;
    if(waiting){                                   // uyaran öncesi tıklama = erken basma
        clearTimeout(isiTimer); record(null,true);
        msg.textContent="Erken basma! Uyaranı bekleyin."; flash("#7A2E33");
        next(); return;
    }
    if(t0==null) return;
    const rt=performance.now()-t0; t0=null;
    if(rt<CFG.fsMs){ record(null,true); msg.textContent="Erken basma ("+Math.round(rt)+" ms)"; }
    else { record(Math.round(rt),false); msg.textContent=Math.round(rt)+" ms"; }  // standart PVT: RT geri bildirimi gösterilir
    flash("#1F6E4A"); next();
});

function flash(c){ stim.style.background=c; }
function next(){
    setTimeout(()=>{
        if(mode==null) return;
        if(mode==='practice' && pCount>=CFG.practice){ startMain(); return; }
        arm();
    }, 600);
}

function startMain(){
    mode='main'; trials=[]; phase.textContent="ANA BLOK · 3 DAKİKA";
    msg.textContent="Ana blok başladı. Kırmızıyı görünce hemen tıklayın.";
    blockEnd=performance.now()+CFG.dur;
    clockTimer=setInterval(()=>{
        const left=Math.max(0,Math.ceil((blockEnd-performance.now())/1000));
        prog.textContent="Kalan: "+left+" sn · Deneme: "+trials.length;
        if(left<=0) endTest();
    },250);
    arm();
}

function endTest(){
    clearInterval(clockTimer); clearTimeout(isiTimer); mode=null;
    stim.style.background="#1A2235"; stim.textContent="Tamamlandı";
    msg.textContent="Sonuçlar kaydediliyor…"; prog.textContent="";
    ctFinish(KEY,{test:"pvt",trials:trials},device);
}

btn.onclick=()=>{
    btn.style.display='none'; mode='practice'; pCount=0;
    phase.textContent="PRATİK · "+CFG.practice+" DENEME";
    msg.textContent="Pratik: kırmızıyı görünce kutuya tıklayın."; arm();
};
""").substitute(
        RUN_ID=run_id, KEY=storage_key, DUR=PVT["duration_ms"],
        ISI_MIN=PVT["isi_min_ms"], ISI_MAX=PVT["isi_max_ms"],
        FS_MS=PVT["false_start_ms"], PRACTICE=PVT["practice_trials"],
    )
    return _shell("PVT — PSİKOMOTOR VİJİLANS", body,
                  "Kutu kırmızıya dönünce olabildiğince hızlı tıklayın. Erken tıklamayın.") \
        + "<script>" + js + "</script>"


# ════════════════════════ GO / NO-GO ═════════════════════════════
def gonogo_html(run_id: str, storage_key: str) -> str:
    body = """
    <div id="stim" style="width:180px;height:180px;margin:0 auto;border-radius:14px;background:#1A2235;
         display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:700;user-select:none">
        +
    </div>
    <div style="margin-top:12px;font-size:13px;color:#8B95B0">
        YEŞİL → <kbd>SPACE</kbd> &nbsp;·&nbsp; KIRMIZI → basma
    </div>
    """
    n_go = round(GONOGO["n_trials"] * GONOGO["go_ratio"])
    js = Template(_COMMON + """
const CFG={ nGo:$N_GO, nNoGo:$N_NOGO, stim:$STIM, win:$WIN, itiMin:$ITI_MIN, itiMax:$ITI_MAX, practice:$PRACTICE };
const KEY="$KEY";
let device=null; ctMeasureDevice(d=>device=d);

const stim=document.getElementById('stim'), msg=document.getElementById('msg'),
      prog=document.getElementById('prog'), btn=document.getElementById('startBtn'),
      phase=document.getElementById('phase');

let mode=null, seq=[], idx=0, trials=[], cur=null, t0=null, responded=false, winTimer=null;

function buildSeq(nGo,nNoGo){                      // sabit sayı + Fisher–Yates karıştırma
    const a=Array(nGo).fill(true).concat(Array(nNoGo).fill(false));
    for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; }
    return a;
}

function showFix(){ stim.style.background="#1A2235"; stim.textContent="+"; }

function trial(){
    if(idx>=seq.length){ endBlock(); return; }
    cur=seq[idx]; responded=false;
    // ITI jitter — "hazır olun" ipucu bilinçli olarak YOK (prepotent yanıt korunur)
    const iti=Math.random()*(CFG.itiMax-CFG.itiMin)+CFG.itiMin;
    setTimeout(()=>{
        if(mode==null) return;
        stim.style.background=cur?"#2EBD6B":"#E5484D";
        stim.textContent=cur?"BAS":"DUR";
        t0=performance.now();
        setTimeout(showFix, CFG.stim);             // uyaran 500 ms sonra kaybolur
        winTimer=setTimeout(()=>finishTrial(null), CFG.win);  // pencere 1000 ms
    }, iti);
}

function finishTrial(rt){
    clearTimeout(winTimer);
    if(mode==='main') trials.push({is_go:cur, responded:responded, rt:rt});
    if(mode==='practice'){                          // geri bildirim YALNIZ pratikte
        const ok=(cur&&responded)||(!cur&&!responded);
        msg.textContent=ok?"✓ Doğru":"✗ Hatalı";
    }
    idx++;
    prog.textContent="Deneme: "+idx+" / "+seq.length;
    showFix(); trial();
}

window.addEventListener('keydown',e=>{
    if(mode==null||e.code!=="Space") return;
    e.preventDefault();
    if(t0==null||responded) return;
    const rt=performance.now()-t0;
    if(rt>CFG.win) return;
    responded=true;
    finishTrial(Math.round(rt));
});

function startMain(){
    mode='main'; seq=buildSeq(CFG.nGo,CFG.nNoGo); idx=0; trials=[];
    phase.textContent="ANA BLOK · "+seq.length+" DENEME";
    msg.textContent="Ana blok: geri bildirim verilmez."; trial();
}
function endBlock(){
    if(mode==='practice'){ startMain(); return; }
    mode=null; stim.textContent="Bitti"; msg.textContent="Sonuçlar kaydediliyor…";
    ctFinish(KEY,{test:"gonogo",trials:trials},device);
}
btn.onclick=()=>{
    btn.style.display='none'; mode='practice';
    seq=buildSeq(Math.round(CFG.practice*0.75), CFG.practice-Math.round(CFG.practice*0.75));
    idx=0; phase.textContent="PRATİK · "+seq.length+" DENEME";
    msg.textContent="Pratik başladı."; trial();
};
""").substitute(
        RUN_ID=run_id, KEY=storage_key,
        N_GO=n_go, N_NOGO=GONOGO["n_trials"] - n_go,
        STIM=GONOGO["stim_ms"], WIN=GONOGO["resp_window_ms"],
        ITI_MIN=GONOGO["iti_min_ms"], ITI_MAX=GONOGO["iti_max_ms"],
        PRACTICE=GONOGO["practice_trials"],
    )
    return _shell("GO/NO-GO — İNHİBİSYON KONTROLÜ", body,
                  "Yeşilde SPACE'e basın, kırmızıda basmayın. Yanıt penceresi 1 sn.") \
        + "<script>" + js + "</script>"


# ════════════════════════ DUAL TASK ══════════════════════════════
def dual_html(run_id: str, storage_key: str) -> str:
    body = """
    <div style="display:flex;gap:16px;justify-content:center">
      <div style="flex:1;background:#0A0F1E;border-radius:14px;padding:16px">
        <div style="font-size:11px;color:#8B95B0;margin-bottom:8px">RENK · turuncu → <kbd>SPACE</kbd></div>
        <div id="colorBox" style="width:110px;height:110px;margin:0 auto;border-radius:55px;background:#555"></div>
      </div>
      <div style="flex:1;background:#0A0F1E;border-radius:14px;padding:16px">
        <div style="font-size:11px;color:#8B95B0;margin-bottom:8px">ŞEKİL · ● → <kbd>D</kbd> · ■ → <kbd>K</kbd></div>
        <div id="shapeBox" style="width:110px;height:110px;margin:0 auto;border-radius:14px;background:#1A2235;
             display:flex;align-items:center;justify-content:center;font-size:56px;color:#FFD966">·</div>
      </div>
    </div>
    """
    js = Template(_COMMON + """
const CFG={ base:$BASE, dual:$DUAL_MS, cInt:$C_INT, target:$TARGET,
            sMin:$S_MIN, sMax:$S_MAX, sVis:$S_VIS, sWin:$S_WIN, prac:$PRAC };
const KEY="$KEY";
let device=null; ctMeasureDevice(d=>device=d);

const cBox=document.getElementById('colorBox'), sBox=document.getElementById('shapeBox'),
      msg=document.getElementById('msg'), prog=document.getElementById('prog'),
      btn=document.getElementById('startBtn'), phase=document.getElementById('phase');

let mode=null;             // 'practice'|'baseline'|'dual'
let baselineColor=[], dualColor=[], dualShape=[];
let curColor=null, colorTimer=null;                // {is_target,t0,responded,rt}
let curShape=null, shapeTimer=null, shapeHide=null; // {shape,t0,answered}
let blockEnd=0, clock=null;

function colorTick(){
    if(curColor && mode!=='practice'){              // önceki uyaranı kapat (yanıtsız → CR/miss)
        push(curColor);
    }
    const isT=Math.random()<CFG.target;
    cBox.style.background = isT ? "#FF8C42" : (Math.random()<0.5?"#3D8BFF":"#A855F7");
    curColor={is_target:isT, t0:performance.now(), responded:false, rt:null};
}
function push(c){
    const rec={is_target:c.is_target, responded:c.responded, rt:c.rt};
    if(mode==='baseline') baselineColor.push(rec);
    else if(mode==='dual') dualColor.push(rec);
}
function scheduleShape(){
    if(mode!=='dual'&&mode!=='practice') return;
    const d=Math.random()*(CFG.sMax-CFG.sMin)+CFG.sMin;
    shapeTimer=setTimeout(()=>{
        if(mode!=='dual'&&mode!=='practice') return;
        const circ=Math.random()<0.5;
        curShape={shape:circ?'circle':'square', t0:performance.now(), answered:false};
        sBox.textContent=circ?'●':'■';
        shapeHide=setTimeout(()=>{ sBox.textContent='·'; },CFG.sVis);
        setTimeout(()=>{                            // pencere kapandı, yanıtsız → miss
            if(curShape && !curShape.answered){
                if(mode==='dual') dualShape.push({shape:curShape.shape,key:null,correct:false,rt:null});
                curShape=null;
            }
            scheduleShape();
        },CFG.sWin);
    },d);
}

window.addEventListener('keydown',e=>{
    if(mode==null) return;
    if(e.code==="Space"){
        e.preventDefault();
        if(curColor && !curColor.responded){
            curColor.responded=true;
            curColor.rt=Math.round(performance.now()-curColor.t0);
            if(mode==='practice') msg.textContent=curColor.is_target?"✓ Renk doğru":"✗ Turuncu değildi";
        }
    }
    if(e.key==='d'||e.key==='D'||e.key==='k'||e.key==='K'){
        if(curShape && !curShape.answered){
            curShape.answered=true;
            const k=e.key.toLowerCase();
            const ok=(k==='d'&&curShape.shape==='circle')||(k==='k'&&curShape.shape==='square');
            const rec={shape:curShape.shape,key:k,correct:ok,
                       rt:Math.round(performance.now()-curShape.t0)};
            if(mode==='dual') dualShape.push(rec);
            if(mode==='practice') msg.textContent=ok?"✓ Şekil doğru":"✗ Yanlış tuş";
            curShape=null;
        }
    }
});

function startBlock(m,durMs,label,withShapes){
    mode=m; phase.textContent=label;
    curColor=null; curShape=null; sBox.textContent='·';
    clearInterval(colorTimer); clearTimeout(shapeTimer); clearTimeout(shapeHide);
    colorTimer=setInterval(colorTick,CFG.cInt); colorTick();
    if(withShapes) scheduleShape();
    blockEnd=performance.now()+durMs;
    clearInterval(clock);
    clock=setInterval(()=>{
        const left=Math.max(0,Math.ceil((blockEnd-performance.now())/1000));
        prog.textContent="Kalan: "+left+" sn";
        if(left<=0) nextBlock();
    },250);
}
function nextBlock(){
    clearInterval(clock); clearInterval(colorTimer);
    clearTimeout(shapeTimer); clearTimeout(shapeHide);
    if(curColor && mode!=='practice') push(curColor);
    if(mode==='practice'){
        msg.textContent="Baseline: YALNIZ renk görevi (30 sn). Karşılaştırma için gerekli.";
        startBlock('baseline',CFG.base,'BASELINE · TEK GÖREV',false);
    } else if(mode==='baseline'){
        msg.textContent="Çift görev başladı: iki kutuyu da izleyin (90 sn).";
        startBlock('dual',CFG.dual,'ÇİFT GÖREV · 90 SN',true);
    } else {
        mode=null; cBox.style.background='#555'; sBox.textContent='·';
        msg.textContent="Sonuçlar kaydediliyor…"; prog.textContent="";
        ctFinish(KEY,{test:"dual",baseline_color:baselineColor,
                      dual_color:dualColor,dual_shape:dualShape},device);
    }
}
btn.onclick=()=>{
    btn.style.display='none';
    msg.textContent="Pratik: turuncu→SPACE, ●→D, ■→K (geri bildirimli).";
    startBlock('practice',CFG.prac,'PRATİK · 15 SN',true);
};
""").substitute(
        RUN_ID=run_id, KEY=storage_key,
        BASE=DUAL["baseline_ms"], DUAL_MS=DUAL["dual_ms"],
        C_INT=DUAL["color_interval_ms"], TARGET=DUAL["target_ratio"],
        S_MIN=DUAL["shape_min_ms"], S_MAX=DUAL["shape_max_ms"],
        S_VIS=DUAL["shape_visible_ms"], S_WIN=DUAL["shape_window_ms"],
        PRAC=DUAL["practice_ms"],
    )
    return _shell("DUAL TASK — BÖLÜNMÜŞ DİKKAT", body,
                  "Önce pratik, sonra 30 sn tek görev (baseline), sonra 90 sn çift görev.") \
        + "<script>" + js + "</script>"
