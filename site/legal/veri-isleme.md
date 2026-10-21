title: Veri İşleme Sözleşmesi
description: Müşteri (veri sorumlusu) ile ITouch (veri işleyen) arasındaki veri işleme koşulları.
order: 8
---
# Veri İşleme Sözleşmesi (DPA)

**Sürüm:** {{legal_version}}

Bu sözleşme, [Kullanım Şartları](kullanim-sartlari.html)'nın ekidir. Müşteri ("**Veri Sorumlusu**"), answerr karar isteklerinde gönderdiği kişisel veriler bakımından {{company.legal_name}}'ni ("**Veri İşleyen**") görevlendirir.

## 1. Konu ve süre

- **İşleme konusu:** Karar isteklerinde gönderilen durum alanlarının politika çekirdeğiyle değerlendirilmesi; karar kaydının, inceleme kuyruğunun ve gölge mod raporlarının tutulması.
- **Veri konusu kişiler:** Veri Sorumlusu'nun müşterileri, kullanıcıları veya çalışanları (Veri Sorumlusu'nun belirlediği ölçüde).
- **Veri kategorileri:** Veri Sorumlusu'nun gönderdiği alanlar. Özel nitelikli kişisel veri gönderilmemesi esastır.
- **Süre:** Hizmet ilişkisi boyunca ve planın saklama süresi kadar.

## 2. Veri İşleyen'in yükümlülükleri

1. Verileri yalnızca Veri Sorumlusu'nun belgelenmiş talimatlarıyla (API çağrıları ve konsol ayarları) işler.
2. Karar kaydında alan değerlerini saklamaz; yalnızca alan adlarını, hükmü, kuralı ve süreyi saklar. İnceleme kuyruğu için durum vektörü, Veri Sorumlusu kapatmadıkça saklanır.
3. Verilere erişimi yetkili personelle sınırlar ve bu kişileri gizlilikle yükümlü kılar.
4. KVKK m.12 kapsamında uygun teknik ve idari tedbirleri alır: TLS, anahtar ve oturumların özet olarak saklanması, rol tabanlı erişim, olay günlüğü, saklama süresinin otomatik uygulanması, yedekleme.
5. Bir veri ihlalini öğrendiğinde Veri Sorumlusu'na gecikmeksizin ve en geç 72 saat içinde bildirir.
6. İlgili kişi başvurularında ve Kurul incelemelerinde Veri Sorumlusu'na makul ölçüde yardımcı olur.
7. Hizmet sona erdiğinde verileri, yasal saklama yükümlülükleri saklı kalmak üzere, saklama süresi sonunda siler.

## 3. Alt işleyenler

| Alt işleyen | Hizmet | Konum |
| --- | --- | --- |
| Contabo GmbH | Sunucu barındırma | Avrupa Birliği |
| Google LLC | reCAPTCHA (yalnızca web formları) | ABD / küresel |
| iyzico Ödeme Hizmetleri A.Ş. (çevrimiçi ödeme açıldığında) | Ödeme | Türkiye |

Yeni bir alt işleyen eklenmeden en az 30 gün önce Veri Sorumlusu'na bildirilir; Veri Sorumlusu makul gerekçeyle itiraz edebilir.

## 4. Yurt dışına aktarım

Barındırma Avrupa Birliği'nde olduğundan kişisel veriler yurt dışına aktarılır. Taraflar bu aktarımın KVKK m.9 ve Kişisel Verilerin Yurt Dışına Aktarılmasına İlişkin Usul ve Esaslar Hakkında Yönetmelik uyarınca yürütülmesi için gerekli standart sözleşmeyi imzalar ve süresi içinde Kurul'a bildirir. Türkiye'de barındırma gerektiren Veri Sorumluları için Kurumsal planda yurt içi veya müşteri ağında kurulum sunulur.

## 5. Denetim

Veri Sorumlusu, yılda bir kez ve makul bir bildirimle, bu sözleşmeye uyumu gösteren bilgi ve belgeleri talep edebilir.
