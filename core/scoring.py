# core/scoring.py
"""Ham deneme verisinden metrik hesaplama.

Tasarım kararı: JS yalnızca HAM olay verisi gönderir (deneme listeleri);
tüm metrikler Python'da hesaplanır. Böylece skorlama denetlenebilir,
test edilebilir ve istemci tarafında manipüle edilemez.

d' için scipy gerekmez: statistics.NormalDist().inv_cdf (stdlib probit).
"""

from statistics import NormalDist, mean, median, stdev

from core.config import FLAGS, GONOGO, PVT, INTRA_INDIVIDUAL_Z

_Z = NormalDist().inv_cdf  # probit (ters standart normal CDF)


# ── PVT ──────────────────────────────────────────────────────────
def score_pvt(raw: dict) -> dict:
    """raw["trials"]: [{rt: ms|null, false_start: bool}, ...] — ana blok."""
    trials = raw.get("trials", [])
    rts = [t["rt"] for t in trials if t.get("rt") is not None and not t.get("false_start")]
    false_starts = sum(1 for t in trials if t.get("false_start"))
    lapses = sum(1 for rt in rts if rt >= PVT["lapse_ms"])

    if not rts:
        return {"valid": False}

    rts_sorted = sorted(rts)
    k = max(1, len(rts) // 10)  # en yavaş/hızlı %10 dilimi
    return {
        "valid": True,
        "n_trials": len(trials),
        "mean_rt": round(mean(rts), 1),
        "median_rt": round(median(rts), 1),
        "reciprocal_rt": round(mean(1000.0 / rt for rt in rts), 3),  # 1/RT (sn^-1) — uyku yoksunluğuna en duyarlı metrik
        "lapses": lapses,
        "false_starts": false_starts,
        "slowest10_mean": round(mean(rts_sorted[-k:]), 1),
        "fastest10_mean": round(mean(rts_sorted[:k]), 1),
        "rts": rts,
    }


# ── Go/No-Go ─────────────────────────────────────────────────────
def score_gonogo(raw: dict) -> dict:
    """raw["trials"]: [{is_go: bool, responded: bool, rt: ms|null}, ...]"""
    trials = raw.get("trials", [])
    go = [t for t in trials if t.get("is_go")]
    nogo = [t for t in trials if not t.get("is_go")]
    if not go or not nogo:
        return {"valid": False}

    hits = sum(1 for t in go if t.get("responded"))
    fas = sum(1 for t in nogo if t.get("responded"))
    hr, far = hits / len(go), fas / len(nogo)

    lo, hi = GONOGO["rate_clamp"]
    hr_c = min(max(hr, lo), hi)   # sonsuz z değerlerine karşı kırpma
    far_c = min(max(far, lo), hi)
    go_rts = [t["rt"] for t in go if t.get("responded") and t.get("rt") is not None]

    return {
        "valid": True,
        "n_trials": len(trials),
        "hit_rate": round(hr, 3),
        "false_alarm_rate": round(far, 3),
        "omission_rate": round(1 - hr, 3),
        "correct_rejections": len(nogo) - fas,
        "dprime": round(_Z(hr_c) - _Z(far_c), 2),
        "mean_rt_go": round(mean(go_rts), 1) if go_rts else None,
        "go_rts": go_rts,
    }


# ── Dual Task ────────────────────────────────────────────────────
def _primary_acc(color_trials: list) -> float | None:
    """4 hücreli puanlama: hit + correct rejection / toplam uyaran.

    Eski kodun hatası: yalnız hit sayılıyor, hedef-dışına basmama (CR)
    puanlanmıyordu → teorik tavan ~%33 idi. Doğrusu sinyal algılama çerçevesi.
    """
    if not color_trials:
        return None
    correct = sum(
        1 for t in color_trials
        if (t.get("is_target") and t.get("responded"))        # hit
        or (not t.get("is_target") and not t.get("responded"))  # correct rejection
    )
    return correct / len(color_trials)


def score_dual(raw: dict) -> dict:
    """raw: {baseline_color: [...], dual_color: [...], dual_shape: [...]}"""
    base_acc = _primary_acc(raw.get("baseline_color", []))
    dual_acc = _primary_acc(raw.get("dual_color", []))
    shapes = raw.get("dual_shape", [])
    if dual_acc is None or not shapes:
        return {"valid": False}

    shape_correct = sum(1 for s in shapes if s.get("correct"))
    shape_rts = [s["rt"] for s in shapes if s.get("correct") and s.get("rt") is not None]

    return {
        "valid": True,
        "baseline_primary_acc": round(base_acc, 3) if base_acc is not None else None,
        "primary_acc": round(dual_acc, 3),
        # Dual-task cost: literatürdeki asıl metrik — baseline'a göre düşüş
        "dual_task_cost": round(base_acc - dual_acc, 3) if base_acc is not None else None,
        "secondary_acc": round(shape_correct / len(shapes), 3),
        "secondary_mean_rt": round(mean(shape_rts), 1) if shape_rts else None,
        "n_color": len(raw.get("dual_color", [])),
        "n_shape": len(shapes),
    }


# ── Bayraklama ───────────────────────────────────────────────────
def flag_status(metric_key: str, value) -> str:
    """'normal' | 'borderline' | 'flag' — README eşik tablolarına göre."""
    if value is None:
        return "n/a"
    cfg = FLAGS[metric_key]
    if cfg["higher_is_worse"]:
        if value > cfg["flag"]:
            return "flag"
        return "normal" if value <= cfg["normal"] else "borderline"
    if value < cfg["flag"]:
        return "flag"
    return "normal" if value >= cfg["normal"] else "borderline"


def evaluate_session(pvt: dict, gng: dict, dual: dict) -> dict:
    """Tüm oturumun metrik→durum haritası. Eksik testler n/a olarak gösterilir."""
    pvt  = pvt  or {}
    gng  = gng  or {}
    dual = dual or {}
    return {
        "pvt_mean_rt":        (pvt.get("mean_rt"),          flag_status("pvt_mean_rt",  pvt.get("mean_rt"))),
        "pvt_lapses":         (pvt.get("lapses"),           flag_status("pvt_lapses",   pvt.get("lapses"))),
        "pvt_false_starts":   (pvt.get("false_starts"),     flag_status("pvt_false_starts", pvt.get("false_starts"))),
        "gng_hit_rate":       (gng.get("hit_rate"),         flag_status("gng_hit_rate", gng.get("hit_rate"))),
        "gng_far":            (gng.get("false_alarm_rate"), flag_status("gng_far",      gng.get("false_alarm_rate"))),
        "gng_dprime":         (gng.get("dprime"),           flag_status("gng_dprime",   gng.get("dprime"))),
        "dual_primary_acc":   (dual.get("primary_acc"),     flag_status("dual_primary_acc",   dual.get("primary_acc"))),
        "dual_secondary_acc": (dual.get("secondary_acc"),   flag_status("dual_secondary_acc", dual.get("secondary_acc"))),
    }

def intra_individual_z(history: list[float], current: float) -> float | None:
    """Yıllık takip: kişinin kendi geçmişine göre z-skoru (>=2 önceki kayıt gerekir)."""
    if len(history) < 2 or current is None:
        return None
    sd = stdev(history)
    if sd == 0:
        return None
    return round((current - mean(history)) / sd, 2)
