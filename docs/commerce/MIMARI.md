# answerr ticari platform — mimari (API 1.3.0)

Sürüm: 15 Ekim 2026 · Sahibi: ITouch Bilişim Sistemleri Ltd. Şti.

## 1. Ne satıyoruz

**answerr Pro:** doğal dilde yazılan, açık kurallara derlenen ve deterministik çalışan karar kapıları.

- Satış birimi **karardır**: `/v1/decide`, `/v1/gates/{id}/decide` ya da bir geri test kaydı.
- Karar anında model çalışmaz. Bu yüzden maliyet sabit ve tahmin edilebilir; brüt marj yazılım marjıdır.
- Plan kataloğunun tek kaynağı `commerce/plans.json` dosyasıdır. Fiyat sayfası CI'da bu dosyayla karşılaştırılır.

| Plan | Aylık | Yıllık (aylık karşılık) | Kota/ay | Aşım /1.000 | Özel kapı | Saklama | Koltuk | Anahtar | Ek özellikler |
|---|---|---|---|---|---|---|---|---|---|
| Keşif | $0 | $0 | 10.000 | — | 1 | 7 gün | 1 | 2 | — |
| Geliştirici | $29 | $24 | 250.000 | $0,15 | 10 | 30 gün | 1 | 5 | — |
| Pro | $99 | $82 | 1.000.000 | $0,10 | 200 | 90 gün | 5 | 20 | gölge mod, geri test, inceleme kuyruğu, CSV, webhook |
| Kurumsal | $24.000+/yıl | sözleşme | sözleşme | — | 200 | 365 gün | 50 | 100 | + SSO*, kendi sunucusu*, Lean 4 doğrulama*, SLA* |
| Pilot (gizli) | $0 · 60 gün | — | 2.000.000 | — | 200 | 90 gün | 5 | 20 | Pro ile aynı; süre bitince Keşif'e düşer |

\* Henüz yok; fiyat sayfasında "YAKINDA" etiketiyle gösteriliyor.

## 2. Bileşenler

```
answerr.me (GitHub Pages)                         api.answerr.me (IIS ARR → NAT → Apache :4431 /v1 → uvicorn ×4, mechsrv)
├─ /pro/            ürün, Kara Kutu, derleyici    ├─ api_server.py         karar, kapılar, derleyici (değişmedi + ölçüm kancası)
├─ /pro/pricing     fiyat + plan talep formu      ├─ policy_kernel.py      tek karar verici (JS eşi tarayıcıda)
├─ /pro/docs        geliştirici belgeleri         └─ commerce/
├─ /pro/console/    müşteri konsolu                   ├─ plans.json        plan kataloğu (tek kaynak)
├─ /pro/console/admin.html  ITouch yönetim            ├─ store.py          SQLite (WAL): hesaplar, üyeler, anahtarlar, kullanım, kayıt…
├─ /pro/status      canlı durum                       ├─ router.py         /v1/auth, /v1/account, /v1/reviews, /v1/backtest, /v1/plans, /v1/admin
└─ /pro/legal/*     yasal metinler (site/legal/*.md)  ├─ mail.py           giriş bağlantısı, davet, plan talebi, kota uyarısı
                                                      ├─ webhooks.py       HMAC imzalı, SSRF korumalı, 3 deneme
                                                      └─ billing.py        ödeme sağlayıcı sınırı (manual | iyzico)
```

- **Menü ve alt bilgi** tek kaynaktan gelir: `scripts/build_site_chrome.py`. Sayfalarda işaretçiler arasında durur, CI `--check` ile denetler. Sayfalar arasında menü artık değişmez.
- **API belgeleri** `/v1/docs`, `/v1/redoc` ve `/v1/openapi.json` altındadır. Önceki `/docs` adresi 404 veriyordu, çünkü Apache yalnızca `/v1` yolunu iletiyor.

## 3. Kimlik ve yetki

