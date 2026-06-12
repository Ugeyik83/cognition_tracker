# app.py  — CognitionTracker Demo (Streamlit Cloud uyumlu)
"""
Akış: welcome (ID + KVKK) → pvt → gonogo → dual → results → [admin]
- declare_component(path) kullanır; st.components.v1.html() yok
- streamlit_autorefresh / streamlit_javascript bağımlılığı yok
- CSV kaydı: results/ dizinine (Streamlit Cloud'da ephemeral — demo için yeterli)
"""

import uuid

import streamlit as st

from components import dual_component, gonogo_component, pvt_component
from core.config import ADMIN_PIN_DEFAULT
from core.data_logger import candidate_history, export_csv, load_all, save_session
from core.scoring import (evaluate_session, intra_individual_z, score_dual,
                          score_gonogo, score_pvt)
from core.ui import FLAG_BADGE, header, inject_css, stepper
from core.data_logger import RESULTS_DIR

st.set_page_config(
    page_title="CognitionTracker",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)
inject_css()


# ── Session state başlatma ────────────────────────────────────────
DEFAULTS = {
    "stage": "welcome",
    "candidate_id": "",
    "consent_given": False,
    "pvt_result": None,
    "gonogo_result": None,
    "dual_result": None,
    "device": {},
    "run_ids": {},
    "session_saved": False,
    "saved_path": "",
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

SS = st.session_state

TESTS = {
    #  stage     başlık                       component_fn      scorer        result_key       sonraki
    "pvt":    ("Modül 1 / 3 — PVT  (~3 dk)",         pvt_component,    score_pvt,    "pvt_result",    "gonogo"),
    "gonogo": ("Modül 2 / 3 — Go/No-Go (~2,5 dk)",   gonogo_component, score_gonogo, "gonogo_result", "dual"),
    "dual":   ("Modül 3 / 3 — Dual Task (~2,5 dk)",  dual_component,   score_dual,   "dual_result",   "results"),
}

METRIC_LABELS = {
    "pvt_mean_rt":        "PVT Ortalama RT (ms)",
    "pvt_lapses":         "PVT Lapse (RT ≥ 500 ms)",
    "pvt_false_starts":   "PVT Erken Basma",
    "gng_hit_rate":       "Go/No-Go İsabet Oranı",
    "gng_far":            "Go/No-Go Yanlış Alarm",
    "gng_dprime":         "Go/No-Go d′",
    "dual_primary_acc":   "Dual — Birincil Doğruluk",
    "dual_secondary_acc": "Dual — İkincil Doğruluk",
}


def reset_session():
    for k, v in DEFAULTS.items():
        SS[k] = v


# ══ WELCOME ══════════════════════════════════════════════════════
def view_welcome():
    header()
    st.markdown("### Yıllık Bilişsel Taramaya Hoş Geldiniz")
    st.caption("3 modül · pratik bloklar dahil ≈ 9 dakika · sabit sıra: PVT → Go/No-Go → Dual Task")

    with st.expander("📄 KVKK Aydınlatma Metni", expanded=False):
        st.markdown("""
- Bu test bilişsel performans verisi üretir; kimliğinizle eşleştirildiğinde
  **KVKK Md. 6 / GDPR Md. 9** kapsamında özel nitelikli kişisel veri sayılabilir.
- Veriler yalnızca bu sunucuda yerel `results/` dizininde saklanır; üçüncü taraflarla paylaşılmaz.
- Amaç: yıllık operatör yeterlilik taraması ve kişisel baseline takibi.
- Verilerinize erişim, silme ve düzeltme taleplerinizi İSG birimine iletebilirsiniz.
        """)

    with st.form("welcome_form"):
        cid     = st.text_input("Operatör ID", placeholder="örn. OP-1042")
        consent = st.checkbox(
            "Aydınlatma metnini okudum; verilerimin işlenmesine **açık rıza** veriyorum."
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            pvt_btn  = st.form_submit_button("▶ PVT",        use_container_width=True)
        with col2:
            gng_btn  = st.form_submit_button("▶ Go/No-Go",   use_container_width=True)
        with col3:
            dual_btn = st.form_submit_button("▶ Dual Task",  use_container_width=True)

        full_btn = st.form_submit_button("Baştan Başla →", use_container_width=True, type="primary")

        def validate():
            if not cid.strip():
                st.error("Operatör ID zorunludur.")
                return False
            if not consent:
                st.error("Açık rıza olmadan teste başlanamaz (KVKK Md. 6).")
                return False
            return True

        if pvt_btn and validate():
            SS.candidate_id = cid.strip(); SS.consent_given = True
            SS.stage = "pvt"; st.rerun()
        if gng_btn and validate():
            SS.candidate_id = cid.strip(); SS.consent_given = True
            SS.stage = "gonogo"; st.rerun()
        if dual_btn and validate():
            SS.candidate_id = cid.strip(); SS.consent_given = True
            SS.stage = "dual"; st.rerun()
        if full_btn and validate():
            SS.candidate_id = cid.strip(); SS.consent_given = True
            SS.stage = "pvt"; st.rerun()

    st.divider()
    with st.expander("🔐 Yönetici Paneli"):
        pin = st.text_input("PIN", type="password", key="admin_pin_in")
        if st.button("Panele Gir"):
            try:
                expected = st.secrets.get("ADMIN_PIN", ADMIN_PIN_DEFAULT)
            except Exception:
                expected = ADMIN_PIN_DEFAULT
            if pin == expected:
                SS.stage = "admin"
                st.rerun()
            else:
                st.error("Hatalı PIN.")


# ══ TEST AŞAMALARI ════════════════════════════════════════════════
def view_test(stage: str):
    title, comp_fn, scorer, result_key, next_stage = TESTS[stage]
    header(SS.candidate_id)
    if st.button("← Ana Sayfa", key=f"home_{SS.stage}"):
        reset_session()
        st.rerun()
    stepper(stage)
    st.markdown(f"#### {title}")

    if SS[result_key] is None:
        # Her aşama için benzersiz run_id — Streamlit rerun'da eski sonuç reddedilir
        if stage not in SS.run_ids:
            SS.run_ids[stage] = uuid.uuid4().hex[:12]
        run_id = SS.run_ids[stage]

        raw = comp_fn(run_id)   # declare_component tamamlanınca dict, öncesinde None döner

        if raw is not None:
            scored = scorer(raw)
            if scored.get("valid"):
                SS[result_key] = scored
                if raw.get("device") and not SS.device:
                    SS.device = raw["device"]
                st.rerun()
            else:
                st.error("Geçerli deneme verisi alınamadı. Lütfen testi yeniden başlatın.")
        return

    # Tamamlandı → özet + devam butonu
    res = SS[result_key]
    st.success("✅ Modül tamamlandı.")
    c1, c2, c3 = st.columns(3)
    if stage == "pvt":
        c1.metric("Ort. RT",   f"{res['mean_rt']} ms")
        c2.metric("Lapse",     res["lapses"])
        c3.metric("Erken Basma", res["false_starts"])
    elif stage == "gonogo":
        c1.metric("İsabet",    f"{res['hit_rate']:.0%}")
        c2.metric("Yanlış Alarm", f"{res['false_alarm_rate']:.0%}")
        c3.metric("d′",        res["dprime"])
    else:
        c1.metric("Birincil",  f"{res['primary_acc']:.0%}")
        c2.metric("İkincil",   f"{res['secondary_acc']:.0%}")
        cost = res.get("dual_task_cost")
        c3.metric("Dual-Task Cost", f"{cost:+.0%}" if cost is not None else "—")

    label = "Sonuç Ekranına Geç →" if next_stage == "results" else "Hazır Olduğunuzda Devam →"
    if st.button(label, use_container_width=True, type="primary"):
        SS.stage = next_stage
        st.rerun()


# ══ SONUÇ EKRANI ══════════════════════════════════════════════════
def view_results():
    header(SS.candidate_id)
    if st.button("← Ana Sayfa", key=f"home_{SS.stage}"):
        reset_session()
        st.rerun()
    pvt, gng, dual = SS.pvt_result, SS.gonogo_result, SS.dual_result

    # Otomatik kayıt (try/except: Streamlit Cloud ephemeral FS'de sessizce devam eder)
    if not SS.session_saved:
        try:
            path = save_session(SS.candidate_id, pvt, gng, dual, SS.device)
            SS.saved_path = str(path)
        except Exception:
            SS.saved_path = "(kayıt yapılamadı)"
        SS.session_saved = True

    st.markdown("### 📋 Tarama Sonucu")
    st.caption(f"Kayıt: `{SS.saved_path}` · Cihaz: {SS.device.get('refresh_hz','?')} Hz")

    evals = evaluate_session(pvt, gng, dual)
    any_flag = any(s == "flag" for _, s in evals.values())

    if any_flag:
        st.error("⚠️ En az bir metrikte **Dikkat Bayrağı** tespit edildi. İSG birimi değerlendirmesi önerilir.")
    else:
        st.success("Tüm metrikler normal eşik aralıklarında.")

    rows = "".join(
        f"<tr><td style='padding:6px 12px'>{METRIC_LABELS[k]}</td>"
        f"<td style='padding:6px 12px;font-weight:600'>{v if v is not None else '—'}</td>"
        f"<td style='padding:6px 12px'>{FLAG_BADGE[s]}</td></tr>"
        for k, (v, s) in evals.items()
    )
    st.markdown(
        "<table style='width:100%;background:#10182B;border-radius:12px'>"
        "<tr style='color:#8B95B0;font-size:12px'>"
        "<th style='text-align:left;padding:8px 12px'>Metrik</th>"
        "<th style='text-align:left;padding:8px 12px'>Değer</th>"
        "<th style='text-align:left;padding:8px 12px'>Durum</th></tr>"
        + rows + "</table>",
        unsafe_allow_html=True,
    )

    # Birey-içi z-skoru (yıllık takip)
    try:
        df = load_all()
        hist = candidate_history(df, SS.candidate_id)
        prior_rts = hist["pvt_mean_rt"].dropna().tolist()
        if len(prior_rts) >= 3:   # bu oturum dahil; ≥3 = en az 2 önceki
            z = intra_individual_z(prior_rts[:-1], pvt.get("mean_rt"))
            if z is not None:
                flag = "🔴 anlamlı bozulma" if abs(z) >= 1.5 else "🟢 stabil"
                st.markdown(f"**Birey-içi değişim (PVT ort. RT):** z = {z}  {flag}")
    except Exception:
        pass

    st.divider()
    # Tamamlanmayan testler varsa uyarı + butonlar
    missing = [s for s in ["pvt", "gonogo", "dual"] if SS.get(f"{s}_result") is None]
    if missing:
        st.warning("⚠️ Tüm modüller tamamlanmadı. Eksik testleri yaparak tam rapor oluşturabilirsiniz.")
        cols = st.columns(len(missing))
        labels = {"pvt": "▶ PVT", "gonogo": "▶ Go/No-Go", "dual": "▶ Dual Task"}
        for i, s in enumerate(missing):
            with cols[i]:
                if st.button(labels[s], use_container_width=True):
                    SS.session_saved = False  # raporu sıfırla, yeni kayıt yapılacak
                    SS.stage = s
                    st.rerun()

    if st.button("🔄 Yeni Aday", use_container_width=True):
        reset_session()
        st.rerun()


# ══ YÖNETİCİ PANELİ ═══════════════════════════════════════════════
def view_admin():
    header()
    st.markdown("### 🔐 Yönetici Paneli")
    try:
        df = load_all()
    except Exception:
        df = None

    if df is None or df.empty:
        st.info("Henüz kayıt yok (veya Streamlit Cloud ephemeral FS sıfırlandı).")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Oturum",    len(df))
        c2.metric("Benzersiz Operatör", df["candidate_id"].nunique())
        flagged = int((df["pvt_lapses"] > 10).sum()) if "pvt_lapses" in df.columns else 0
        c3.metric("Lapse Bayraklı",   flagged)

        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 CSV İndir", export_csv(df), "cognition_results.csv", "text/csv"
        )

        st.markdown("#### 📈 Operatör Trend")
        kandidatlar = sorted(df["candidate_id"].dropna().astype(str).unique().tolist())
        if not kandidatlar:
            st.info("Henüz operatör kaydı yok.")
        else:
            cand = st.selectbox("Operatör", kandidatlar)

        metric = st.selectbox("Metrik", [
            "pvt_mean_rt", "pvt_lapses", "gng_dprime",
            "dual_primary_acc", "dual_task_cost",
        ])
        import plotly.express as px
        h = candidate_history(df, cand).dropna(subset=[metric])
        if len(h) >= 2:
            fig = px.line(h, x="timestamp", y=metric, markers=True,
                          template="plotly_dark", title=f"{cand} — {metric}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Trend için en az 2 kayıt gerekir.")

    st.divider()
    st.markdown("#### 🗑️ Kayıt Sil")
    col_a, col_b = st.columns(2)
    with col_a:
        sil_aday = st.selectbox("Silinecek operatör", ["— seçin —"] + kandidatlar, key="sil_sec")
        if st.button("Bu adayı sil", type="secondary"):
            if sil_aday != "— seçin —":
                for p in sorted(RESULTS_DIR.glob(f"{sil_aday}_*.csv")):
                    p.unlink()
                st.success(f"{sil_aday} silindi.")
                st.rerun()
    with col_b:
        st.write("")
        st.write("")
        if st.button("⚠️ Tüm kayıtları sil", type="secondary"):
            for p in RESULTS_DIR.glob("*.csv"):
                p.unlink()
            st.success("Tüm kayıtlar silindi.")
            st.rerun()

    if st.button("← Çıkış"):
        SS.stage = "welcome"
        st.rerun()


# ══ ROUTER ════════════════════════════════════════════════════════
if SS.stage == "welcome":
    view_welcome()
elif SS.stage in TESTS:
    view_test(SS.stage)
elif SS.stage == "results":
    view_results()
elif SS.stage == "admin":
    view_admin()
