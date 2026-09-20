# ⚡ A.N.S.W.E.R.R. — Sıfır-Gecikmeli Refleks Yapay Zekası

[![Canlı Demo: GitHub Pages](https://img.shields.io/badge/Canl%C4%B1%20Demo-GitHub%20Pages-38bdf8.svg)](https://pcworm.github.io/answerr/)
[![Web Sitesi: answerr.me](https://img.shields.io/badge/Alan%20Ad%C4%B1-answerr.me-818cf8.svg)](https://answerr.me)
[![werr Çekirdek Motoru](https://img.shields.io/badge/werr-S%C4%B1f%C4%B1r--Bellek%20Motoru-10b981.svg)](https://github.com/pCwOrM/werr)
[![Müzakereci Yapay Zeka](https://img.shields.io/badge/Sistem--2-M%C3%BCzakereci%20YZ-c084fc.svg)](https://answerr.me)
[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-yellow.svg)](./LICENSE)

> **A**daptive **N**on-tensor **S**ignal **W**ave & **E**rror **R**eflex **R**esonator  
> *(Uyarlanabilir Tensörsüz Sinyal Dalgası ve Hata Refleksi Rezonatörü)*  
> *"Don't just chat. Get the Answerr. Sadece sohbet etmeyin; milisaniyenin altında 0-byte VRAM ile kesin kararı alın."*

### 🧬 Neden 1 Numara? (Mimari Sütunlar)
* **Adaptive (Uyarlanabilir):** Üstel hareketli ortalama (EMA $\alpha=0.03$) ve dinamik eşikleme yeteneği ile çalışma zamanında esnek adaptasyon.
* **Non-tensor (Tensörsüz):** 0-VRAM devrimini doğrudan ismin kalbine çakar; GPU ağırlığı depolamadan çıplak donanımda veya tarayıcıda çalışır.
* **Signal (Sinyal):** Gelen operasyonel durum (state) ve telemetrinin dinamik bir sinyal dalgası olduğunu vurgular.
* **Wave & Error (Dalga ve Hata):** wevv motorunun dalga yayılımı ve Mandelbrot kaotik sınırındaki ($\partial M$) hata navigasyonunun matematiksel özünü taşır.
* **Reflex Resonator (Refleks Rezonatörü):** Hem omurilik refleksini hem de akustik faz rezonansını (tınlamayı) tek hamlede ifade eder.

🌐 **Canlı Web Platformu:** [https://answerr.me](https://answerr.me)  
⚡ **Canlı REST API:** [https://api.answerr.me:4431](https://api.answerr.me:4431)  
🌐 **GitHub Pages Demosu:** [https://pcworm.github.io/answerr/](https://pcworm.github.io/answerr/)

---

## 🌟 Genel Bakış

**A.N.S.W.E.R.R.**, iki temel bilişsel düzeyi birleştiren yeni nesil bir karar motorudur:
1. **Sistem-2 Müzakeresi (LLM / Müzakereci Yapay Zeka):** Karmaşık insan dilini ve durum parametrelerini anlar, operasyonel bağlamı çıkarır ve kararı stratejik olarak açıklar (Bulut API'leri veya yerel açık kaynak modellerle tam uyumlu).
2. **Sistem-1 Omurilik Refleksi ([werr](https://github.com/pCwOrM/werr)):** Mandelbrot fraktal sınırındaki 24 baytlık $(c_x, c_y, \text{zoom})$ koordinat tohumunu dinamik olarak modüle eder ve **0 Byte VRAM** ile **< 1 ms** içinde kesin tipli kararları (`noul`, `choice`, `score`) üretir.

Böylece basit bir onay veya mikroservis yönlendirmesi için devasa modellerin gigabaytlarca VRAM tüketmesi ve yüzlerce milisaniye beklemesi gerekmez; triyaj kararı doğrudan evrensel geometriden türer.

---

## ⚡ Bilişsel Mimari ve Akış

1. **Soru Girişi:** Kullanıcı sayfanın ortasındaki modern karar girdi kutusuna operasyonel senaryosunu yazar (örn: *"Anonim IP'den dakikada 180 istek geliyor, bu istek engellensin mi?"*).
2. **Sistem-2 Derleme:** Gemini Flash, soruyu analiz ederek wevv'in anlayacağı parametrelere dönüştürür:
   - `state`: `{ user_role: "guest", req_frequency: 180, auth_status: false }`
   - `question`: `noul` (Boolean karar)
3. **Sistem-1 Refleksi (wevv):** wevv motoru tohum koordinatını sarsar, 4-Kuadran ($Q_1-Q_4$) kaçış dinamiklerini hesaplar ve milisaniyenin altında sonucu döndürür:
   - `decision: false` (İstek reddedildi)
   - `noul: 0.08`, `güven: %84`
   - `gecikme: 0.82 ms`, `VRAM: 0 Bayt`
4. **Telemetri HUD ve Yorum:** answerr arayüzünde karara ait canlı Mandelbrot kaçış kanvası, kuadran enerjileri ve Gemini'nin stratejik yorumu şık kartlar halinde görüntülenir.

---

## 🚀 Hızlı Başlangıç

### Yöntem 1: Basit Web Sunucusu ile Çalıştırma
```bash
cd answerr
python -m http.server 8080
```
Tarayıcınızda `http://localhost:8080` adresine gidin.

### Yöntem 2: FastAPI Sunucusu ile Çalıştırma
```bash
cd answerr
pip install -r requirements.txt
uvicorn server.main:app --reload --port 8000
```

---

## 🌐 Canlı Üretim REST API (Sıfır-VRAM Refleks Motoru)

Answerr, canlı sunucu üzerinde koşan, milisaniyenin altında kararlar üreten bir REST API servisi sunar:
* **API Ana Adresi:** `https://api.answerr.me:4431`

### 1. Sağlık ve Sıfır-VRAM Durumu
```bash
curl -k https://api.answerr.me:4431/v1/health
```
Yanıt:
```json
{
  "status": "healthy",
  "engine": "wevv-reflex",
  "version": "0.2.2",
  "vram_bytes": 0,
  "memory_architecture": "0 Byte VRAM / 24 Byte Mandelbrot Coordinate Triplet",
  "latency_benchmark_ms": 6.72
}
```

### 2. Anlık Refleks Kararı Alma (Tek Soru)
```bash
curl -k -X POST https://api.answerr.me:4431/v1/decide \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Yetkili API islemi onaylansin mi?",
    "state": {"user_role": "admin", "failed_attempts": 0, "req_frequency": 1.2}
  }'
```
Yanıt:
```json
{
  "status": "success",
  "decision": true,
  "label": "ALLOWED",
  "answers": {
    "primary_decision": {"type": "noul", "boolean": true, "noul": 0.9999, "confidence": 0.9998}
  },
  "telemetry": {
    "engine_latency_ms": 11.13,
    "vram_bytes": 0
  }
}
```

### 3. OpenAI Uyumlu Uç Nokta (/v1/chat/completions)
Answerr'ı LangChain, LlamaIndex veya OpenAI Python SDK'sına doğrudan bağlayabilirsiniz:
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.answerr.me:4431/v1",
    api_key="none"
)

response = client.chat.completions.create(
    model="wevv-reflex-v1",
    messages=[
        {"role": "user", "content": "Admin kullanici 0 hata ile istek yapti"}
    ]
)
print(response.choices[0].message.content)
```

---


## 🛡️ wevv ve answerr Temel Üstünlükleri

* **Sıfır Halüsinasyon (Zero Hallucination):** Geleneksel dil modelleri olasılıksal belirteç (token) örneklemesi yaptığı için uydurma üretir. `wevv`, deterministik Mandelbrot kaçış matematiği ile çalıştığından %100 tekrarlanabilir, tutarlı ve halüsinasyonsuz kararlar verir.
* **Asla Çökmez / Sıfır Hata (Zero Crash):** Dağılım dışı (OOD) ya da saldırı amaçlı prompt enjeksiyonlarında dahi kaotik rezonatör sinyali sönümler ve sistemi kilitlemeden geçerli tipli bir yanıt üretir.
* **Evrensel Kapsam (Universal State Coverage):** Her türlü operasyonel durum verisini (rakamlar, metinler, boolean bayraklar) anında modüle edip kesin çıktılara (`noul`, `choice`, `score`) dönüştürür.
* **Sıfır Bellek & Sıfır Maliyet (0 Byte VRAM):** Tensör ağırlığı taşımadığından dev GPU sunucularına ihtiyaç duymaz; doğrudan tarayıcıda veya en hafif işlemcide < 1 ms hızında çalışır.
* **Çekirdek Motor Reposu:** [https://github.com/pCwOrM/wevv](https://github.com/pCwOrM/wevv)

---

## 📄 Lisans

MIT Lisansı. Telif Hakkı (c) 2026 Volkan Dağlı / ITouch Systems.
