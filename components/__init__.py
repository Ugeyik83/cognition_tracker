# components/__init__.py
"""
Her test için Streamlit custom component tanımlaması.
declare_component(path=...) → statik HTML dosyasını servis eder,
iki yönlü iletişimi WebSocket üzerinden yönetir.
st.components.v1.html() (deprecated 1.58) kullanılmaz.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as stc

from core.config import DUAL, GONOGO, PVT

_DIR = Path(__file__).parent


@st.cache_resource
def _declare():
    return {
        "pvt":    stc.declare_component("ct_pvt",    path=str(_DIR / "pvt")),
        "gonogo": stc.declare_component("ct_gonogo",  path=str(_DIR / "gonogo")),
        "dual":   stc.declare_component("ct_dual",    path=str(_DIR / "dual")),
    }


def pvt_component(run_id: str):
    c = _declare()["pvt"]
    return c(
        run_id=run_id,
        duration_ms=PVT["duration_ms"],
        isi_min=PVT["isi_min_ms"],
        isi_max=PVT["isi_max_ms"],
        false_start_ms=PVT["false_start_ms"],
        practice=PVT["practice_trials"],
        key=f"pvt_{run_id}",
        default=None,
        height=460,
    )


def gonogo_component(run_id: str):
    c = _declare()["gonogo"]
    n_go   = round(GONOGO["n_trials"] * GONOGO["go_ratio"])
    n_nogo = GONOGO["n_trials"] - n_go
    return c(
        run_id=run_id,
        n_go=n_go,
        n_nogo=n_nogo,
        stim=GONOGO["stim_ms"],
        win=GONOGO["resp_window_ms"],
        iti_min=GONOGO["iti_min_ms"],
        iti_max=GONOGO["iti_max_ms"],
        practice=GONOGO["practice_trials"],
        key=f"gonogo_{run_id}",
        default=None,
        height=480,
    )


def dual_component(run_id: str):
    c = _declare()["dual"]
    return c(
        run_id=run_id,
        baseline_ms=DUAL["baseline_ms"],
        dual_ms=DUAL["dual_ms"],
        color_interval=DUAL["color_interval_ms"],
        target_ratio=DUAL["target_ratio"],
        shape_min=DUAL["shape_min_ms"],
        shape_max=DUAL["shape_max_ms"],
        shape_vis=DUAL["shape_visible_ms"],
        shape_win=DUAL["shape_window_ms"],
        practice_ms=DUAL["practice_ms"],
        key=f"dual_{run_id}",
        default=None,
        height=540,
    )
