# ⚡ A.N.S.W.E.R.R. — Sıfır-Gecikmeli Refleks Yapay Zekası

[![Canlı Demo: GitHub Pages](https://img.shields.io/badge/Canl%C4%B1%20Demo-GitHub%20Pages-38bdf8.svg)](https://pcworm.github.io/answerr/)
[![Web Sitesi: answerr.me](https://img.shields.io/badge/Alan%20Ad%C4%B1-answerr.me-818cf8.svg)](https://answerr.me)
[![wevv Çekirdek Motoru](https://img.shields.io/badge/wevv-S%C4%B1f%C4%B1r--Bellek%20Motoru-10b981.svg)](https://github.com/pCwOrM/wevv)
[![Müzakereci Yapay Zeka](https://img.shields.io/badge/Sistem--2-M%C3%BCzakereci%20YZ-c084fc.svg)](https://answerr.me)
[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-yellow.svg)](./LICENSE)

> **A**daptive **N**ext-gen **S**ignal **W**ave & **E**rror **R**eflex **R**easoner  
> *"Don't just chat. Get the Answerr. Sadece sohbet etmeyin; milisaniyenin altında 0-byte VRAM ile kesin kararı alın."*

🌐 **Canlı Demo (GitHub Pages):** [https://pcworm.github.io/answerr/](https://pcworm.github.io/answerr/)  
🌐 **Özel Alan Adı:** [https://answerr.me](https://answerr.me)

---

## 🌟 Genel Bakış

**A.N.S.W.E.R.R.**, iki temel bilişsel düzeyi birleştiren yeni nesil bir karar motorudur:
1. **Sistem-2 Müzakeresi (LLM / Müzakereci Yapay Zeka):** Karmaşık insan dilini ve durum parametrelerini anlar, operasyonel bağlamı çıkarır ve kararı stratejik olarak açıklar (Bulut API'leri veya yerel açık kaynak modellerle tam uyumlu).
2. **Sistem-1 Omurilik Refleksi ([wevv](https://github.com/pCwOrM/wevv)):** Mandelbrot fraktal sınırındaki 24 baytlık $(c_x, c_y, \text{zoom})$ koordinat tohumunu dinamik olarak modüle eder ve **0 Byte VRAM** ile **< 1 ms** içinde kesin tipli kararları (`noul`, `choice`, `score`) üretir.

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

## 🛡️ wevv ve answerr Temel Üstünlükleri

* **Sıfır Halüsinasyon (Zero Hallucination):** Geleneksel dil modelleri olasılıksal belirteç (token) örneklemesi yaptığı için uydurma üretir. `wevv`, deterministik Mandelbrot kaçış matematiği ile çalıştığından %100 tekrarlanabilir, tutarlı ve halüsinasyonsuz kararlar verir.
* **Asla Çökmez / Sıfır Hata (Zero Crash):** Dağılım dışı (OOD) ya da saldırı amaçlı prompt enjeksiyonlarında dahi kaotik rezonatör sinyali sönümler ve sistemi kilitlemeden geçerli tipli bir yanıt üretir.
* **Evrensel Kapsam (Universal State Coverage):** Her türlü operasyonel durum verisini (rakamlar, metinler, boolean bayraklar) anında modüle edip kesin çıktılara (`noul`, `choice`, `score`) dönüştürür.
* **Sıfır Bellek & Sıfır Maliyet (0 Byte VRAM):** Tensör ağırlığı taşımadığından dev GPU sunucularına ihtiyaç duymaz; doğrudan tarayıcıda veya en hafif işlemcide < 1 ms hızında çalışır.
* **Çekirdek Motor Reposu:** [https://github.com/pCwOrM/wevv](https://github.com/pCwOrM/wevv)

---

## 📄 Lisans

MIT Lisansı. Telif Hakkı (c) 2026 Volkan Dağlı / ITouch Systems.
