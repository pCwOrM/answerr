<div align="center">

# ANSWERR
### Sıfır-Gecikmeli Refleks Yapay Zekâ ve Çift Bilişli Karar Çalışma Alanı

[![Lisans: BSL 1.1](https://img.shields.io/badge/Lisans-BSL_1.1-0ea5e9.svg)](LICENSE)
[![Üretim Ortamı: answerr.me](https://img.shields.io/badge/%C3%9Cretim-answerr.me-38bdf8.svg)](https://answerr.me)
[![Motor: WERR](https://img.shields.io/badge/Motor-WERR_Refleks-10b981.svg)](https://github.com/pCwOrM/werr)
[![Kâhin: Werracle](https://img.shields.io/badge/K%C3%A2hin-Werracle_On--Chain-f59e0b.svg)](https://github.com/pCwOrM/werracle)
[![FastAPI Çalışma Zamanı](https://img.shields.io/badge/API-FastAPI_0.110+-6366f1.svg)](api/)
[![WebMCP Başarısı](https://img.shields.io/badge/WebMCP-%25100_Do%C4%9Fruluk-emerald.svg)](tests/)

<p align="center">
  <b>Üst düzey doğal dil talimatlarını ve kurumsal güvenlik politikalarını (Sistem-2), sıfır-bellekli deterministik WERR prosedürel reflekslerine (Sistem-1) dönüştüren; mikrosaniye altı yürütme hızı ve sıfır halüsinasyon garantisi sunan çift bilişli karar çerçevesi.</b>
</p>

[Hızlı Başlangıç](#-hızlı-başlangıç-ve-yerel-api) •
[Çift Bilişli Mimari](#-çift-bilişli-mimari) •
[API Referansı](#-api-uç-noktaları-ve-kullanım) •
[WebMCP ve Kıyaslamalar](#-ampirik-kıyaslamalar-ve-webmcp) •
[Kurumsal Çalışma Alanı](#-kurumsal-çalışma-alanı-pro) •
[Ekosistem](#-werr-ekosistemi) •
[Araştırma Kronolojisi](RESEARCH_CHRONOLOGY.md) •
[English Documentation](README.md)

</div>

---

## 🏛️ Yeni Bir Paradigma

Modern otonom ajanlar ve kurumsal otomasyon iş akışları kritik bir darboğazla kısıtlanmıştır: **kritik yürütme yollarındaki olasılıksal determinizm eksikliği**. Karmaşık görevleri doğrudan büyük üretimsel modellere devretmek; öngörülemeyen gecikmeler ($500\,\text{ms} - 3\,\text{s}$), yüksek token maliyetleri ve felaketle sonuçlanabilecek uç durum halüsinasyonları doğurur.

**answerr**, bu sorunu **Çift Bilişli (Dual-Cognition) Bir Boru Hattı** ile çözer:
1. **Sistem-2 (Bilinçli Politika Derleyicisi):** Üst düzey kullanıcı niyeti, kurumsal güvenlik politikaları ve doğal dil kuralları çözümlenerek sınırlı koordinat değişmezlerine dönüştürülür.
2. **Sistem-1 (Deterministik WERR Refleksi):** Çalışma zamanı yürütmesi, API kapıları ve durum geçişleri; **WERR** sıfır-bellekli fraktal motoru üzerinden $\le 0.3\,\mu\text{s}$ içinde, sıfır ağırlık ve sıfır VRAM tüketimiyle tamamlanır.

```
                   Kullanıcı İstemi / Kurumsal Politika
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │      Sistem-2 Muhakemesi        │
                    │    Doğal Dil Kural Derleyicisi  │
                    └────────────────┬────────────────┘
                                     │ Deterministik Tohum İzdüşümü
                                     ▼
                    ┌─────────────────────────────────┐
                    │       Sistem-1 WERR Refleksi    │
                    │   Sıfır-Bellek Kaçış Değişmezi  │  ◄── < 0.3 μs Yürütme
                    └────────────────┬────────────────┘
                                     │
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
           [İZİN VER / ENGELLE] [Rota İndeksi]      [Risk Skoru]
               noul(q, c)       choice(q, opts)      score(m, v)
```

---

## ⚡ Hızlı Başlangıç ve Yerel API

answerr API sunucusu yerel olarak çalıştırılabilir veya Docker konteyneri ile dağıtılabilir.

### Yerel Python Kurulumu

```bash
git clone https://github.com/pCwOrM/answerr.git
cd answerr
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

### Hızlı Refleks Karar Çağrısı

```python
import requests

# Mikrosaniye altı Sistem-1 refleks kapısını sorgula
response = requests.post(
    "https://api.answerr.me/v1/systemone/gate",
    json={
        "question": "500 USDC tutarındaki otomatik çekim işlemine izin verilsin mi?",
        "context": "Günlük limit: 500/10000 limit, beyaz listedeki alıcı 0x48f..."
    }
)

decision = response.json()
print("Refleks Kapısı Kararı:", decision)
# Çıktı: {"allowed": true, "latency_us": 0.28, "engine": "werr-v0.5.1"}
```

---

## 📐 API Uç Noktaları ve Kullanım

answerr yüksek verimli, OpenAPI uyumlu bir REST API sunar:

| Uç Nokta | Metot | Biliş Seviyesi | İşlev |
|---|---|---|---|
| `/v1/systemone/gate` | `POST` | Sistem-1 (WERR) | Ultra hızlı ikili boolean refleks kapısı (`noul`) |
| `/v1/systemone/choice` | `POST` | Sistem-1 (WERR) | Deterministik kategorik seçenek yönlendirici (`choice`) |
| `/v1/systemone/score` | `POST` | Sistem-1 (WERR) | Normalize edilmiş sürekli risk skoru (`score`) |
| `/v1/policies/compile` | `POST` | Sistem-2 $\rightarrow$ Sistem-1 | Doğal dil kurallarını değişmez refleks tohumlarına derler |
| `/v1/audit/verify` | `POST` | Deterministik Denetim | Yürütme karmasını Lean 4 topolojik sınırıyla doğrular |

Etkileşimli Swagger dokümantasyonuna `https://api.answerr.me/docs` adresinden erişilebilir.

---

## 📊 Ampirik Kıyaslamalar ve WebMCP

answerr, titiz otomatik test ortamlarında kapsamlı biçimde değerlendirilmiştir:

* **WebMCP Kıyaslaması:** 42 otomatik tarayıcı kontrol senaryosunda **%100 sıfır-hata karar doğruluğu** elde etti (`windtunnel_webmcp_evaluation.py`).
* **İşlem Kapasitesi:** Bellek ayırmaksızın CPU çekirdeği başına **> 3.200.000 değerlendirme/saniye** olarak ölçümlendi.
* **Gecikme Profili:** $p_{50} = 0.28\,\mu\text{s}$, $p_{99} = 0.35\,\mu\text{s}$ ile yapay zekâ çıkarım gecikmesini kurumsal mikroservis yollarından tamamen sildi.

Tüm ampirik test logları, stres testleri ve ablasyon kayıtları [RESEARCH_CHRONOLOGY.md](RESEARCH_CHRONOLOGY.md) dosyasında eksiksiz sunulmaktadır.

---

## 🌐 Kurumsal Çalışma Alanı & Pro Konsol

answerr hem genel erişime açık bir arayüz hem de kurumsal yönetim katmanı sunar:

* **Genel Arayüz:** [https://answerr.me](https://answerr.me) — Etkileşimli karar simülatörü ve model test ortamı.
* **Kurumsal Konsol:** [https://answerr.me/pro/](https://answerr.me/pro/) — Politika derleyicisi, rol tabanlı erişim kapıları ve denetim defteri.
* **WerrSoma Görselleştirici:** [https://werrsoma.answerr.me](https://werrsoma.answerr.me) — Yüksek boyutlu konnektom ve karar topolojisi görselleştiricisi.

---

## 🌐 WERR Ekosistemi

answerr, üçlü WERR mimarisinin uygulama ve orkestrasyon katmanıdır:

```
                          ┌─────────────────────────────┐
                          │            WERR             │
                          │    Çekirdek Matematik Motor │
                          │  Sıfır-Bellekli Sistem-1    │
                          └──────────────┬──────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
  ┌─────────────────────────────┐                 ┌─────────────────────────────┐
  │          Werracle           │                 │           answerr           │
  │ Blokzincir Karar Kâhini     │                 │   Çift Bilişli Çalışma Alanı│
  │  DeFi Risk Radarı & DaaS    │                 │   Doğal Dil Güvenlik API'si │
  │   https://radar.werracle.com│                 │     https://answerr.me      │
  └─────────────────────────────┘                 └─────────────────────────────┘
```

* **[`werr`](https://github.com/pCwOrM/werr):** Çekirdek prosedürel fraktal motor ve Lean 4 sertifikalı biçimsel ispatlar.
* **[`werracle`](https://github.com/pCwOrM/werracle):** Blokzincir üzeri EVM kâhini, Q16.16 kaçış matematiği ve Uniswap v4 takas kancaları.
* **`answerr`:** Çekirdek çift bilişli çalışma alanı, doğal dil politika derleyicisi ve bulut REST uç noktaları.

---

## 📄 Akademik Atıf ve Arşiv Kaynakları

Bu araştırmayı bilimsel yayınlarınızda referans gösterirken lütfen aşağıdaki künyeyi kullanın:

```bibtex
@software{dagli2026answerr,
  author       = {Dağlı, Volkan and Dağlı, Zerrin and Dağlı, Dağhan},
  title        = {{answerr: Zero-Latency Reflex AI and Dual-Cognition Decision Workspace}},
  month        = oct,
  year         = 2026,
  publisher    = {Zenodo},
  version      = {v1.1.0},
  doi          = {10.5281/zenodo.22939253},
  url          = {https://github.com/pCwOrM/answerr}
}
```

* **İlişkili Ön Baskı:** arXiv:2609.25498 `[cs.AI / math.DS]` ([https://arxiv.org/abs/2609.25498](https://arxiv.org/abs/2609.25498))
* **Tam Araştırma Kronolojisi:** [`RESEARCH_CHRONOLOGY.md`](RESEARCH_CHRONOLOGY.md)

---

## ⚖️ Lisans ve Fikri Mülkiyet

* **Açık Bilim, Eğitim ve Değerlendirme Kullanımı:** Lisanslı Eser; **Business Source License 1.1 (BSL 1.1)** kapsamında ticari olmayan tüm akademik araştırmalar, kişisel incelemeler ve testler için serbestçe çalıştırılabilir, kaynak kodu incelenebilir ve yinelenebilir.
* **Ticari Faaliyetler ve Üretim Lisanslaması:** Her türlü ticari üretim kullanımı, barındırılan SaaS dağıtımı veya ticari entegrasyon, Lisans Veren'den yazılı Ticari Lisans alınmasını gerektirir:
  * **Lisans Veren:** `ITOUCH BİLİŞİM SİSTEMLERİ MÜHENDİSLİK DANIŞMANLIK SANAYİ VE TİCARET LİMİTED ŞİRKETİ` (`ITouch Sistemleri` · Çukurova Teknokent, Adana, Türkiye).
  * **Bilimsel Ortak Yazarlar ve Mucitler:** Volkan Dağlı (*Anadolu Üniversitesi*), Dr. Zerrin Dağlı (*Mersin Üniversitesi — Akademik Danışman, Ortak Yazar ve Ortak Mucit*), Dağhan Dağlı (*Toros Üniversitesi — Ortak Yazar ve Ortak Mucit*).
  * **Hak Devri ve Yetki Silsilesi:** Bilimsel ortak yazarlar ve mucitler, fikri mülkiyet yönetimi ve temsil yetkisini Volkan Dağlı'ya; Volkan Dağlı ise münhasır küresel ticari lisanslama, marka ve operasyon haklarını ITouch Bilişim Sistemleri Ltd. Şti.'ye devretmiştir.
  * **Ticari Markalar:** `WERR™`, `Werracle™`, `answerr™` ve `WerrSoma™` markalarının mülkiyeti münhasıran ITouch Bilişim Sistemleri Ltd. Şti.'ye aittir.
  * **Patent Başvuruları:** TÜRKPATENT **TR 2026/016285** ve **TR 2026/016633**.
  * **İletişim:** `ask@answerr.me` · `info@itouch.com.tr`

---

<div align="center">
  <sub>ITouch Bilişim Sistemleri tarafından geliştirilmiştir · Çukurova Teknokent, Adana, Türkiye</sub><br>
  <sub>Telif Hakkı &copy; 2026 ITouch Bilişim Sistemleri Ltd. Şti. Tüm hakları saklıdır.</sub>
</div>
