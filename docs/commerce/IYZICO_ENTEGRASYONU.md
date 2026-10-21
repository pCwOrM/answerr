# iyzico entegrasyonu — ITouch için adım adım

Güncelleme: 22 Ekim 2026. Kaynak: docs.iyzico.com (Abonelik, Ödeme Formu, Webhook, HMACSHA256, Sandbox ve Entegrasyon Kontrol Listesi sayfaları) ve iyzico yardım merkezi.

Bugünkü durum (API 1.3.1): kartla ödeme **iyzico Ödeme Formu (Checkout Form)** ile kodlandı ve test edildi; müşteriye açılması `ANSWERR_PAYMENT_PROVIDER=iyzico` ile olur. O açılana kadar havale/EFT ve yönetici onayı (`ManualProvider`) geçerlidir. Abonelik eklentisi **gerekmez**: her ödeme bir dönem satın alır (aylık 31 gün, yıllık 366 gün), otomatik çekim yoktur, bitişten 7 gün önce e-postayla hatırlatılır.

## A. ITouch'un yapacakları (iyzico tarafı)

### 1. Sandbox hesabı (bugün, 10 dakika)
1. Hesabı aç: https://sandbox-merchant.iyzipay.com/auth/register. Sandbox'ta SMS kodu her zaman `123456`.
2. Anahtarları al: **Ayarlar › Firma Ayarları › API Anahtarları › Görüntüle**. Gereken değerler:
   - API Key
   - Secret Key
   - Merchant ID
3. Bu üç değeri yalnızca mechsrv'deki `/etc/answerr/answerr.env` dosyasına yaz. Sohbete ya da repoya yazma.
   ```
   IYZICO_API_KEY=sandbox-...
   IYZICO_SECRET_KEY=sandbox-...
   IYZICO_MERCHANT_ID=...
   IYZICO_BASE_URL=https://sandbox-api.iyzipay.com
   ANSWERR_PAYMENT_PROVIDER=manual        # entegrasyon testleri bitene kadar manual kalır
   ```

### 2. Canlı üye işyeri hesabı (başvuru, birkaç iş günü)
- **Başvuru:** iyzico.com › İşletmeler › Başvur. Şirket tipi: **Limited Şirket**. Satış kanalı: **Web sitesi (answerr.me)**. Ürün: **yazılım hizmeti / SaaS abonelik**.
- **Hazırda olan belgeler** (`C:\Setup\ITouch\Şirket Evrakları`):
  - Vergi levhası: `IVD-VRG_LVH_I85SD6WRNF_4690944558.pdf`
  - Faaliyet belgesi (17.03.2026): `itouch_faaliyet_belgesi (1).pdf`
  - Ticaret sicil gazeteleri: `ticaret_sicil_*.pdf`
  - İmza sirküleri (07.10.2026): `itouch_imza_sirkuler_bdagli.PDF`
  - Ortaklık teyit belgesi: `itouch_ortaklık.pdf`
- **Ayrıca istenecekler:**
  - Şirket adına banka hesabının IBAN'ı
  - Yetkili kişinin kimlik bilgileri
  - Yetkili kişinin cep telefonu ve e-postası
- **Sözleşme:** dijital olarak e-postayla gelir ve panelden onaylanır. Islak imza ya da tarama kabul edilmez. Madde değişikliği yapılmaz.
- **Site denetimine hazırlık:** answerr.me'de gerekenlerin hepsi hazır.
  - Yasal sayfalar: Kullanım Şartları, Gizlilik, KVKK, **Ön Bilgilendirme Formu**, Mesafeli Satış Sözleşmesi, İptal-İade, Çerez.
  - Her sayfanın alt bilgisinde unvan, adres, MERSİS, vergi ve iletişim bilgileri.
  - Fiyatlar sayfası ve SSL.
  - "Taslak" notu hukuki onaydan sonra `site/site_config.json` içinden kaldırılmalı.

### 3. Panelden açılacak ek hizmetler
- **Abonelik** (Ek Hizmetler): ilk 3 ay ücretsiz, sonra 199 TL. Abonelik yalnızca kredi kartıyla çalışır.
- **Çoklu para birimi:** yıllık 99 TL. USD ile ödeme almak için gerekir.
  - Abonelik planında **USD/EUR fiyatlı planlar yalnızca yabancı kartla ödenebilir**.
  - Bu yüzden Türkiye'deki müşteriler için **TRY planları zorunlu**; USD planlar yalnızca yurt dışı müşteriler içindir.
- **Webhook:**
  - Adres: **Ayarlar › Firma Ayarları › İşyeri Bildirimleri**. Abonelik bildirimi için ayrı bir URL alanı var: `https://api.answerr.me/v1/billing/iyzico/webhook`.
  - İmzalı bildirimi (`X-IYZ-SIGNATURE-V3`) açtırmak için **entegrasyon@iyzico.com** adresine yazılmalı.

