/**
 * answerr.me/pro — WERR-24B™ Cybernetic Sovereign i18n Engine
 * Complete Bilingual (Turkish & English) Translation Dictionary & Controller
 * Official Corporate Architecture by ITouch Bilişim Sistemleri Ltd. Şti.
 */

(function () {
  const I18N_DICT = {
    tr: {
      // Top Ribbon
      ribbonCorp: "Resmi Kurumsal Ürün: <a href=\"https://itouch.com.tr\" target=\"_blank\" rel=\"noopener\" class=\"corp-link\">ITouch Bilişim Sistemleri Ltd. Şti.</a> (Çukurova Teknokent)",
      ribbonVault: "Kasa: <strong style=\"color:var(--emerald-bright)\">WERR-24B™ EGEMEN ÇEKİRDEK</strong>",
      ribbonApi: "API: <strong style=\"color:var(--cyan-bright)\">api.answerr.me (:443)</strong>",
      ribbonStatus: "DURUM: AKTİF • SIFIR VRAM",

      // Nav
      brandTag: "WERR-24B™ KASA",
      navProduct: "Ürün & Canlı Kasa",
      navStudio: "Politika Stüdyosu",
      navResearch: "arXiv, HuggingFace & Patentler",
      navApi: "REST API (/docs)",
      navClassic: "Klasik Konsol",
      btnSealPolicy: "Politika Mühürle →",
      btnCorpContact: "ITouch Bilişim",

      // Hero
      heroEyebrow: "🔒 PATENTLİ WERR-24B™ ÇEKİRDEĞİ • SİSTEM-2 DERLER, SİSTEM-1 MİKROSANİYEDE İNFAZ EDER",
      heroTitle: "Milyarlarca Parametre Değil.<br /><span class=\"grad\">24 Baytlık Mühürlü Kesinlik.</span>",
      heroLead: "Kurumsal kurallarınızı doğal dilde yazın; <strong>answerr</strong> bunları <strong>ITouch Bilişim</strong>'in patentli <strong>WERR-24B™ Sınır Rezonansı</strong> ile yalnızca <strong>24 Baytlık şifreli bir karara</strong> kristalleştirsin. GPU yok, ağırlık dosyası yok, çalışma anında halüsinasyon yok — her ortamda <strong>&lt; 0.5 ms</strong> içinde kriptografik denetim iziyle kesin karar.",
      heroBtnStudio: "✨ Doğal Dilden 24B Politika Mühürle",
      heroBtnSandbox: "🛡️ Canlı Kasa Testi (Sandbox)",
      heroBtnResearch: "📄 5 arXiv Makalesi & HuggingFace",

      // Metrics
      metric1Val: "< 0.5 ms",
      metric1Label: "Omurilik Refleksi Gecikmesi (Çalışma Anında LLM Yok)",
      metric2Val: "0-Byte VRAM",
      metric2Label: "GPU & Tensör Ağırlığı Yok • 24-Bayt Mühürlü Tohum",
      metric3Val: "SHA-256 Seal",
      metric3Label: "Değiştirilemez Kriptografik Politika Mührü & Denetim İzi",
      metric4Val: "ABSTAIN_REVIEW",
      metric4Label: "Tanınmayan Şema (OOD) Kalkanı — Sıfır Kör Tahmin",

      // Vault Secret Formula Callout
      vaultCalloutTitle: "🧪 \"Sihri Göster, Formülü Kasada Mühürle\" — WERR-24B™ Kara Kutu Güvencesi",
      vaultCalloutDesc: "Tıpkı gizli bir endüstriyel formül gibi, <strong>WERR-24B™</strong> çekirdeğinin içsel sınır matematiği ve çok ölçekli rezonans katsayıları <strong>ITouch Bilişim</strong> kasasında (TR 2026/016285 & TR 2026/016633) korunur. Sisteminize yalnızca <strong>mikrosaniyelik deterministik karar</strong>, <strong>SHA-256 denetim mührü</strong> ve <strong>OOD güvenlik kalkanı</strong> döner.",
      vaultStampStatus: "FORMÜL DURUMU",
      vaultStampLocked: "🔒 KASADA MÜHÜRLÜ 24B",
      vaultStampPatent: "TÜRKPATENT KORUMALI",

      // Sandbox
      sandboxTag: "CANLI KURUMSAL KARAR KASASI (INTERACTIVE SANDBOX)",
      sandboxTitle: "Milisaniye Altı Refleksi ve OOD Kalkanını Canlı Deneyin",
      sandboxDesc: "Aşağıdaki 4 kurumsal kapıdan birini seçin veya JSON verisini değiştirin. Kasa, içsel formülü ifşa etmeden kriptografik karar mührünü ve sorumluluk kalkanını (ABSTAIN_REVIEW) canlı üretir.",
      step1Title: "1. Kurumsal Koruma Kapısı Seçin",
      step2Title: "2. Operasyonel Sinyal Paketi (JSON)",
      btnQueryVault: "⚡ Kasaya Sor",
      step3Title: "3. Mühürlü Karar & Kurumsal Denetim Özeti",
      oscTitle: "TRIPOD REZONANS DALGA HUD (0.60x • 1.00x • 1.60x)",
      oscLive: "CANLI REZONANS AKTİF",
      publicEnvelopeTitle: "Mühürlü Denetim Çıktısı (Public Audit Envelope):",

      // Gate Tabs
      tabAgentBlockTitle: "🛡️ AI Ajan / MCP Korkuluğu (Blok)",
      tabAgentBlockSub: "Yıkıcı SQL & Yüksek Tutar",
      tabAgentSafeTitle: "✅ AI Ajan / MCP Korkuluğu (Onay)",
      tabAgentSafeSub: "Salt-Okunur Güvenli Araç",
      tabFintechTitle: "💳 TR Fintech & Fraud Kapısı",
      tabFintechSub: "Kart Hızı & Anomali (KVKK)",
      tabOodTitle: "⚠️ Şema Dışı (OOD) Kalkanı",
      tabOodSub: "Tanınmayan Veri → ABSTAIN_REVIEW",

      // Trace Labels
      trPolicyKey: "Aktif Politika Kapısı:",
      trSealKey: "Kriptografik Mühür:",
      trRulesKey: "Karar Gerekçesi:",
      trFieldsKey: "Şema Doğrulaması:",
      trSeedKey: "24-Bayt Çekirdek:",

      // Pricing Section
      pricingTag: "KURUMSAL LİSANSLAMA — ITOUCH BİLİŞİM SİSTEMLERİ LTD. ŞTİ.",
      pricingTitle: "Geliştirici Çekirdeğinden Egemen Kurumsal Kasaya",
      pricingDesc: "<strong>answerr.me</strong>, Çukurova Teknokent bünyesindeki <strong>ITouch Bilişim Sistemleri Mühendislik Danışmanlık San. ve Tic. Ltd. Şti.</strong> tarafından geliştirilmekte ve BSL 1.1 ticari lisansıyla sunulmaktadır.",
      tier1Badge: "DEVELOPER RUNTIME",
      tier1Title: "werr Open SDK",
      tier1Price: "Ücretsiz",
      tier1Sub: "Akademik araştırma, değerlendirme ve hızlı prototipleme",
      tier1F1: "<code>pip install werr</code> & Tarayıcı SDK",
      tier1F2: "<code>noul</code>, <code>choice</code>, <code>score</code> karar tipleri",
      tier1F3: "0-Byte VRAM yerel refleks çalışma zamanı",
      tier1F4: "OOD <code>ABSTAIN_REVIEW</code> şema koruması",
      tier1Btn: "pip install werr",

      tier2Badge: "KURUMSAL BULUT KAPISI",
      tier2Title: "answerr Pro & Agent Gate",
      tier2Price: "$149 <span style=\"font-size:14px; font-weight:500; color:var(--text-muted)\">/ ay</span>",
      tier2Sub: "Fintech, E-Ticaret, SaaS ve AI Ajan (MCP) ekipleri",
      tier2F1: "<strong>Doğal Dilden 24B Politika Stüdyosu</strong>",
      tier2F2: "Özel Mühürlü Kapılar (<code>/v1/gates/{id}/decide</code>)",
      tier2F3: "SHA-256 Kriptografik Denetim İzi",
      tier2F4: "AI Ajan MCP & TR E-Ticaret Fraud Kalkanları",
      tier2F5: "Aylık 5 Milyon Milisaniye Altı Karar",
      tier2Btn: "Politika Stüdyosunda Başla →",

      tier3Badge: "ON-PREMISE & SOVEREIGN",
      tier3Title: "answerr Sovereign Vault",
      tier3Price: "Kurumsal Lisans",
      tier3Sub: "Bankacılık, Savunma, Siber Güvenlik ve Kritik Altyapılar",
      tier3F1: "<strong>ITouch Bilişim BSL 1.1 Ticari Üretim Lisansı</strong>",
      tier3F2: "On-Premise / Air-Gapped Kapalı Devre Kasa",
      tier3F3: "Gölge Mod (Shadow Mode) & Champion/Challenger",
      tier3F4: "Donanım / Edge & WerrSoma Nöromorfik Refleks",
      tier3F5: "99.99% Kurumsal SLA & 7/24 Mühendislik Desteği",
      tier3Btn: "info@itouch.com.tr ile İletişime Geçin",

      // Footer
      footerCorp: "<strong>answerr.me</strong> — Resmi Ticari Sağlayıcı: <a href=\"https://itouch.com.tr\" target=\"_blank\" rel=\"noopener\" class=\"corp-link\">ITouch Bilişim Sistemleri Mühendislik Danışmanlık San. ve Tic. Ltd. Şti.</a>",
      footerLegal: "Çukurova Teknokent (Adana) • MERSİS: <code>0469094455800001</code> • Patentler: <code>TR 2026/016285</code> & <code>TR 2026/016633</code>",

      // Studio Page
      studioTitle: "Doğal Dilden WERR-24B™ Mühürlü Karar Kapısına",
      studioDesc: "Kurallarınızı Türkçe veya İngilizce yazın. <strong>Sistem-2 Derleyici</strong>, içsel matematiksel formülü kasada gizli tutarak politikanızı <strong>24 Baytlık bir tohuma</strong> ve <strong>SHA-256 Kriptografik Mührüne</strong> dönüştürür.",
      studioStep1: "1. Doğal Dil Politika Tanımı",
      studioTemplatesLabel: "Hazır Kurumsal Şablonlar (Tıklayın):",
      tplMcp: "🛡️ AI Ajan MCP Korkuluğu",
      tplFintech: "💳 TR E-Ticaret & Kart Hızı",
      tplWaf: "🌐 Zero-Trust API Güvenliği",
      lblGateId: "Politika Kapı Kimliği (gate_id)",
      lblDomain: "Koruma Alanı (Manifold)",
      lblPrompt: "Doğal Dil Politika Metni (Türkçe veya İngilizce)",
      btnCompile: "✨ WERR-24B™ Kasasında Derle & SHA-256 Mührü Üret",
      lblCertBox: "Mühürlenen 24-Bayt Kasa Sertifikası (Sovereign Policy Certificate)",
      certEndpointLbl: "Kapı uç noktası:",
      certSealLbl: "SHA-256 Politika Mührü:",
      certFormulaLbl: "Çekirdek Formülü:",
      certRulesLbl: "Derlenen Kesin Kurallar:",
      studioStep2: "2. Mühürlü Kapıyı Test Et & Entegre Et",
      lblTestInput: "Canlı Test Girdisi (JSON State)",
      btnTestGate: "⚡ Mühürlü Kapıya Sor (System-1 < 0.5 ms)",
      lblTestResult: "Canlı Karar ve Mühürlü Denetim Zarfı",
      lblSdkSnippet: "Üretim Entegrasyon Kodu (Python & cURL)",
      btnCopy: "📋 Kopyala",
      btnCopied: "✅ Kopyalandı!",

      // Research Page
      researchTag: "AÇIK BİLİM KANITLARI & KAPALI KASA TİCARİ SIRRI",
      researchTitle: "arXiv Makaleleri, Hugging Face Veri Setleri ve TÜRKPATENT Başvuruları",
      researchDesc: "<strong>answerr</strong>, dünyada hem <strong>arXiv</strong> ve <strong>Hugging Face</strong> üzerinde bağımsız kıyaslamalarla doğrulanmış matematiksel temellere sahip olan, hem de üretimdeki <strong>WERR-24B™ Kalibrasyon Formülünü</strong> ticari sır ve patent koruması altında tutan çift katmanlı bir derin teknoloji (Deep-Tech) ürünüdür.",
      secArxivTitle: "1. Resmi arXiv Yayınlarımız & Hugging Face Makale/Veri Seti Kayıtları",
      secBenchTitle: "2. Bağımsız Uluslararası Kıyaslamalar (Benchmarks)",
      secMatrixTitle: "3. Kurumsal Mimari Katmanları",
      btnReadArxiv: "arXiv'de Oku →",
      btnHfDataset: "HuggingFace Veri Seti →",
      btnHfPaper: "HuggingFace Sayfası →",
      btnViewGh: "GitHub Kaydını Gör →",
      btnInspectDataset: "Veri Setini İncele →",
      btnCorpContactLink: "ITouch Bilişim Kurumsal →",
      p1Title: "Universal Fractal Natural Language Decision Map: Real-Time Edge Triage Across Heterogeneous Domains",
      p1Desc: "Sıfır GPU belleği (0-Byte VRAM) ile doğal dil karar uzaylarını milisaniye altında sınıflandıran çekirdek WERR mimarisi ve açık karar veri seti.",
      p2Title: "Zero-Storage Procedural Neural Synthesis via Boundary Dynamics: Formal Verification in Lean 4",
      p2Desc: "Tensör ağırlıkları depolamak yerine çalışma zamanında 24-Bayt tohumdan deterministik sınır sentezi ve Lean 4 (0 sorry) biçimsel doğrulaması.",
      p3Title: "Orbital Error Dynamics (OED): Self-Organized Criticality & Ephemeral Parameter Resonance",
      p3Desc: "Çok ölçekli yörünge hata dinamikleri ve sınır rezonansı ile aşırı öğrenme (overfitting) olmadan deterministik karar ayrımı.",
      p4Title: "Werracle: Sub-Cent Intra-Block AI Reflex Oracles & Flash-Loan Circuit Breakers for EVM",
      p4Desc: "Akıllı sözleşmeler ve otonom finansal ajanlar için blok içi milisaniye altı güvenlik kesicisi ve tek slot (32-Bayt) karar kahini.",
      p5Title: "Machine-Checked Computational Group Theory in Lean 4 (35 Formal Theorems, 0 sorry)",
      p5Desc: "Schreier-Sims sabitleyici zincirleri, BSGS eleme ve ayrık cebirsel değişmezlerin Lean 4 ile makine tarafından doğrulanmış kanıtları.",
      patentCardTitle: "Endüstriyel Patent Koruması & ITouch Bilişim Ticari Sır Kasası",
      patentCardDesc: "Teorik çerçeve akademik şeffaflıkla paylaşılırken; üretimdeki <strong>WERR-24B™</strong> kalibrasyon katsayıları ve derleyici dönüşüm matrisleri <strong>ITouch Bilişim Sistemleri Ltd. Şti.</strong> ticari sırrı ve patent başvuruları kapsamında korunmaktadır.",
      b1Title: "%100 Doğruluk (49 / 49)",
      b1Desc: "Otonom WebMCP ajan yönlendirme ve araç seçimi kıyaslamasında 0-Byte VRAM ile 49 senaryonun tamamında kusursuz isabet.",
      b2Title: "53.0× Daha Hızlı (1,389 karar/sn)",
      b2Desc: "8 GB GPU VRAM tüketen Diffusion-Gemma (761.8 ms) karşısında 0-Byte VRAM ile kare başına 14.37 ms gecikme ve %0 yanlış pozitif.",
      b3Title: "Tekrarlanabilir Karar Veri Seti",
      b3Desc: "Deterministik karar izleri (noul, choice, score) ve çoklu etki alanı doğrulama paketleri Hugging Face üzerinde açık erişimde.",
      thLayer: "Katman / Modül",
      thFunc: "Fonksiyonu",
      thStatus: "Erişim / Koruma Statüsü",
      row1Desc: "Doğal dilden 24-Bayt mühürlü politikaya derleme ve REST karar kapıları (api.answerr.me)",
      row1Status: "ITouch Bilişim Ticari Ürün",
      row2Desc: "Sıfır bellekli sınır rezonansı ve çok ölçekli Tripod karar çekirdeği",
      row2Status: "Patent & Ticari Sır Korumalı",
      row3Desc: "Şema dışı (OOD) bilinmeyen girdilerde yanlış özgüveni sıfırlayan kurumsal sorumluluk kalkanı",
      row3Status: "Üretim Standart Kalkanı",
      row4Desc: "158K nöronlu konnektom refleksi (werrsoma.answerr.me) ve EVM blok içi kahini (arXiv:2609.30719)",
      row4Status: "İleri Ar-Ge & Dikey Çözümler"
    },

    en: {
      // Top Ribbon
      ribbonCorp: "Official Corporate Product: <a href=\"https://itouch.com.tr\" target=\"_blank\" rel=\"noopener\" class=\"corp-link\">ITouch Information Systems Ltd.</a> (Cukurova Technopark)",
      ribbonVault: "Vault: <strong style=\"color:var(--emerald-bright)\">WERR-24B™ SOVEREIGN CORE</strong>",
      ribbonApi: "API: <strong style=\"color:var(--cyan-bright)\">api.answerr.me (:443)</strong>",
      ribbonStatus: "STATUS: ACTIVE • ZERO VRAM",

      // Nav
      brandTag: "WERR-24B™ VAULT",
      navProduct: "Product & Live Vault",
      navStudio: "Policy Studio",
      navResearch: "arXiv, HuggingFace & Patents",
      navApi: "REST API (/docs)",
      navClassic: "Classic Console",
      btnSealPolicy: "Seal Policy →",
      btnCorpContact: "ITouch Systems",

      // Hero
      heroEyebrow: "🔒 PATENTED WERR-24B™ CORE • SYSTEM-2 DELIBERATES, SYSTEM-1 EXECUTES IN MICROSECONDS",
      heroTitle: "Not Billions of Parameters.<br /><span class=\"grad\">24 Bytes of Sealed Certainty.</span>",
      heroLead: "Write your enterprise policies in natural language; <strong>answerr</strong> crystallizes them via <strong>ITouch Systems</strong>' patented <strong>WERR-24B™ Boundary Resonance</strong> into a <strong>24-Byte encrypted decision seed</strong>. Zero GPU, zero weights file, zero runtime hallucination — deterministic decisions with cryptographic audit trace in <strong>&lt; 0.5 ms</strong>.",
      heroBtnStudio: "✨ Seal 24B Policy from Natural Language",
      heroBtnSandbox: "🛡️ Live Vault Sandbox",
      heroBtnResearch: "📄 5 arXiv Papers & HuggingFace",

      // Metrics
      metric1Val: "< 0.5 ms",
      metric1Label: "Spinal Reflex Latency (Zero Runtime LLM)",
      metric2Val: "0-Byte VRAM",
      metric2Label: "Zero GPU & Tensor Weights • 24-Byte Sealed Seed",
      metric3Val: "SHA-256 Seal",
      metric3Label: "Immutable Cryptographic Policy Seal & Audit Trace",
      metric4Val: "ABSTAIN_REVIEW",
      metric4Label: "Out-of-Domain (OOD) Shield — Zero Blind Guessing",

      // Vault Secret Formula Callout
      vaultCalloutTitle: "🧪 \"Show the Magic, Seal the Formula in the Vault\" — WERR-24B™ Black Box Guarantee",
      vaultCalloutDesc: "Just like a secret industrial formula, the internal boundary mathematics and multi-scale resonance constants of the <strong>WERR-24B™</strong> core are protected in the <strong>ITouch Systems</strong> vault (Patents Pending TR 2026/016285 & TR 2026/016633). Your operational pipelines receive only <strong>sub-millisecond deterministic verdicts</strong>, <strong>SHA-256 audit seals</strong>, and <strong>OOD safety shields</strong>.",
      vaultStampStatus: "FORMULA STATUS",
      vaultStampLocked: "🔒 VAULT-SEALED 24B",
      vaultStampPatent: "PATENT PROTECTED",

      // Sandbox
      sandboxTag: "LIVE ENTERPRISE DECISION VAULT (INTERACTIVE SANDBOX)",
      sandboxTitle: "Experience Sub-Millisecond Reflex & OOD Shield Live",
      sandboxDesc: "Select one of the 4 enterprise gates below or modify the JSON payload. The vault outputs cryptographic seals and liability shields (ABSTAIN_REVIEW) live without exposing internal formula secrets.",
      step1Title: "1. Select Sovereign Gate",
      step2Title: "2. Operational Telemetry Signal (JSON)",
      btnQueryVault: "⚡ Query Vault",
      step3Title: "3. Sealed Verdict & Public Audit Envelope",
      oscTitle: "TRIPOD RESONANCE OSCILLOSCOPE HUD (0.60x • 1.00x • 1.60x)",
      oscLive: "LIVE RESONANCE ENGAGED",
      publicEnvelopeTitle: "Sealed Audit Output (Public Audit Envelope):",

      // Gate Tabs
      tabAgentBlockTitle: "🛡️ AI Agent / MCP Guardrail (Block)",
      tabAgentBlockSub: "Destructive SQL & High Amount",
      tabAgentSafeTitle: "✅ AI Agent / MCP Guardrail (Allow)",
      tabAgentSafeSub: "Read-Only Safe Action",
      tabFintechTitle: "💳 Fintech & Payment Fraud Gate",
      tabFintechSub: "Velocity & Device Anomaly",
      tabOodTitle: "⚠️ Out-of-Domain (OOD) Shield",
      tabOodSub: "Unrecognized Signals → ABSTAIN_REVIEW",

      // Trace Labels
      trPolicyKey: "Active Policy Gate:",
      trSealKey: "Cryptographic Seal:",
      trRulesKey: "Decision Rationale:",
      trFieldsKey: "Schema Verification:",
      trSeedKey: "24-Byte Kernel:",

      // Pricing Section
      pricingTag: "ENTERPRISE LICENSING — ITOUCH INFORMATION SYSTEMS LTD.",
      pricingTitle: "From Developer Runtime to Sovereign Air-Gapped Vault",
      pricingDesc: "<strong>answerr.me</strong> is engineered by <strong>ITouch Information Systems Engineering Consulting Industry & Trade Ltd.</strong> (Cukurova Technopark) and licensed under the BSL 1.1 commercial license.",
      tier1Badge: "DEVELOPER RUNTIME",
      tier1Title: "werr Open SDK",
      tier1Price: "Free",
      tier1Sub: "Academic research, benchmarking and rapid prototyping",
      tier1F1: "<code>pip install werr</code> & Browser SDK",
      tier1F2: "<code>noul</code>, <code>choice</code>, <code>score</code> typed answers",
      tier1F3: "0-Byte VRAM local reflex runtime",
      tier1F4: "OOD <code>ABSTAIN_REVIEW</code> schema protection",
      tier1Btn: "pip install werr",

      tier2Badge: "ENTERPRISE CLOUD GATE",
      tier2Title: "answerr Pro & Agent Gate",
      tier2Price: "$149 <span style=\"font-size:14px; font-weight:500; color:var(--text-muted)\">/ mo</span>",
      tier2Sub: "Fintech, E-Commerce, SaaS & AI Agent (MCP) teams",
      tier2F1: "<strong>Natural Language to 24B Policy Studio</strong>",
      tier2F2: "Custom Sealed Gates (<code>/v1/gates/{id}/decide</code>)",
      tier2F3: "SHA-256 Cryptographic Audit Trace",
      tier2F4: "AI Agent MCP & Fintech Fraud Shields",
      tier2F5: "5 Million Sub-Millisecond Decisions / Month",
      tier2Btn: "Start in Policy Studio →",

      tier3Badge: "ON-PREMISE & SOVEREIGN",
      tier3Title: "answerr Sovereign Vault",
      tier3Price: "Enterprise License",
      tier3Sub: "Banking, Defense, Cybersecurity & Mission-Critical Systems",
      tier3F1: "<strong>ITouch Systems BSL 1.1 Production License</strong>",
      tier3F2: "On-Premise / Air-Gapped Closed Vault",
      tier3F3: "Shadow Mode & Champion/Challenger A/B",
      tier3F4: "Hardware / Edge & WerrSoma Neuromorphic Reflex",
      tier3F5: "99.99% Enterprise SLA & 24/7 Engineering Support",
      tier3Btn: "Contact info@itouch.com.tr",

      // Footer
      footerCorp: "<strong>answerr.me</strong> — Official Commercial Entity: <a href=\"https://itouch.com.tr\" target=\"_blank\" rel=\"noopener\" class=\"corp-link\">ITouch Information Systems Ltd.</a>",
      footerLegal: "Cukurova Technopark (Adana, Turkiye) • MERSIS: <code>0469094455800001</code> • Patents: <code>TR 2026/016285</code> & <code>TR 2026/016633</code>",

      // Studio Page
      studioTitle: "From Natural Language to WERR-24B™ Sealed Gate",
      studioDesc: "Define your rules in English or Turkish. The <strong>System-2 Compiler</strong> transforms your rules into a <strong>24-Byte seed</strong> and <strong>SHA-256 Cryptographic Seal</strong> while guarding the internal formula within the vault.",
      studioStep1: "1. Natural Language Policy Definition",
      studioTemplatesLabel: "Enterprise Presets (Click to load):",
      tplMcp: "🛡️ AI Agent MCP Guardrail",
      tplFintech: "💳 E-Commerce & Card Velocity",
      tplWaf: "🌐 Zero-Trust API Security",
      lblGateId: "Policy Gate ID (gate_id)",
      lblDomain: "Protection Domain (Manifold)",
      lblPrompt: "Natural Language Policy Text (English or Turkish)",
      btnCompile: "✨ Compile in WERR-24B™ Vault & Generate Seal",
      lblCertBox: "Sealed 24-Byte Policy Certificate (Sovereign Policy Certificate)",
      certEndpointLbl: "Gate Endpoint:",
      certSealLbl: "SHA-256 Policy Seal:",
      certFormulaLbl: "Kernel Formula:",
      certRulesLbl: "Compiled Hard Rules:",
      studioStep2: "2. Test Sealed Gate & Integrate",
      lblTestInput: "Live Test State (JSON)",
      btnTestGate: "⚡ Query Sealed Gate (System-1 < 0.5 ms)",
      lblTestResult: "Live Decision & Sealed Audit Envelope",
      lblSdkSnippet: "Production Integration Snippet (Python & cURL)",
      btnCopy: "📋 Copy",
      btnCopied: "✅ Copied!",

      // Research Page
      researchTag: "OPEN SCIENCE EVIDENCE & SEALED VAULT TRADE SECRETS",
      researchTitle: "arXiv Preprints, Hugging Face Repositories & Patent Filings",
      researchDesc: "<strong>answerr</strong> operates as a dual-layer Deep-Tech platform: theoretical foundations are verified openly on <strong>arXiv</strong> and <strong>Hugging Face</strong> with independent benchmarks, while production <strong>WERR-24B™ calibration kernels</strong> remain protected trade secrets and patented IP.",
      secArxivTitle: "1. Official arXiv Papers & Hugging Face Records",
      secBenchTitle: "2. Independent International Benchmarks",
      secMatrixTitle: "3. Enterprise Architecture Layers",
      btnReadArxiv: "Read on arXiv →",
      btnHfDataset: "HuggingFace Dataset →",
      btnHfPaper: "HuggingFace Page →",
      btnViewGh: "View on GitHub →",
      btnInspectDataset: "Inspect Dataset →",
      btnCorpContactLink: "ITouch Systems Corporate →",
      p1Title: "Universal Fractal Natural Language Decision Map: Real-Time Edge Triage Across Heterogeneous Domains",
      p1Desc: "Core WERR architecture classifying natural language decision spaces in sub-milliseconds with 0-Byte VRAM, and open decisions dataset.",
      p2Title: "Zero-Storage Procedural Neural Synthesis via Boundary Dynamics: Formal Verification in Lean 4",
      p2Desc: "Zero-storage runtime deterministic boundary synthesis from a 24-Byte seed with machine-checked Lean 4 formal verification (0 sorry).",
      p3Title: "Orbital Error Dynamics (OED): Self-Organized Criticality & Ephemeral Parameter Resonance",
      p3Desc: "Multi-scale orbital error dynamics and boundary resonance enabling deterministic decision separation without overfitting.",
      p4Title: "Werracle: Sub-Cent Intra-Block AI Reflex Oracles & Flash-Loan Circuit Breakers for EVM",
      p4Desc: "Sub-cent intra-block security circuit breaker and single 32-byte storage slot decision oracle for smart contracts & autonomous agents.",
      p5Title: "Machine-Checked Computational Group Theory in Lean 4 (35 Formal Theorems, 0 sorry)",
      p5Desc: "Machine-checked Lean 4 proofs for Schreier-Sims stabilizer chains, BSGS sifting, and discrete algebraic invariants.",
      patentCardTitle: "Industrial Patent Protection & ITouch Systems Trade Secret Vault",
      patentCardDesc: "While theoretical foundations are shared with academic transparency, production <strong>WERR-24B™</strong> calibration kernels and compiler matrices remain protected trade secrets and patented IP of <strong>ITouch Information Systems Ltd.</strong>",
      b1Title: "100% Accuracy (49 / 49)",
      b1Desc: "Flawless score across all 49 scenarios in autonomous WebMCP agent routing and tool selection with 0-Byte VRAM.",
      b2Title: "53.0× Faster (1,389 decisions/sec)",
      b2Desc: "14.37 ms per frame latency and 0% false positives with 0-Byte VRAM, versus 8 GB GPU VRAM Diffusion-Gemma (761.8 ms).",
      b3Title: "Reproducible Decisions Dataset",
      b3Desc: "Deterministic decision traces (noul, choice, score) and multi-domain evaluation suites hosted openly on Hugging Face.",
      thLayer: "Layer / Module",
      thFunc: "Function",
      thStatus: "Access / Protection Status",
      row1Desc: "Natural language compilation to 24-Byte sealed policies and REST decision gates (api.answerr.me)",
      row1Status: "ITouch Systems Commercial Product",
      row2Desc: "Zero-memory boundary resonance and multi-scale Tripod decision kernel",
      row2Status: "Patented & Trade Secret Protected",
      row3Desc: "Enterprise liability shield neutralizing false confidence on out-of-domain (OOD) inputs",
      row3Status: "Production Standard Shield",
      row4Desc: "158K-neuron connectome reflex (werrsoma.answerr.me) and EVM intra-block oracle (arXiv:2609.30719)",
      row4Status: "Deep R&D & Vertical Solutions"
    }
  };

  class ProI18n {
    constructor() {
      this.lang = localStorage.getItem('answerr_pro_lang') || 'tr';
      if (!['tr', 'en'].includes(this.lang)) {
        this.lang = 'tr';
      }
    }

    t(key) {
      const dict = I18N_DICT[this.lang] || I18N_DICT.tr;
      return dict[key] || I18N_DICT.en[key] || key;
    }

    setLanguage(newLang) {
      if (!['tr', 'en'].includes(newLang)) return;
      this.lang = newLang;
      localStorage.setItem('answerr_pro_lang', newLang);
      document.documentElement.lang = newLang;
      this.applyTranslations();
      this.updateSwitcherButtons();
      window.dispatchEvent(new CustomEvent('proLanguageChanged', { detail: { lang: newLang } }));
    }

    toggle() {
      this.setLanguage(this.lang === 'tr' ? 'en' : 'tr');
    }

    updateSwitcherButtons() {
      document.querySelectorAll('.lang-switch-btn').forEach(btn => {
        if (this.lang === 'tr') {
          btn.innerHTML = `<span>TR</span> <span class="lang-active">EN</span>`;
          btn.setAttribute('title', 'Switch to English');
        } else {
          btn.innerHTML = `<span class="lang-active">TR</span> <span>EN</span>`;
          btn.setAttribute('title', 'Türkçeye geç');
        }
      });
    }

    applyTranslations() {
      document.documentElement.lang = this.lang;

      // 1. Plain text / safe innerHTML translation
      document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = this.t(key);
        if (val) {
          el.innerHTML = val;
        }
      });

      // 2. Attributes
      document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const val = this.t(key);
        if (val) el.setAttribute('placeholder', val);
      });

      document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        const val = this.t(key);
        if (val) el.setAttribute('title', val);
      });
    }

    init() {
      document.documentElement.lang = this.lang;
      this.applyTranslations();
      this.updateSwitcherButtons();

      document.querySelectorAll('.lang-switch-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          this.toggle();
        });
      });
    }
  }

  window.ProI18n = new ProI18n();

  document.addEventListener('DOMContentLoaded', () => {
    window.ProI18n.init();
  });
})();
