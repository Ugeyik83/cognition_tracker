"""
utils/nav.py
Tüm sayfalarda kullanılan ortak sidebar navigasyonu.
"""
import streamlit as st


def render_nav(active: str = "home"):
    """
    Sidebar navigasyon.
    active: "home" | "pvt" | "gonogo" | "dual" | "dashboard"
    """
    pvt_done  = st.session_state.get("pvt_result")    is not None
    gng_done  = st.session_state.get("gonogo_result") is not None
    dual_done = st.session_state.get("dual_result")   is not None
    cid       = st.session_state.get("candidate_id", "")

    with st.sidebar:
        st.markdown(f"""
        <div style="padding:8px 0 16px">
            <div style="font-size:15px;font-weight:700;color:#F0F4FF">CognitionTracker</div>
            <div style="font-size:11px;color:#8B95B0;margin-top:2px">Forklift Bilişsel Tarama</div>
        </div>
        """, unsafe_allow_html=True)

        if cid:
            st.markdown(f"""
            <div style="background:#1A2235;border:1px solid rgba(61,139,255,0.2);
                        border-radius:8px;padding:10px 12px;margin-bottom:12px">
                <div style="font-size:10px;color:#8B95B0;margin-bottom:2px">AKTİF ADAY</div>
                <div style="font-size:14px;font-weight:700;color:#3D8BFF">{cid}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("**Testler**")

        def nav_item(label, check, page_key):
            icon = "✅" if check else ("▶" if page_key == active else "○")
            color = "#00E5A0" if check else ("#3D8BFF" if page_key == active else "#8B95B0")
            st.markdown(
                f'<div style="font-size:13px;color:{color};padding:4px 0">'
                f'{icon} {label}</div>',
                unsafe_allow_html=True,
            )

        nav_item("1 · PVT",       pvt_done,  "pvt")
        nav_item("2 · Go/No-Go",  gng_done,  "gonogo")
        nav_item("3 · Dual Task", dual_done, "dual")

        st.divider()
        st.markdown("**Sonuçlar**")
        nav_item("Dashboard", False, "dashboard")

        # İlerleme
        completed = sum([pvt_done, gng_done, dual_done])
        st.markdown(f"""
        <div style="margin-top:16px">
            <div style="display:flex;justify-content:space-between;
                        font-size:11px;color:#8B95B0;margin-bottom:6px">
                <span>İlerleme</span><span>{completed}/3</span>
            </div>
            <div style="height:4px;background:#1A2235;border-radius:2px">
                <div style="height:4px;background:#3D8BFF;border-radius:2px;
                            width:{int(completed/3*100)}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
