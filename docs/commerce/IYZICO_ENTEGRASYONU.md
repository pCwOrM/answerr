# iyzico entegrasyonu — hazırlık ve adımlar

Durum: **bilerek en sona bırakıldı.** Kod tarafında sınır hazır (`commerce/billing.py`); ödeme bugün `ManualProvider` ile, yani havale/EFT ve yönetici onayıyla yürüyor.

## Ön koşullar (ITouch)

- [ ] iyzico üye işyeri hesabının **canlı** ve **sandbox** API anahtarları
- [ ] Site denetimi için gerekenler:
  - [ ] Mesafeli satış sözleşmesi, iade/iptal, gizlilik ve KVKK sayfaları (taslak olarak var)
  - [ ] Şirket unvanı, adres, telefon ve e-posta her sayfanın alt bilgisinde (telefon `site/site_config.json` içinde boş, doldurulmalı)
  - [ ] Hukuki inceleme tamamlanınca `legal_status_*` notu kaldırılmalı
- [ ] Fatura: iyzico tahsil eder, yasal fatura ITouch'un e-Fatura/e-Arşiv entegratöründen kesilir

## Tasarım

1. **Konsol › Plan ve fatura › "Bu plana geç":**
   - `POST /v1/account/plan-request` → `billing.provider().checkout(...)`
   - iyzico etkinken yanıtta ödeme formu URL'si (checkout form) döner; konsol kullanıcıyı oraya yönlendirir
2. **Geri dönüş:**
   - `POST /v1/billing/iyzico/callback` (eklenecek) → `IyzicoProvider.handle_callback` → ödeme doğrulanır (retrieve + imza kontrolü)
   - Ardından `store.set_plan(..., request_id=...)` ve `mark_statement(..., status="paid", provider="iyzico", provider_ref=paymentId)`
3. **Yenileme:**
   - iyzico abonelik ürünü (aylık/yıllık), webhook ile yenileme ve başarısızlık bildirimi
   - Başarısız ödemede 7 gün tolerans, ardından `set_plan("kesif")`
4. **Aşım:** dönem sonunda ekstreden hesaplanan aşım tutarı ayrı tahsilat ya da bir sonraki yenilemeye ekleme olarak alınır
5. **Kur:** USD fiyat × TCMB satış kuru (fatura günü). Tahsilat TL olarak yapılır, kur kaynağı ekstreye yazılır.

## Ortam değişkenleri

```
ANSWERR_PAYMENT_PROVIDER=iyzico
IYZICO_API_KEY=...
IYZICO_SECRET_KEY=...
IYZICO_BASE_URL=https://sandbox-api.iyzipay.com   # canlı: https://api.iyzipay.com
```

## Kabul ölçütleri

1. Sandbox'ta Geliştirici ve Pro, aylık ve yıllık; 3D Secure başarılı ve başarısız senaryolar.
2. Callback tekrarında (idempotency) plan iki kez değişmez, ekstre iki kez ödenmez.
3. Kart bilgisi hiçbir zaman answerr sunucusuna, kayda ya da e-postaya düşmez.
4. Testler: `tests/test_commerce.py` içine sağlayıcı sahteleriyle akış testleri; smoke testine sandbox tahsilatı eklenmez.

> İmza ve uç nokta ayrıntıları iyzico'nun güncel belgelerinden entegrasyon günü doğrulanmalıdır; bu belge bunları ezbere yazmaz.
