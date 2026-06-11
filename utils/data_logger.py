"""
utils/data_logger.py

CSV tabanlı sonuç kaydı.
Her aday için benzersiz dosya → race condition yok.
"""

import csv
import os
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path("results")


def _ensure_dir():
    RESULTS_DIR.mkdir(exist_ok=True)


def save_session(candidate_id: str, pvt: dict, gonogo: dict, dual: dict) -> Path:
    """
    Tek adayın tüm test sonuçlarını bir satır olarak yazar.
    Döndürür: yazılan dosya yolu
    """
    _ensure_dir()
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{candidate_id}_{ts}.csv"

    row = {
        "candidate_id":   candidate_id,
        "timestamp":      datetime.now().strftime("%Y-%m-%d %H:%M"),
        # PVT
        "pvt_mean_rt":    pvt.get("mean_rt"),
        "pvt_median_rt":  pvt.get("median_rt"),
        "pvt_lapses":     pvt.get("lapses"),
        "pvt_false_starts": pvt.get("false_starts"),
        "pvt_n_trials":   pvt.get("n_trials"),
        # Go/No-Go
        "gng_hit_rate":        gonogo.get("hit_rate"),
        "gng_false_alarm_rate": gonogo.get("false_alarm_rate"),
        "gng_omission_rate":   gonogo.get("omission_rate"),
        "gng_dprime":          gonogo.get("dprime"),
        "gng_mean_rt_go":      gonogo.get("mean_rt_go"),
        # Dual Task
        "dual_primary_acc":   dual.get("primary_accuracy"),
        "dual_secondary_acc": dual.get("secondary_accuracy"),
        "dual_primary_correct": dual.get("primary_correct"),
        "dual_secondary_correct": dual.get("secondary_correct"),
    }

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writeheader()
        writer.writerow(row)

    return path


def load_all() -> list[dict]:
    """results/ altındaki tüm CSV'leri okur, liste döndürür."""
    _ensure_dir()
    rows = []
    for p in sorted(RESULTS_DIR.glob("*.csv")):
        try:
            with open(p, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
        except Exception:
            continue
    return rows
