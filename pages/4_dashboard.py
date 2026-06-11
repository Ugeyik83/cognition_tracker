"""
pages/4_dashboard.py — Sonuç Görselleştirme

Mevcut adayın sonuçları + tüm geçmiş adaylarla karşılaştırma.
Plotly grafikleri, CSV indir.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from utils.data_logger import load_all

st.set_page_config(page_title="Dashboard | Dikkat Testi", layout="wide")
st.title("📊 Sonuç Dashboard")

# ── Mevcut aday özeti ─────────────────────────────────────────
pvt    = st.session_state.get("pvt_result")
gonogo = st.session_state.get("gonogo_result")
dual   = st.session_state.get("dual_result")
cid    = st.session_state.get("candidate_id", "—")

if pvt or gonogo or dual:
    st.subheader(f"Aday: {cid}")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**Modül 1 — PVT**")
        if pvt:
            mean_rt = pvt.get("mean_rt") or 0
            lapses  = pvt.get("lapses") or 0
            st.metric("Ort. RT",    f"{mean_rt} ms",
                      delta="Normal" if mean_rt < 300 else "Yüksek",
                      delta_color="normal" if mean_rt < 300 else "inverse")
            st.metric("Lapse (>500ms)", lapses,
                      delta="OK" if lapses < 5 else "⚠",
                      delta_color="normal" if lapses < 5 else "inverse")
            st.metric("Erken Basma", pvt.get("false_starts") or 0)
        else:
            st.info("Henüz tamamlanmadı")

    with c2:
        st.markdown("**Modül 2 — Go/No-Go**")
        if gonogo:
            hr  = float(gonogo.get("hit_rate") or 0)
            fa  = float(gonogo.get("false_alarm_rate") or 0)
            dp  = float(gonogo.get("dprime") or 0)
            st.metric("Hit Rate",    f"{hr:.0%}")
            st.metric("False Alarm", f"{fa:.0%}",
                      delta="OK" if fa < 0.10 else "⚠",
                      delta_color="normal" if fa < 0.10 else "inverse")
            st.metric("d-prime",     f"{dp:.2f}",
                      delta="İyi" if dp > 2.5 else "Düşük",
                      delta_color="normal" if dp > 2.5 else "inverse")
        else:
            st.info("Henüz tamamlanmadı")

    with c3:
        st.markdown("**Modül 3 — Dual Task**")
        if dual:
            pa = float(dual.get("primary_accuracy") or 0)
            sa = float(dual.get("secondary_accuracy") or 0)
            st.metric("Birincil Görev", f"{pa:.0%}")
            st.metric("İkincil Görev",  f"{sa:.0%}")
            st.metric("Ortalama",       f"{(pa+sa)/2:.0%}")
        else:
            st.info("Henüz tamamlanmadı")

    st.divider()

# ── Geçmiş veriler ────────────────────────────────────────────
all_rows = load_all()

if not all_rows:
    st.info("Henüz kayıtlı sonuç yok.")
    st.stop()

df = pd.DataFrame(all_rows)

# Sayısal dönüşüm
numeric_cols = [
    "pvt_mean_rt", "pvt_lapses", "pvt_false_starts",
    "gng_hit_rate", "gng_false_alarm_rate", "gng_dprime",
    "dual_primary_acc", "dual_secondary_acc",
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

st.subheader(f"Tüm Adaylar — {len(df)} kayıt")

# Filtre
col_f1, col_f2 = st.columns(2)
with col_f1:
    if "pvt_mean_rt" in df.columns:
        max_rt = int(df["pvt_mean_rt"].dropna().max() or 1000)
        rt_filter = st.slider("Max PVT Ort. RT (ms)", 0, max_rt, max_rt)
        df = df[df["pvt_mean_rt"] <= rt_filter]

# Tablo
st.dataframe(df, use_container_width=True, height=300)

# ── Grafikler ─────────────────────────────────────────────────
st.divider()
g1, g2 = st.columns(2)

with g1:
    if "pvt_mean_rt" in df.columns:
        st.markdown("#### PVT — RT Dağılımı")
        fig = px.histogram(
            df, x="pvt_mean_rt", nbins=15,
            color_discrete_sequence=["#00C88C"],
            labels={"pvt_mean_rt": "Ortalama RT (ms)"},
        )
        fig.add_vline(x=300, line_dash="dash", line_color="#FF8C00",
                      annotation_text="300ms eşiği")
        fig.update_layout(
            paper_bgcolor="#0F1419", plot_bgcolor="#161E26",
            font_color="#D2DCE1", margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

with g2:
    if "gng_dprime" in df.columns:
        st.markdown("#### Go/No-Go — d-prime Dağılımı")
        fig2 = px.histogram(
            df, x="gng_dprime", nbins=15,
            color_discrete_sequence=["#3B82F6"],
            labels={"gng_dprime": "d-prime"},
        )
        fig2.add_vline(x=2.5, line_dash="dash", line_color="#00C88C",
                       annotation_text="İyi performans")
        fig2.update_layout(
            paper_bgcolor="#0F1419", plot_bgcolor="#161E26",
            font_color="#D2DCE1", margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)

# Dual Task scatter
if "dual_primary_acc" in df.columns and "dual_secondary_acc" in df.columns:
    st.markdown("#### Dual Task — Birincil vs İkincil Görev Doğruluğu")
    fig3 = px.scatter(
        df, x="dual_primary_acc", y="dual_secondary_acc",
        hover_data=["candidate_id"] if "candidate_id" in df.columns else None,
        color_discrete_sequence=["#A855F7"],
        labels={
            "dual_primary_acc":   "Birincil Görev Doğruluğu",
            "dual_secondary_acc": "İkincil Görev Doğruluğu",
        },
    )
    fig3.update_layout(
        paper_bgcolor="#0F1419", plot_bgcolor="#161E26",
        font_color="#D2DCE1", margin=dict(t=20, b=20),
        xaxis=dict(tickformat=".0%", range=[0, 1.05]),
        yaxis=dict(tickformat=".0%", range=[0, 1.05]),
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── CSV İndir ─────────────────────────────────────────────────
st.divider()
st.download_button(
    "⬇ Tüm Sonuçları CSV İndir",
    data=df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
    file_name="dikkat_testi_sonuclari.csv",
    mime="text/csv",
)