| Kimlik | Biçim | Saklama | Kapsam |
|---|---|---|---|
| API anahtarı | `ans_live_…` (40 karakter) | yalnızca SHA-256 | kararlar, incelemeler, sonuç bildirimi, kullanım, kayıt, geri test |
| Oturum | `ans_sess_…`, 7 gün | yalnızca SHA-256 | konsol: yukarıdakilere ek olarak anahtar, üye, plan, fatura, ayarlar |
| Giriş bağlantısı | `ans_link_…`, 20 dk, tek kullanımlık | yalnızca SHA-256 | kayıt, giriş, davet; adres başına saatte en fazla 5 |
| Yönetici | `X-Admin-Key` (`ANSWERR_ADMIN_KEY`) | ortam dosyası | /v1/admin/* |
| İç kiracı | `ANSWERR_API_KEYS` (itouch) | ortam dosyası | eski davranış; ölçülmez |

- **Roller:** sahip > yönetici > inceleyici. İnceleyici yalnızca okur ve inceleme sonuçlandırır.
- **Konsola özel işlemler:** anahtar, üye ve plan işlemleri yalnızca oturumla yapılır (`session_required`). Sızan bir API anahtarı yeni anahtar üretemez.
- **Önbellek:** iptal edilen anahtar her işçide en geç 30 saniyede düşer (anahtar önbelleği).
- **Kayıt formu:** KVKK aydınlatmasının okunduğu ve kullanım şartlarının kabul edildiği onaylanmadan hesap açılmaz. Onaylar `terms_version` ve zaman damgasıyla saklanır. reCAPTCHA ve IP başına saatte 5 istek sınırı uygulanır. Giriş isteği hesabın varlığını açığa çıkarmaz.

## 4. Karar yolu (ölçümlü)

```
istek → middleware: kimlik (anahtar/oturum → acct:<id>), hız sınırı (api_key katmanı 600/dk)
      → post_decide: quota_check (429 quota_exceeded | 403 account_suspended) → çekirdek → yanıt
      → _meter: usage(+1) · usage_daily(+hüküm) · decisions(kayıt) · [REVIEW ∧ canlı ∧ Pro+] reviews(+webhook)
               · %80/%100 kota e-postası + quota.warning webhook'u
```

- **Dönem:** Türkiye saatiyle takvim ayı.
- **Kayıt:** alan **adları** tutulur, **değerleri** tutulmaz. İnceleme kuyruğu, inceleyici görebilsin diye durumu saklar; hesap bunu kapatabilir.
- **Gölge mod** (`mode: shadow`): kayda geçer ve sayılır, incelemeye düşmez. Müşterinin kendi kararı `observed_outcome` ya da `POST /v1/decisions/{id}/outcome` ile eklenir. Rapor uyumu ve sıkı/gevşek farkları verir.
- **Geri test:** çağrı başına en fazla 1.000 kayıt; her kayıt bir karar sayılır.
- **Saklama süresi:** her işçide saatte bir `purge()` çalışır. Plan saklama süresini, süresi dolan bağlantıları ve oturumları temizler.

## 5. Faturalama

1. `generate_statements(dönem)` her hesap için ekstreyi hesaplar: plan tabanı (aylık ya da yıllık) + aşım (başlayan her 1.000 karar).
2. Ekstre **taslaktır**. Yasal fatura ITouch'un e-Fatura/e-Arşiv entegratöründen kesilir. Numarası `mark_statement(issued, e_invoice_no)` ile eklenir, ödeme `paid` ile işaretlenir.
3. **Para birimi:** USD fiyat; Türkiye'deki müşteriye fatura tarihindeki TCMB döviz satış kuruyla TL fatura.
4. **Bugünkü tahsilat (`ManualProvider`):** plan talebi → ask@answerr.me'ye bildirim → havale/EFT bilgisi e-postayla → ödeme gelince yönetim panelinden onay → plan anında etkin.
5. **iyzico:** `billing.IyzicoProvider` sınırı hazır, uygulama son adım. Bkz. `IYZICO_ENTEGRASYONU.md`.

## 6. Veri ve uyum

- **Hosting:** Contabo GmbH, AB. KVKK m.9 kapsamında yurt dışına aktarım var; metinlerde açıkça yazıyor. Standart sözleşme imzalanıp Kurul'a bildirilmesi gerekiyor.
- **Veri işleme sözleşmesi:** müşteri veri sorumlusu, ITouch veri işleyen (`pro/legal/veri-isleme.html`).
- **Yasal metinlerin kaynağı:** `site/legal/*.md` + `site/site_config.json`. Hepsi "yürürlük öncesi taslak" notu taşır; hukuki inceleme sonrası not `site_config.json` içinden kaldırılır.

## 7. Geri dönülebilirlik

- **Site:**
  - Önceki /pro ve site sürümleri depodaki `archive/site/` altında arşivlenmiştir (canlı yayından hariç tutulur).
  - Etiketler: `pro-v1.2.0`, `pro-v1.3.0`.
  - Bu sürüm tek commit olarak `git revert` ile geri alınabilir.
- **API:**
  - `deploy/deploy_mechsrv_v130.sh` önce yedek alır: kod, systemd drop-in, env ve **commerce.sqlite çevrimiçi kopyası**.
  - Sırası: aşamada testler, kanarya (:8561, ayrı DB) ve 24 smoke testi, ardından geçiş ve canlıda smoke. Hata olursa otomatik geri alır.
  - `--rollback` yalnızca kodu döndürür, müşteri DB'sine dokunmaz. 1.2.0 kodu ticari tabloları görmezden gelir.
- **Veritabanı:** şema yalnızca `CREATE TABLE IF NOT EXISTS` ile ekleniyor; eski tablo değişmiyor.
