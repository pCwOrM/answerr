title: Gizlilik Politikası
description: answerr'in hangi veriyi neden tuttuğu, ne kadar sakladığı ve nasıl koruduğu.
order: 3
---
# Gizlilik Politikası

**Sürüm:** {{legal_version}}

Kısa özet: Karar vermek için gönderdiğiniz veriyi saklamamaya çalışırız. Karar kaydında alan **adları**, hüküm, kural ve süre tutulur; alan **değerleri** tutulmaz. Tek istisna, insana devredilen kararlardır: inceleyicinin karar verebilmesi için durum vektörü inceleme kuyruğunda saklanır. Bunu konsoldan kapatabilirsiniz.

## Karar istekleri

| Ne | Tutuluyor mu? | Ne kadar? |
| --- | --- | --- |
| Hüküm, kural kimliği, gerekçe, gecikme, politika mührü | Evet | Plan saklama süresi |
| Gönderilen alanların adları | Evet | Plan saklama süresi |
| Gönderilen alanların değerleri | Hayır | — |
| İnsana devredilen kararların durum vektörü | Evet (kapatılabilir) | Plan saklama süresi; çözülmemiş kayıt 7 günde sona erer |
| Sizin referans kimliğiniz (`external_id`) | Evet | Plan saklama süresi |
| Gölge modda bildirdiğiniz gerçek sonuç | Evet | Plan saklama süresi |

### Anonim demo istekleri ve araştırma telemetrisi

API anahtarı olmadan yapılan demo istekleri (answerr.me üzerindeki Kara Kutu ve benzeri sayfalar) müşteri karar kaydına yazılmaz. Bu istekler, werr araştırma motorunun geliştirilmesi için **araştırma telemetrisine** gönderilir.

- **Ne gönderilir:** Durum alanlarının ilk 20'si, metinlerde ilk 100 karakter, soru metni ve hüküm.
- **Ne maskelenir:** Parola, anahtar ve gizli bilgi taşıyan alan adları `[REDACTED]` olarak, e-posta adresleri ve erişim anahtarı biçimindeki değerler de maskelenerek gönderilir.
- **Ne kaydedilmez:** IP adresi telemetriye yazılmaz.
- **Nasıl kullanılabilir:** Bu kayıtlar anonim araştırma veri setlerinde kullanılabilir. Demo alanına kişisel veri yazmayın.

API anahtarıyla gelen müşteri trafiği telemetriye **gönderilmez**. Yalnızca istek içinde `werr_params.telemetry_opt_in: true` ile açıkça izin verilirse gönderilir.

## Hesap verileri

E-posta, şirket adı, üyeler, plan, fatura bilgileri ve kullanım sayıları hesabınız açık olduğu sürece tutulur. Ayrıntılar [KVKK Aydınlatma Metni](kvkk-aydinlatma.html) içindedir.

## Ödemeler

Kartla ödemeler iyzico'nun güvenli ödeme sayfasında yapılır. Kart numarası, son kullanma tarihi ve güvenlik kodu answerr'a hiç ulaşmaz; yalnızca ödeme tutarı, durumu, iyzico işlem numarası ve kartın son 4 hanesi saklanır. Havalede transfer referansı, kripto ödemede işlem kodu (TXID) ve ağ saklanır. Fatura bilgileriniz e-Arşiv / e-Fatura düzenlemek için kullanılır.

## Güvenlik

- API anahtarları, oturum ve giriş bağlantıları yalnızca SHA-256 özetleri olarak saklanır; anahtarın kendisini biz de göremeyiz.
- Bağlantılar TLS ile şifrelidir. Webhook'lar HMAC-SHA256 ile imzalanır ve yalnızca herkese açık https adreslerine gönderilir.
- Erişim, rol tabanlıdır (sahip, yönetici, inceleyici). Hesap işlemleri olay günlüğüne yazılır ve konsolda görünür.

## Yapay zekâ ve eğitim

Karar anında model çalışmaz. Verileriniz herhangi bir yapay zekâ modelini eğitmek için kullanılmaz.

## Silme

Hesabınızı kapatmak ya da verilerinizin silinmesini istemek için {{company.email}} adresine yazın. Fatura kayıtları yasal saklama süresi boyunca tutulur.