### 4. Karar: Türk lirası fiyat listesi
22.10.2026 TCMB USD satış kuru 49,6015 ile önerilen yuvarlanmış liste (KDV hariç):

| Plan | Aylık | Yıllık (aylık karşılık) | Aşım / 1.000 karar |
|---|---|---|---|
| Geliştirici | 1.449 ₺ | 1.199 ₺ | 7,50 ₺ |
| Pro | 4.899 ₺ | 4.049 ₺ | 5,00 ₺ |

Onaylanırsa `commerce/plans.json` dosyasına `price_monthly_try` ve `price_yearly_per_month_try` alanları eklenir. Fiyat sayfası ve mesafeli satış sözleşmesi iki para birimini gösterecek şekilde güncellenir.

## B. answerr tarafındaki entegrasyon (1.3.1 — uygulandı)

Uç noktalar:

| Uç nokta | Ne yapar |
|---|---|
| `GET /v1/plans` | `card_payments` (açık mı) ve TL fiyatlar |
| `GET /v1/account/checkout/quote?plan=&cycle=` | KDV hariç, KDV, toplam (TL) |
| `POST /v1/account/checkout` | Fatura bilgisi ve iki onay (ön bilgilendirme, mesafeli satış) zorunlu. iyzico `checkoutform/initialize/auth/ecom` çağrılır; `payment_page_url` döner. Tek çekim, `VIRTUAL` ürün, TRY |
| `POST /v1/billing/iyzico/callback` | Tarayıcı dönüşü. Token yalnızca ipucudur: sonuç `checkoutform/auth/ecom/detail` ile sunucudan sorgulanır; durum, `paymentStatus=SUCCESS`, `fraudStatus=1`, conversationId, basketId, tutar ve para birimi tutmazsa plan açılmaz. Konsola `?payment=paid|failed|review|unknown` ile döner, token URL'ye yazılmaz |
| `POST /v1/billing/iyzico/webhook` | iyzico bildirimi. Gövdeye güvenilmez; içindeki token yeniden sorgulanır. `X-IYZ-SIGNATURE-V3` gelirse doğrulanır, yanlışsa yok sayılır. Her zaman 200 döner |
| `GET /v1/account/payments` | Müşterinin kart ödemeleri |
| `GET /v1/admin/payments` | Tüm ödemeler (yönetici) |
| `POST /v1/admin/payments/test` | 1–10 TL entegrasyon testi; plan değiştirmez, müşteri ödemeleri kapalıyken de çalışır |
| `POST /v1/admin/payments/{id}/recheck` | Bekleyen ya da incelemedeki ödemeyi iyzico’ya yeniden sorar |
| `POST /v1/admin/payments/{id}/refunded` | Panelden yapılan iptal/iadeyi kaydeder, ödenen dönemi geri alır (konsol › Yönetim’de düğme) |

Ödeme alınınca: plan etkinleşir (yenilemede süre mevcut bitişin üstüne eklenir), bekleyen plan talebi onaylanır, `MAIL_NOTIFY_TO` adresine **Paraşüt'te fatura kesmek için gereken tüm alıcı bilgileri** ve müşteriye makbuz e-postası gider. İncelemeye düşen ödeme için ayrıca uyarı e-postası gider. Kart verisi answerr'a hiç ulaşmaz; yalnızca son 4 hane saklanır.

### Canlıya alma sırası
1. `deploy/deploy_mechsrv_v131.sh` (yedek, test, kanarya, otomatik geri dönüş). `ANSWERR_PAYMENT_PROVIDER=manual` kalır.
2. Yönetici testi (gerçek kart, 1 TL):
   ```
   curl -s -X POST https://api.answerr.me/v1/admin/payments/test -H "X-Admin-Key: …" -H "Content-Type: application/json" \
        -d '{"email":"pcworm@pcworm.net","amount_try":"1.00"}'
   ```
   Dönen `payment_page_url` açılır, kartla ödenir; tarayıcı konsola `?payment=paid` ile dönmeli, `GET /v1/admin/payments` içinde `paid` görünmeli, ask@ adresine bildirim gelmeli. Sonra iyzico panelinden **iade** edilir.
3. `/etc/answerr/answerr.env` içinde `ANSWERR_PAYMENT_PROVIDER=iyzico` yapılır ve servis yeniden başlatılır. Konsolda "Kartla öde" düğmesi görünür.
4. iyzico panelinde İşyeri Bildirimleri adresi: `https://api.answerr.me/v1/billing/iyzico/webhook`. İmzalı bildirim için entegrasyon@iyzico.com'a yazılır (zorunlu değil; imzasız bildirim de yeniden sorgulandığı için güvenlidir).

### Sonraki adım (isteğe bağlı): otomatik yenileme
Otomatik çekim istenirse iyzico Abonelik eklentisi açılır (`/v2/subscription/...`: ürün, ödeme planları, abonelik ödeme formu, `subscription.order.success/failure` bildirimleri). Bu durumda mesafeli satış sözleşmesindeki "kendiliğinden yenilenmez" maddesi değiştirilmelidir.
