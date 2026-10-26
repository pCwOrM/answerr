title: Kullanım Şartları
description: answerr karar API'si, konsolu ve web sitesinin kullanım şartları.
order: 1
---
# Kullanım Şartları

**Sürüm:** {{legal_version}}

Bu şartlar, {{company.legal_name}} ("**ITouch**", "biz") tarafından sunulan answerr karar API'si, answerr konsolu, answerr.me web sitesi ve ilgili belgelerin ("**Hizmet**") kullanımını düzenler. Hesap oluşturarak ya da Hizmet'i kullanarak bu şartları kabul etmiş olursunuz. Bir kurum adına kabul ediyorsanız, o kurumu bağlamaya yetkili olduğunuzu beyan edersiniz.

## 1. Taraflar ve iletişim

- **Hizmet sağlayıcı:** {{company.legal_name}}
- **MERSİS:** {{company.mersis}} · **Vergi:** {{company.tax}} · {{company.trade_registry}}
- **Adres:** {{company.address}}
- **E-posta:** {{company.email}} · **Telefon:** {{company.phone}} · **KEP:** {{company.kep}}

## 2. Hizmetin tanımı

answerr; doğal dilde yazılan karar politikalarını açık kurallara derleyen ve bu kurallara göre her istek için **GEÇ (ALLOW)**, **İNSANA DEVRET (REVIEW)** ya da **DUR (DENY)** hükmü veren bir yazılım hizmetidir. Hükümler deterministiktir: aynı politika ve aynı girdi aynı sonucu verir. Karar anında bir yapay zekâ modeli çalışmaz.

Hizmet; API'yi, konsolu (hesap, API anahtarları, kullanım, karar kaydı, inceleme kuyruğu, gölge mod ve geri test raporları, plan ve ödeme bilgileri) ve belgeleri kapsar. Plan içerikleri [Fiyatlar](../pricing.html) sayfasında ve `GET /v1/plans` uç noktasında yayımlanır.

## 3. Hesap ve güvenlik

1. Hesap bir iş e-postasıyla açılır; girişler e-postaya gönderilen tek kullanımlık bağlantılarla yapılır.
2. API anahtarları yalnızca oluşturuldukları anda gösterilir. Anahtarlarınızın gizliliğinden ve anahtarlarınızla yapılan isteklerden siz sorumlusunuz. Sızdığını düşündüğünüz anahtarı konsoldan hemen iptal edin.
3. Hesaba üye ekleyebilirsiniz (sahip, yönetici, inceleyici rolleri). Üyelerin işlemlerinden hesap sahibi sorumludur.

## 4. Kabul edilebilir kullanım

Hizmet'i şunlar için kullanamazsınız:

- Hukuka aykırı bir amaç, kişilerin temel hak ve özgürlüklerini ihlal eden otomatik kararlar ya da ayrımcılık;
- Hizmet'in güvenliğini, kotalarını veya hız sınırlarını aşmaya ya da başka kullanıcıların verisine erişmeye çalışmak;
- Hizmet'i tersine mühendislikle kopyalayıp rakip bir hizmet sunmak (açık kaynak bileşenlerin kendi lisansları saklıdır);
- Gerekli olmayan özel nitelikli kişisel verileri (sağlık, biyometrik, ceza mahkûmiyeti vb.) karar isteklerine koymak.

## 5. Otomatik kararlar ve sorumluluk dağılımı

answerr bir karar **aracıdır**; hükmü uygulayıp uygulamama kararı ve bu kararın sonuçları sizindir. Politikalarınızı siz yazar ve onaylarsınız. Önemli sonuçlar doğuran işlemler (ödeme, erişim, veri silme gibi) için İNSANA DEVRET hükmünü insan incelemesine bağlamanızı ve kişilere itiraz imkânı tanımanızı öneririz. KVKK m.11/1-(g) uyarınca yalnızca otomatik sistemlerle analiz edilen verilere dayanan aleyhe sonuçlara itiraz hakkı, sizin müşterilerinize karşı sizin yükümlülüğünüzdür.

## 6. Planlar, kota ve ücretler

