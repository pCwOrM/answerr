/**
 * landing.js - Controller for answerr Landing Page (answerr.me)
 * Manages multi-language (TR / EN) switching, interactive simulation toggle,
 * scenario presets switcher, code snippet tab switching, and smooth navigation.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Theme Persistence & Toggle
  const savedTheme = localStorage.getItem('answerr-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  const btnLandingTheme = document.getElementById('btn-landing-theme');
  if (btnLandingTheme) {
    btnLandingTheme.innerHTML = savedTheme === 'dark' ? '🌙' : '☀️';
    btnLandingTheme.addEventListener('click', () => {
      const curTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const nextTheme = curTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', nextTheme);
      localStorage.setItem('answerr-theme', nextTheme);
      btnLandingTheme.innerHTML = nextTheme === 'dark' ? '🌙' : '☀️';
    });
  }

  let currentLang = localStorage.getItem('answerr_pro_lang') || localStorage.getItem('answerr_lang') || 'tr';
  let activeScenario = 'ddos';

  const SCENARIOS = {
    ddos: {
      state: `{\n  "client_role": "guest",\n  "auth_valid": false,\n  "req_per_min": 180,\n  "target": "/api/v1/export"\n}`,
      code: `<span style="color:#f43f5e">if not</span> response.<span style="color:#38bdf8">boolean</span>(<span style="color:#10b981">"allow"</span>):\n    <span style="color:#38bdf8">QUARANTINE_IP</span>(request)\n<span style="color:#f43f5e">else</span>:\n    <span style="color:#38bdf8">EXECUTE_DIRECT</span>()`,
      icon: '🛡️',
      verdictClass: 'denied',
      status: {
        tr: 'GÜVENLİK ENGELİ (FALSE)',
        en: 'SECURITY BLOCKED (FALSE)'
      },
      confidence: {
        tr: '• p=0.0821 (Güven: %96)',
        en: '• p=0.0821 (Confidence: 96%)'
      },
      metrics: '⚡ 0.38 ms • 💾 0-Byte VRAM • 🔑 24B Seed'
    },
    flashloan: {
      state: `{\n  "pool": "UniswapV3_USDC_ETH",\n  "pool_depth_usd": 12450000,\n  "borrow_amount_usd": 4800000,\n  "price_impact_pct": 3.82,\n  "mempool_sandwiched": true\n}`,
      code: `<span style="color:#64748b">// Werracle Circuit Breaker (EVM Slot: 32B)</span>\n<span style="color:#f43f5e">if</span> (werracle.<span style="color:#38bdf8">evaluateReflex</span>(poolId) == ACTION_HALT) {\n    <span style="color:#f43f5e">revert</span> <span style="color:#38bdf8">FlashLoanManipulated</span>();\n}`,
      icon: '⚡',
      verdictClass: 'alert',
      status: {
        tr: 'CIRCUIT BREAKER: HALT (REVERT)',
        en: 'CIRCUIT BREAKER: HALT (REVERT)'
      },
      confidence: {
        tr: '• p=0.0142 (Kayma Riski: %99.4)',
        en: '• p=0.0142 (Slippage Risk: 99.4%)'
      },
      metrics: '⚡ 0.42 ms • ⛽ < 21k Gas • 📜 cs.CR:2609.30719'
    },
    flight: {
      state: `{\n  "organism": "Drosophila_158k",\n  "optic_flow_vector": [-0.84, 0.12],\n  "haltere_gyro_hz": 210,\n  "collision_threat_ms": 14.2\n}`,
      code: `<span style="color:#64748b"># FlyWire 158K Whole-Brain Connectome</span>\n<span style="color:#f43f5e">if</span> werrsoma.<span style="color:#38bdf8">reflex</span>(<span style="color:#10b981">"evade_predator"</span>):\n    wing_stroke_amplitude.<span style="color:#38bdf8">adjust</span>(left=+18.4, right=-6.2)`,
      icon: '🧬',
      verdictClass: 'allowed',
      status: {
        tr: 'SAKINMA MANEVRASI AKTİF (EVADE)',
        en: 'EVASIVE MANEUVER TRIGGERED'
      },
      confidence: {
        tr: '• p=0.9840 (Bio-Soma: %99.8)',
        en: '• p=0.9840 (Bio-Soma: 99.8%)'
      },
      metrics: '⚡ 0.19 ms • 🧠 158K Nöron • 📜 DOI:10.5281/23072929'
    }
  };

  const LANDING_I18N = {
    tr: {
      navProVault: "<span style='color:#06b6d4;'>PRO</span> Kasa &amp; Stüdyo",
      navFeatures: "Özellikler",
      navArchitecture: "4'lü Mimari",
      navPapers: "Yayınlar &amp; İspatlar",
      navDocs: "API Docs",
      navEcosystem: "Ekosistem",
      ddSomaDesc: "158K Nöron Biyonöromorfik Konnektom",
      ddWerracleDesc: "Blok-İçi Flash-Loan Devre Kesicisi",
      ddGauntletDesc: "Bare-Metal 27.8x Hız Doğrulaması",
      ddGithubTitle: "GitHub Depoları (answerr &amp; werr)",
      drwPlatformGroup: "Platform &amp; Karar",
      drwProStudio: "PRO Kasa &amp; Politika Stüdyosu",
      drwSomaLink: "WerrSoma 158K Canlı Portal",
      navLaunchApp: "Karar Motorunu Başlat",
      navLaunchAppMobile: "Karar Motoru",
      badgePill: "0-Byte VRAM • &lt; 0.5 ms Fraktal Refleks • Lean 4 Doğrulanmış (0 Sorry)",
      heroHeadline: "Sohbet Etme.<br>Karar Werr!",
      heroSubhead: "Yazılımlar, akıllı sözleşmeler, mikroservisler ve otonom sistemler için dünyanın ilk <strong>Sistem-1</strong> fraktal karar motoru. Deterministik Mandelbrot sınır dinamiğiyle mikrosaniyede tip-güvenli kararlar üretin; halüsinasyon riskini sıfırlayın.",
      heroCtaPrimary: "⚡ Hemen Başla (Ücretsiz & Keyless)",
      heroCtaConnectome: "🧬 WerrSoma 3D Canlı Portalı",
      heroCtaSecondary: "📦 pip install werr (GitHub)",
      ribbonTitle: "📜 Yayınlar ve Formel Doğrulama Teminatları:",
      simTabDDoS: "🛡️ API Güvenliği",
      simTabFlashloan: "⚡ DeFi Flash-Loan",
      simTabFlight: "🧬 Biyonöronal Uçuş",
      simInputTitle: "Gelen Sinyal (State Vector)",
      simSmartCodeTitle: "Akıllı Kod (Smart If-Statement)",
      simStatusDenied: "GÜVENLİK ENGELİ (FALSE)",
      featuresEyebrow: "Neden answerr?",
      featuresTitle: "Geleneksel LLM'lerin Bittiği Yerde Başlayan Refleks",
      featuresDesc: "Geleneksel dil modelleri yavaş, pahalı ve olasılıksaldır. answerr, mikrosaniye hızında kesin kararlar alırken doğal diyalog ve formel güvence sağlar.",
      p1Title: "&lt; 0.5 ms Fraktal Refleks",
      p1Text: "Mandelbrot kaçış dinamikleriyle mikrosaniyelik Sistem-1 omurilik refleksleri. Ağ gecikmesi olmadan yerel tarayıcıda, edge cihazlarda veya sunucuda anında çalışır.",
      p2Title: "0-Byte Tensör VRAM",
      p2Text: "Ağır GPU matris çarpmalarına, devasa model ağırlıklarına ve sunucu maliyetlerine son. 0-Byte tensör belleği ile mikrodenetleyicide veya akıllı sözleşmede bile çalışır.",
      p3Title: "Sıfır Halüsinasyon (Lean 4)",
      p3Text: "Olasılıksal tahminler yerine fraktal sınır geometrisi ve formal matematiksel ispatlar. Her durum vektörü için %100 tekrarlanabilir ve Lean 4 ile doğrulanmış kararlar.",
      p4Title: "Web3 Slot &amp; Biyo-Konnektom",
      p4Text: "Ethereum EVM akıllı sözleşmelerinde tek 32-bayt depolama slotuyla blok-içi flash-loan savunması ve Princeton FlyWire 158K Drosophila konnektom biyo-refleks entegrasyonu.",
      archEyebrow: "Egemen Mimari",
      archTitle: "4'lü Bilişsel Egemen Yığın (Quad-Cognitive Stack)",
      archDesc: "Mikrosaniyelik omurilik reflekslerinden on-chain DeFi güvenliğine ve 158 bin nöronluk biyonöromorfik konnektoma uzanan tam spektrum.",
      st1Badge: "SİSTEM-1: REFLEKS",
      st1Sub: "Deterministik Fraktal Omurilik Çekirdeği",
      st1Desc: "Mandelbrot sınır dinamikleri (&part;M) ile 0-Byte VRAM ve &lt; 0.5 ms icra. Olasılıksal tensörler yerine kesin geometrik karar bölgeleri.",
      st1Link: "GitHub Çekirdeği →",
      st2Badge: "SİSTEM-2: MÜZAKERE",
      st2Sub: "Bilişsel Durum Derleyicisi &amp; Çalışma Alanı",
      st2Desc: "Doğal dil senaryolarını yapılandırılmış durum vektörlerine dönüştürür. Gemini 2.5 Flash / Claude müzakeresini werr omurilik refleksiyle birleştirir.",
      st2Link: "Çalışma Alanına Gir →",
      st3Badge: "SİSTEM-WEB3: ZİNCİR-ÜSTÜ",
      st3Sub: "EVM 32-Bayt Slot &amp; Flash-Loan Kalkanı",
      st3Desc: "Ethereum ve EVM uyumlu blokzincirlerde tek bir 32-baytlık slotta (~20k gas) blok-içi milisaniye-altı yapay zekâ kararları ve MEV arbitraj savunması.",
      st3Link: "Web3 Simülatörü →",
      st4Badge: "SİSTEM-BİYO: KONNEKTOM",
      st4Sub: "158K Nöron Biyo-Sentetik Uçuş Refleks Yayı",
      st4Desc: "Princeton FlyWire Drosophila tüm-beyin konnektomunun (158.169 nöron, 3.99M sinaps) werr fraktal motoru ile in silico entegrasyonu. Sub-4ms biyo-refleks döngüsü.",
      st4Link: "3D Canlı Portal →",
      papersEyebrow: "Bilimsel Temeller",
      papersTitle: "Yayınlar ve Formel Lean 4 İspatları",
      papersDesc: "answerr ekosistemi spekülasyonlara değil, arXiv'de yayınlanmış ön-baskılara (hakem sürecinden geçmemiş) ve CERN Zenodo kayıtlarına dayanır.",
      pp1Desc: "werr motorunun temelini oluşturan fraktal karar haritası, Euler eşikleri ve sıfır-VRAM mikroservis karar mimarisi.",
      pp2Desc: "Mandelbrot sınır dinamiklerinin Lean 4 / Mathlib4 ortamında 0 sorry ile formel olarak doğrulanması ve 40 çekirdekli bare-metal telemetrisi.",
      pp3Desc: "Ethereum akıllı sözleşmelerinde blok-içi milisaniyelik karar icrası, 32-bayt slot mimarisi ve ZK-ML'e kıyasla 1000x hızlanma.",
      pp4Desc: "Yörünge hata dinamikleri, geçici parametre rezonansı ve fraktal nöron sentezinin teorik fizik ve karmaşık sistemler temeli.",
      pp5Desc: "GAP cebir sisteminin çekirdek algoritmalarının Lean 4'te makine onaylı doğrulanması (35 teorem, 0 sorry, 0 admit).",
      pp6Desc: "158.169 biyolojik nöron ve 3.99M sinapsın werr karar motoruyla birleşimi. Sub-4ms otonom uçuş kontrolü ve canlı 3D haritalama.",
      ppArxivAbs: "arXiv Özeti ↗",
      ppPdfBtn: "PDF İndir",
      ppPortalBtn: "Canlı 3D Portal",
      devEyebrow: "Entegrasyon",
      devTitle: "3 Satırda Üretime Hazır Refleks",
      devDesc: "Python, REST API veya EVM akıllı sözleşmeleriyle sisteminize saniyeler içinde ekleyin.",
      ctaHeadline: "Karmaşık LLM Gecikmelerine Veda Edin.",
      ctaSubhead: "answerr ile anında karar almaya başlayın. Kayıt gerekmez, tamamen ücretsiz ve anahtarsız mod aktiftir.",
      ctaButton: "Karar Çalışma Alanını Aç ⚡",
      footerCredits: "© 2026 answerr.me • ITouch Systems. Tüm hakları saklıdır. • <a href='mailto:ask@answerr.me' style='color:#38bdf8;text-decoration:none;'>ask@answerr.me</a>",
      footerWorkspace: "Karar Çalışma Alanı",
      footerApi: "API Docs &amp; Telemetri"
    },
    en: {
      navProVault: "<span style='color:#06b6d4;'>PRO</span> Vault &amp; Studio",
      navFeatures: "Features",
      navArchitecture: "4-Pillar Stack",
      navPapers: "Papers &amp; Proofs",
      navDocs: "API Docs",
      navEcosystem: "Ecosystem",
      ddSomaDesc: "158K Neuron Bioneuromorphic Connectome",
      ddWerracleDesc: "Intra-Block Flash-Loan Circuit Breaker",
      ddGauntletDesc: "Bare-Metal 27.8x Speed Validation",
      ddGithubTitle: "GitHub Repositories (answerr &amp; werr)",
      drwPlatformGroup: "Platform &amp; Decision",
      drwProStudio: "PRO Vault &amp; Policy Studio",
      drwSomaLink: "WerrSoma 158K Live Portal",
      navLaunchApp: "Launch Decision Engine",
      navLaunchAppMobile: "Decision Engine",
      badgePill: "0-Byte VRAM • &lt; 0.5 ms Fractal Reflex • Lean 4 Verified (0 Sorry)",
      heroHeadline: "Don't Just Chat.<br>Get The Answerr!",
      heroSubhead: "The world's first <strong>System-1</strong> fractal decision infrastructure for software, smart contracts, microservices, and autonomous systems. Generates typed, calibrated decisions with deterministic Mandelbrot boundary dynamics in microseconds. Zero hallucination.",
      heroCtaPrimary: "⚡ Start Now (100% Free & Keyless)",
      heroCtaConnectome: "🧬 WerrSoma 3D Live Portal",
      heroCtaSecondary: "📦 pip install werr (GitHub)",
      ribbonTitle: "📜 Published Papers & Formal Proof Assurances:",
      simTabDDoS: "🛡️ API Security",
      simTabFlashloan: "⚡ DeFi Flash-Loan",
      simTabFlight: "🧬 Bioneuronal Flight",
      simInputTitle: "Incoming Signal (State Vector)",
      simSmartCodeTitle: "Smart If-Statement (Production Code)",
      simStatusDenied: "SECURITY BLOCKED (FALSE)",
      featuresEyebrow: "Why answerr?",
      featuresTitle: "Reflex Decision Making Where Traditional LLMs Fall Short",
      featuresDesc: "LLMs are slow, expensive, and probabilistic. answerr delivers microsecond deterministic reflexes while maintaining rich dialogue and formal mathematical assurances.",
      p1Title: "&lt; 0.5 ms Fractal Reflex",
      p1Text: "Microsecond System-1 spinal reflexes calculated via Mandelbrot escape dynamics. Runs locally in your browser, edge devices, or cloud servers with zero network delay.",
      p2Title: "0-Byte Tensor VRAM",
      p2Text: "No massive GPU matrix multiplications or costly inference servers. Operates with 0-byte tensor memory, even on microcontrollers or EVM smart contracts.",
      p3Title: "Zero Hallucination (Lean 4)",
      p3Text: "Rooted in deterministic fractal boundary geometry rather than probabilistic tokens. 100% reproducible and formally machine-verified in Lean 4 for every state vector.",
      p4Title: "Web3 Slot &amp; Bio-Connectome",
      p4Text: "Intra-block flash-loan defense in a single 32-byte Ethereum EVM storage slot and bio-reflex integration with the Princeton FlyWire 158K Drosophila connectome.",
      archEyebrow: "Sovereign Architecture",
      archTitle: "The Quad-Cognitive Sovereign Stack",
      archDesc: "From microsecond spinal reflexes to on-chain DeFi circuit breakers and 158K-neuron neuromorphic connectomes.",
      st1Badge: "SYSTEM-1: REFLEX",
      st1Sub: "Deterministic Fractal Spinal Kernel",
      st1Desc: "0-Byte VRAM and &lt; 0.5 ms execution via Mandelbrot boundary dynamics (&part;M). Exact geometric decision regions instead of probabilistic tensors.",
      st1Link: "GitHub Kernel →",
      st2Badge: "SYSTEM-2: DELIBERATION",
      st2Sub: "Cognitive State Compiler &amp; Workspace",
      st2Desc: "Compiles natural language scenarios into structured state vectors. Bridges Gemini 2.5 Flash / Claude deliberation with the werr spinal reflex.",
      st2Link: "Enter Workspace →",
      st3Badge: "SYSTEM-WEB3: ON-CHAIN",
      st3Sub: "EVM 32-Byte Slot &amp; Flash-Loan Shield",
      st3Desc: "Sub-millisecond intra-block AI decisions and MEV arbitrage defense inside a single 32-byte slot (~20k gas) on Ethereum and EVM chains.",
      st3Link: "Web3 Simulator →",
      st4Badge: "SYSTEM-BIO: CONNECTOME",
      st4Sub: "158K Neuron Bio-Synthetic Flight Reflex Arc",
      st4Desc: "In silico integration of the Princeton FlyWire Drosophila whole-brain connectome (158,169 neurons, 3.99M synapses) with the werr fractal engine. Sub-4ms bio-reflex loop.",
      st4Link: "3D Live Portal →",
      papersEyebrow: "Scientific Foundations",
      papersTitle: "Published Papers & Formal Lean 4 Proofs",
      papersDesc: "The answerr ecosystem is grounded in peer-accessible preprints (arXiv, SSRN) and permanent CERN Zenodo open-science records.",
      pp1Desc: "The foundational fractal decision map of the werr engine, Euler thresholds, and zero-VRAM microservice decision architecture.",
      pp2Desc: "Formal verification of Mandelbrot boundary dynamics in Lean 4 / Mathlib4 with 0 sorry and 40-core bare-metal gauntlet telemetry.",
      pp3Desc: "Intra-block millisecond decision execution in Ethereum smart contracts, 32-byte slot architecture, and 1000x speedup over ZK-ML.",
      pp4Desc: "Theoretical physics and complex systems foundations of orbital error dynamics, ephemeral parameter resonance, and fractal neural synthesis.",
      pp5Desc: "Machine-checked formal verification of core GAP computational group theory algorithms in Lean 4 (35 theorems, 0 sorry, 0 admit).",
      pp6Desc: "Integration of 158,169 biological neurons and 3.99M synapses with the werr decision engine. Sub-4ms autonomous flight control and live 3D mapping.",
      ppArxivAbs: "arXiv Abstract ↗",
      ppPdfBtn: "Download PDF",
      ppPortalBtn: "Live 3D Portal",
      devEyebrow: "Integration",
      devTitle: "Production-Ready in 3 Lines of Code",
      devDesc: "Seamlessly integrate via Python, REST API, or EVM smart contracts in seconds.",
      ctaHeadline: "Say Goodbye to Sluggish LLM Latencies.",
      ctaSubhead: "Start making instant, typed decisions with answerr right now. No sign-up, no API key required.",
      ctaButton: "Open Decision Workspace ⚡",
      footerCredits: "© 2026 answerr.me • ITouch Systems. All rights reserved. • <a href='mailto:ask@answerr.me' style='color:#38bdf8;text-decoration:none;'>ask@answerr.me</a>",
      footerWorkspace: "Decision Workspace",
      footerApi: "API Docs &amp; Telemetry"
    }
  };

  // Language Elements Binding
  const btnLangToggleEl = document.getElementById('btn-landing-lang');
  const currentLangTextEl = document.getElementById('landing-lang-text');

  function renderScenario(scenarioKey) {
    activeScenario = scenarioKey;
    const s = SCENARIOS[scenarioKey] || SCENARIOS.ddos;
    const stateEl = document.getElementById('sim-code-state');
    const codeEl = document.getElementById('sim-code-statement');
    const badgeEl = document.getElementById('sim-verdict-badge');
    const iconEl = document.getElementById('sim-verdict-icon');
    const textEl = document.getElementById('sim-verdict-text');
    const confEl = document.getElementById('sim-verdict-confidence');
    const metricEl = document.getElementById('sim-metric-latency');

    if (stateEl) stateEl.textContent = s.state;
    if (codeEl) codeEl.innerHTML = s.code;
    if (iconEl) iconEl.textContent = s.icon;
    if (textEl) textEl.textContent = s.status[currentLang] || s.status.tr;
    if (confEl) confEl.textContent = s.confidence[currentLang] || s.confidence.tr;
    if (metricEl) metricEl.parentElement.innerHTML = s.metrics;

    if (badgeEl) {
      badgeEl.classList.remove('denied', 'alert', 'allowed');
      if (s.verdictClass === 'alert') {
        badgeEl.style.borderColor = 'rgba(245, 158, 11, 0.4)';
        badgeEl.style.background = 'rgba(245, 158, 11, 0.12)';
        badgeEl.style.color = '#f59e0b';
      } else if (s.verdictClass === 'allowed') {
        badgeEl.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        badgeEl.style.background = 'rgba(16, 185, 129, 0.12)';
        badgeEl.style.color = '#10b981';
      } else {
        badgeEl.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        badgeEl.style.background = 'rgba(239, 68, 68, 0.12)';
        badgeEl.style.color = '#ef4444';
      }
    }
  }

  // Setup Scenario Selector Buttons
  const scenarioButtons = document.querySelectorAll('.sim-scenario-selector .sim-tab');
  scenarioButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      scenarioButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const sc = btn.getAttribute('data-scenario');
      renderScenario(sc);
    });
  });

  function applyLanguage(lang) {
    currentLang = lang;
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

    // Re-render active scenario text in new language
    renderScenario(activeScenario);
  }

  if (btnLangToggleEl) {
    btnLangToggleEl.addEventListener('click', () => {
      currentLang = currentLang === 'tr' ? 'en' : 'tr';
      localStorage.setItem('answerr_lang', currentLang);
      localStorage.setItem('answerr_pro_lang', currentLang);
      applyLanguage(currentLang);
    });
  }

  // Initialize Language & Scenario
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
  const codeSnippetSolidity = document.getElementById('snippet-solidity');

  codeTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      codeTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const lang = tab.getAttribute('data-tab');
      if (codeSnippetPython) codeSnippetPython.style.display = lang === 'python' ? 'block' : 'none';
      if (codeSnippetCurl) codeSnippetCurl.style.display = lang === 'curl' ? 'block' : 'none';
      if (codeSnippetSolidity) codeSnippetSolidity.style.display = lang === 'solidity' ? 'block' : 'none';
    });
  });

  // Mobile Navigation Drawer Toggle & Backdrop
  const btnMobileMenu = document.getElementById('btn-mobile-menu');
  const btnCloseDrawer = document.getElementById('btn-close-drawer');
  const mobileNavDrawer = document.getElementById('mobile-nav-drawer');
  const mobileDrawerBackdrop = document.getElementById('mobile-drawer-backdrop');

  function openMobileDrawer() {
    if (mobileNavDrawer) mobileNavDrawer.classList.add('open');
    if (mobileDrawerBackdrop) mobileDrawerBackdrop.classList.add('open');
    if (btnMobileMenu) {
      btnMobileMenu.classList.add('open');
      btnMobileMenu.setAttribute('aria-expanded', 'true');
    }
    document.body.style.overflow = 'hidden';
  }

  function closeMobileDrawer() {
    if (mobileNavDrawer) mobileNavDrawer.classList.remove('open');
    if (mobileDrawerBackdrop) mobileDrawerBackdrop.classList.remove('open');
    if (btnMobileMenu) {
      btnMobileMenu.classList.remove('open');
      btnMobileMenu.setAttribute('aria-expanded', 'false');
    }
    document.body.style.overflow = '';
  }

  if (btnMobileMenu) {
    btnMobileMenu.addEventListener('click', (e) => {
      e.stopPropagation();
      if (mobileNavDrawer && mobileNavDrawer.classList.contains('open')) {
        closeMobileDrawer();
      } else {
        openMobileDrawer();
      }
    });
  }
  if (btnCloseDrawer) btnCloseDrawer.addEventListener('click', closeMobileDrawer);
  if (mobileDrawerBackdrop) mobileDrawerBackdrop.addEventListener('click', closeMobileDrawer);

  document.querySelectorAll('[data-nav-close]').forEach(link => {
    link.addEventListener('click', closeMobileDrawer);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeMobileDrawer();
    }
  });
});
