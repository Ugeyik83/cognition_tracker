# Forklift Operatörü Bilişsel Tarama Sistemi

**Forklift operatörlerinin yıllık bilişsel yeterlilik taraması için bilimsel temelli, tarayıcı tabanlı bir değerlendirme bataryası.**

Python + Streamlit ile geliştirilmiştir. Tepki süresi ölçümü, JavaScript'te `performance.now()` kullanılarak istemci tarafında (client-side) gerçekleştirilir — sunucu gecikmesinden (server latency) tamamen bağımsızdır.

---

## Neden Forklift Operatörleri?

Forklift operasyonları, depo ve endüstriyel ortamlardaki en yüksek riskli faaliyetler arasındadır. OSHA'ya (Occupational Safety and Health Administration — ABD İş Güvenliği ve Sağlık İdaresi) göre forklift kazaları yılda en az **85 ölüm, 34.900 ciddi yaralanma ve 61.800 hafif yaralanmaya** neden olmaktadır. Araştırmalar, **dikkatsizlik, bozulmuş yargılama ve bilişsel yorgunluğu** birincil etkenler olarak tutarlı biçimde işaret etmektedir.

> *"Forklift kazalarının büyük çoğunluğu, operatörün dikkatsizliği, yanlış anlama veya hatalı yargısı gibi insan hatalarından kaynaklanmaktadır."*
> — Frontiers in Neuroscience, [EEG Teknikleriyle Forklift Operatörlerinin Durum Farkındalığının Tanınması](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2024.1323190/full) (2024)

Bu sistem, güvenli forklift operasyonuyla doğrudan ilişkili üç bilişsel alanı tarar:

| Bilişsel Alan | Forklift Güvenliğiyle İlişkisi |
|---------------|-------------------------------|
| Sürekli dikkat (vigilance) | Uzun vardiyalı tekrarlayan operasyonlarda uyanıklığı koruma |
| İnhibisyon kontrolü (inhibitory control) | Yayaya çarpmadan önce zamanında durabilme |
| Bölünmüş dikkat (divided attention) | Ayna, yük, çevre gibi birden fazla uyaranı eş zamanlı yönetme |

---

## Kurulum

**Python 3.9 veya üzeri gereklidir.**

```bash
python --version   # 3.9+ olmalı
git clone https://github.com/KULLANICI_ADINIZ/cognition_tracker.git
cd cognition_tracker
pip install -r requirements.txt
streamlit run app.py
```

---

## Proje Yapısı

```
cognition_tracker/
├── app.py                  # Giriş noktası, session state yönetimi
├── pages/
│   ├── 1_pvt.py            # Modül 1: PVT testi
│   ├── 2_go_nogo.py        # Modül 2: Go/No-Go testi
│   ├── 3_dual_task.py      # Modül 3: Çift Görev testi + CSV kayıt
│   └── 4_dashboard.py      # Sonuç görselleştirme (Plotly)
├── utils/
│   ├── js_components.py    # İstemci taraflı JS bileşenleri (RT ölçümü)
│   └── data_logger.py      # CSV kalıcı depolama katmanı
└── results/                # Operatör sonuçları (git dışında tutulur)
```

---

## Test Bataryası — Bilimsel Arka Plan

### Modül 1 — PVT (Psychomotor Vigilance Task — Psikomotor Uyanıklık Testi)

**Süre:** 3 dakika | **Protokol:** 2–8 saniye arasında rastgele ISI (Inter-Stimulus Interval — Uyaranlar Arası Aralık) ile görsel uyaran

**Ne ölçer:** Sürekli dikkat (sustained attention / vigilance) — öngörülemeyen, seyrek uyaranlara tutarlı tepki verme hazırlığını sürdürme kapasitesi. Rastgele ISI tasarımı kritiktir: sabit aralık kullanılsaydı operatör ritmi ezberler ve gerçek dikkat kapasitesi ölçülemezdi.

**Forklift operatörü için neden önemli:** Uzun vardiyalı, tekrarlayan depo operasyonları tam olarak dikkat bozulmasının yaşandığı koşullardır. PVT, operasyonel ortamlarda yorgunluğa bağlı dikkat düşüşünü tespit eden en kapsamlı biçimde doğrulanmış araçtır.

