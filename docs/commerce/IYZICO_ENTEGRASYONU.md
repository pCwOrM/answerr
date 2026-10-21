# iyzico entegrasyonu — ITouch için adım adım

Güncelleme: 22 Ekim 2026. Kaynak: docs.iyzico.com (Abonelik, Ödeme Formu, Webhook, HMACSHA256, Sandbox ve Entegrasyon Kontrol Listesi sayfaları) ve iyzico yardım merkezi.

Bugünkü durum: answerr, ödemeyi `ManualProvider` ile alıyor (havale/EFT ve yönetici onayı). Kod tarafında `commerce/billing.py` içinde `IyzicoProvider` için yer hazır.

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

## B. answerr tarafındaki entegrasyon (sandbox anahtarları gelince)

Doğrulanmış API yüzeyi:

| Adım | Uç nokta |
|---|---|
| Kimlik doğrulama | `Authorization: IYZWSv2 base64("apiKey:…&randomKey:…&signature:" + hex(HMAC-SHA256(randomKey + uriPath + body, secretKey)))` ve `x-iyzi-rnd` başlığı |
| Ürün (bir kez) | `POST /v2/subscription/products` → "answerr" |
| Ödeme planları (bir kez) | `POST /v2/subscription/products/{productRef}/pricing-plans` — her plan için `currencyCode` TRY ya da USD, `paymentInterval` MONTHLY ya da YEARLY, `planPaymentType` RECURRING |
| Ödeme formu | `POST /v2/subscription/checkoutform/initialize` — `callbackUrl`, `pricingPlanReferenceCode`, `subscriptionInitialStatus: ACTIVE`, `customer` (ad, soyad, e-posta, cep telefonu, TCKN/VKN, fatura adresi) |
| Sonuç | `GET /v2/subscription/checkoutform/{token}` |
| Plan yükseltme | `POST /v2/subscription/subscriptions/{ref}/upgrade` — `upgradePeriod` NOW ya da NEXT_PERIOD |
| İptal | `POST /v2/subscription/subscriptions/{ref}/cancel` |
| Kart güncelleme | `POST /v2/subscription/card-update/checkoutform/initialize` |
| Webhook | `iyziEventType`: `subscription.order.success` / `subscription.order.failure`. İmza: `hex(HMAC-SHA256(merchantId + secretKey + eventType + subscriptionReferenceCode + orderReferenceCode + customerReferenceCode, secretKey))` = `X-IYZ-SIGNATURE-V3` |

Akış:
1. Müşteri konsolda planı seçer. Ön bilgilendirme ve mesafeli satış onayı alınır. `POST /v1/account/plan-request` çağrılır, `billing.provider().checkout()` ödeme formu token'ı döner ve konsol iyzico formunu açar.
2. `callbackUrl` (`/v1/billing/iyzico/callback`) üzerinden sonuç sorgulanır, başarılıysa `store.set_plan(...)` çağrılır. Ekstre `paid / provider=iyzico / provider_ref=subscriptionReferenceCode` olarak işaretlenir.
3. Her dönemin tahsilatı webhook ile gelir:
   - `success` → ekstre ödendi.
   - `failure` → 7 gün tolerans ve e-posta. Sonra Keşif'e düşer.
4. Konsola üç düğme eklenir: "Kartımı güncelle", "Aboneliği iptal et", "Planı yükselt".
5. Aşım için abonelik dışında ayrı bir tahsilat yapılır (ödeme formu, dönem sonu). Başlangıçta aşım kapalı bırakılabilir.

Kabul ölçütleri:
- Sandbox test kartlarıyla şu senaryolar geçmeli:
  - Geliştirici ve Pro planları, aylık ve yıllık
  - 3DS başarılı ve başarısız ödeme
  - Yenileme ödemesinin başarısız olması
  - Plan yükseltme ve iptal
- Webhook aynı bildirimi tekrar gönderdiğinde plan ve ekstre iki kez işlenmemeli.
- Kart verisi hiçbir zaman answerr sunucusuna, kayıtlara ya da e-postalara ulaşmamalı.
