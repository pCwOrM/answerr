# answerr operasyon el kitabı (ITouch iç kullanım)

## Günlük

- **Yönetim paneli:** https://answerr.me/pro/console/admin.html. Yönetici anahtarı `/etc/answerr/answerr.env` içindeki `ANSWERR_ADMIN_KEY` değeridir ve yalnızca sekme oturumunda tutulur.
- **Bekleyen plan talepleri:** ödeme geldiyse **Onayla** (plan hemen etkinleşir), gelmediyse bekletin. Talepler ask@answerr.me'ye de e-postayla düşer.
- **Hizmet durumu:** https://answerr.me/pro/status.html

## Kurumsal veya pilot müşteri açma

1. Panel › Hesaplar › e-posta, şirket ve plan (`pilot` 60 gün, `kurumsal`) → **Oluştur**.
2. Ekranda bir kez görünen ilk API anahtarını müşteriye güvenli bir kanaldan iletin.
3. Müşteri https://answerr.me/pro/console/ adresinden aynı e-postayla giriş yapar.

## Ay sonu faturalama

1. Ayın 1'i: Panel › Ekstreler › dönem (varsayılan geçen ay) › **Taslakları üret**.
2. Her taslak için e-Fatura veya e-Arşiv faturayı muhasebe entegratöründen kesin. Tutar USD × TCMB satış kuru; KDV ayrıca eklenir.
3. Fatura numarasını girip **Kesildi** deyin. Ödeme gelince **Ödendi** deyin.
4. Ödenmeyen hesaplar: 15 gün sonra hatırlatma, 30 gün sonra durum `suspended`. Askıdaki hesap API'de 403 alır.

## KVKK talepleri

- **Silme talebi:** `DELETE /v1/admin/accounts/{id}` (yönetici anahtarıyla). Ekstreler muhasebe kaydı olduğu için korunur.
- **Bilgi talebi:** `GET /v1/admin/accounts/{id}` hesap, üye, anahtar özeti, olay günlüğü ve ekstreleri döndürür.

## Yükleme ve geri alma

```bash
# mechsrv'de, paket klasöründe
sudo bash deploy/deploy_mechsrv_v130.sh             # yedek → aşama testleri → kanarya → geçiş → smoke
sudo bash deploy/deploy_mechsrv_v130.sh --rollback  # yalnızca kodu önceki hâline döndürür (müşteri DB'si korunur)
python3 deploy/smoke_checks.py https://api.answerr.me   # dışarıdan doğrulama (yönetici anahtarı verilirse ticari akış da sınanır)
```

- **Yedekler:** `/opt/backups/answerr_api_v130_<zaman>/` altında kod, drop-in, env ve `commerce.sqlite` çevrimiçi kopyası.
- **DB'yi elle geri yükleme** (yalnızca gerekirse, servis durdurulmuşken):
  `cp /opt/backups/…/commerce.sqlite /var/lib/answerr/commerce.sqlite && chown pcworm: /var/lib/answerr/commerce.sqlite`

## Site

- **Menü ve alt bilgi:** `scripts/build_site_chrome.py` içinde düzenlenir. Ardından `python scripts/build_site_chrome.py`; CI `--check` ile denetler.
- **Yasal metinler:** kaynak `site/legal/*.md`, şirket bilgileri `site/site_config.json`.
- **Fiyat:** önce `commerce/plans.json` dosyası, sonra `pro/pricing.html` ve `site/legal/mesafeli-satis.md`. Test, sayfa ile kataloğun uyumunu denetler.