> *"Uyanıklık ve dikkat, güvenli taşıma operasyonları için kritiktir; ancak yorgunluk ve uyku hali tepki sürelerini yavaşlatarak, dikkat boşluklarını artırarak ve yargılama ile karar verme becerilerini bozarak bu kapasiteleri tehlikeye atar."*
> — PMC, [Operatör Yorgunluğunu Ele Almanın Önemi](https://pmc.ncbi.nlm.nih.gov/articles/PMC4457397/)

**Performans kriterleri:**

| Metrik | Normal | Dikkat Bayrağı |
|--------|--------|----------------|
| Ortalama RT (Reaction Time — Tepki Süresi) | 150–300 ms | > 350 ms |
| Lapse sayısı (RT > 500 ms) | < 5 | > 10 |
| Erken basma (uyarandan önce tepki) | < 3 | > 8 |

**Neden 3 dakika?** Standart PVT süresi 10 dakikadır (Dinges & Powell, 1985). Kısaltılmış 3 dakikalık versiyon, yorgunluğa bağlı bozulmaya karşı yüksek duyarlılığını koruyarak operasyonel tarama bağlamları için doğrulanmıştır.

**Temel kaynaklar:**
- Dinges, D.F. & Powell, J.W. (1985). Microcomputer analyses of performance on a portable, simple visual RT task during sustained operations. *Behavior Research Methods*, 17(6), 652–655.
- Basner, M. & Dinges, D.F. (2011). Maximizing sensitivity of the psychomotor vigilance test (PVT) to sleep loss. *Sleep*, 34(5), 581–591. [DOI: 10.1093/sleep/34.5.581](https://doi.org/10.1093/sleep/34.5.581) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/21532951/)

---

### Modül 2 — Go/No-Go (Tepki Ver / Tepki Verme Testi)

**Süre:** ~2 dakika | **Deneme sayısı:** 60 (%75 Go, %25 No-Go)

**Ne ölçer:** İnhibisyon kontrolü (inhibitory control) — baskın, otomatik bir motor tepkiyi baskılama kapasitesi. %75/%25 oranı standarttır: sık Go denemeleri bir tepki eğilimi oluşturur ve operatör bunu No-Go denemelerinde geçersiz kılmak zorunda kalır.

**Forklift operatörü için neden önemli:** Başlatılmış bir hareketi durdurabilme — yayaya çarpmadan önce frenleme, aşırı yükseliş öncesi kaldırmayı durdurma — doğrudan inhibisyon kontrolünün bir ifadesidir. İnhibisyon kapasitesi düşük operatörler, zaman baskısı altında daha yüksek hatalı tepki oranı gösterir.

> *"Go/no-go görevleri, güvenlik farkındalığıyla ilişkili kritik bilişsel özellikleri değerlendirmek için kullanılmış ve inşaat güvenliği yönetiminde daha geniş uygulamalar için ölçeklendirilebileceği gösterilmiştir."*
> — ScienceDirect, [Go/Nogo Görevlerinde Tehdit Kaynaklı Dürtüsellik](https://www.sciencedirect.com/science/article/abs/pii/S105381001930073X)

**Performans kriterleri:**

| Metrik | Normal | Dikkat Bayrağı |
|--------|--------|----------------|
| İsabet oranı — HR (Hit Rate — Doğru Go Tepkisi) | > %85 | < %75 |
| Yanlış alarm oranı — FAR (False Alarm Rate — Hatalı No-Go Tepkisi) | < %10 | > %20 |
| d-prime (d') — sinyal algılama duyarlılığı | > 2,5 | < 1,5 |

**d-prime formülü:**

```
d' = Z(İsabet Oranı) − Z(Yanlış Alarm Oranı)
```

Z, standart normal kümülatif dağılımın ters fonksiyonudur (probit). Uç değer koruması: her iki oran da sonsuz değerlerden kaçınmak için [0,01; 0,99] aralığına sınırlandırılır.
Uygulama: `utils/js_components.py → gonogo_component() → normPPF()`

Yüksek d', tepkiyle ilgili (Go) ve ilgisiz (No-Go) uyaranlar arasında daha iyi ayrım yapıldığını gösterir — tepki yanlılığından (response bias) bağımsız olarak.

**Temel kaynaklar:**
- Donders, F.C. (1969). On the speed of mental processes. *Acta Psychologica*, 30, 412–431.
- Green, D.M. & Swets, J.A. (1966). *Signal Detection Theory and Psychophysics.* Wiley.
- Verbruggen, F. & Logan, G.D. (2008). Automatic and controlled response inhibition. *Psychological Bulletin*, 134(3), 327–356. [PubMed](https://pubmed.ncbi.nlm.nih.gov/18444702/)

---

### Modül 3 — Çift Görev (Dual Task — Bölünmüş Dikkat Testi)

**Süre:** 90 saniye

**Ne ölçer:** Bölünmüş dikkat (divided attention) ve merkezi yürütücü (central executive) kapasitesi — iki bağımsız bilişsel talebi eş zamanlı yönetme becerisi. Baddeley'in çalışma belleği (working memory) çok bileşenli modelini temel alır.

**Görev tasarımı:**
- **Birincil görev (sürekli):** Renk ayrımı — turuncu daireye tepki ver (SPACE), mavi/mor dikkat dağıtıcılara tepki verme. Seçici sürekli dikkati ölçer.
- **İkincil görev (asenkron):** Şekil ayrımı — daire (D tuşu) veya kare (K tuşu), her 2–4,5 saniyede bir rastgele belirir. Beklenmedik kesintilere tepki verme kapasitesini ölçer.

Asenkron tasarım bilinçli bir tercihtir: operatör ikincil uyaranın ne zaman geleceğini bilmez; bu durum, yayaların, alarmların ve sinyallerin süregelen görevleri kesintiye uğrattığı gerçek depo koşullarını simüle eder.

**Performans kriterleri:**

| Metrik | Normal | Dikkat Bayrağı |
|--------|--------|----------------|
| Birincil görev doğruluğu | > %80 | < %65 |
| İkincil görev doğruluğu | > %70 | < %55 |

**Forklift operatörü için neden önemli:** Forklift kullanmak; yük konumunu, çevreyi, aynaları ve zemin işaretlerini eş zamanlı izlemeyi gerektirir. Bölünmüş dikkat kapasitesi, bu tür çok talepli ortamlardaki performansı doğrudan öngörür.

**Temel kaynaklar:**
- Baddeley, A. (1992). Working memory. *Science*, 255(5044), 556–559. [DOI: 10.1126/science.1736359](https://doi.org/10.1126/science.1736359)
- Baddeley, A. (2000). The episodic buffer: a new component of working memory? *Trends in Cognitive Sciences*, 4(11), 417–423. [DOI: 10.1016/S1364-6613(00)01538-2](https://doi.org/10.1016/S1364-6613(00)01538-2)

---

## Teknik Notlar

### RT Ölçüm Hassasiyeti

Streamlit'in `st.button` bileşeni 100–400 ms'lik sunucu gidiş-dönüş gecikmesi ekler; bu durum, PVT lapse (dikkat boşluğu) eşiğini (500 ms) zamanlama için kullanıldığında anlamsız kılar.

**Çözüm:** Tüm RT ölçümü tarayıcıda `performance.now()` (~1 ms hassasiyet, 60 Hz'de ~16 ms render ofseti) ile çalışır. Sonuçlar test tamamlanınca `localStorage`'a yazılır ve Python tarafından toplu olarak alınır — ölçüm sırasında gerçek zamanlı HTTP gidiş-dönüşü yoktur.

`st_autorefresh` her 2 saniyede bir test tamamlanmasını tespit etmek için yoklama yapar. Bu durum RT ölçümünü etkilemez; zamanlama tamamen istemci taraflıdır.

### Oturum Durumu Yönetimi

`st.session_state`, sayfa geçişlerinde korunur. Sayfa yenilendiğinde durum temizlenir — veri kaybını önlemek için sonuçlar, üç modülün tamamı tamamlandıktan hemen sonra CSV'ye yazılır.

### Veri Güvenliği ve KVKK Uyumu

- Tüm test sonuçları, uygulamanın çalıştığı makinedeki `results/` dizininde **yerel olarak** depolanır.
- Operatör kimlik bilgileriyle birleştirilmiş bilişsel performans verileri, **KVKK** (Kişisel Verilerin Korunması Kanunu) Madde 6 ve GDPR (General Data Protection Regulation — Avrupa Genel Veri Koruma Tüzüğü) Madde 9 kapsamında özel nitelikli kişisel veri sayılabilir.
- Dağıtım öncesinde: her operatör için aydınlatma metni ve veri işleme rıza formu hazırlayın.
- Operatör kimliği–sonuç eşleştirme tabloları bu sistemden ayrı, güvenli bir ortamda tutulmalıdır.
- Yerel ağ üzerinden erişim söz konusuysa ağ güvenliği sistem yöneticisinin sorumluluğundadır.
- `results/` dizini `.gitignore` dosyasında listelenmiştir — veriler hiçbir zaman versiyon kontrolüne dahil edilmez.

---

## Kaynaklar

1. Dinges, D.F. & Powell, J.W. (1985). Microcomputer analyses of performance on a portable, simple visual RT task during sustained operations. *Behavior Research Methods*, 17(6), 652–655.
2. Basner, M. & Dinges, D.F. (2011). Maximizing sensitivity of the psychomotor vigilance test (PVT) to sleep loss. *Sleep*, 34(5), 581–591. https://doi.org/10.1093/sleep/34.5.581
3. Baddeley, A. (1992). Working memory. *Science*, 255(5044), 556–559. https://doi.org/10.1126/science.1736359
4. Green, D.M. & Swets, J.A. (1966). *Signal Detection Theory and Psychophysics.* Wiley.
5. Verbruggen, F. & Logan, G.D. (2008). Automatic and controlled response inhibition. *Psychological Bulletin*, 134(3), 327–356. https://pubmed.ncbi.nlm.nih.gov/18444702/
6. OSHA Forklift Güvenlik Verileri. https://www.osha.gov/powered-industrial-trucks
7. Frontiers in Neuroscience (2024). EEG Teknikleriyle Forklift Operatörlerinin Durum Farkındalığının Tanınması. https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2024.1323190/full
8. PMC (2015). Operatör Yorgunluğunu Ele Almanın Önemi. https://pmc.ncbi.nlm.nih.gov/articles/PMC4457397/
