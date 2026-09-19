# 🔮 answerr: Çift-Bilişsel Yapay Zeka Karar Chatbotu

[![Canlı Demo: GitHub Pages](https://img.shields.io/badge/Canl%C4%B1%20Demo-GitHub%20Pages-38bdf8.svg)](https://pcworm.github.io/answerr/)
[![Web Sitesi: answerr.me](https://img.shields.io/badge/Alan%20Ad%C4%B1-answerr.me-818cf8.svg)](https://answerr.me)
[![wevv Çekirdek Motoru](https://img.shields.io/badge/wevv-S%C4%B1f%C4%B1r--Bellek%20Motoru-10b981.svg)](https://github.com/pCwOrM/wevv)
[![Gemini 2.5 Flash](https://img.shields.io/badge/Sistem--2-Gemini%20Flash-c084fc.svg)](https://deepmind.google/technologies/gemini/)
[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-yellow.svg)](./LICENSE)

> **Gemini düşünür; wevv sıfır-bellek fraktal geometrisiyle anında karar verir.**  
> *"Yapılandırılmamış doğal dil sorularını, 0 bayt tensör ağırlığıyla milisaniyenin altında tipli kararlara dönüştürür."*

🌐 **Canlı Demo (GitHub Pages):** [https://pcworm.github.io/answerr/](https://pcworm.github.io/answerr/)  
🌐 **Özel Alan Adı:** [https://answerr.me](https://answerr.me)

---

## 🌟 Genel Bakış

**answerr**, iki temel bilişsel düzeyi birleştiren yeni nesil bir yapay zeka karar arayüzüdür:
1. **Sistem-2 Müzakeresi (Google Gemini Flash):** Kullanıcının serbest metin olarak sorduğu karmaşık senaryoyu dinler, arka plandaki operasyonel durum vektörünü (`state`) ve karar tipini çıkarır; ardından nihai matematiksel kararı anlaşılır bir dille yorumlayıp aksiyon önerir.
2. **Sistem-1 Omurilik Refleksi ([wevv](https://github.com/pCwOrM/wevv)):** Mandelbrot fraktal sınırındaki 24 baytlık $(c_x, c_y, \text{zoom})$ koordinat tohumunu dinamik olarak modüle eder ve **0 Byte VRAM / tensör ağırlığı** ile **< 1 ms** içinde kesin tipli kararları (`noul`, `choice`, `score`) üretir.

Böylece basit bir onay veya mikroservis yönlendirmesi için devasa modellerin gigabaytlarca VRAM tüketmesi ve yüzlerce milisaniye beklemesi gerekmez; triyaj kararı doğrudan evrensel geometriden türer.

---

## ⚡ Bilişsel Mimari ve Akış

1. **Soru Girişi:** Kullanıcı sayfanın ortasındaki ChatGPT / Gemini benzeri modern sohbet kutusuna senaryosunu yazar (örn: *"Anonim IP'den dakikada 180 istek geliyor, bu istek engellensin mi?"*).
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

## 🧪 Bilimsel Temel

* **Temel Makale:** *"Universal Fractal Natural Language Decision Map: Real-Time Edge Triage Across Heterogeneous Domains"* (Dağlı vd., Eylül 2026).
* **Teori:** *"Mandelbrot Fractal Neural Synthesis"* (IEEE / Zenodo DOI: [10.5281/zenodo.22802921](https://doi.org/10.5281/zenodo.22802921)).
* **wevv Motoru:** [https://github.com/pCwOrM/wevv](https://github.com/pCwOrM/wevv).

---

## 📄 Lisans

MIT Lisansı. Telif Hakkı (c) 2026 Volkan Dağlı / ITouch Systems.
