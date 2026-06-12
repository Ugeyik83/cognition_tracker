# core/config.py
"""Protokol sabitleri ve eşik değerleri — tek doğruluk kaynağı.

Tüm test parametreleri ve README'deki Normal / Dikkat Bayrağı eşikleri
burada tanımlanır. JS bileşenleri bu değerleri parametre olarak alır,
böylece kod ile dokümantasyon ayrışamaz.
"""

# ── PVT-B (Basner & Dinges 2011; Dinges & Powell 1985) ──────────
PVT = {
    "duration_ms": 30_000,         # 3 dakika sabit süre (deneme sayısı değil) / şu an 30 saniye, gelecekte 3 dakika olabilir
    "isi_min_ms": 2_000,           # ISI 2–8 sn (rastgele, uniform)
    "isi_max_ms": 8_000,
    "lapse_ms": 500,               # lapse eşiği: RT >= 500 ms
    "false_start_ms": 100,         # RT < 100 ms veya uyaran öncesi = erken basma
    "practice_trials": 3,
}

# ── Go/No-Go (Verbruggen & Logan 2008) ───────────────────────────
GONOGO = {
    "n_trials": 10,               # toplam deneme sayısı (pratik dahil) / şu an 10, gelecekte 60 olabilir
    "go_ratio": 0.75,              # 45 Go / 15 No-Go (sabit sayı, karıştırılmış)
    "stim_ms": 500,                # uyaran ekranda kalma süresi
    "resp_window_ms": 1_000,       # uyaran başlangıcından itibaren yanıt penceresi
    "iti_min_ms": 900,             # denemeler arası jitter (hazır ipucu YOK)
    "iti_max_ms": 1_300,
    "practice_trials": 8,
    "rate_clamp": (0.01, 0.99),    # d' için HR/FAR kırpma aralığı
}

# ── Dual Task (Baddeley 1992) ────────────────────────────────────
DUAL = {
    "baseline_ms": 15_000,         # tek-görev baseline (yalnız renk) → dual-task cost normal 30
    "dual_ms": 30_000,             # çift görev ana blok / normal 90
    "color_interval_ms": 1_800,    # renk uyaranı süresi = yanıt penceresi
    "target_ratio": 0.33,          # turuncu oranı
    "shape_min_ms": 2_000,         # ikincil uyaran asenkron aralığı
    "shape_max_ms": 4_500,
    "shape_visible_ms": 1_500,
    "shape_window_ms": 2_000,      # şekil başlangıcından itibaren yanıt penceresi
    "practice_ms": 10_000,         # pratik süresi / normal 15
}

# ── Dikkat Bayrağı eşikleri (README tablolarıyla birebir) ────────
FLAGS = {
    "pvt_mean_rt":    {"normal": 300, "flag": 350, "higher_is_worse": True,  "unit": "ms"},
    "pvt_lapses":     {"normal": 5,   "flag": 10,  "higher_is_worse": True,  "unit": ""},
    "pvt_false_starts": {"normal": 3, "flag": 8,   "higher_is_worse": True,  "unit": ""},
    "gng_hit_rate":   {"normal": 0.85, "flag": 0.75, "higher_is_worse": False, "unit": "%"},
    "gng_far":        {"normal": 0.10, "flag": 0.20, "higher_is_worse": True,  "unit": "%"},
    "gng_dprime":     {"normal": 2.5,  "flag": 1.5,  "higher_is_worse": False, "unit": ""},
    "dual_primary_acc":   {"normal": 0.80, "flag": 0.65, "higher_is_worse": False, "unit": "%"},
    "dual_secondary_acc": {"normal": 0.70, "flag": 0.55, "higher_is_worse": False, "unit": "%"},
}

# Yıllık takipte birey-içi değişim bayrağı: |z| >= bu değer ise işaretle
INTRA_INDIVIDUAL_Z = 1.5

ADMIN_PIN_DEFAULT = "1983"  # st.secrets["ADMIN_PIN"] ile geçersiz kılınabilir
