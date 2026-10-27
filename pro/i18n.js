/* answerr.me/pro — TR / EN dictionary and switcher */
(function () {
  'use strict';
  const D = {
    tr: {
      hudRight: 'ÇALIŞMA ANINDA MODEL YOK · HER KARARIN İZİ VAR',
      hudOnline: 'API ÇEVRİMİÇİ', hudOffline: 'API’YE ULAŞILAMADI · TARAYICIDAKİ ÇEKİRDEK KULLANILIYOR', hudKernel: 'çekirdek',
      navHow: 'Nasıl çalışır', navConsole: 'Kara Kutu', navStudio: 'Derleyici', navDocs: 'Geliştiriciler', navPricing: 'Fiyatlar', navEcosystem: 'Ekosistem', navResearch: 'Araştırma', navVision: 'Werr Evreni', navApi: 'API belgeleri', navAccess: 'Erken erişim',
      heroEyebrow: '◇ Olay ufku protokolü · karar kapısı',
      heroTitle: 'Ajanınız harekete geçmeden önce, son söz <em>deterministik</em>.',
      heroLead: 'Kurallarınızı Türkçe ya da İngilizce yazın. answerr onları açık, sürümlenmiş kurallara derler; aynı girdiye her seferinde aynı kararı verir ve nedenini kaydeder. Tanımadığı bir durumda tahmin etmez, insana devreder.',
      heroCta1: 'Kara Kutuyu aç', heroCta2: 'Bir politika derle',
      triadTitle: 'Üç hüküm, üçüncü yok', vAllow: 'GEÇ', vReview: 'İNSANA DEVRET', vDeny: 'DUR',
      triadAllow: 'Kural açık, sinyaller tanıdık.', triadReview: 'Bilinmeyen alan, eksik bilgi ya da eşik.', triadDeny: 'Kural tetiklendi; gerekçe kayıtta.',
      t1t: 'Aynı girdi, aynı karar', t1d: 'Sunucu, tarayıcı ve Node aynı çekirdeği çalıştırır; testlerle eşitliği denetlenir.',
      t2t: 'Çalışma anında model yok', t2d: 'Dil yalnız politikayı yazarken taslağa çevrilir.',
      t3t: 'Bilinmeyen → insana', t3d: 'Tanınmayan tek bir alan bile kararı incelemeye gönderir.',
      t4t: 'Her kararın izi', t4d: 'Kural, aday hükümler, alan katkıları ve politika mührü (SHA-256).',
      kkEyebrow: 'Kara kutu · canlı', kkTitle: 'Bir durum gönderin, hükmü ve gerekçesini görün.',
      kkLead: 'Kararlar api.answerr.me üzerindeki yerleşik kapılardan gelir. API’ye ulaşılamazsa aynı çekirdek tarayıcıda çalışır ve bu açıkça belirtilir.',
      kkIn: '01 · Kapı ve senaryo', kkGate: 'Kapı', kkState: 'Durum vektörü (düzenlenebilir JSON)', kkRun: 'Kapıya sor',
      kkOut: '02 · Hüküm', kkConf: 'GÜVEN', kkRule: 'KURAL', kkLat: 'GECİKME',
      kkTrace: '03 · Uçuş kaydı', kkCand: 'Aday hükümler (en ağır olan kazanır)', kkContrib: 'Alan katkıları (risk puanı)',
      kkRisk: 'toplam risk puanı', kkUnk: 'TANINMAYAN ALANLAR ·', kkNone: 'yok', kkMissing: 'EKSİK ZORUNLU ALANLAR ·',
      kkPolicy: 'politika', kkSeal: 'mühür',
      kkSrcApi: 'kaynak: api.answerr.me (ağ dahil gidiş-dönüş)', kkSrvMs: 'sunucu içi', kkSrcLocal: 'kaynak: tarayıcıdaki çekirdek (API kullanılamadı ya da eski sürüm)',
      kkBadJson: 'Durum geçerli bir JSON nesnesi olmalı.', kk429: 'İstek sınırı doldu; birkaç saniye sonra yeniden deneyin.', kkNoApi: 'API’ye ulaşılamadı ve yerel çekirdek yüklenemedi.',
      evTitle: 'Üç evre. Sistem-2 yazar, Sistem-1 infaz eder.', evLead: 'Düşünme işi politikayı yazarken bir kez yapılır. Karar anında yalnızca derlenmiş, onaylanmış kurallar çalışır.',
      ev1k: 'EVRE 01', ev1s: 'YAZ', ev1t: 'Kuralı kendi dilinizde yazın', ev1c: '“Ajan silme ya da para transferi aracı çağırırsa reddet. 5.000 doları aşan işlemi insana gönder.”',
      ev2k: 'EVRE 02', ev2s: 'DERLE', ev2t: 'Her cümle bir kurala bağlanır', ev2c: 'testler ve denetimler çalıştırılır; belirsizlikler soru olarak döner',
      ev3k: 'EVRE 03', ev3s: 'İNFAZ', ev3t: 'Her yerde aynı hüküm', ev3c: 'REST API · tarayıcı · Node · Python\nhüküm + kural + iz + politika mührü',
      olTitle: 'Ölçüm, iddia değil.', olLead: 'Bu sayfadaki rakamlar ya şu an tarayıcınızda ölçülür ya da henüz yoktur ve öyle yazılır.',
      m1: 'Bu oturumda ölçülen API yanıtı (ortanca, ağ dahil)', m1n: 'Kara Kutu’yu çalıştırın',
      m2: 'Karar anında çalışan model ağırlığı (bayt)', m2n: 'kaynak kodda doğrulanabilir',
      m3: 'Çekirdek, eşitlik, derleyici ve API testi (CI)', m3n: 'Python ve JS aynı vektörlerle',
      m4b: 'Henüz yok', m4: 'Gölge mod pilotu: yakalanan / kaçan', m4n: 'tasarım ortağı pilotundan sonra yayımlanacak',
      yoTitle: 'Üç yörünge', yo1k: 'Ana yörünge', yo1t: 'AI ajan aksiyon kapısı',
      yo1d: 'Ajan bir aracı çalıştırmadan önce sorar. Silme ve yetki araçları durur, yazma ve para hareketleri insana gider, okuma geçer.',
      yo2k: 'Yörünge 2', yo2t: 'Ödeme ve sipariş riski', yo2d: 'Türkçe kurallar, mevcut kurallarınızın yanında gölge modda deneme, KVKK’ya uygun barındırma seçeneği.',
      yo3k: 'Yörünge 3', yo3t: 'API kötüye kullanım', yo3d: 'Hata, hız ve kimlik sinyallerinden gerekçeli erişim kararı.',
      erK: 'Tasarım ortaklığı · 5 koltuk', erTitle: 'Mevcut kurallarınızın yanında, gölge modda başlayalım.',
      erLead: 'Pilot ücretsizdir. Fiyatlandırma pilot sonuçlarıyla birlikte açıklanacak.', erMail: 'İş e-postası', erPh: 'ad@sirket.com', erBtn: 'Koltuk iste', erSending: 'Gönderiliyor…', erOk: 'Talebiniz alındı; onay e-postası gönderdik. İki iş günü içinde dönüş yapacağız.', erBad: 'Lütfen geçerli bir iş e-postası girin.', erFallback: 'Sunucuya ulaşılamadı; e-posta programınız açılıyor.',
      fApi: 'API belgeleri', fResearch: 'Araştırma arşivi', fClassic: 'Klasik konsol', fArchive: 'Önceki sürüm (13 Ekim)',
      fRecaptcha: 'Bu site reCAPTCHA ile korunur; Google <a href="https://policies.google.com/privacy">Gizlilik Politikası</a> ve <a href="https://policies.google.com/terms">Hizmet Şartları</a> geçerlidir.',
      stHud: 'TASLAK HİÇBİR ZAMAN OTOMATİK KAYDEDİLMEZ', stEyebrow: 'Derleyici · doğal dilden kurala', stTitle: 'Cümleden kurala. Kurala insan imzası.',
      stLead: 'Her kural hangi cümleden geldiğini gösterir. Derleyicinin tahmin etmek zorunda kaldığı her yer size soru olarak döner. Taslak kaydedilmez; kaydetmek için API anahtarı gerekir.',
      st1: '01 · Politika metni', tplAgent: 'AI ajan kapısı', tplPay: 'Ödeme riski', tplApi: 'API kötüye kullanım',
      stGate: 'Kapı kimliği', stNl: 'Politika (Türkçe ya da İngilizce)', stSample: 'Örnek durum (JSON) — alan adları buradan seçilir', stCompile: 'Derle ve sına',
      st2: '02 · Derlenen kurallar', stEmpty: 'Henüz derlenmedi.', st3: '03 · Testler, denetimler, mühür',
      stTry: 'Örnek durumla dene', stDl: 'Taslağı indir (JSON)', stCp: 'Kayıt komutunu kopyala',
      stWorking: 'Derleniyor…', stDone: 'Derlendi', stOldApi: 'Sunucudaki API henüz derleyicinin yeni sürümünü çalıştırmıyor (1.2.0 gerekli).', stNoApi: 'Derleyici API’sine ulaşılamadı.',
      stNoRules: 'Hiçbir cümle kurala dönüşmedi.', stAsks: 'DERLEYİCİ SORUYOR', stNoQ: 'Açık soru yok.',
      thInput: 'GİRDİ', thExpect: 'BEKLENEN', thGot: 'ÇIKAN', stChecks: 'Çalıştırılan denetimler', stTestsOk: 'test geçti',
      stStatus: 'durum:', stReady: 'incelemeye hazır', stNeeds: 'yanıt bekleyen sorular var',
      stNeedSample: 'Önce bir örnek durum girin.', stTryOut: 'ÖRNEK DURUMUN HÜKMÜ ·', stCopied: 'Kayıt komutu panoya kopyalandı (API anahtarı gerekir).',
      rsHud: 'ARAŞTIRMA ARŞİVİ · ÜRÜN KARARLARINDAN AYRI', rsEyebrow: 'Araştırma arşivi', rsTitle: 'werr araştırma motoru: makaleler, veri, kıyaslamalar',
      rsLead: 'Bu çalışmalar Mandelbrot sınırı üzerine kurulu werr araştırma motoruna aittir. answerr Pro’daki kapı kararları ise açık kurallardan oluşan politika çekirdeğinden gelir; ikisi ayrı tutulur.',
      rsPapers: 'Ön baskılar', rsP1: 'Heterojen alanlarda gerçek zamanlı karar sınıflandırması.',
      rsP2: 'Mandelbrot sınırına yakın bir koordinat tohumundan karar sınırı üretimi; özelliklerin Lean 4 ile biçimselleştirilmesi ve CPU sunucuda ölçümler.',
      rsP3: 'Sabit noktalı aritmetikle zincir üstü karar kâhini; Uniswap v4 ücret ayarı örneği.',
      rsP4: 'GAP permütasyon grubu algoritmalarının (Schreier-Sims, BSGS, bölüntü inceltme) Lean 4 ile doğrulanması.',
      rsP5: 'Ağ ağırlıklarının saklanmak yerine karmaşık ikinci derece dönüşümden üretilmesi; Two-Moons’ta %77,7 (gradyanla eğitilen temel model %85,7).',
      rsData: 'Veri ve kıyaslamalar', rsD1: '1.205 karar kaydı ve 3.200’den fazla değerlendirme sorusu (JSONL).', rsOpen: 'Veri setini aç',
      rsD2: 'Topluluk kıyaslamasına gönderilen sonuç kaydı.', rsOpen2: 'Kaydı aç', rsD3t: 'Karşılaştırmalı çalıştırma', rsD3: 'Bağımsız depoda açılan karşılaştırma kaydı.',
      rsP6: 'Tamsayı çarpımı sınırları üzerine tensör taşıyıcı sıkıştırması (W = 176M); CrocSwap/integer-mult-bounds deposuna katkı olarak eklendi.', rsD4: 'Araştırma motorunun Python paketi: <code>pip install werr</code>.', rsOpen3: 'Paketi aç', rsCorpus: 'Kümülatif külliyat', rsIp: 'Fikri mülkiyet başvuruları', rsPending: 'beklemede', rsIp1: 'Prosedürel ve matematiksel sentez algoritmaları (werr; werracle ve WerreduR kayıtlarında öncelik olarak anılır).', rsIp2: 'Konnektom entegrasyonu (WerrSoma).', rsOrg: 'Kuruluş', rcTitle: 'Araştırma kayıtları', rcNote: 'werr araştırma motoruna ait; ürün kararları politika çekirdeğinden gelir.',
      rsNote: 'Ön baskılar hakem değerlendirmesinden geçmemiş olabilir. Topluluk kıyaslamalarındaki kayıtlar gönderim kaydıdır, bağımsız doğrulama değildir. Patent başvuruları incelemededir; tescil edilmiş patent değildir.',
      // Footer & Ecosystem keys (TR)
      fWerrIo: 'werr.io · Motor',
      fWerracleIo: 'werracle.io · Web3',
      fRadarApi: 'radar.werracle.com · DeFi Risk DaaS',
      fWerracleCom: 'werracle.com · Kurumsal',
      fWerrRepo: 'werr çekirdeği (GitHub)',
      fClassic: 'Klasik konsol',
      fLicense: 'Lisans (BSL 1.1)',
      fCompanyShort: 'ITouch Bilişim Sistemleri',
      fPortal: 'Araştırma Portalı · v4.1',
      fArchive12: 'Arşiv · v1.2',
      fArchive06: 'Arşiv · v0.6',
      fcProduct: 'Ürün',
      fcDev: 'Geliştiriciler',
      fcCompany: 'Şirket',
      fcLegal: 'Yasal',
      fStatus: 'Hizmet durumu',
      fPilot: 'Tasarım ortaklığı',
      fDocs: 'Belgeler',
      fApiRef: 'API referansı',
      fWebhooks: "Webhook'lar",
      navEcosystem: 'Ekosistem',
      navVision: 'Werr Evreni',
      footTag: 'Doğal dilde yazılan, deterministik çalışan karar politikaları. Çalışma anında model yok; her kararın izi var.',
      footOrg: 'ITouch Bilişim Sistemleri · Çukurova Üniversitesi Teknokent',
      fRecaptcha: 'Bu site reCAPTCHA ile korunur; Google <a href="https://policies.google.com/privacy">Gizlilik Politikası</a> ve <a href="https://policies.google.com/terms">Hizmet Şartları</a> geçerlidir.',
      lgTerms: 'Kullanım şartları',
      lgKvkk: 'KVKK aydınlatma metni',
      lgPrivacy: 'Gizlilik politikası',
      lgPre: 'Ön bilgilendirme formu',
      lgSales: 'Mesafeli satış sözleşmesi',
      lgRefund: 'İptal ve iade',
      lgCookies: 'Çerez politikası',
      lgDpa: 'Veri işleme sözleşmesi',

    },
    en: {
      hudRight: 'NO MODEL AT DECISION TIME · EVERY DECISION HAS A TRACE',
      hudOnline: 'API ONLINE', hudOffline: 'API UNREACHABLE · USING THE IN-BROWSER KERNEL', hudKernel: 'kernel',
      navHow: 'How it works', navConsole: 'Black Box', navStudio: 'Compiler', navDocs: 'Developers', navPricing: 'Pricing', navEcosystem: 'Ecosystem', navResearch: 'Research', navVision: 'Werr Universe', navApi: 'API docs', navAccess: 'Early access',
      heroEyebrow: '◇ Event horizon protocol · decision gate',
      heroTitle: 'Before your agent acts, the last word is <em>deterministic</em>.',
      heroLead: 'Write your rules in Turkish or English. answerr compiles them into explicit, versioned rules; the same input always gets the same decision, with its reason recorded. When it does not recognise a situation it does not guess — it hands it to a human.',
      heroCta1: 'Open the Black Box', heroCta2: 'Compile a policy',
      triadTitle: 'Three verdicts, no fourth', vAllow: 'ALLOW', vReview: 'HAND TO HUMAN', vDeny: 'DENY',
      triadAllow: 'Explicit rule, familiar signals.', triadReview: 'Unknown field, missing data or a threshold.', triadDeny: 'A rule fired; the reason is recorded.',
      t1t: 'Same input, same decision', t1d: 'Server, browser and Node run the same kernel; parity is enforced by tests.',
      t2t: 'No model at decision time', t2d: 'Language is only used to draft the policy.',
      t3t: 'Unknown → human', t3d: 'A single unrecognised field sends the decision to review.',
      t4t: 'A trace for every decision', t4d: 'Rule, candidate verdicts, field contributions and policy seal (SHA-256).',
      kkEyebrow: 'Black box · live', kkTitle: 'Send a state, see the verdict and its reason.',
      kkLead: 'Decisions come from the built-in gates on api.answerr.me. If the API is unreachable, the same kernel runs in your browser and the page says so.',
      kkIn: '01 · Gate and scenario', kkGate: 'Gate', kkState: 'State vector (editable JSON)', kkRun: 'Ask the gate',
      kkOut: '02 · Verdict', kkConf: 'CONFIDENCE', kkRule: 'RULE', kkLat: 'LATENCY',
      kkTrace: '03 · Flight record', kkCand: 'Candidate verdicts (most severe wins)', kkContrib: 'Field contributions (risk score)',
      kkRisk: 'total risk score', kkUnk: 'UNRECOGNISED FIELDS ·', kkNone: 'none', kkMissing: 'MISSING REQUIRED FIELDS ·',
      kkPolicy: 'policy', kkSeal: 'seal',
      kkSrcApi: 'source: api.answerr.me (network round trip)', kkSrvMs: 'server-side', kkSrcLocal: 'source: in-browser kernel (API unavailable or older version)',
      kkBadJson: 'The state must be a valid JSON object.', kk429: 'Rate limit reached; try again in a few seconds.', kkNoApi: 'The API is unreachable and the local kernel could not load.',
      evTitle: 'Three phases. System 2 writes, System 1 executes.', evLead: 'The thinking happens once, while the policy is written. At decision time only compiled, approved rules run.',
      ev1k: 'PHASE 01', ev1s: 'WRITE', ev1t: 'Write the rule in your own words', ev1c: '“Deny the agent any delete or money-transfer tool. Send anything above 5,000 dollars to a human.”',
      ev2k: 'PHASE 02', ev2s: 'COMPILE', ev2t: 'Every sentence maps to a rule', ev2c: 'tests and checks run; anything ambiguous comes back as a question',
      ev3k: 'PHASE 03', ev3s: 'EXECUTE', ev3t: 'The same verdict everywhere', ev3c: 'REST API · browser · Node · Python\nverdict + rule + trace + policy seal',
      olTitle: 'Measurements, not claims.', olLead: 'Numbers on this page are either measured in your browser right now, or they do not exist yet and say so.',
      m1: 'API response measured this session (median, network included)', m1n: 'Run the Black Box',
      m2: 'Model weights running at decision time (bytes)', m2n: 'verifiable in the source',
      m3: 'Kernel, parity, compiler and API tests (CI)', m3n: 'Python and JS on the same vectors',
      m4b: 'Not yet', m4: 'Shadow-mode pilot: caught / missed', m4n: 'published after the design-partner pilot',
      yoTitle: 'Three orbits', yo1k: 'Main orbit', yo1t: 'AI agent action gate',
      yo1d: 'The agent asks before it runs a tool. Delete and privilege tools stop, writes and money movements go to a human, reads pass.',
      yo2k: 'Orbit 2', yo2t: 'Payment and order risk', yo2d: 'Rules in Turkish, shadow-mode trials next to your current rules, KVKK-compliant hosting option.',
      yo3k: 'Orbit 3', yo3t: 'API abuse', yo3d: 'Access decisions with reasons, from error, rate and identity signals.',
      erK: 'Design partnership · 5 seats', erTitle: 'Let’s start in shadow mode, next to your current rules.',
      erLead: 'The pilot is free. Pricing will be announced with the pilot results.', erMail: 'Work e-mail', erPh: 'name@company.com', erBtn: 'Request a seat', erSending: 'Sending…', erOk: 'Request received; a confirmation is on its way. We will reply within two working days.', erBad: 'Please enter a valid work e-mail address.', erFallback: 'The server is unreachable; opening your mail client.',
      fApi: 'API docs', fResearch: 'Research archive', fClassic: 'Classic console', fArchive: 'Previous version (13 Oct)',
      fRecaptcha: 'This site is protected by reCAPTCHA and the Google <a href="https://policies.google.com/privacy">Privacy Policy</a> and <a href="https://policies.google.com/terms">Terms of Service</a> apply.',
      stHud: 'DRAFTS ARE NEVER SAVED AUTOMATICALLY', stEyebrow: 'Compiler · from language to rules', stTitle: 'From sentence to rule. A human signs the rule.',
      stLead: 'Every rule shows the sentence it came from. Wherever the compiler had to guess, you get a question. Drafts are not stored; registering a gate needs an API key.',
      st1: '01 · Policy text', tplAgent: 'AI agent gate', tplPay: 'Payment risk', tplApi: 'API abuse',
      stGate: 'Gate id', stNl: 'Policy (Turkish or English)', stSample: 'Sample state (JSON) — field names are taken from here', stCompile: 'Compile and test',
      st2: '02 · Compiled rules', stEmpty: 'Nothing compiled yet.', st3: '03 · Tests, checks, seal',
      stTry: 'Try with the sample state', stDl: 'Download draft (JSON)', stCp: 'Copy register command',
      stWorking: 'Compiling…', stDone: 'Compiled', stOldApi: 'The server API does not run the new compiler yet (needs 1.2.0).', stNoApi: 'The compiler API is unreachable.',
      stNoRules: 'No sentence became a rule.', stAsks: 'THE COMPILER ASKS', stNoQ: 'No open questions.',
      thInput: 'INPUT', thExpect: 'EXPECTED', thGot: 'GOT', stChecks: 'Executed checks', stTestsOk: 'tests passed',
      stStatus: 'status:', stReady: 'ready for review', stNeeds: 'questions need answers',
      stNeedSample: 'Enter a sample state first.', stTryOut: 'VERDICT FOR THE SAMPLE ·', stCopied: 'Register command copied (needs an API key).',
      rsHud: 'RESEARCH ARCHIVE · SEPARATE FROM PRODUCT DECISIONS', rsEyebrow: 'Research archive', rsTitle: 'The werr research engine: papers, data, benchmarks',
      rsLead: 'These works belong to the werr research engine built on the Mandelbrot boundary. Gate decisions in answerr Pro come from the policy kernel of explicit rules; the two are kept apart.',
      rsPapers: 'Preprints', rsP1: 'Real-time decision triage across heterogeneous domains.',
      rsP2: 'Decision boundaries generated from a coordinate seed near the Mandelbrot boundary; properties formalised in Lean 4, measured on a CPU server.',
      rsP3: 'Fixed-point on-chain decision oracle; Uniswap v4 fee adjustment example.',
      rsP4: 'Lean 4 verification of GAP permutation-group algorithms (Schreier-Sims, BSGS, partition refinement).',
      rsP5: 'Network weights generated from a complex quadratic map instead of stored; 77.7% on Two-Moons (gradient-trained baseline 85.7%).',
      rsData: 'Data and benchmarks', rsD1: '1,205 decision records and more than 3,200 evaluation questions (JSONL).', rsOpen: 'Open the dataset',
      rsD2: 'Result record submitted to a community benchmark.', rsOpen2: 'Open the record', rsD3t: 'Comparative run', rsD3: 'Comparison record opened in an independent repository.',
      rsP6: 'Tensor carrier compression for integer-multiplication bounds (W = 176M); incorporated into CrocSwap/integer-mult-bounds.', rsD4: 'Python package of the research engine: <code>pip install werr</code>.', rsOpen3: 'Open the package', rsCorpus: 'Cumulative corpus', rsIp: 'Intellectual-property applications', rsPending: 'pending', rsIp1: 'Procedural and mathematical synthesis algorithms (werr; cited as priority in the werracle and WerreduR records).', rsIp2: 'Connectome integration (WerrSoma).', rsOrg: 'Organisation', rcTitle: 'Research records', rcNote: 'These belong to the werr research engine; product decisions come from the policy kernel.',
      rsNote: 'Preprints may not be peer reviewed. Records in community benchmarks are submissions, not independent verification. Patent applications are pending, not granted patents.',
      // Footer & Ecosystem keys (EN)
      fWerrIo: 'werr.io · Engine',
      fWerracleIo: 'werracle.io · Web3',
      fRadarApi: 'radar.werracle.com · DeFi Risk DaaS',
      fWerracleCom: 'werracle.com · Enterprise',
      fWerrRepo: 'werr kernel (GitHub)',
      fClassic: 'Classic console',
      fLicense: 'Licence (BSL 1.1)',
      fCompanyShort: 'ITouch Systems',
      fPortal: 'Research Portal · v4.1',
      fArchive12: 'Archive · v1.2',
      fArchive06: 'Archive · v0.6',
      fcProduct: 'Product',
      fcDev: 'Developers',
      fcCompany: 'Company',
      fcLegal: 'Legal',
      fStatus: 'Service status',
      fPilot: 'Design partnership',
      fDocs: 'Docs',
      fApiRef: 'API reference',
      fWebhooks: 'Webhooks',
      navEcosystem: 'Ecosystem',
      navVision: 'Werr Universe',
      footTag: 'Decision policies written in natural language, executed deterministically. No model at decision time; every decision leaves a trace.',
      footOrg: 'ITouch Systems · Cukurova University Science Park',
      fRecaptcha: 'This site is protected by reCAPTCHA; Google <a href="https://policies.google.com/privacy">Privacy Policy</a> and <a href="https://policies.google.com/terms">Terms of Service</a> apply.',
      lgTerms: 'Terms of service',
      lgKvkk: 'KVKK notice',
      lgPrivacy: 'Privacy policy',
      lgPre: 'Pre-contract information',
      lgSales: 'Distance sales agreement',
      lgRefund: 'Cancellation & refund',
      lgCookies: 'Cookie policy',
      lgDpa: 'Data processing agreement',

    }
  };

  class ProI18n {
    constructor() {
      let saved = null;
      try { saved = localStorage.getItem('answerr_pro_lang') || localStorage.getItem('answerr_lang'); } catch (e) { saved = null; }
      const nav = (navigator.language || 'tr').toLowerCase();
      this.lang = saved === 'en' || saved === 'tr' ? saved : (nav.startsWith('tr') ? 'tr' : 'en');
    }
    extend(dict) { Object.keys(dict).forEach(l => { D[l] = Object.assign(D[l] || {}, dict[l]); }); }
    t(key) { return (D[this.lang] && D[this.lang][key]) || D.tr[key] || key; }
    setLanguage(l) {
      if (l !== 'tr' && l !== 'en') return;
      this.lang = l;
      try {
        localStorage.setItem('answerr_pro_lang', l);
        localStorage.setItem('answerr_lang', l);
      } catch (e) { /* private mode */ }
      this.apply();
      window.dispatchEvent(new CustomEvent('proLanguageChanged', { detail: { lang: l } }));
    }
    apply() {
      document.documentElement.lang = this.lang;
      document.querySelectorAll('[data-i18n]').forEach(el => {
        const k = el.getAttribute('data-i18n');
        const v = this.t(k);
        if (v && v !== k) {
          if (v.indexOf('<') >= 0) el.innerHTML = v; else el.textContent = v;
        }
      });
      document.querySelectorAll('[data-i18n-placeholder]').forEach(el => el.setAttribute('placeholder', this.t(el.getAttribute('data-i18n-placeholder'))));
      document.querySelectorAll('.lang-switch-btn').forEach(btn => {
        btn.innerHTML = this.lang === 'tr' ? '<span class="lang-active">TR</span> <span>EN</span>' : '<span>TR</span> <span class="lang-active">EN</span>';
        btn.setAttribute('title', this.lang === 'tr' ? 'Switch to English' : 'Türkçeye geç');
        btn.setAttribute('aria-label', this.lang === 'tr' ? 'Switch to English' : 'Türkçeye geç');
      });
    }
    init() {
      this.apply();
      document.querySelectorAll('.lang-switch-btn').forEach(btn => btn.addEventListener('click', (e) => {
        e.preventDefault();
        this.setLanguage(this.lang === 'tr' ? 'en' : 'tr');
      }));
    }
  }

  window.ProI18n = new ProI18n();
  document.addEventListener('DOMContentLoaded', () => window.ProI18n.init());
})();
