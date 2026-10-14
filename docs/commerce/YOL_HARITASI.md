# answerr ticarileşme yol haritası

15 Ekim 2026 itibarıyla. Her aşamanın bir **kapısı** var: kapı geçilmeden bir sonraki aşamaya harcama yapılmaz.

## Aşama 0 — Satılabilir çekirdek (TAMAM, API 1.3.0)

- [x] Hesap, e-posta bağlantısıyla giriş, roller, üye daveti, koltuk sınırı
- [x] API anahtarları (özet saklama, konsola özel yönetim, iptal)
- [x] Plan kataloğu, ölçüm, kota, 429, aşım, %80/%100 uyarı
- [x] Karar kaydı (alan değeri yok), plan bazlı saklama, CSV
- [x] İnsan inceleme kuyruğu + imzalı webhook'lar
- [x] Gölge mod + raporu, geri test
- [x] Plan talebi → yönetici onayı, aylık ekstre, e-Fatura numarası eşleme
- [x] Konsol, yönetim paneli, geliştirici belgeleri, durum sayfası, `/v1/docs`
- [x] Ortak menü/alt bilgi, yasal metin taslakları (7 belge)
- [x] Testler: 94 pytest + 24 smoke + Playwright uçtan uca

**Kapı:** canlıda bir dış kişi 15 dakikada hesap açıp ilk kararını alır.

## Aşama 1 — İlk gelir (0–6 hafta)

| # | İş | Sahibi | Not |
|---|---|---|---|
| 1 | Yasal metinlerin avukat incelemesi; telefon ve KEP bilgisi `site_config.json` dosyasına | ITouch + hukuk | iyzico başvurusunun ön koşulu |
| 2 | KVKK: yurt dışı aktarım standart sözleşmesi + VERBİS kontrolü | ITouch | AB hosting nedeniyle zorunlu |
| 3 | e-Fatura/e-Arşiv entegratörü ile ekstre → fatura akışı (elle başlar) | muhasebe | ekstre numarası referans olur |
| 4 | 10 tasarım ortağı adayı (Teknokent, fintech, e-ticaret, ajan geliştiricileri) → 5 pilot | satış | pilot planı yönetici panelinden 60 gün |
| 5 | Haftalık gölge raporu e-postası (pilotlara) | ürün | `shadow_report` verisi hazır |
| 6 | Ticari API'yi araştırma yükünden ayrı VM'ye almak | operasyon | SLA'nın ön koşulu |

**Kapı:** 3 pilot gölgede, en az 1 ücretli Pro.

## Aşama 2 — Self-servis ödeme (6–10 hafta)

1. iyzico üye işyeri başvurusu: yasal sayfalar, şirket evrakı, site denetimi.
2. `IyzicoProvider` için checkout form ve abonelik API'si; sandbox → canlı.
3. Kartla ödeme sonrası planın otomatik etkinleşmesi. Ödeme başarısız olursa 7 gün tolerans, ardından Keşif'e düşme.
4. Fatura e-postası ve konsolda fatura PDF bağlantısı.

**Kapı:** insan müdahalesi olmadan ödeme → plan → fatura akışının uçtan uca çalışması.

## Aşama 3 — Pro'yu derinleştirme (2–5. ay)

- Champion/challenger: iki politika aynı trafikte; istatistiksel kapı geçilince terfi.
- Drift alarmı: hüküm dağılımı kayınca e-posta/webhook (`usage_daily` hazır).
- SDK'lar: Python (`answerr`), TypeScript, MCP sunucusu (ajan çerçeveleri için tek satır entegrasyon).
- Slack/Teams onay düğmeleri (inceleme kuyruğu webhook'ları üzerine).
- Politika sürüm geçmişi ve fark görünümü (mühürler zaten var).

## Aşama 4 — Kurumsal (5–12. ay)

- SSO/SAML (Keycloak/Entra), denetçi rolü.
- Kendi sunucusunda kurulum paketi (Docker + lisans dosyası); hava boşluklu kurulum.
- Lean 4 ile politika özelliği doğrulaması ("yönetici asla kilitlenmez", "tutar arttıkça risk azalmaz").
- ISO 27001 hazırlığı; banka müşterileri için BDDK dış hizmet gereklilikleri.
- %99,9 SLA: iki bölge, sağlık izleme, durum sayfası olay geçmişi.

## Aşama 5 — Protokol ve lisans hatları (paralel, fırsata göre)

- werr ticari lisansı (BSL 1.1 gömme/SaaS).
- Werracle protokol ücreti (zincir üstü pilot).
- WerreduR okul/platform lisansı.
- Patent lisansı ve Ar-Ge ortaklıkları (TR 2026/016285, TR 2026/016633 — beklemede).

## Ölçütler (yönetim panelinde ya da hesaplanabilir)

- **Kazanım:** kayıt/hafta, ilk karara ulaşma oranı (24 saat içinde), Keşif → ücretli dönüşümü
- **Gelir:** MRR (panelde), ARPA, aşım geliri payı
- **Kullanım:** dönem başına karar, %80 kota uyarısı alan hesap sayısı (yükseltme adayı)
- **Değer:** pilotlarda gölge uyum oranı, "sizden sıkı" vakaların gerçek dolandırıcılık/olay oranı
- **Kayıp:** ödeme sonrası 90 günde iptal

## Riskler

1. **Tek sunucu ve araştırma yüküyle paylaşım.** Aşama 1 madde 6 çözmeden SLA verilmez.
2. **Yasal metinler taslak.** Ücretli tahsilattan önce hukuki onay şart.
3. **USD fiyat / TL fatura.** Kur riski müşteride; TL sabit fiyat istenirse plan kataloğuna TL sütunu eklenir.
4. **Odak.** Araştırma hatları (WerrSoma, Güneş Dili, Lean) ürün takvimine bağlanmamalı; vitrin olarak kalmalı.
