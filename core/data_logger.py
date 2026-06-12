# core/data_logger.py
"""CSV tabanlı kalıcı kayıt. Aday+zaman damgalı dosya → eşzamanlılık çakışması yok."""

import csv
import io
from datetime import datetime
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path("results")

NUMERIC_COLS = [
    "pvt_mean_rt", "pvt_median_rt", "pvt_reciprocal_rt", "pvt_lapses",
    "pvt_false_starts", "pvt_slowest10", "gng_hit_rate", "gng_far",
    "gng_dprime", "gng_mean_rt_go", "dual_baseline_acc", "dual_primary_acc",
    "dual_task_cost", "dual_secondary_acc", "dual_secondary_rt",
]


def save_session(candidate_id: str, pvt: dict, gng: dict, dual: dict, device: dict) -> Path:
    """Oturum sonunda OTOMATİK çağrılır (app.py → dual tamamlanınca)."""
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now()
    path = RESULTS_DIR / f"{candidate_id}_{ts:%Y%m%d_%H%M%S}.csv"

    row = {
        "candidate_id": candidate_id,
        "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
        # PVT
        "pvt_mean_rt": pvt.get("mean_rt"),
        "pvt_median_rt": pvt.get("median_rt"),
        "pvt_reciprocal_rt": pvt.get("reciprocal_rt"),
        "pvt_lapses": pvt.get("lapses"),
        "pvt_false_starts": pvt.get("false_starts"),
        "pvt_slowest10": pvt.get("slowest10_mean"),
        "pvt_n_trials": pvt.get("n_trials"),
        # Go/No-Go
        "gng_hit_rate": gng.get("hit_rate"),
        "gng_far": gng.get("false_alarm_rate"),
        "gng_dprime": gng.get("dprime"),
        "gng_mean_rt_go": gng.get("mean_rt_go"),
        # Dual Task
        "dual_baseline_acc": dual.get("baseline_primary_acc"),
        "dual_primary_acc": dual.get("primary_acc"),
        "dual_task_cost": dual.get("dual_task_cost"),
        "dual_secondary_acc": dual.get("secondary_acc"),
        "dual_secondary_rt": dual.get("secondary_mean_rt"),
        # Cihaz meta-verisi — RT karşılaştırılabilirliği için zorunlu
        "device_refresh_hz": device.get("refresh_hz"),
        "device_pixel_ratio": device.get("dpr"),
        "device_ua": device.get("ua", "")[:120],
    }

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        w.writeheader()
        w.writerow(row)
    return path


def load_all() -> pd.DataFrame:
    """Tüm kayıtlar — sayısal kolonlar coerce edilir (eski string-kolon hatasının düzeltmesi)."""
    RESULTS_DIR.mkdir(exist_ok=True)
    frames = [pd.read_csv(p, encoding="utf-8-sig") for p in sorted(RESULTS_DIR.glob("*.csv"))]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for c in NUMERIC_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def candidate_history(df: pd.DataFrame, candidate_id: str) -> pd.DataFrame:
    if df.empty:
        return df
    return df[df["candidate_id"] == candidate_id].sort_values("timestamp")


def export_csv(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8-sig")
