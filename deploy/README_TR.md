# answerr 1.2.0 — yükleme

Bu paket iki yere gider:

1. **GitHub (answerr.me sitesi):** `/pro` sayfaları, `js/policy-kernel.js`, `js/werr-engine.js`, `chat.html`.
   GitHub Pages yayınladığı için `main` dalına gönderilince site güncellenir.
2. **Sunucu (api.answerr.me):** `api_server.py`, `policy_*.py`, `policies/builtin_gates.json`.

Site API'den önce yayınlanabilir. Eski API kullanılırken Kara Kutu aynı çekirdeği tarayıcıda çalıştırır ve bunu sayfada belirtir.
Derleyici ise API 1.2.0 yüklenene kadar "sunucu henüz yeni sürümü çalıştırmıyor" mesajı verir.

## 1. GitHub

Repo klasöründe:

```bash
git am answerr_v120.patch        # ya da dosyaları üzerine kopyalayıp commit edin
git push origin main
```

## 2. Sunucu

```bash
scp answerr_v120_bundle.tar.gz root@pcworm.net:/root/
ssh root@pcworm.net
mkdir -p /root/answerr_v120 && tar -xzf /root/answerr_v120_bundle.tar.gz -C /root/answerr_v120
sudo bash /root/answerr_v120/deploy/deploy_api_v120.sh
```

Betik:

- yedek alır (`/opt/backups/answerr_api_v120_<zaman>/`, içinde `RESTORE.txt`),
- yeni kodu servis kullanıcısıyla içe aktararak sınar,
- servisi yeniden başlatır, sağlık ve işlev testini yapar (`bulk_delete_users` → DENY),
- bir adım başarısız olursa her şeyi otomatik geri alır,
- `/etc/answerr/answerr.env` yoksa oluşturur ve `itouch` kiracısı için yeni bir API anahtarı yazar,
- api.answerr.me nginx sitesinde `X-Real-IP` yoksa ekler (`nginx -t` geçmezse dokunmaz).

## Sonra yapılacaklar

- **reCAPTCHA gizli anahtarı:** `/etc/answerr/answerr.env` içindeki `RECAPTCHA_SECRET=` boş.
  Google reCAPTCHA konsolunda `6LdP-JgqAAAAAJLdy_W8uowqstSa4XKlJTOkVAux` anahtarının answerr.me alan adına kayıtlı olduğunu doğrulayıp gizli anahtarı yazın.
  Ardından `systemctl restart answerr-api`. Boşken tarayıcı istekleri anonim hız sınırında (60/dk) çalışır.
- **Eski yönetici anahtarı:** 10 Ekim'de sızdığı belirlenen eski answerr yönetici anahtarı bu sürümde kullanılmıyor. Kimlik doğrulama yalnızca `ANSWERR_API_KEYS` ile yapılıyor. Eski anahtarı başka bir yerde (ör. gateway) kullanıyorsanız orada da iptal edin.
- **kasa_kayma:** answerr kod dosyaları değiştiği için ilk çalışmada kayma raporlayacak. Yeni kasa mühürlenmeli.

## Kapsam

| Alan | Değişiklik |
|---|---|
| Karar çekirdeği | `policy_kernel.py` ↔ `js/policy-kernel.js`, 41 ortak test vektörüyle birebir eşit |
| Araç sınıfları | silme/yetki → DUR, para/yazma → İNSANA, okuma → GEÇ; `bulk_delete_users`, `deleteUser`, Türkçe adlar yakalanır |
| Bilinmeyen alan | tek bir tanınmayan alan bile katı modda İNSANA |
| Hüküm anlamı | soru metninden bağımsız; soru yalnızca evet/hayır yönünü belirler |
| Kapı kaydı | API anahtarı zorunlu, kiracı sahipliği, diske kalıcı, çok işçili güvenli |
| Derleyici | şemadan alan seçimi, cümle→kural izi, sorular, otomatik testler, çalıştırılan denetimler; hiçbir şey otomatik kaydedilmez |
| reCAPTCHA | sunucuda doğrulanır; doğrulanmayan istek "aktif" sayılmaz |
| İstemci IP | proxy başlıkları yalnızca güvenilir proxy'den kabul edilir |
| Mühür | tam SHA-256, kanonik JSON |
| /pro | Karar Gözlemevi tasarımı, canlı Kara Kutu, derleyici, araştırma arşivi; doğrulanamayan iddialar kaldırıldı |
| Testler | 70 test (çekirdek, Python/JS eşitliği, derleyici, API); CI'da Node ve werr ile |
