/**
 * landing.js - Controller for answerr Landing Page (answerr.me)
 * Manages multi-language (TR / EN) switching, interactive simulation toggle,
 * code snippet tab switching, and smooth navigation.
 */

document.addEventListener('DOMContentLoaded', () => {
  let currentLang = localStorage.getItem('answerr_lang') || 'tr';

  const LANDING_I18N = {
    tr: {
      navFeatures: "Özellikler",
      navEcosystem: "İkiz Ekosistem",
      navDeveloper: "Geliştirici",
      navLaunchApp: "Karar Motorunu Başlat",
      navLaunchAppMobile: "Karar Motoru",
      badgePill: "0-Byte VRAM • < 0.5 ms Fraktal Omurilik Refleksi",
      heroHeadline: "Sadece Sohbet Etme.<br>Karar Werr!",
      heroSubhead: "Yazılımlar, API'lar ve otonom sistemler için dünyanın ilk <strong>Sistem-1</strong> fraktal karar motoru. Deterministik Mandelbrot sınır dinamiğiyle mikrosaniyede tip-güvenli kararlar üretin; halüsinasyon riskini sıfırlayın.",
      heroCtaPrimary: "⚡ Hemen Başla (Ücretsiz & Keyless)",
      heroCtaSecondary: "📦 pip install werr (GitHub)",
      simInputTitle: "Gelen Sinyal (State Vector)",
      simVerdictTitle: "werr Sistem-1 Refleksi",
      simSmartCodeTitle: "Akıllı Kod (Smart If-Statement)",
      simStatusAllowed: "İSTEK ONAYLANDI (TRUE)",
      simStatusDenied: "GÜVENLİK ENGELİ (FALSE)",
      simConfidenceText: "• p=0.0821 (Güven: %96)",
      featuresEyebrow: "Neden answerr?",
      featuresTitle: "Geleneksel LLM'lerin Bittiği Yerde Başlayan Refleks",
      featuresDesc: "Geleneksel dil modelleri yavaş, pahalı ve olasılıksaldır. answerr & werr ikilisi, refleks hızında kesin kararlar alırken doğal diyalog gücünü korur.",
      p1Title: "< 0.5 ms Fraktal Refleks",
      p1Text: "Mandelbrot kaçış dinamikleriyle mikrosaniyelik Sistem-1 omurilik refleksleri. Ağ gecikmesi olmadan yerel tarayıcıda veya sunucuda anında çalışır.",
      p2Title: "0-Byte Tensör VRAM",
      p2Text: "Ağır GPU matris çarpmalarına, devasa model ağırlıklarına ve sunucu maliyetlerine son. 0-Byte tensör belleği ile mikrodenetleyicide bile çalışır.",
      p3Title: "Sıfır Halüsinasyon",
      p3Text: "Olasılıksal tahminler yerine fraktal sınır geometrisi kullanır. Her durum vektörü için %100 tekrarlanabilir, matematiksel olarak kanıtlanabilir kararlar.",
      ecoEyebrow: "Mimari",
      ecoTitle: "answerr & werr İkiz Ekosistemi",
      ecoDesc: "Doğal diyalog gerektiğinde answerr, mikrosaniyelik refleks gerektiğinde werr.",
      ecoSideAnswerrTitle: "answerr (Bulut & Web Platformu)",
      ecoSideAnswerrText: "Sistem-2 müzakereci yapay zeka, Google Gemini Flash entegrasyonu, web çalışma alanı ve kurumsal API ağ geçidi.",
      ecoSideWerrTitle: "werr (Spinal Reflex Core)",
      ecoSideWerrText: "Sistem-1 deterministik omurilik çekirdeği. Sıfır tensör belleği, Mandelbrot fraktal karar motoru. Uygulamanıza gömün (pip install werr).",
      ecoBtnWorkspace: "Çalışma Alanına Git →",
      ecoBtnGithub: "GitHub'da İncele →",
      devEyebrow: "Entegrasyon",
      devTitle: "3 Satırda Üretime Hazır Refleks",
      devDesc: "Python veya doğrudan REST API ile sisteminize saniyeler içinde ekleyin.",
      ctaHeadline: "Karmaşık LLM Gecikmelerine Veda Edin.",
      ctaSubhead: "answerr ile anında karar almaya başlayın. Kayıt gerekmez, tamamen ücretsiz ve anahtarsız mod aktiftir.",
      ctaButton: "Karar Çalışma Alanını Aç ⚡",
      footerCredits: "© 2026 answerr.me • Volkan Dağlı tarafından geliştirildi. Tüm hakları saklıdır.",
      footerWorkspace: "Karar Çalışma Alanı",
      footerApi: "API & Telemetri"
    },
    en: {
      navFeatures: "Features",
      navEcosystem: "Twin Ecosystem",
      navDeveloper: "Developers",
      navLaunchApp: "Launch Decision Engine",
      navLaunchAppMobile: "Decision Engine",
      badgePill: "0-Byte VRAM • < 0.5 ms Fractal Spinal Reflex",
      heroHeadline: "Don't Just Chat.<br>Get The Answerr!",
      heroSubhead: "The world's first <strong>System-1</strong> fractal decision infrastructure for software, APIs, and autonomous systems. Generates typed, calibrated decisions with deterministic Mandelbrot boundary dynamics in microseconds. Zero hallucination.",
      heroCtaPrimary: "⚡ Start Now (100% Free & Keyless)",
      heroCtaSecondary: "📦 pip install werr (GitHub)",
      simInputTitle: "Incoming Signal (State Vector)",
      simVerdictTitle: "werr System-1 Reflex",
      simSmartCodeTitle: "Smart If-Statement (Production Code)",
      simStatusAllowed: "REQUEST APPROVED (TRUE)",
      simStatusDenied: "SECURITY BLOCKED (FALSE)",
      simConfidenceText: "• p=0.0821 (Confidence: 96%)",
      featuresEyebrow: "Why answerr?",
      featuresTitle: "Reflex Decision Making Where Traditional LLMs Fall Short",
      featuresDesc: "LLMs are slow, expensive, and probabilistic. answerr & werr combine microsecond deterministic reflexes with deliberative dialogue.",
      p1Title: "< 0.5 ms Fractal Reflex",
      p1Text: "Microsecond System-1 spinal reflexes calculated via Mandelbrot escape dynamics. Runs locally in your browser or edge microservices with zero cloud latency.",
      p2Title: "0-Byte Tensor VRAM",
      p2Text: "No massive GPU matrix multiplications or expensive cloud inference instances. Operates with 0-byte tensor memory, even on microcontrollers.",
      p3Title: "Zero Hallucination",
      p3Text: "Rooted in deterministic fractal boundary physics instead of probabilistic tokens. 100% reproducible and verifiable for every state vector.",
      ecoEyebrow: "Architecture",
      ecoTitle: "answerr & werr Twin Ecosystem",
      ecoDesc: "When you need natural dialogue, call answerr. When you need microsecond reflexes, embed werr.",
      ecoSideAnswerrTitle: "answerr (Cloud & Web Platform)",
      ecoSideAnswerrText: "System-2 deliberative reasoning, Google Gemini Flash integration, interactive web workspace, and enterprise API gateway.",
      ecoSideWerrTitle: "werr (Spinal Reflex Core)",
      ecoSideWerrText: "System-1 deterministic spinal kernel. Zero tensor memory, Mandelbrot fractal decision engine. Embed directly (pip install werr).",
      ecoBtnWorkspace: "Open Workspace →",
      ecoBtnGithub: "Explore on GitHub →",
      devEyebrow: "Integration",
      devTitle: "Production-Ready in 3 Lines of Code",
      devDesc: "Seamlessly integrate via Python or direct REST API in seconds.",
      ctaHeadline: "Say Goodbye to Sluggish LLM Latencies.",
      ctaSubhead: "Start making instant, typed decisions with answerr right now. No sign-up, no API key required.",
      ctaButton: "Open Decision Workspace ⚡",
      footerCredits: "© 2026 answerr.me • Crafted by Volkan Dağlı. All rights reserved.",
      footerWorkspace: "Decision Workspace",
      footerApi: "API & Telemetry"
    }
  };

  // Language Elements Binding
  const btnLangToggleEl = document.getElementById('btn-landing-lang');
  const currentLangTextEl = document.getElementById('landing-lang-text');

  function applyLanguage(lang) {
    const t = LANDING_I18N[lang] || LANDING_I18N.tr;
    document.documentElement.lang = lang;
    document.title = lang === 'tr' 
      ? "answerr | Sıfır Gecikmeli Refleks Yapay Zekası (answerr.me)" 
      : "answerr | The Zero-Latency Reflex AI (answerr.me)";
    if (currentLangTextEl) currentLangTextEl.textContent = lang.toUpperCase();

    // Text bindings by data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (t[key]) {
        el.innerHTML = t[key];
      }
    });
  }

  if (btnLangToggleEl) {
    btnLangToggleEl.addEventListener('click', () => {
      currentLang = currentLang === 'tr' ? 'en' : 'tr';
      localStorage.setItem('answerr_lang', currentLang);
      applyLanguage(currentLang);
    });
  }

  // Initialize Language
  applyLanguage(currentLang);

  // Smooth Scrolling for Anchor Links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#' || !targetId) return;
      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Code Snippet Tabs
  const codeTabs = document.querySelectorAll('.code-tab');
  const codeSnippetPython = document.getElementById('snippet-python');
  const codeSnippetCurl = document.getElementById('snippet-curl');

  codeTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      codeTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const lang = tab.getAttribute('data-tab');
      if (lang === 'python') {
        if (codeSnippetPython) codeSnippetPython.style.display = 'block';
        if (codeSnippetCurl) codeSnippetCurl.style.display = 'none';
      } else {
        if (codeSnippetPython) codeSnippetPython.style.display = 'none';
        if (codeSnippetCurl) codeSnippetCurl.style.display = 'block';
      }
    });
  });
});
