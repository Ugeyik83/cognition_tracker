"""
pages/4_dashboard.py — Dashboard, yeni tasarım.
"""

import pandas as pd
import streamlit as st
from utils.styles import BASE_CSS, page_header, verdict_badge
from utils.nav import render_nav
from utils.data_logger import load_all, export_csv

st.set_page_config(page_title="Dashboard | CognitionTracker", layout="wide",
                   initial_sidebar_state="expanded")
st.html(BASE_CSS)
render_nav("dashboard")
st.html(page_header("Operatör Dashboard", "Tüm test sonuçları"))

rows = load_all()

if not rows:
    st.html("""
    <div style="padding:60px;text-align:center;color:#4A526A">
        <div style="font-size:40px;margin-bottom:12px">📭</div>
        <div style="font-size:16px">Henüz kayıtlı sonuç yok.</div>
        <div style="font-size:13px;margin-top:6px">
            Testleri tamamladıktan sonra buraya yansır.
        </div>
    </div>
    """)
    st.stop()

df = pd.DataFrame(rows)
numeric_cols = ["pvt_mean_rt","pvt_lapses","pvt_false_starts",
                "gng_hit_rate","gng_false_alarm_rate","gng_dprime",
                "dual_primary_acc","dual_secondary_acc"]
for c in numeric_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

total  = len(df)
uygun  = int((df.get("verdict","") == "UYGUN").sum())     if "verdict" in df.columns else 0
kosul  = int((df.get("verdict","") == "KOŞULLU").sum())   if "verdict" in df.columns else 0
fail   = int((df.get("verdict","") == "UYGUN DEĞİL").sum()) if "verdict" in df.columns else 0

# ── Özet kartlar ─────────────────────────────────────────────
st.html(f"""
<div style="padding:20px;background:#0A0F1E">
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px">

    <div style="background:rgba(61,139,255,0.08);border:1px solid rgba(61,139,255,0.25);
                border-radius:12px;padding:14px">
        <div style="font-size:10px;font-weight:500;color:#8B95B0;margin-bottom:6px">TOPLAM ADAY</div>
        <div style="font-size:26px;font-weight:700;color:#3D8BFF;letter-spacing:-1px">{total}</div>
        <div style="font-size:11px;color:#8B95B0;margin-top:3px">Kayıtlı sonuç</div>
    </div>

    <div style="background:#111827;border:1px solid rgba(255,255,255,0.08);
                border-radius:12px;padding:14px">
        <div style="font-size:10px;font-weight:500;color:#8B95B0;margin-bottom:6px">UYGUN</div>
        <div style="font-size:26px;font-weight:700;color:#00E5A0;letter-spacing:-1px">{uygun}</div>
        <div style="font-size:11px;color:#8B95B0;margin-top:3px">
            {f'%{int(uygun/total*100)}' if total else '—'} geçme oranı
        </div>
    </div>

    <div style="background:#111827;border:1px solid rgba(255,255,255,0.08);
                border-radius:12px;padding:14px">
        <div style="font-size:10px;font-weight:500;color:#8B95B0;margin-bottom:6px">KOŞULLU</div>
        <div style="font-size:26px;font-weight:700;color:#F5A623;letter-spacing:-1px">{kosul}</div>
        <div style="font-size:11px;color:#8B95B0;margin-top:3px">Takip gerekli</div>
    </div>

    <div style="background:#111827;border:1px solid rgba(255,255,255,0.08);
                border-radius:12px;padding:14px">
        <div style="font-size:10px;font-weight:500;color:#8B95B0;margin-bottom:6px">UYGUN DEĞİL</div>
        <div style="font-size:26px;font-weight:700;color:#FF4D6A;letter-spacing:-1px">{fail}</div>
        <div style="font-size:11px;color:#8B95B0;margin-top:3px">30 gün sonra tekrar</div>
    </div>
</div>
""")

# ── Tablo ─────────────────────────────────────────────────────
disp_cols = {
    "candidate_id": "ADAY ID",
    "timestamp":    "TARİH",
    "pvt_mean_rt":  "PVT RT",
    "gng_dprime":   "d-prime",
    "dual_primary_acc": "DUAL",
}
avail = {k: v for k, v in disp_cols.items() if k in df.columns}

st.html("""
<div style="background:#111827;border:1px solid rgba(255,255,255,0.08);
            border-radius:12px;overflow:hidden;margin-bottom:20px">
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:13px 16px;border-bottom:1px solid rgba(255,255,255,0.08)">
        <div style="font-size:13px;font-weight:600;color:#F0F4FF">Son Adaylar</div>
    </div>
""")

# Tablo başlığı
header_cols = list(avail.values()) + ["KARAR"]
header_html = "".join(
    f'<th style="font-size:10px;font-weight:500;color:#4A526A;padding:8px 14px;'
    f'text-align:left;border-bottom:1px solid rgba(255,255,255,0.06)">{h}</th>'
    for h in header_cols
)
rows_html = ""
for _, row in df.tail(20).iloc[::-1].iterrows():
    cells = ""
    for col in avail.keys():
        val = row.get(col, "—")
        if col == "pvt_mean_rt" and val:
            try:
                v = float(val)
                color = "#00E5A0" if v < 300 else ("#F5A623" if v < 400 else "#FF4D6A")
                val = f'<span style="color:{color}">{v:.0f} ms</span>'
            except: pass
        elif col == "gng_dprime" and val:
            try:
                v = float(val)
                color = "#00E5A0" if v > 2.5 else ("#F5A623" if v > 1.5 else "#FF4D6A")
                val = f'<span style="color:{color}">{v:.2f}</span>'
            except: pass
        elif col == "dual_primary_acc" and val:
            try:
                v = float(val)
                val = f"{v:.0%}"
            except: pass
        first = col == list(avail.keys())[0]
        style = "font-weight:500;color:#F0F4FF" if first else "color:#8B95B0"
        cells += f'<td style="font-size:13px;padding:10px 14px;{style};border-bottom:1px solid rgba(255,255,255,0.04)">{val}</td>'

    verdict = row.get("verdict", "")
    badge_cfg = {
        "UYGUN":       ("rgba(0,229,160,0.1)",  "#00E5A0"),
        "KOŞULLU":     ("rgba(245,166,35,0.1)",  "#F5A623"),
        "UYGUN DEĞİL": ("rgba(255,77,106,0.1)",  "#FF4D6A"),
    }
    bg, color = badge_cfg.get(verdict, ("rgba(255,255,255,0.06)", "#8B95B0"))
    verdict_cell = (f'<td style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.04)">'
                    f'<span style="font-size:11px;font-weight:600;padding:3px 9px;'
                    f'border-radius:20px;background:{bg};color:{color}">{verdict or "—"}</span></td>')

    rows_html += f"<tr>{cells}{verdict_cell}</tr>"

st.html(f"""
<table style="width:100%;border-collapse:collapse">
    <thead><tr>{header_html}</tr></thead>
    <tbody>{rows_html}</tbody>
</table>
</div>
</div>
""")

# ── CSV indir ─────────────────────────────────────────────────
st.download_button(
    "⬇ CSV İndir",
    data=export_csv(df),
    file_name="cognition_tracker_sonuclari.csv",
    mime="text/csv",
)