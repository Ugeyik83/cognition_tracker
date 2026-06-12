# 🧠 CognitionTracker

**Forklift Operatörü Bilişsel Tarama Sistemi**

Yıllık bilişsel yeterlilik taraması için bilimsel temelli, tarayıcı tabanlı değerlendirme bataryası. Üç standardize edilmiş nöropsikolojik test içerir: PVT-B, Go/No-Go ve Dual Task. Streamlit Cloud üzerinde çalışır; kurulum gerektirmez.

---

## İçindekiler

1. [Neden Bu Sistem?](#neden-bu-sistem)
2. [Hızlı Başlangıç](#hızlı-başlangıç)
3. [Mimari](#mimari)
4. [Test Protokolleri](#test-protokolleri)
5. [Metrikler ve Eşik Değerleri](#metrikler-ve-eşik-değerleri)
6. [Kullanıcı Akışı](#kullanıcı-akışı)
7. [Yönetici Paneli](#yönetici-paneli)
8. [Yapılandırma](#yapılandırma)
9. [Veri Yapısı](#veri-yapısı)
10. [KVKK / GDPR](#kvkk--gdpr)
11. [Bilimsel Kaynaklar](#bilimsel-kaynaklar)
12. [Sınırlılıklar](#sınırlılıklar)

---

## Neden Bu Sistem?

Forklift operatörlerinin neden olduğu iş kazaları incelendiğinde, insan faktörlerinin (yorgunluk, dikkat dağınıklığı, yavaş reaksiyon) kaza riskini belirgin biçimde artırdığı görülmektedir. Geleneksel yıllık sağlık taramaları bu bilişsel bileşenleri ölçmez.

CognitionTracker şu soruları yanıtlar:

- Operatörün **reaksiyon süresi** normal sınırlar içinde mi?
- **İnhibisyon kontrolü** (ani dur kararı) yeterli mi?
- **Dikkat bölme kapasitesi** (eş zamanlı uyaran yönetimi) ne düzeyde?
- Geçen yıla göre **bilişsel bozulma** var mı?

---

## Hızlı Başlangıç

### Yerel Kurulum

```bash
# Python 3.10+ gereklidir
git clone https://github.com/Ugeyik83/cognition_tracker.git
cd cognition_tracker
pip install -r requirements.txt
streamlit run app.py
```

Tarayıcıda `http://localhost:8501` açılır.

### Streamlit Cloud

1. GitHub reposunu fork edin
2. [share.streamlit.io](https://share.streamlit.io) → New app → repoyu seçin → `app.py`
3. Advanced settings → Secrets:
   ```toml
   ADMIN_PIN = "sizin_pininiz"
   ```
4. Deploy

### Bağımlılıklar

```
streamlit >= 1.32.0
pandas    >= 2.0.0
plotly    >= 5.20.0
```

Üçüncü taraf bağımlılık yoktur. `streamlit-javascript` ve `streamlit-autorefresh` kullanılmaz.

---

## Mimari

```
cognition_tracker/
│
├── app.py                      # Ana uygulama — wizard router
│
├── components/                 # İstemci taraflı test bileşenleri
│   ├── __init__.py             # declare_component tanımlamaları
│   ├── pvt/index.html          # PVT-B JavaScript bileşeni
│   ├── gonogo/index.html       # Go/No-Go JavaScript bileşeni
│   └── dual/index.html         # Dual Task JavaScript bileşeni
│
├── core/
│   ├── config.py               # Tüm protokol sabitleri (TEK kaynak)
│   ├── scoring.py              # Metrik hesaplama (Python, sunucu tarafı)
│   ├── data_logger.py          # CSV okuma/yazma
│   └── ui.py                   # CSS, stepper, bayrak rozetleri
│
├── results/                    # Operatör CSV kayıtları (.gitignore'da)
├── .streamlit/config.toml      # Tema ayarları
└── requirements.txt
```

### Veri Hattı

```
JS (performance.now()) → ham deneme verisi
        ↓
Streamlit component protocol (window.parent.postMessage)
        ↓
Python (declare_component return value)
        ↓
core/scoring.py → metrikler
        ↓
core/data_logger.py → CSV
        ↓
Yönetici Paneli → Plotly trend grafikleri
```

**Önemli tasarım kararları:**

- Tüm RT ölçümü `performance.now()` ile istemci tarafında yapılır (~0.1 ms çözünürlük). Sunucu gecikmesi ölçüme karışmaz.
- JS yalnızca **ham deneme verisi** üretir. Tüm metrikler (d′, lapse, dual-task cost) Python'da hesaplanır — denetlenebilir ve istemci tarafında manipüle edilemez.
- `st.components.v1.html()` (Streamlit 1.58'de deprecated) kullanılmaz. Bunun yerine `declare_component(path=...)` ile bidirectional WebSocket protokolü kullanılır.

---

## Test Protokolleri

### 1. PVT-B — Psikomotor Vijilans Testi

**Literatür:** Basner & Dinges (2011); Dinges & Powell (1985)

**Amaç:** Sürekli dikkat ve psikomotor hızı ölçer. Uyku yoksunluğu ve yorgunluğa en duyarlı nörokognitif test olarak kabul edilir.

**Protokol:**

| Parametre | Değer | Açıklama |
|---|---|---|
| Süre | 3 dakika (sabit) | Deneme sayısı değil süre bazlı |
| ISI | 2–8 saniye (uniform rastgele) | Uyaranlar arası bekleme süresi |
| Uyaran | Kırmızı kutu | Ekran ortasında beliriyor |
| Yanıt | SPACE tuşu | Mümkün olduğunca hızlı |
| Lapse eşiği | RT ≥ 500 ms | Dikkat çöküşü göstergesi |
| Erken basma | RT < 100 ms veya uyaran öncesi | İmpulsivite göstergesi |
| Pratik | 3 deneme | Ana bloktan önce |

**Geri bildirim:** Her denemede RT değeri gösterilir (PVT standart protokolü).

**Hesaplanan metrikler:**
- Ortalama RT (ms)
- Medyan RT (ms)
- 1/RT — reciprocal RT (sn⁻¹): uyku yoksunluğuna en duyarlı dönüşüm
- Lapse sayısı (RT ≥ 500 ms)
- Erken basma sayısı
- En yavaş %10 ortalaması

---

### 2. Go/No-Go — İnhibisyon Kontrolü

**Literatür:** Verbruggen & Logan (2008)

**Amaç:** Prepotent (otomatik) yanıt eğilimini baskılama kapasitesini ölçer. Ani dur kararlarının nörokognitif temelidir.

**Protokol:**

| Parametre | Değer | Açıklama |
|---|---|---|
| Toplam deneme | 60 (demo: 20) | Ana blok |
| Go oranı | %75 (45 deneme) | Yeşil — SPACE |
| No-Go oranı | %25 (15 deneme) | Kırmızı — basma |
| Uyaran süresi | 500 ms | Ekranda görünme süresi |
| Yanıt penceresi | 1000 ms | Uyaran başlangıcından itibaren |
| ITI | 900–1300 ms (jitter) | Denemeler arası bekleme |
| "Hazır" ipucu | YOK | Prepotent yanıt eğilimini korumak için |
| Sıralama | Fisher–Yates karıştırma | Sabit Go/No-Go sayısı + rastgele sıra |
| Pratik | 8 deneme (demo: 4) | Geri bildirimli |

**Geri bildirim:** Yalnızca pratik bloğunda. Ana blokta feedback verilmez (öğrenme yanlılığını önler).

**Hesaplanan metrikler:**
- İsabet oranı — HR (Go'da doğru basma)
- Yanlış alarm oranı — FAR (No-Go'da yanlış basma)
- Omission oranı (Go'da basmama)
- Doğru ret sayısı — CR (No-Go'da doğru basmama)
- **d′ (d-prime):** Z(HR) − Z(FAR), [0.01–0.99] kırpmalı
- Go ortalama RT (ms)

---

### 3. Dual Task — Bölünmüş Dikkat

**Literatür:** Baddeley (1992); Wickens (2002)

**Amaç:** Çalışma belleği kapasitesini ve dikkat bölme yeteneğini ölçer. Operatörün birden fazla uyaranı eş zamanlı yönetme kapasitesinin göstergesidir.

**Görev yapısı:**

**Birincil görev (sürekli):** Renk izleme
- Her 1.8 saniyede bir renk değişiyor (turuncu / mavi / mor)
- Turuncu görününce → SPACE

**İkincil görev (aralıklı):** Şekil tanıma
- Rastgele aralıklarla (2–4.5 sn) daire (●) veya kare (■) çıkıyor
- Daire → ← sol ok tuşu
- Kare → → sağ ok tuşu
- 1.5 sn görünür, 2 sn yanıt penceresi

**Blok yapısı:**

| Blok | Süre | Amaç |
|---|---|---|
| Pratik | 10 sn | Geri bildirimli alıştırma |
| Baseline (tek görev) | 15 sn | Yalnız renk görevi — karşılaştırma referansı |
| Dual Task (çift görev) | 30 sn | Her iki görev birlikte |

**Hesaplanan metrikler:**
- Birincil doğruluk: (hit + correct rejection) / toplam — 4 hücreli puanlama
- İkincil doğruluk: şekilde doğru yanıt oranı
- İkincil ortalama RT (ms)
- **Dual-Task Cost:** Baseline doğruluk − Dual doğruluk (literatürdeki asıl metrik)

> **Not:** Eski versiyondaki hata: yalnızca hit sayılıyordu, correct rejection hesaba katılmıyordu. Bu durumda turuncu oranı %33 olduğu için teorik tavan ~%33'te kalıyordu. Doğru 4 hücreli puanlama ile tavan %100'dür.

---

## Metrikler ve Eşik Değerleri

Eşikler `core/config.py → FLAGS` içinde tanımlanır ve sonuç ekranında renk kodlu olarak gösterilir.

| Metrik | Normal | Sınırda | Dikkat Bayrağı |
|---|---|---|---|
| PVT Ortalama RT | ≤ 300 ms | 300–350 ms | > 350 ms |
| PVT Lapse | ≤ 5 | 5–10 | > 10 |
| PVT Erken Basma | ≤ 3 | 3–8 | > 8 |
| Go/No-Go İsabet | ≥ %85 | %75–85 | < %75 |
| Go/No-Go Yanlış Alarm | ≤ %10 | %10–20 | > %20 |
| Go/No-Go d′ | ≥ 2.5 | 1.5–2.5 | < 1.5 |
| Dual Birincil Doğruluk | ≥ %80 | %65–80 | < %65 |
| Dual İkincil Doğruluk | ≥ %70 | %55–70 | < %55 |

### Birey-İçi Z-Skoru (Yıllık Takip)

Tek seferlik taramanın popülasyon normlarıyla karşılaştırılması yanıltıcı olabilir. Asıl değer **kişinin kendi baseline'ına göre değişimdir.**

≥ 2 önceki kayıt varsa sistem otomatik olarak hesaplar:

```
z = (güncel_değer − kişisel_ortalama) / kişisel_std
```

`|z| ≥ 1.5` → anlamlı bozulma uyarısı

---

## Kullanıcı Akışı

```
Giriş Ekranı
├── Operatör ID gir
├── KVKK rızası onayla
└── Başlangıç seç:
    ├── ▶ PVT
    ├── ▶ Go/No-Go
    ├── ▶ Dual Task
    └── Baştan Başla → (PVT → Go/No-Go → Dual Task)

Test Ekranı (her modül)
├── Yatay stepper (ilerleme göstergesi)
├── Pratik blok (geri bildirimli)
├── Ana blok (geri bildirimsiz)
└── Modül özeti + Devam butonu

Sonuç Ekranı
├── Bayrak tablosu (Normal / Sınırda / Dikkat Bayrağı)
├── Birey-içi z-skoru (≥3 kayıt varsa)
├── Eksik test uyarısı + tamamlama butonları
└── Yeni Aday butonu
```

> **Standardizasyon notu:** Resmi yıllık taramada sabit sıra (PVT → Go/No-Go → Dual Task) kullanılmalıdır. Test sırası, yorgunluk ve öğrenme transferi üzerinden karıştırıcı değişken etkisi yaratır; sıra değişirse yıllar arası karşılaştırma geçersiz olur. İstenilen testten başlama özelliği yalnızca geliştirme ve demo amaçlıdır.

---

## Yönetici Paneli

**Erişim:** Ana sayfa → "Yönetici Paneli" → PIN (varsayılan: `core/config.py → ADMIN_PIN_DEFAULT`)

PIN'i değiştirmek için `.streamlit/secrets.toml`:
```toml
ADMIN_PIN = "güçlü_pin"
```

**Özellikler:**

| Özellik | Açıklama |
|---|---|
| Özet metrikler | Toplam oturum, benzersiz operatör, lapse bayraklı oturum |
| Kayıt tablosu | Tüm operatörlerin tüm test sonuçları |
| CSV indirme | Excel'de açılabilir format (UTF-8 BOM ile Türkçe karakter desteği) |
| Trend grafiği | Seçilen operatör × seçilen metrik × zaman ekseni (Plotly) |
| Aday silme | Seçilen operatörün tüm kayıtlarını siler |
| Toplu silme | Tüm kayıtları siler |
| Metrik açıklamaları | Her metriğin klinik yorumu ve eşik değerleri |

---

## Yapılandırma

Tüm protokol parametreleri `core/config.py` içindedir. Bu dosya **tek doğruluk kaynağıdır** — hem Python metrik hesaplama hem de JavaScript bileşenler bu değerleri kullanır.

### Demo vs. Gerçek Tarama Süreleri

```python
# Demo (hızlı test için)
PVT:    duration_ms  = 30_000    # 30 saniye
GONOGO: n_trials     = 20
DUAL:   baseline_ms  = 15_000    # 15 saniye
        dual_ms      = 30_000    # 30 saniye

# Gerçek tarama (literatür standardı)
PVT:    duration_ms  = 180_000   # 3 dakika
GONOGO: n_trials     = 60
DUAL:   baseline_ms  = 30_000    # 30 saniye
        dual_ms      = 90_000    # 90 saniye
```

### Tema

`.streamlit/config.toml`:
```toml
[theme]
base                  = "dark"
primaryColor          = "#3D8BFF"
backgroundColor       = "#0A0F1E"
secondaryBackgroundColor = "#10182B"
textColor             = "#F0F4FF"
```

---

## Veri Yapısı

Her oturum ayrı bir CSV dosyasına kaydedilir: `results/{candidate_id}_{YYYYMMDD_HHMMSS}.csv`

### CSV Kolonları

| Kolon | Tip | Açıklama |
|---|---|---|
| `candidate_id` | str | Operatör ID |
| `timestamp` | datetime | Oturum tarihi ve saati |
| `pvt_mean_rt` | float | PVT ortalama RT (ms) |
| `pvt_median_rt` | float | PVT medyan RT (ms) |
| `pvt_reciprocal_rt` | float | 1/RT (sn⁻¹) |
| `pvt_lapses` | int | RT ≥ 500 ms sayısı |
| `pvt_false_starts` | int | Erken basma sayısı |
| `pvt_slowest10` | float | En yavaş %10 ortalaması (ms) |
| `pvt_n_trials` | int | Toplam deneme sayısı |
| `gng_hit_rate` | float | İsabet oranı (0–1) |
| `gng_far` | float | Yanlış alarm oranı (0–1) |
| `gng_dprime` | float | d′ |
| `gng_mean_rt_go` | float | Go denemelerinde ortalama RT (ms) |
| `dual_baseline_acc` | float | Baseline birincil doğruluk (0–1) |
| `dual_primary_acc` | float | Dual birincil doğruluk (0–1) |
| `dual_task_cost` | float | Baseline − Dual farkı |
| `dual_secondary_acc` | float | İkincil doğruluk (0–1) |
| `dual_secondary_rt` | float | İkincil ortalama RT (ms) |
| `device_refresh_hz` | int | Ekran yenileme hızı (Hz) |
| `device_pixel_ratio` | float | Cihaz piksel oranı |
| `device_ua` | str | Tarayıcı user-agent (120 karakter) |

> **Cihaz meta-verisi neden önemli:** RT değerleri cihaza göre farklılık gösterir. 60 Hz ve 144 Hz ekranlarda ölçülen RT'ler doğrudan karşılaştırılamaz. Cihaz bilgisi her kayda eklenerek yıllar arası karşılaştırmada bu faktör kontrol altına alınır.

---

## KVKK / GDPR

Operatör kimliğiyle eşleştirilmiş bilişsel performans verisi **KVKK Madde 6 / GDPR Madde 9** kapsamında **özel nitelikli kişisel veri** sayılabilir.

**Sistem tarafından alınan önlemler:**

- Teste başlamadan önce **aydınlatma metni okunması ve açık rıza onayı** zorunludur
- Veriler yalnızca yerel `results/` dizininde saklanır; ağ üzerinden üçüncü taraflara iletilmez
- `results/` dizini `.gitignore` ile versiyon kontrolü dışında tutulur

**Kurumun alması gereken ek önlemler:**

- Kimlik–sonuç eşleştirme tablolarını ayrı ve güvenli bir ortamda saklayın
- Veri saklama süresini belirleyin ve periyodik imha prosedürü oluşturun
- Operatörlere erişim, düzeltme ve silme haklarını kullanabilecekleri bir kanal sağlayın
- Veri işleme faaliyetleri siciline ekleyin (KVKK Md. 16)
- Streamlit Cloud kullanılıyorsa Streamlit'in veri işleme sözleşmesini inceleyin

---

## Bilimsel Kaynaklar

1. **Dinges, D.F. & Powell, J.W.** (1985). Microcomputer analyses of performance on a portable, simple visual RT task during sustained operations. *Behavior Research Methods*, 17(6), 652–655.

2. **Basner, M. & Dinges, D.F.** (2011). Maximizing sensitivity of the psychomotor vigilance test (PVT) to sleep loss. *Sleep*, 34(5), 581–591. https://doi.org/10.1093/sleep/34.5.581

3. **Verbruggen, F. & Logan, G.D.** (2008). Response inhibition in the stop-signal paradigm. *Trends in Cognitive Sciences*, 12(11), 418–424.

4. **Green, D.M. & Swets, J.A.** (1966). *Signal Detection Theory and Psychophysics.* Wiley. (d′ formülasyonu)

5. **Baddeley, A.** (1992). Working memory. *Science*, 255(5044), 556–559. (Dual task paradigması)

6. **Wickens, C.D.** (2002). Multiple resources and performance prediction. *Theoretical Issues in Ergonomics Science*, 3(2), 159–177.

7. **OSHA 29 CFR 1910.178** — Powered Industrial Trucks. https://www.osha.gov/powered-industrial-trucks

---

## Sınırlılıklar

| Sınırlılık | Açıklama |
|---|---|
| **Streamlit Cloud ephemeral FS** | Sunucu her restart'ta `results/` sıfırlanır. Kalıcı kullanım için şirket içi sunucu veya harici veritabanı gerekir. |
| **Tarayıcı zamanlama hassasiyeti** | `performance.now()` çözünürlüğü bazı tarayıcılarda Spectre koruması nedeniyle 1 ms'ye yuvarlanabilir. Klinik kullanım için özel RT donanımı önerilir. |
| **Ekran yenileme hızı** | 60 Hz ekranda uyaran gecikmesi ~16.7 ms olabilir. Yüksek frekanslı monitörler daha hassas ölçüm sağlar. |
| **Normatif veri** | Eşik değerleri genel popülasyon literatüründen alınmıştır. Kuruma özgü norm oluşturmak için en az 30 operatörden baseline verisi toplanması önerilir. |
| **Tek oturum geçerliliği** | Tek test sonucu tanısal değil tarama niteliğindedir. Dikkat bayrağı çıkan operatörler için nöropsikoloji uzmanı değerlendirmesi gerekir. |
| **Mobil destek** | Ok tuşu gerektiren Dual Task mobil cihazlarda çalışmaz. PVT ve Go/No-Go dokunmatik ekranda test edilmemiştir. |

---

## Lisans

MIT License — Detaylar için `LICENSE` dosyasına bakın.

---

*CognitionTracker, İSG yöneticileri ve iş sağlığı profesyonelleri için geliştirilmiştir. Klinik tanı aracı değildir.*
