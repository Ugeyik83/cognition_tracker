# CognitionTracker — Forklift Operatörü Bilişsel Tarama Sistemi

Forklift operatörlerinin yıllık bilişsel yeterlilik taraması için bilimsel temelli, tarayıcı tabanlı değerlendirme bataryası. **PVT-B → Go/No-Go → Dual Task** sabit sıralı sihirbaz (wizard) akışıyla çalışır.

> Bu sürüm (v2), v1'deki kopuk veri hattını (iframe → Python), eksik CSV kaydını ve
> literatür dışı protokolleri düzelten tam yeniden yazımdır. Dokümantasyon kodla birebir uyumludur;
> tüm protokol parametreleri `core/config.py` tek kaynağından gelir.

## Kurulum

```bash
# Python 3.10+ gereklidir
git clone https://github.com/Ugeyik83/cognition_tracker.git
cd cognition_tracker
pip install -r requirements.txt
streamlit run app.py
```

Yönetici paneli PIN'i: `.streamlit/secrets.toml` içine `ADMIN_PIN = "...."` yazın
(varsayılan: `core/config.py → ADMIN_PIN_DEFAULT`).

## Mimari

```
cognition_tracker/
├── app.py                # Tek sayfalı wizard: welcome → pvt → gonogo → dual → results (+ admin)
├── core/
│   ├── config.py         # TÜM protokol sabitleri ve bayrak eşikleri (tek doğruluk kaynağı)
│   ├── tests_js.py       # İstemci taraflı test bileşenleri (performance.now, ham veri üretir)
│   ├── bridge.py         # iframe → Python köprüsü (localStorage + run_id + polling)
│   ├── scoring.py        # Tüm metrikler Python'da (d′, lapse, 1/RT, dual-task cost, z-skor)
│   ├── data_logger.py    # CSV kalıcılık (otomatik kayıt, sayısal coercion)
│   └── ui.py             # CSS, stepper, bayrak rozetleri
└── results/              # Operatör sonuçları (git dışında)
```

**Veri hattı:** `components.html` sandbox'lı iframe'de çalıştığından sayfa DOM'una yazamaz.
Test JS'i sonucu `run_id` etiketiyle `localStorage`'a yazar; Python tarafı
`streamlit-autorefresh` (1,5 sn) + `streamlit-javascript` ile okur, `run_id` doğrular,
metrikleri hesaplar ve anahtarı temizler. RT ölçümü tamamen istemci taraflıdır
(`performance.now()`); sunucu gecikmesi ölçüme karışmaz.

**Neden sabit sıra / neden sol menü yok:** Tarama bataryalarında test sırası
standardizasyon gereğidir; sıra etkisi ve yorgunluk karıştırıcı değişken olur ve
yıllar arası karşılaştırmayı bozar. Bu nedenle serbest gezinme bilinçli olarak kaldırılmıştır.

## Test Protokolleri (kodla birebir, `core/config.py`)

| | PVT-B | Go/No-Go | Dual Task |
|---|---|---|---|
| Süre / deneme | **3 dk** sabit süre | **60 deneme** (%75 Go / %25 No-Go, sabit sayı + karıştırma) | 15 sn pratik + **30 sn baseline** (tek görev) + **90 sn** çift görev |
| Zamanlama | ISI 2–8 sn uniform | Uyaran 500 ms, pencere 1000 ms, ITI 900–1300 ms jitter ("hazır" ipucu yok) | Renk 1,8 sn döngü; şekil asenkron 2–4,5 sn, 1,5 sn görünür |
| Pratik | 3 deneme | 8 deneme | 15 sn |
| Geri bildirim | RT gösterimi (standart PVT protokolü) | **Yalnız pratikte** | **Yalnız pratikte** |
| Metrikler | mean/median RT, **1/RT**, lapse (≥500 ms), erken basma, en yavaş %10 | HR, FAR, omission, **d′** (oranlar [0,01–0,99] kırpılır), Go-RT | 4 hücreli birincil doğruluk (hit+CR), ikincil doğruluk+RT, **dual-task cost** |

Ham deneme verisi JS'te toplanır; **tüm metrikler Python'da** (`core/scoring.py`) hesaplanır —
denetlenebilir ve istemci tarafında manipüle edilemez. d′ için `statistics.NormalDist`
(stdlib) kullanılır; scipy bağımlılığı yoktur.

## Değerlendirme

- **Eşik bayrakları** (`core/config.py → FLAGS`): Normal / Sınırda / Dikkat Bayrağı,
  sonuç ekranında renk kodlu tablo.
- **Birey-içi takip:** ≥2 geçmiş kayıt varsa PVT ortalama RT için z-skoru
  (`INTRA_INDIVIDUAL_Z = 1.5` üzeri anlamlı bozulma). Yıllık taramanın asıl değeri budur.
- **Cihaz meta-verisi:** ekran yenileme hızı (rAF ile ölçülür), DPR, user-agent —
  RT'lerin yıllar arası karşılaştırılabilirliği için her kayda eklenir.

## KVKK / GDPR

Operatör kimliğiyle eşleşmiş bilişsel performans verisi **KVKK Md. 6 / GDPR Md. 9**
kapsamında özel nitelikli sayılabilir. Uygulama, teste başlamadan önce **aydınlatma
metni + açık rıza** onayı zorunlu kılar; veriler yalnızca yerel `results/` dizininde
tutulur ve `.gitignore` ile versiyon kontrolünün dışındadır. Kimlik–sonuç eşleştirme
tablolarını ayrı ve güvenli bir ortamda saklayın.

## Kaynaklar

1. Dinges, D.F. & Powell, J.W. (1985). *Behavior Research Methods*, 17(6), 652–655.
2. Basner, M. & Dinges, D.F. (2011). *Sleep*, 34(5), 581–591. https://doi.org/10.1093/sleep/34.5.581
3. Verbruggen, F. & Logan, G.D. (2008). *Psychological Bulletin*, 134(3), 327–356.
4. Green, D.M. & Swets, J.A. (1966). *Signal Detection Theory and Psychophysics.* Wiley.
5. Baddeley, A. (1992). Working memory. *Science*, 255(5044), 556–559.
6. OSHA Powered Industrial Trucks. https://www.osha.gov/powered-industrial-trucks

## Lisans

MIT
