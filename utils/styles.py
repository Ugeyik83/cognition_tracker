"""
utils/styles.py
Tüm sayfalarda kullanılan ortak CSS ve HTML bileşenleri.
"""

# Renk sistemi — hardcode hex (CSS variable yok, Streamlit iframe uyumlu)
COLORS = {
    "bg":       "#0A0F1E",
    "bg2":      "#111827",
    "bg3":      "#1A2235",
    "border":   "rgba(255,255,255,0.08)",
    "border2":  "rgba(255,255,255,0.14)",
    "blue":     "#3D8BFF",
    "blue_dim": "rgba(61,139,255,0.1)",
    "green":    "#00E5A0",
    "green_dim":"rgba(0,229,160,0.1)",
    "amber":    "#F5A623",
    "amber_dim":"rgba(245,166,35,0.1)",
    "red":      "#FF4D6A",
    "red_dim":  "rgba(255,77,106,0.1)",
    "text":     "#F0F4FF",
    "text2":    "#8B95B0",
    "text3":    "#4A526A",
}

BASE_CSS = """
<style>
/* Streamlit chrome gizle */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
div[data-testid="stToolbar"] { display: none !important; }

/* Genel */
body, .stApp {
    background: #0A0F1E !important;
    color: #F0F4FF !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Streamlit input override */
input[type="text"], .stTextInput input {
    background: #1A2235 !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-radius: 10px !important;
    color: #F0F4FF !important;
    padding: 10px 14px !important;
}
.stButton > button {
    background: #3D8BFF !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
}
.stButton > button:hover { background: #5A9FFF !important; }
</style>
"""

def page_header(title: str, subtitle: str = "") -> str:
    """Sayfa üst bar HTML"""
    return f"""
    <div style="
        background:#111827;
        border-bottom:1px solid rgba(255,255,255,0.08);
        padding:14px 24px;
        display:flex;
        align-items:center;
        gap:12px;
        margin-bottom:0;
    ">
        <div style="
            width:32px;height:32px;border-radius:8px;
            background:#3D8BFF;
            display:flex;align-items:center;justify-content:center;
        ">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                 stroke="white" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
        </div>
        <div>
            <div style="font-size:15px;font-weight:600;color:#F0F4FF;line-height:1.2">{title}</div>
            {f'<div style="font-size:11px;color:#8B95B0">{subtitle}</div>' if subtitle else ''}
        </div>
    </div>
    """

def progress_sidebar(steps: list, current: int) -> str:
    """
    Sol kenar adım göstergesi.
    steps: [{"name": "PVT", "dur": "3 dk"}, ...]
    current: aktif adım indeksi (0-based), -1 = tamamlandı
    """
    items_html = ""
    for i, step in enumerate(steps):
        if i < current:
            dot_style = "background:rgba(0,229,160,0.1);border:1.5px solid #00E5A0;color:#00E5A0"
            dot_content = "✓"
            name_color = "#8B95B0"
            bg = ""
        elif i == current:
            dot_style = "background:rgba(61,139,255,0.15);border:1.5px solid #3D8BFF;color:#3D8BFF"
            dot_content = str(i + 1)
            name_color = "#3D8BFF"
            bg = "background:rgba(61,139,255,0.1);"
        else:
            dot_style = "border:1.5px solid rgba(255,255,255,0.14);color:#4A526A"
            dot_content = str(i + 1)
            name_color = "#4A526A"
            bg = ""

        items_html += f"""
        <div style="display:flex;align-items:center;gap:10px;
                    padding:8px;border-radius:8px;{bg}">
            <div style="width:22px;height:22px;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;
                        font-size:11px;font-weight:600;flex-shrink:0;{dot_style}">
                {dot_content}
            </div>
            <div>
                <div style="font-size:13px;font-weight:500;color:{name_color}">
                    {step['name']}
                </div>
                <div style="font-size:11px;color:#4A526A">{step['dur']}</div>
            </div>
        </div>
        """

    pct = int((current / len(steps)) * 100)

    return f"""
    <div style="
        width:200px;min-height:100%;
        background:#111827;
        border-right:1px solid rgba(255,255,255,0.08);
        padding:20px;
        display:flex;flex-direction:column;gap:10px;
        position:fixed;top:0;left:0;bottom:0;
        z-index:10;
    ">
        <div style="font-size:10px;font-weight:600;letter-spacing:0.8px;
                    color:#4A526A;text-transform:uppercase;margin-bottom:4px">
            Test Adımları
        </div>
        {items_html}
        <div style="margin-top:auto">
            <div style="display:flex;justify-content:space-between;
                        font-size:11px;color:#8B95B0;margin-bottom:6px">
                <span>İlerleme</span><span>{current}/{len(steps)}</span>
            </div>
            <div style="height:4px;background:#1A2235;border-radius:2px">
                <div style="height:4px;background:#3D8BFF;border-radius:2px;
                            width:{pct}%"></div>
            </div>
        </div>
    </div>
    <div style="margin-left:200px;">
    """

def metric_card(label: str, value: str, color: str = "#F0F4FF") -> str:
    return f"""
    <div style="
        flex:1;background:#1A2235;
        border:1px solid rgba(255,255,255,0.08);
        border-radius:10px;padding:12px;
    ">
        <div style="font-size:10px;color:#8B95B0;font-weight:500;margin-bottom:4px">
            {label}
        </div>
        <div style="font-size:22px;font-weight:700;color:{color};
                    font-variant-numeric:tabular-nums;letter-spacing:-0.5px">
            {value}
        </div>
    </div>
    """

def verdict_badge(verdict: str) -> str:
    cfg = {
        "UYGUN":        ("rgba(0,229,160,0.1)",  "#00E5A0"),
        "KOŞULLU":      ("rgba(245,166,35,0.1)",  "#F5A623"),
        "UYGUN DEĞİL":  ("rgba(255,77,106,0.1)",  "#FF4D6A"),
    }
    bg, color = cfg.get(verdict, ("rgba(255,255,255,0.1)", "#8B95B0"))
    return f"""<span style="font-size:11px;font-weight:600;padding:3px 9px;
                border-radius:20px;background:{bg};color:{color}">
                {verdict}</span>"""