1. Ücretsiz Keşif planı dışındaki planlar ücretlidir. Türkiye'deki müşteriler [Fiyatlar](../pricing.html) sayfasındaki Türk lirası fiyatlarını (veya kripto varlık ile USD karşılığını) öder; 4691 sayılı Kanun ve 3065 sayılı KDV Kanunu Geçici 20/1 maddesi (Teknopark Ar-Ge yazılım istisnası) ile Hizmet İhracatı kapsamında faturalar %0 KDV (KDV muafiyetli) olarak düzenlenir ve toplam tutar ödemeden önce gösterilir.
2. Bir karar, `/v1/decide` ya da `/v1/gates/{id}/decide` çağrısı veya `/v1/backtest` içindeki bir kayıttır. Politika derleme, okuma ve sağlık çağrıları ile açık çekirdeğin sizin ortamınızda çalışması sayılmaz.
3. Aylık kota dolduğunda, aşım açık değilse karar çağrıları HTTP 429 döner. Aşımı açarsanız aşım, başlayan her 1.000 karar için plan fiyatıyla faturalanır.
4. Kota ve kullanım sayaçları Türkiye saatine göre her takvim ayının başında sıfırlanır. Ödenmiş plan dönemi aylık ödemede 31, yıllık ödemede 366 gündür ve kendiliğinden yenilenmez. Ödeme ve iade koşulları [Mesafeli Satış Sözleşmesi](mesafeli-satis.html) ile [İptal ve İade](iade-iptal.html) metinlerinde yer alır.
5. Fiyat değişiklikleri en az 30 gün önce e-postayla bildirilir; ödenmiş dönemlere uygulanmaz, yalnızca sonraki satın almalarda geçerli olur. Kurucu müşterilere verilen fiyat sabitleme taahhüdü yazılı olarak bildirilen süre boyunca geçerlidir.

## 7. Veriler

Karar isteklerinde gönderdiğiniz veriler bakımından **veri sorumlusu siz**, ITouch ise **veri işleyendir**; bu ilişki [Veri İşleme Sözleşmesi](veri-isleme.html) ile düzenlenir. Hesap verileriniz için ITouch veri sorumlusudur; ayrıntılar [KVKK Aydınlatma Metni](kvkk-aydinlatma.html) ve [Gizlilik Politikası](gizlilik.html) içindedir. Karar kaydı, planınızın saklama süresi sonunda kendiliğinden silinir.

## 8. Hizmet düzeyi

Hizmet "olduğu gibi" sunulur. Planda aksi yazılı değilse belirli bir erişilebilirlik oranı taahhüt edilmez. Hizmet durumu [Durum](../status.html) sayfasında yayımlanır. Kurumsal planda SLA ayrı sözleşmeyle belirlenir.

## 9. Fikri mülkiyet

Hizmet, yazılım, politika çekirdeği, derleyici ve marka hakları ITouch'a aittir; açık kaynak bileşenler kendi lisanslarına (ör. BSL 1.1) tabidir. Yazdığınız politikalar ve gönderdiğiniz veriler sizindir. Hizmet'i iyileştirmek için yalnızca anonim ve toplu kullanım istatistiklerini kullanabiliriz.

## 10. Sorumluluğun sınırı

Kanunun izin verdiği ölçüde, ITouch'un bu şartlardan doğan toplam sorumluluğu, talebe konu olaydan önceki 12 ayda Hizmet için ödediğiniz ücretlerle sınırlıdır. Dolaylı zararlardan, kâr kaybından ve sizin politikalarınızın veya hükümleri uygulama biçiminizin sonuçlarından sorumlu değiliz. Kasıt ve ağır ihmal hâlleri ile tüketici sıfatına sahip kullanıcılar bakımından 6502 sayılı Kanun'un emredici hükümleri saklıdır.

## 11. Askıya alma ve fesih

Hesabınızı istediğiniz zaman kapatabilirsiniz. Bu şartların ağır ihlali, ödenmeyen faturalar ya da Hizmet'in güvenliğini tehdit eden kullanım hâlinde hesabı askıya alabilir veya kapatabiliriz; mümkünse önceden bildiririz. Kapanışta API anahtarları ve oturumlar iptal edilir, karar kayıtları saklama süresi sonunda silinir, yasal olarak saklanması gereken fatura kayıtları saklanır.

## 12. Değişiklikler

Bu şartları değiştirebiliriz. Esaslı değişiklikler yürürlükten en az 30 gün önce e-postayla bildirilir. Değişikliği kabul etmezseniz yürürlük tarihine kadar hesabınızı kapatabilirsiniz; bu durumda ödenmiş dönemin kalan kısmının bedeli iade edilir. Yürürlükten sonra Hizmet'i kullanmaya devam etmeniz yeni şartları kabul ettiğiniz anlamına gelir.

## 13. Uygulanacak hukuk ve yetki

Bu şartlara Türkiye Cumhuriyeti hukuku uygulanır. Tacirler arasındaki uyuşmazlıklarda Adana Mahkemeleri ve İcra Daireleri yetkilidir. Tüketici sıfatına sahipseniz Tüketici Hakem Heyetleri ve Tüketici Mahkemelerine başvuru hakkınız saklıdır.
