# app.py
"""CognitionTracker — tek sayfalı sihirbaz (wizard) mimarisi.

Akış (sabit sıra — tarama bataryalarında standardizasyon gereği):
    welcome (ID + KVKK rızası) → pvt → gonogo → dual → results
Dashboard, operatör akışından ayrılmış yönetici görünümüdür (PIN korumalı).

pages/ klasörü bilinçli olarak yoktur: Streamlit'in otomatik sol menüsü
(serbest gezinme) hem UX hem metodoloji açısından kaldırılmıştır.
"""



import streamlit as st
import streamlit.components.v1 as components

from core import bridge, tests_js
from core.config import ADMIN_PIN_DEFAULT
from core.data_logger import candidate_history, export_csv, load_all, save_session
from core.scoring import (evaluate_session, intra_individual_z, score_dual,
                          score_gonogo, score_pvt)
from core.ui import FLAG_BADGE, header, inject_css, stepper

st.set_page_config(page_title="CognitionTracker", page_icon="🧠",
                   layout="centered", initial_sidebar_state="collapsed")
inject_css()

# ── Session state ─────────────────────────────────────────────────
DEFAULTS = {
    "stage": "welcome",
    "candidate_id": "",
    "consent_given": False,
    "pvt_result": None, "gonogo_result": None, "dual_result": None,
    "device": {},
    "session_saved": False,
    "saved_path": "",
    "run_ids": {},
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

SS = st.session_state

TESTS = {
    # stage: (başlık, html_builder, scorer, result_key, sonraki stage)
    "pvt":    ("Modül 1 / 3 — PVT (3 dk)",          tests_js.pvt_html,    score_pvt,    "pvt_result",    "gonogo"),
    "gonogo": ("Modül 2 / 3 — Go/No-Go (~2,5 dk)",  tests_js.gonogo_html, score_gonogo, "gonogo_result", "dual"),
    "dual":   ("Modül 3 / 3 — Dual Task (~2,5 dk)", tests_js.dual_html,   score_dual,   "dual_result",   "results"),
}

METRIC_LABELS = {
    "pvt_mean_rt": "PVT Ortalama RT (ms)", "pvt_lapses": "PVT Lapse (RT ≥ 500 ms)",
    "pvt_false_starts": "PVT Erken Basma", "gng_hit_rate": "Go/No-Go İsabet Oranı",
    "gng_far": "Go/No-Go Yanlış Alarm", "gng_dprime": "Go/No-Go d′",
    "dual_primary_acc": "Dual — Birincil Doğruluk", "dual_secondary_acc": "Dual — İkincil Doğruluk",
}


def reset_session():
    for k, v in DEFAULTS.items():
        SS[k] = v


# ══════════════════ WELCOME (ID + KVKK rızası) ════════════════════
def view_welcome():
    header()
    st.markdown("### Yıllık bilişsel taramaya hoş geldiniz")
    st.caption("3 modül · pratik bloklar dahil ≈ 9 dakika · sabit sıra: PVT → Go/No-Go → Dual Task")

    with st.expander("📄 KVKK Aydınlatma Metni (özet)", expanded=False):
        st.markdown("""
- Bu test, **bilişsel performans verisi** üretir; kimliğinizle eşleştirildiğinde
  **KVKK Md. 6 / GDPR Md. 9** kapsamında özel nitelikli kişisel veri sayılabilir.
- Veriler **yalnızca bu cihazda, yerel `results/` dizininde** saklanır; ağa gönderilmez.
- Amaç: yıllık operatör yeterlilik taraması ve kişisel baseline takibi.
- Verilerinize erişim, silme ve düzeltme taleplerinizi İSG birimine iletebilirsiniz.
        """)

    with st.form("welcome_form"):
        cid = st.text_input("Operatör ID", placeholder="örn. OP-1042")
        consent = st.checkbox("Aydınlatma metnini okudum; verilerimin işlenmesine **açık rıza** veriyorum.")
        if st.form_submit_button("Taramaya Başla →", use_container_width=True):
            if not cid.strip():
                st.error("Operatör ID zorunludur.")
            elif not consent:
                st.error("Açık rıza olmadan teste başlanamaz (KVKK Md. 6).")
            else:
                SS.candidate_id = cid.strip()
                SS.consent_given = True
                SS.stage = "pvt"
                st.rerun()

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


# ══════════════════ TEST AŞAMALARI ════════════════════════════════
def view_test(stage: str):
    title, builder, scorer, result_key, next_stage = TESTS[stage]
    header(SS.candidate_id)
    stepper(stage)
    st.markdown(f"#### {title}")

    if SS[result_key] is None:
        # run_id bu aşamaya ilk girişte üretilir; eski localStorage verisi reddedilir
        if stage not in SS.run_ids:
            SS.run_ids[stage] = bridge.new_run_id()
        run_id = SS.run_ids[stage]
        storage_key = f"ct_result_{stage}"

        components.html(builder(run_id, storage_key), height=560, scrolling=False)

        raw = bridge.poll_result(storage_key, run_id, widget_key=stage)
        if raw:
            scored = scorer(raw)
            if scored.get("valid"):
                SS[result_key] = scored
                if raw.get("device") and not SS.device:
                    SS.device = raw["device"]  # cihaz meta-verisi (refresh Hz, DPR, UA)
                bridge.clear_key(storage_key, widget_key=stage)
                st.rerun()
            else:
                st.error("Geçerli deneme verisi alınamadı. Testi yeniden başlatın.")
        return

    # Test tamamlandı → kısa özet + otomatik ilerleme onayı
    res = SS[result_key]
    st.success("✅ Modül tamamlandı ve kaydedildi.")
    cols = st.columns(3)
    if stage == "pvt":
        cols[0].metric("Ortalama RT", f"{res['mean_rt']} ms")
        cols[1].metric("Lapse (≥500 ms)", res["lapses"])
        cols[2].metric("Erken Basma", res["false_starts"])
    elif stage == "gonogo":
        cols[0].metric("İsabet Oranı", f"{res['hit_rate']:.0%}")
        cols[1].metric("Yanlış Alarm", f"{res['false_alarm_rate']:.0%}")
        cols[2].metric("d′", res["dprime"])
    else:
        cols[0].metric("Birincil Doğruluk", f"{res['primary_acc']:.0%}")
        cols[1].metric("İkincil Doğruluk", f"{res['secondary_acc']:.0%}")
        cost = res.get("dual_task_cost")
        cols[2].metric("Dual-Task Cost", f"{cost:+.0%}" if cost is not None else "—")

    label = "Sonuç Ekranına Geç →" if next_stage == "results" else "Hazır Olduğunuzda Devam →"
    if st.button(label, use_container_width=True, type="primary"):
        SS.stage = next_stage
        st.rerun()


# ══════════════════ SONUÇ EKRANI ══════════════════════════════════
def view_results():
    header(SS.candidate_id)
    pvt, gng, dual = SS.pvt_result, SS.gonogo_result, SS.dual_result

    # Otomatik CSV kaydı — eski kodun çağrılmayan save_session() hatasının düzeltmesi
    if not SS.session_saved:
        path = save_session(SS.candidate_id, pvt, gng, dual, SS.device)
        SS.session_saved, SS.saved_path = True, str(path)

    st.markdown("### 📋 Tarama Sonucu")
    st.caption(f"Kayıt: `{SS.saved_path}` · Cihaz: {SS.device.get('refresh_hz', '?')} Hz")

    evals = evaluate_session(pvt, gng, dual)
    any_flag = any(s == "flag" for _, s in evals.values())
    if any_flag:
        st.error("⚠️ En az bir metrikte **Dikkat Bayrağı**. İSG birimi değerlendirmesi önerilir.")
    else:
        st.success("Tüm metrikler eşik aralıklarında.")

    rows = "".join(
        f"<tr><td style='padding:6px 12px'>{METRIC_LABELS[k]}</td>"
        f"<td style='padding:6px 12px;font-weight:600'>{v if v is not None else '—'}</td>"
        f"<td style='padding:6px 12px'>{FLAG_BADGE[s]}</td></tr>"
        for k, (v, s) in evals.items()
    )
    st.markdown(
        f"<table style='width:100%;background:#10182B;border-radius:12px'>"
        f"<tr style='color:#8B95B0;font-size:12px'><th style='text-align:left;padding:8px 12px'>Metrik</th>"
        f"<th style='text-align:left;padding:8px 12px'>Değer</th>"
        f"<th style='text-align:left;padding:8px 12px'>Durum</th></tr>{rows}</table>",
        unsafe_allow_html=True,
    )

    # Birey-içi değişim (yıllık takibin asıl değeri)
    hist = candidate_history(load_all(), SS.candidate_id)
    prior = hist[hist["timestamp"].dt.strftime("%Y%m%d_%H%M%S").apply(
        lambda s: s not in SS.saved_path)]  # bu oturum hariç
    if len(prior) >= 2:
        z = intra_individual_z(prior["pvt_mean_rt"].dropna().tolist(), pvt.get("mean_rt"))
        if z is not None:
            st.markdown(f"**Birey-içi değişim (PVT ortalama RT):** z = {z} "
                        + ("🔴 anlamlı bozulma" if z >= 1.5 else "🟢 stabil"))

    st.divider()
    if st.button("🔄 Yeni Aday", use_container_width=True):
        reset_session()
        st.rerun()


# ══════════════════ YÖNETİCİ PANELİ ═══════════════════════════════
def view_admin():
    header()
    st.markdown("### 🔐 Yönetici Paneli — Tüm Kayıtlar")
    df = load_all()
    if df.empty:
        st.info("Henüz kayıt yok.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Oturum", len(df))
        c2.metric("Benzersiz Operatör", df["candidate_id"].nunique())
        flagged = int((df["pvt_lapses"] > 10).sum()) if "pvt_lapses" in df else 0
        c3.metric("Lapse Bayraklı Oturum", flagged)

        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("📥 Tüm verileri CSV indir", export_csv(df),
                           "cognition_results.csv", "text/csv")

        st.markdown("#### 📈 Operatör Trend Analizi")
        cand = st.selectbox("Operatör", sorted(df["candidate_id"].unique()))
        metric = st.selectbox("Metrik", ["pvt_mean_rt", "pvt_lapses", "gng_dprime",
                                         "dual_primary_acc", "dual_task_cost"])
        h = candidate_history(df, cand).dropna(subset=[metric])
        if len(h) >= 2:
            import plotly.express as px
            fig = px.line(h, x="timestamp", y=metric, markers=True,
                          template="plotly_dark", title=f"{cand} — {metric}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Trend için en az 2 kayıt gerekir.")

    if st.button("← Çıkış"):
        SS.stage = "welcome"
        st.rerun()


# ══════════════════ ROUTER ════════════════════════════════════════
if SS.stage == "welcome":
    view_welcome()
elif SS.stage in TESTS:
    view_test(SS.stage)
elif SS.stage == "results":
    view_results()
elif SS.stage == "admin":
    view_admin()
