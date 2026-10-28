/* answerr console — accounts, keys, usage, decision log, reviews, shadow mode, team, plan & billing, settings.
   Talks to api.answerr.me with a session token (Authorization: Bearer ans_sess_…). Every server value is escaped. */
(function () {
  'use strict';
  // the console holds sessions and API keys: never run it inside someone else's frame (clickjacking)
  if (window.top !== window.self) { try { window.top.location.href = window.location.href; } catch (e) { document.documentElement.innerHTML = ''; } return; }
  const A = () => window.ProApp;
  const L = () => (window.ProI18n ? window.ProI18n.lang : 'tr');
  const SKEY = 'answerr_session';
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const $ = (sel, el) => (el || document).querySelector(sel);
  const $$ = (sel, el) => Array.from((el || document).querySelectorAll(sel));

  /* ------------------------------------------------------------------ dictionary */
  const T = {
    tr: {
      signin: 'Giriş', signup: 'Hesap aç', email: 'İş e-postası', company: 'Şirket (isteğe bağlı)', companyLabel: 'Şirket / ad soyad',
      terms: '<a href="../legal/kullanim-sartlari.html" target="_blank" rel="noopener">Kullanım şartlarını</a> ve <a href="../legal/veri-isleme.html" target="_blank" rel="noopener">veri işleme sözleşmesini</a> kabul ediyorum.',
      kvkk: '<a href="../legal/kvkk-aydinlatma.html" target="_blank" rel="noopener">KVKK aydınlatma metnini</a> okudum.',
      marketing: 'Ürün duyurularını e-postayla almak istiyorum (isteğe bağlı).',
      sendLink: 'Giriş bağlantısı gönder', createAcc: 'Ücretsiz hesap aç', sent: 'Bağlantı yola çıktı. E-postanızı kontrol edin (20 dakika geçerli).',
      authLead: 'Şifre yok: e-postanıza tek kullanımlık bir bağlantı gönderiyoruz.', signupLead: 'Keşif planı ücretsizdir: ayda 10.000 karar, kart gerekmez.',
      verifying: 'Bağlantı doğrulanıyor…', badLink: 'Bu bağlantı geçersiz ya da süresi dolmuş. Yeni bir bağlantı isteyin.',
      nav: { overview: 'Genel bakış', keys: 'API anahtarları', gates: 'Kapılar', decisions: 'Karar kaydı', reviews: 'İnceleme kuyruğu', shadow: 'Gölge ve geri test', team: 'Ekip', billing: 'Plan ve fatura', settings: 'Ayarlar' },
      logout: 'Çıkış', plan: 'Plan', used: 'Bu ay kullanılan', remaining: 'Kalan', period: 'Dönem', unlimited: 'sözleşmeli',
      last30: 'Son 30 gün', quick: 'İlk çağrı', welcomeKey: 'İlk API anahtarınız. Yalnızca şimdi gösteriliyor; bir parola kasasına kaydedin.',
      copy: 'Kopyala', copied: 'Kopyalandı', label: 'Etiket', created: 'Oluşturuldu', lastUsed: 'Son kullanım', status: 'Durum',
      active: 'etkin', revoked: 'iptal', revoke: 'İptal et', sure: 'Emin misiniz?', newKey: 'Yeni anahtar', create: 'Oluştur',
      gatesLead: 'Kendi kapılarınız. Yeni kapıyı Derleyici’de yazıp buraya yapıştırın ya da API ile kaydedin.', openStudio: 'Derleyiciyi aç',
      pasteGate: 'Kapı JSON’u (derleyicinin policy_spec çıktısı)', register: 'Kaydet', del: 'Sil', none: 'Kayıt yok.',
      verdict: 'Hüküm', rule: 'Kural', gate: 'Kapı', mode: 'Mod', time: 'Zaman', observed: 'Gerçek sonuç', all: 'Tümü', more: 'Daha fazla',
      csv: 'CSV indir', retention: 'Saklama', days: 'gün',
      pending: 'Bekleyen', approved: 'Onaylanan', rejected: 'Reddedilen', expired: 'Süresi dolan', approve: 'Onayla', reject: 'Reddet', note: 'Not',
      noState: 'Durum saklanmadı (Ayarlar › inceleme durumu kapalı).',
      agreement: 'Uyum', stricter: 'Sizden sıkı (olası yakalama)', looser: 'Sizden gevşek (olası kaçırma)', labelled: 'Etiketli', decisionsN: 'Karar',
      rowsAre: 'Satır: answerr hükmü · Sütun: sizin sonucunuz', backtest: 'Geri test', btLead: 'Geçmiş kayıtları bir kapıya karşı çalıştırın (en fazla 1.000; her kayıt bir karar sayılır).',
      records: 'Kayıtlar (JSON dizisi: {"state": {...}, "observed_outcome": "DENY", "id": "…"})', run: 'Çalıştır', differences: 'Farklar',
      members: 'Üyeler', role: 'Rol', invite: 'Davet et', seats: 'Koltuk', remove: 'Çıkar', joined: 'Katıldı', invited: 'Davet edildi',
      roles: { owner: 'sahip', admin: 'yönetici', reviewer: 'inceleyici' },
      current: 'Mevcut plan', choose: 'Bu plana geç', monthly: 'Aylık', yearly: 'Yıllık', perMonth: '/ ay', perYear: '/ yıl', contact: 'Görüşelim',
      salesOk: '<a href="../legal/on-bilgilendirme.html" target="_blank" rel="noopener">Ön bilgilendirme formunu</a> ve <a href="../legal/mesafeli-satis.html" target="_blank" rel="noopener">mesafeli satış sözleşmesini</a> okudum, onaylıyorum; hizmetin anında ifa edildiğini ve bu nedenle cayma hakkının bulunmadığını biliyorum.',
      reqSent: 'Talebiniz alındı. Ödeme bilgilerini bir iş günü içinde e-postayla gönderiyoruz; plan ödemeyle etkinleşir.',
      crTitle: '⚡ USDC / USDT ile ödeme (%0 KDV)', crWeb3: '⚡ Base USDC ile tek tıkla öde (MetaMask / Rabby)', crNet: 'Ağ', crAddr: 'Ödeme adresi', crTx: 'İşlem kodu (TXID)', crTxPh: '0x… ya da 64 karakterlik TRON işlem kodu', crVerify: '✓ Doğrula ve planı etkinleştir',
      crAmount: '{p} ({c}) — ödenecek tutar: {a} USDC / USDT (%0 KDV)', crNoWallet: 'Tarayıcıda Web3 cüzdanı (MetaMask / Rabby) bulunamadı. Aşağıdan ağı seçip işlem koduyla doğrulayabilirsiniz.', crConnecting: 'Base Mainnet (Chain ID 8453) cüzdanına bağlanılıyor…', crConfirm: 'Cüzdanınızda {a} USDC transferini onaylayın…', crSent: 'Transfer gönderildi, blok onayı bekleniyor…', crNeedTx: 'İşlem kodunu (TXID) girin.', crVerifying: 'Blokzincirde doğrulanıyor…', crErr: 'Hata: ',
      bankReq: 'Havale/EFT talebiniz alındı. Alıcı: ITOUCH BİLİŞİM SİSTEMLERİ LTD. ŞTİ. (TEB) · TL IBAN <code>TR92 0003 2000 0000 0070 5754 65</code> · USD IBAN <code>TR83 0003 2000 0000 0088 9467 48</code> · EUR IBAN <code>TR28 0003 2000 0000 0088 9467 68</code>. Açıklamaya hesap e-postanızı yazın. Proforma faturanızı aşağıdaki ödemeler tablosundan indirebilirsiniz; ödeme ulaşınca planınız etkinleşir.',
      invPdf: '📄 Fatura (PDF)', proPdf: '📄 Proforma (PDF)', pendingCard: 'Hesabınız açıldı. Kartla ödemek için önce aşağıdaki fatura bilgilerini (adres, şehir, telefon dahil) kaydedin, sonra {p} planında “Kartla öde”ye basın.', st: { paid: 'ödendi', initiated: 'bekliyor', failed: 'başarısız', pending_review: 'incelemede', refunded: 'iade edildi' }, perThousand: '1.000 karar başına',
      errs: { bad_email: 'Geçerli bir e-posta adresi girin.', consent_required: 'Devam etmek için onay kutularını işaretleyin.', billing_incomplete: 'Önce fatura bilgilerinizi tamamlayın.', bad_tx_hash: 'İşlem kodu (TXID) geçersiz.', tx_already_used: 'Bu işlem kodu daha önce kullanıldı.', tx_not_found: 'İşlem bulunamadı ya da henüz onaylanmadı; birkaç dakika sonra yeniden deneyin.', transfer_not_found: 'Bu işlemde ödeme adresimize USDC/USDT transferi bulunamadı.', insufficient_amount: 'Gönderilen tutar plan bedelinden az.', tx_reverted: 'İşlem zincirde başarısız olmuş.', quote_required: 'Önce ödeme tutarınızı alın, sonra tam o tutarı gönderin.', quote_expired: 'Ödeme tutarının süresi doldu; yenisini alın.', quote_not_yours: 'Bu ödeme tutarı başka bir siparişe ait.', quote_mismatch: 'Bu ödeme tutarı başka bir plan ya da dönem için verilmiş; yenisini alın.', quote_used: 'Bu ödeme tutarı zaten kullanıldı.', quotes_busy: 'Şu an çok fazla açık kripto sipariş var; biraz sonra deneyin ya da kart/havale seçin.', tx_before_quote: 'Bu transfer ödeme tutarı verilmeden önce yapılmış; bu sipariş için kullanılamaz.', mismatched_amount: 'Gönderilen tutar sipariş tutarınızla aynı değil; küsurat dahil tam tutarı gönderin.', member_exists: 'Bu e-postayla bir hesap var; giriş yapıp Plan ve fatura bölümünden ödeyin.', tx_too_old: 'Bu transfer çok eski; yeni bir satın alma için kullanılamaz. Ödemeyi yapıp işlem kodunu 72 saat içinde girin.', unsupported_network: 'Bu ağ desteklenmiyor.', verification_error: 'Zincir doğrulaması şu an yapılamadı; biraz sonra yeniden deneyin.', card_payments_off: 'Kartla ödeme şu an kapalı; havale ya da kripto seçin.', payment_init_failed: 'Ödeme sayfası açılamadı; biraz sonra yeniden deneyin.', rate: 'Çok fazla deneme yapıldı; bir süre sonra yeniden deneyin.', recaptcha: 'Bot doğrulaması başarısız oldu; sayfayı yenileyip tekrar deneyin.' },
      when: 'Tarih', scheduled: 'Planınız ödenmiş dönem sonunda Keşif’e geçecek; yenileme ücreti alınmaz.', payCard: 'Kartla öde', payCrypto: '⚡ Kripto ile öde (USDC / USDT)', payBank: 'Havale / EFT ile talep et', renew: 'Kartla yenile', plusVat: '(%0 KDV)', vatIncl: '%0 KDV · Teknopark Muafiyetli',
      payOpening: 'Ödeme sayfası açılıyor…', payNeedBilling: 'Kartla ödeme için önce aşağıdaki fatura bilgilerini doldurup kaydedin.',
      payPaid: 'Ödemeniz alındı; planınız etkin. Faturanız iki iş günü içinde e-postayla gelir.', payFailed: 'Ödeme tamamlanmadı; karttan para çekilmedi. Yeniden deneyebilirsiniz.',
      payReview: 'Ödeme bankadan döndü ama otomatik onaylanmadı; ekibimiz bir iş günü içinde dönüş yapacak.', payUnknown: 'Ödeme sonucu doğrulanamadı. Kartınızdan çekim yapıldıysa ask@answerr.me adresine yazın.',
      payments: 'Ödemeler ve Ticari Faturalar', paidUntil: 'Ödenmiş dönem sonu', cardNote: 'Kartla ödeme iyzico 3D Secure güvenli ödeme sayfasında, kripto ödeme ise 1-Tık Base USDC cüzdanı veya çoklu ağ USDT/USDC (TRC20 / EVM) ile anında yapılır. 4691 s. Kanun ve 3065 s. KDV Kanunu Geçici 20/1 (Teknopark Ar-Ge Yazılım İstisnası) uyarınca tüm ödemeler %0 KDV olarak faturalanır ve PDF Ticari Faturanız anında indirilir.',
      pendingReq: 'Bekleyen talep', statements: 'Ekstreler', estimate: 'Bu dönem tahmini', base: 'Plan', overage: 'Aşım', total: 'Toplam',
      einv: 'e-Fatura', billingInfo: 'Fatura bilgileri', save: 'Kaydet', saved: 'Kaydedildi',
      bf: { legal_name: 'Unvan / ad soyad', contact_name: 'Yetkili kişi (ad soyad)', tax_office: 'Vergi dairesi', tax_id: 'VKN / TCKN', address: 'Adres', city: 'Şehir', country: 'Ülke', invoice_email: 'Fatura e-postası', phone: 'Telefon' },
      overageOn: 'Aşım açık: kota dolunca kararlar devam eder ve aşım faturalanır.', overageToggle: 'Aşıma izin ver',
      webhook: 'Webhook adresi (https)', secret: 'İmza anahtarı', show: 'Göster', rotate: 'Yenile', test: 'Test gönder', deliveries: 'Son teslimler',
      storeState: 'İnsana devredilen kararların durum vektörünü inceleme kuyruğunda sakla', lang: 'Bildirim dili', events: 'Olay günlüğü',
      upgrade: 'Bu özellik planınızda yok.', seePlans: 'Planları gör', quotaFull: 'Aylık kota doldu; aşımı açın ya da planı yükseltin.',
      err: 'Bir şey ters gitti', netErr: 'API’ye ulaşılamadı.', sessionEnded: 'Oturum sona erdi; yeniden giriş yapın.',
      prefix: 'Ön ek', version: 'Sürüm', seal: 'Mühür', rules: 'Kurallar', emailCol: 'E-posta', webhooksTitle: 'Webhook’lar'
    },
    en: {
      signin: 'Sign in', signup: 'Create account', email: 'Work e-mail', company: 'Company (optional)', companyLabel: 'Company / full name',
      terms: 'I accept the <a href="../legal/kullanim-sartlari.html" target="_blank" rel="noopener">terms of service</a> and the <a href="../legal/veri-isleme.html" target="_blank" rel="noopener">data processing agreement</a>.',
      kvkk: 'I have read the <a href="../legal/kvkk-aydinlatma.html" target="_blank" rel="noopener">GDPR privacy notice</a>.',
      marketing: 'Send me product announcements by e-mail (optional).',
      sendLink: 'Send sign-in link', createAcc: 'Create free account', sent: 'Link sent. Check your inbox (valid for 20 minutes).',
      authLead: 'No passwords: we e-mail you a single-use link.', signupLead: 'The Explore plan is free: 10,000 decisions a month, no card.',
      verifying: 'Checking your link…', badLink: 'This link is invalid or has expired. Ask for a new one.',
      nav: { overview: 'Overview', keys: 'API keys', gates: 'Gates', decisions: 'Decision log', reviews: 'Review queue', shadow: 'Shadow & backtest', team: 'Team', billing: 'Plan & billing', settings: 'Settings' },
      logout: 'Sign out', plan: 'Plan', used: 'Used this month', remaining: 'Remaining', period: 'Period', unlimited: 'contracted',
      last30: 'Last 30 days', quick: 'First call', welcomeKey: 'Your first API key. Shown only now; store it in a password manager.',
      copy: 'Copy', copied: 'Copied', label: 'Label', created: 'Created', lastUsed: 'Last used', status: 'Status',
      active: 'active', revoked: 'revoked', revoke: 'Revoke', sure: 'Sure?', newKey: 'New key', create: 'Create',
      gatesLead: 'Your own gates. Write a new one in the Compiler and paste it here, or register it through the API.', openStudio: 'Open the compiler',
      pasteGate: 'Gate JSON (the compiler’s policy_spec)', register: 'Register', del: 'Delete', none: 'Nothing yet.',
      verdict: 'Verdict', rule: 'Rule', gate: 'Gate', mode: 'Mode', time: 'Time', observed: 'Real outcome', all: 'All', more: 'More',
      csv: 'Download CSV', retention: 'Retention', days: 'days',
      pending: 'Pending', approved: 'Approved', rejected: 'Rejected', expired: 'Expired', approve: 'Approve', reject: 'Reject', note: 'Note',
      noState: 'State not stored (Settings › review state is off).',
      agreement: 'Agreement', stricter: 'Stricter than you (potential catch)', looser: 'Looser than you (potential miss)', labelled: 'Labelled', decisionsN: 'Decisions',
      rowsAre: 'Rows: answerr verdict · Columns: your outcome', backtest: 'Backtest', btLead: 'Replay historical records against a gate (up to 1,000; each record counts as a decision).',
      records: 'Records (JSON array: {"state": {...}, "observed_outcome": "DENY", "id": "…"})', run: 'Run', differences: 'Differences',
      members: 'Members', role: 'Role', invite: 'Invite', seats: 'Seats', remove: 'Remove', joined: 'Joined', invited: 'Invited',
      roles: { owner: 'owner', admin: 'admin', reviewer: 'reviewer' },
      current: 'Current plan', choose: 'Switch to this plan', monthly: 'Monthly', yearly: 'Yearly', perMonth: '/ mo', perYear: '/ yr', contact: 'Talk to us',
      salesOk: 'I have read and accept the <a href="../legal/on-bilgilendirme.html" target="_blank" rel="noopener">pre-contract information form</a> and the <a href="../legal/mesafeli-satis.html" target="_blank" rel="noopener">distance sales agreement</a>; I understand the service is performed immediately and therefore has no withdrawal right.',
      reqSent: 'Request received. We will e-mail payment details within one working day; the plan activates on payment.',
      crTitle: '⚡ Pay with USDC / USDT (0% VAT)', crWeb3: '⚡ One-click pay with Base USDC (MetaMask / Rabby)', crNet: 'Network', crAddr: 'Payment address', crTx: 'Transaction hash (TXID)', crTxPh: '0x… or 64-character TRON transaction id', crVerify: '✓ Verify and activate the plan',
      crAmount: '{p} ({c}) — amount due: {a} USDC / USDT (0% VAT)', crNoWallet: 'No Web3 wallet (MetaMask / Rabby) found in this browser. Choose a network below and verify with the transaction hash.', crConnecting: 'Connecting to Base Mainnet (chain ID 8453)…', crConfirm: 'Confirm the {a} USDC transfer in your wallet…', crSent: 'Transfer sent, waiting for confirmation…', crNeedTx: 'Enter the transaction hash (TXID).', crVerifying: 'Verifying on-chain…', crErr: 'Error: ',
      bankReq: 'Your bank-transfer request is in. Beneficiary: ITOUCH BILISIM SISTEMLERI LTD. STI. (TEB, SWIFT TEBUTRIS) · TRY IBAN <code>TR92 0003 2000 0000 0070 5754 65</code> · USD IBAN <code>TR83 0003 2000 0000 0088 9467 48</code> · EUR IBAN <code>TR28 0003 2000 0000 0088 9467 68</code>. Put your account e-mail in the reference. Download the proforma invoice from the payments table below; the plan activates when the payment arrives.',
      invPdf: '📄 Invoice (PDF)', proPdf: '📄 Proforma (PDF)', pendingCard: 'Your account is ready. To pay by card, first save the billing details below (including address, city and phone), then press “Pay by card” on the {p} plan.', st: { paid: 'paid', initiated: 'pending', failed: 'failed', pending_review: 'in review', refunded: 'refunded' }, perThousand: 'per 1,000 decisions',
      errs: { bad_email: 'Enter a valid e-mail address.', consent_required: 'Tick the consent boxes to continue.', billing_incomplete: 'Complete your billing details first.', bad_tx_hash: 'The transaction hash (TXID) is not valid.', tx_already_used: 'This transaction hash has already been used.', tx_not_found: 'Transaction not found or not confirmed yet; try again in a few minutes.', transfer_not_found: 'No USDC/USDT transfer to our payment address was found in this transaction.', insufficient_amount: 'The amount sent is lower than the plan price.', mismatched_amount: 'Transfer amount does not match your account quote. Please send the exact amount including cents.', tx_reverted: 'The transaction failed on-chain.', quote_required: 'Get your payment amount first, then send exactly that amount.', quote_expired: 'The payment amount has expired; get a new one.', quote_not_yours: 'This payment amount belongs to another order.', quote_mismatch: 'This payment amount was issued for another plan or period; get a new one.', quote_used: 'This payment amount has already been used.', quotes_busy: 'Too many open crypto orders right now; try again shortly or pay by card or transfer.', tx_before_quote: 'This transfer was made before the payment amount was issued; it cannot be used for this order.', member_exists: 'This e-mail already has an account; sign in and pay from Plan & billing.', tx_too_old: 'This transfer is too old to be used for a new purchase. Enter the transaction hash within 72 hours of paying.', unsupported_network: 'This network is not supported.', verification_error: 'On-chain verification is not available right now; try again shortly.', card_payments_off: 'Card payments are closed right now; choose bank transfer or crypto.', payment_init_failed: 'The payment page could not be opened; try again shortly.', rate: 'Too many attempts; please try again later.', recaptcha: 'Bot check failed; reload the page and try again.' },
      when: 'Date', scheduled: 'Your plan moves to Explore at the end of the paid period; no renewal is charged.', payCard: 'Pay by card', payCrypto: '⚡ Pay with Crypto (USDC / USDT)', payBank: 'Request bank transfer', renew: 'Renew by card', plusVat: '(0% VAT)', vatIncl: '0% VAT · Technopark Exempt',
      payOpening: 'Opening the payment page…', payNeedBilling: 'To pay by card, fill in and save the billing details below first.',
      payPaid: 'Payment received; your plan is active. The invoice arrives by e-mail within two working days.', payFailed: 'The payment was not completed and nothing was charged. You can try again.',
      payReview: 'The bank returned the payment but it was not approved automatically; our team will get back to you within one working day.', payUnknown: 'The payment result could not be verified. If your card was charged, write to ask@answerr.me.',
      payments: 'Payments & Commercial Invoices', paidUntil: 'Paid until', cardNote: 'Pay instantly by card (iyzico 3D Secure) or crypto (1-Click Base USDC wallet or multi-chain TRC20/EVM USDT & USDC). All invoices are 0% VAT (%0 KDV Technopark R&D Software & Export Exemption) with an instant downloadable PDF Commercial Invoice.',
      pendingReq: 'Pending request', statements: 'Statements', estimate: 'This period (estimate)', base: 'Plan', overage: 'Overage', total: 'Total',
      einv: 'e-Invoice', billingInfo: 'Billing details', save: 'Save', saved: 'Saved',
      bf: { legal_name: 'Legal name', contact_name: 'Contact person', tax_office: 'Tax office', tax_id: 'Tax ID', address: 'Address', city: 'City', country: 'Country', invoice_email: 'Invoice e-mail', phone: 'Phone' },
      overageOn: 'Overage on: decisions continue after the quota and are billed.', overageToggle: 'Allow overage',
      webhook: 'Webhook URL (https)', secret: 'Signing secret', show: 'Show', rotate: 'Rotate', test: 'Send test', deliveries: 'Recent deliveries',
      storeState: 'Keep the state vector of REVIEW decisions in the review queue', lang: 'Notification language', events: 'Event log',
      upgrade: 'This feature is not in your plan.', seePlans: 'See plans', quotaFull: 'Monthly quota reached; enable overage or upgrade.',
      err: 'Something went wrong', netErr: 'Could not reach the API.', sessionEnded: 'Session ended; please sign in again.',
      prefix: 'Prefix', version: 'Version', seal: 'Seal', rules: 'Rules', emailCol: 'E-mail', webhooksTitle: 'Webhooks'
    }
  };
  const t = (k) => { const d = T[L()] || T.tr; return k.split('.').reduce((o, p) => (o && o[p] !== undefined ? o[p] : null), d) ?? k; };

  /* ------------------------------------------------------------------ state & api */
  const S = { session: null, account: null, view: 'overview', plans: null, cache: {} };
  try { S.session = localStorage.getItem(SKEY); } catch (e) { S.session = null; }
  function saveSession(v) { S.session = v; try { v ? localStorage.setItem(SKEY, v) : localStorage.removeItem(SKEY); } catch (e) { /* private mode */ } }

  async function call(method, path, body, opts) {
    opts = opts || {};
    const headers = { 'Content-Type': 'application/json' };
    if (S.session && !opts.anon) headers.Authorization = 'Bearer ' + S.session;
    if (opts.recaptcha) { const tok = await A().recaptchaToken(opts.recaptcha); if (tok) headers['X-Recaptcha-Token'] = tok; }
    let res;
    try {
      res = await fetch(A().API + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
    } catch (e) { return { ok: false, status: 0, data: { message: t('netErr') } }; }
    if (opts.raw) return res;
    let data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    if (res.status === 401 && S.session && !opts.anon) { saveSession(null); S.account = null; toast(t('sessionEnded')); renderAuth('signin'); }
    return { ok: res.ok, status: res.status, data: data || {} };
  }
  function msg(r) {
    const d = r.data || {};
    if (d.error === 'feature_unavailable') return t('upgrade');
    if (d.error === 'quota_exceeded') return t('quotaFull');
    if (d.error && t('errs.' + d.error) !== 'errs.' + d.error) return t('errs.' + d.error) + (d.error === 'billing_incomplete' || d.error === 'insufficient_amount' ? ' (' + (d.message || '') + ')' : '');
    if (r.status === 429) return t('errs.rate');
    if (/recaptcha/i.test(String(d.error || d.message || ''))) return t('errs.recaptcha');
    if (Array.isArray(d.detail)) return t('err') + ' (' + r.status + ')';
    return d.message || d.detail || (t('err') + ' (' + r.status + ')');
  }
  function toast(text) {
    const el = document.createElement('div');
    el.className = 'toast'; el.setAttribute('role', 'status'); el.textContent = text;
    document.body.appendChild(el); setTimeout(() => el.remove(), 4200);
  }
  const fmtN = (n) => (n == null ? '—' : Number(n).toLocaleString(L() === 'tr' ? 'tr-TR' : 'en-US'));
  const fmtT = (ts) => (ts ? new Date(ts * 1000).toLocaleString(L() === 'tr' ? 'tr-TR' : 'en-GB', { dateStyle: 'short', timeStyle: 'short' }) : '—');
  const money = (c, cur) => (c / 100).toLocaleString('en-US', { style: 'currency', currency: cur || 'USD' });
  const vchip = (v) => `<span class="chip ${v === 'ALLOW' ? 'v-allow' : v === 'DENY' ? 'v-deny' : 'v-review'}">${esc(v || '—')}</span>`;
  const root = () => document.getElementById('csRoot');

  /* ------------------------------------------------------------------ auth */
  let activeAuthPlan = null;
  let activeAuthCycle = 'monthly';
  let activeAuthPayTab = 'card';
  let activeBankCur = null;
  let authQuote = null;   // crypto: order-specific amount for this e-mail/plan/cycle
  const EVM_DEPOSIT = '0x4945ef6e124eea2176ddf050b33db42b0ae8c7f7';
  const TRON_DEPOSIT = 'TLMhaDJTVYBHBSGJ9nCQGLvqnYFPsBgLJu';
  const AUTH_PLANS = {
    kesif: { usd_m: 0, usd_y: 0, try_m: 0, try_y: 0, quota: 10000 },
    gelistirici: { usd_m: 29, usd_y: 24, try_m: 1449, try_y: 1199, quota: 250000 },
    pro: { usd_m: 99, usd_y: 82, try_m: 4899, try_y: 4049, quota: 1000000 },
    kurumsal: { usd_m: null, quota: null }
  };
  const U = {
    tr: {
      names: { kesif: 'Keşif', gelistirici: 'Geliştirici', pro: 'Pro', kurumsal: 'Kurumsal' },
      desc: { kesif: 'Ayda 10.000 karar · kart gerekmez', gelistirici: 'Ayda 250.000 karar · 10 özel kapı', pro: 'Ayda 1.000.000 karar · gölge mod ve insan onayı', kurumsal: 'Özel hacim · SLA · yerinde kurulum' },
      free: 'Ücretsiz', custom: 'Teklif', perMo: '/ay', planApi: '{p} planı ve API anahtarı', paidLead: '{d}. API anahtarınız hemen verilir; fatura %0 KDV (Teknokent istisnası).',
      cycle: 'Faturalama dönemi', monthly: 'Aylık', yearly: 'Yıllık (%17 indirim)', optional: '(isteğe bağlı)',
      companyPh: 'Şirket unvanı ya da ad soyad', taxId: 'Vergi no / TCKN', taxPh: 'Fatura için VKN / TCKN', addr: 'Fatura şehri / ülke', addrPh: 'Adana, Türkiye',
      method: 'Ödeme yöntemi', mCard: '💳 Kart (iyzico 3D)', mBank: '🏦 Havale / EFT', mCrypto: '⚡ Kripto (USDC / USDT)',
      net: 'Ağ ve token', copy: 'Kopyala', copied: 'Kopyalandı', txid: 'İşlem kodu (TXID) *', txPh: '0x… ya da TRON işlem kodu',
      cryptoNote: 'Tutar: <b>{a} USDC/USDT</b> (%0 KDV). İşleminizin hesabınızla güvenli ve otomatik eşleşmesi için lütfen küsurat dahil tam tutarı ({a}) gönderiniz. Zincirde doğrulanınca planınız hemen etkinleşir.',
      bankCur: 'Fatura para birimi', bankBenef: 'Alıcı', bankNote: 'Hesabınız ve API anahtarınız hemen açılır (Keşif). Proforma faturanız (PDF) hazırlanır; havale ulaşınca planınız etkinleşir ve fatura ödendi olarak damgalanır.',
      cardTitle: '💳 iyzico 3D Secure ile kart ödemesi', cardNote: 'Tutar: <b>{a}</b> (%0 KDV, Teknokent istisnası), tek çekim. Hesabınız hemen açılır; ardından fatura adresinizi tamamlayıp iyzico ödeme sayfasına geçersiniz.',
      talk: '✉️ Kurumsal görüşme planla', btnFree: '🚀 Ücretsiz API anahtarımı al', btnCrypto: '✓ Ödemeyi doğrula ve API anahtarımı al', btnBank: '📄 Proforma fatura oluştur ve API anahtarımı al', btnCard: '💳 Devam et: kartla öde',
      working: 'İşleniyor…', opening: 'Ödeme sayfası açılıyor…', ready: 'API anahtarınız hazır', keyLead: 'API anahtarınız (isteklerde <code>Authorization: Bearer</code> başlığıyla gönderin). Yalnızca şimdi gösteriliyor:',
      qGet: '💲 Ödeme tutarımı al', qAmount: 'Gönderilecek tam tutar (72 saat geçerli)', qLead: 'Plan bedeli {a}. Önce e-postanızı yazıp ödeme tutarınızı alın: siparişinize özel küsuratlı bir tutar verilir; transferi bu tutarla yapın.',
      copyKey: '📋 Anahtarı kopyala', enter: '➡️ Konsola gir', invPaid: '📄 Faturayı indir (PDF)', invPro: '📄 Proforma faturayı indir (PDF)', invNo: 'Fatura no', linkSent: 'E-postanızı kontrol edin'
    },
    en: {
      names: { kesif: 'Explore', gelistirici: 'Developer', pro: 'Pro', kurumsal: 'Enterprise' },
      desc: { kesif: '10,000 decisions a month · no card needed', gelistirici: '250,000 decisions a month · 10 custom gates', pro: '1,000,000 decisions a month · shadow mode and human review', kurumsal: 'Custom volume · SLA · on-premise' },
      free: 'Free', custom: 'Quote', perMo: '/mo', planApi: '{p} plan and API key', paidLead: '{d}. Your API key is issued immediately; invoices carry 0% VAT (Technopark exemption).',
      cycle: 'Billing period', monthly: 'Monthly', yearly: 'Yearly (17% off)', optional: '(optional)',
      companyPh: 'Company name or full name', taxId: 'Tax ID', taxPh: 'Tax ID for the invoice', addr: 'Billing city / country', addrPh: 'Berlin, Germany',
      method: 'Payment method', mCard: '💳 Card (iyzico 3D)', mBank: '🏦 Bank transfer', mCrypto: '⚡ Crypto (USDC / USDT)',
      net: 'Network and token', copy: 'Copy', copied: 'Copied', txid: 'Transaction hash (TXID) *', txPh: '0x… or TRON transaction id',
      cryptoNote: 'Amount: <b>{a} USDC/USDT</b> (0% VAT). To ensure secure and instant automated binding to your account, please send the exact amount including cents ({a}). Once verified on-chain your plan activates at once.',
      bankCur: 'Invoice currency', bankBenef: 'Beneficiary', bankNote: 'Your account and API key open immediately (Explore). A proforma invoice (PDF) is prepared; the plan activates when the transfer arrives and the invoice is stamped PAID.',
      cardTitle: '💳 Card payment with iyzico 3D Secure', cardNote: 'Amount: <b>{a}</b> (0% VAT, Technopark exemption), single charge. Your account opens immediately; then you complete your billing address and continue to the iyzico payment page.',
      talk: '✉️ Book an enterprise call', btnFree: '🚀 Get my free API key', btnCrypto: '✓ Verify payment and get my API key', btnBank: '📄 Create proforma invoice and get my API key', btnCard: '💳 Continue: pay by card',
      working: 'Working…', opening: 'Opening the payment page…', ready: 'Your API key is ready', keyLead: 'Your API key (send it as <code>Authorization: Bearer</code>). It is shown only now:',
      qGet: '💲 Get my payment amount', qAmount: 'Exact amount to send (valid 72 hours)', qLead: 'Plan price {a}. Enter your e-mail and get your payment amount first: you receive an order-specific amount with cents; send exactly that amount.',
      copyKey: '📋 Copy key', enter: '➡️ Enter the console', invPaid: '📄 Download invoice (PDF)', invPro: '📄 Download proforma invoice (PDF)', invNo: 'Invoice no', linkSent: 'Check your e-mail'
    }
  };
  const u = (k, vars) => { let s = (U[L()] || U.tr)[k]; if (s == null) s = U.tr[k]; if (vars) Object.keys(vars).forEach(v => { s = String(s).split('{' + v + '}').join(vars[v]); }); return s; };
  const uName = (p) => u('names')[p] || p;
  const fmtTry = (v) => Number(v).toLocaleString(L() === 'tr' ? 'tr-TR' : 'en-US', { maximumFractionDigits: 2 }) + ' ₺';

  async function downloadInvoice(path, btn) {
    // fetch with the session header (no credentials in URLs), then open the PDF; a window opened before the await
    // keeps popup blockers quiet
    const w = window.open('', '_blank');
    const res = await call('GET', path, null, { raw: true });
    if (!res.ok) { if (w) w.close(); toast(t('err')); return; }
    const url = URL.createObjectURL(await res.blob());
    if (w) w.location.href = url; else { const a = document.createElement('a'); a.href = url; a.target = '_blank'; a.rel = 'noopener'; document.body.appendChild(a); a.click(); a.remove(); }
    if (btn) btn.blur();
  }

  function renderAuth(tab, planOverride) {
    tab = tab || (location.hash.indexOf('signup') >= 0 ? 'signup' : 'signin');
    if (planOverride) {
      activeAuthPlan = AUTH_PLANS[planOverride] ? planOverride : 'kesif';
      try {
        const url = new URL(location.href);
        url.searchParams.set('plan', activeAuthPlan);
        history.replaceState(null, '', url.toString());
      } catch (e) { /* ignore */ }
    } else if (!activeAuthPlan) {
      const qp = new URLSearchParams(location.search).get('plan');
      activeAuthPlan = (qp && AUTH_PLANS[qp]) ? qp : 'kesif';
    }
    if (!activeBankCur) activeBankCur = L() === 'tr' ? 'TRY' : 'USD';

    const prev = (id) => ($('#' + id) || {}).value || '';
    const prevChk = (id) => Boolean(($('#' + id) || {}).checked);
    const prevEmail = prev('auEmail'), prevCo = prev('auCo'), prevTax = prev('auTax'), prevAddr = prev('auAddr'), prevTx = prev('auTxHash');
    const prevNet = prev('auNet') || 'base';
    const prevTerms = prevChk('auTerms'), prevKvkk = prevChk('auKvkk'), prevMkt = prevChk('auMkt');
    const who = document.getElementById('csWho');
    if (who) who.textContent = '';

    const isPaid = ['gelistirici', 'pro'].includes(activeAuthPlan);
    const P = AUTH_PLANS[activeAuthPlan];
    const yearly = activeAuthCycle === 'yearly';
    const amtUsd = isPaid ? String(yearly ? P.usd_y * 12 : P.usd_m) : '0';
    if (authQuote && (authQuote.email !== prevEmail.trim().toLowerCase() || authQuote.plan !== activeAuthPlan || authQuote.cycle !== activeAuthCycle)) authQuote = null;
    const amtTry = isPaid ? (yearly ? P.try_y * 12 : P.try_m) : 0;
    const pill = (on, color) => `padding:8px 4px;border-radius:8px;border:1px solid ${on ? color : 'var(--line,#1e293b)'};background:${on ? 'rgba(245,158,11,0.12)' : 'transparent'};color:${on ? '#fff' : 'var(--muted,#94a3b8)'};cursor:pointer;text-align:center;`;
    const tabBtn = (m, color) => `flex:1;padding:8px;border-radius:6px;border:1px solid ${activeAuthPayTab === m ? color : '#334155'};background:${activeAuthPayTab === m ? 'rgba(56,189,248,0.10)' : 'transparent'};color:#fff;cursor:pointer;font-size:12px;font-weight:600;min-height:40px;`;
    const submitLabel = tab !== 'signup' ? t('sendLink') : (!isPaid ? u('btnFree') : (activeAuthPayTab === 'crypto' ? u('btnCrypto') : activeAuthPayTab === 'bank' ? u('btnBank') : u('btnCard')));

    root().innerHTML = `
      <div class="auth-box cs-card" style="max-width:${tab === 'signup' && isPaid ? '620px' : '480px'};margin:0 auto">
        <div class="tabs" role="tablist">
          <button role="tab" type="button" data-at="signin" aria-selected="${tab === 'signin'}">${esc(t('signin'))}</button>
          <button role="tab" type="button" data-at="signup" aria-selected="${tab === 'signup'}">${esc(t('signup'))} &amp; API</button>
        </div>
        <h1 style="font-size:26px;margin:8px 0 4px">${esc(tab === 'signup' ? (isPaid ? u('planApi', { p: uName(activeAuthPlan) }) : t('signup')) : t('signin'))}</h1>
        <p class="muted" style="margin:0 0 16px;font-size:13px">${esc(tab === 'signup' ? (isPaid ? u('paidLead', { d: u('desc')[activeAuthPlan] }) : t('signupLead')) : t('authLead'))}</p>

        ${tab === 'signup' ? `
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:14px;" role="group" aria-label="Plan">
          ${['kesif', 'gelistirici', 'pro', 'kurumsal'].map(pId => {
            const pi = AUTH_PLANS[pId];
            return `<button type="button" data-plan-pick="${pId}" aria-pressed="${activeAuthPlan === pId}" style="${pill(activeAuthPlan === pId, 'var(--amber,#f59e0b)')}">
              <div style="font-weight:700;font-size:12px;">${esc(uName(pId))}</div>
              <div style="font-size:10px;margin-top:2px;">${pi.usd_m == null ? esc(u('custom')) : (pi.usd_m === 0 ? esc(u('free')) : '$' + pi.usd_m + esc(u('perMo')))}</div>
            </button>`;
          }).join('')}
        </div>
        ${isPaid ? `
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;background:rgba(255,255,255,0.03);border:1px solid var(--line,#1e293b);padding:8px 12px;border-radius:8px;margin-bottom:14px;font-size:12px;">
          <span style="color:var(--muted)">${esc(u('cycle'))}</span>
          <div style="display:flex;gap:6px;" role="group" aria-label="${esc(u('cycle'))}">
            <button type="button" id="cyMonthly" aria-pressed="${!yearly}" style="padding:6px 10px;border-radius:6px;border:1px solid ${!yearly ? 'var(--amber)' : '#334155'};background:${!yearly ? 'rgba(245,158,11,0.15)' : 'transparent'};color:#fff;cursor:pointer;font-size:11px;">${esc(u('monthly'))} · $${P.usd_m}</button>
            <button type="button" id="cyYearly" aria-pressed="${yearly}" style="padding:6px 10px;border-radius:6px;border:1px solid ${yearly ? 'var(--amber)' : '#334155'};background:${yearly ? 'rgba(245,158,11,0.15)' : 'transparent'};color:#fff;cursor:pointer;font-size:11px;">${esc(u('yearly'))} · $${P.usd_y * 12}</button>
          </div>
        </div>` : ''}` : ''}

        <form id="authForm" style="display:flex;flex-direction:column;gap:12px">
          <div class="field"><label for="auEmail">${esc(t('email'))} *</label><input id="auEmail" type="email" required autocomplete="email" value="${esc(prevEmail)}" placeholder="developer@company.com"></div>
          ${tab === 'signup' ? `
          <div class="field"><label for="auCo">${esc(t('companyLabel'))} ${isPaid ? '*' : esc(u('optional'))}</label><input id="auCo" type="text" ${isPaid ? 'required' : ''} maxlength="120" autocomplete="organization" value="${esc(prevCo)}" placeholder="${esc(u('companyPh'))}"></div>
          ${isPaid ? `
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;">
            <div class="field"><label for="auTax">${esc(u('taxId'))}</label><input id="auTax" type="text" maxlength="50" value="${esc(prevTax)}" placeholder="${esc(u('taxPh'))}"></div>
            <div class="field"><label for="auAddr">${esc(u('addr'))}</label><input id="auAddr" type="text" maxlength="120" value="${esc(prevAddr)}" placeholder="${esc(u('addrPh'))}"></div>
          </div>
          <div style="border-top:1px solid var(--line,#1e293b);padding-top:12px;margin-top:4px;">
            <div style="font-size:12px;font-weight:600;margin-bottom:8px;color:#cbd5e1;" id="payMethodLbl">${esc(u('method'))}</div>
            <div style="display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap" role="group" aria-labelledby="payMethodLbl">
              <button type="button" data-pay-m="card" aria-pressed="${activeAuthPayTab === 'card'}" style="${tabBtn('card', '#10b981')}">${esc(u('mCard'))}</button>
              <button type="button" data-pay-m="bank" aria-pressed="${activeAuthPayTab === 'bank'}" style="${tabBtn('bank', '#f59e0b')}">${esc(u('mBank'))}</button>
              <button type="button" data-pay-m="crypto" aria-pressed="${activeAuthPayTab === 'crypto'}" style="${tabBtn('crypto', '#38bdf8')}">${esc(u('mCrypto'))}</button>
            </div>
            ${activeAuthPayTab === 'crypto' ? `
            <div style="background:#080c14;border:1px solid #1e293b;border-radius:8px;padding:12px;margin-bottom:12px;">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
                <label for="auNet" style="font-size:11px;color:var(--muted)">${esc(u('net'))}</label>
                <select id="auNet" style="padding:6px 8px;border-radius:6px;border:1px solid #334155;background:#0f1422;color:#fff;font-size:12px;">
                  ${[['base', 'Base Mainnet (USDC)'], ['trc20', 'TRON TRC20 (USDT)'], ['arbitrum', 'Arbitrum One (USDC)'], ['ethereum', 'Ethereum ERC20 (USDC / USDT)'], ['bsc', 'BNB Smart Chain BEP20 (USDT / USDC)']]
                    .map(([v, l]) => `<option value="${v}" ${prevNet === v ? 'selected' : ''}>${l}</option>`).join('')}
                </select>
              </div>
              <div style="background:#05070c;border:1px solid #334155;border-radius:6px;padding:8px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;gap:6px;">
                <code id="auDepositAddr" style="font-size:11px;color:#10b981;word-break:break-all;">${prevNet === 'trc20' ? TRON_DEPOSIT : EVM_DEPOSIT}</code>
                <button type="button" id="btnCopyDep" style="padding:6px 10px;font-size:11px;border-radius:4px;border:1px solid #334155;background:#1e293b;color:#fff;cursor:pointer;">${esc(u('copy'))}</button>
              </div>
              <div class="field" style="margin-bottom:0"><label for="auTxHash" style="font-size:11px">${esc(u('txid'))}</label>
                <input id="auTxHash" type="text" value="${esc(prevTx)}" placeholder="${esc(u('txPh'))}" style="font-family:monospace;font-size:12px;"></div>
              ${authQuote
                ? `<div style="margin-top:8px;padding:8px;border:1px solid #10b981;border-radius:6px"><div style="font-size:11px;color:var(--muted)">${esc(u('qAmount'))}</div><div style="font-size:20px;font-weight:700;color:#10b981;font-family:monospace">${esc(authQuote.amount)} USDC / USDT</div></div>
                   <div id="auCryptoNote" style="font-size:11px;color:var(--muted);margin-top:6px;">${u('cryptoNote', { a: esc(authQuote.amount) })}</div>`
                : `<button type="button" id="btnQuote" class="btn-ghost btn-sm" style="margin-top:8px">${esc(u('qGet'))}</button>
                   <div id="auCryptoNote" style="font-size:11px;color:var(--muted);margin-top:6px;">${esc(u('qLead', { a: '$' + amtUsd }))}</div>`}
            </div>` : ''}
            ${activeAuthPayTab === 'bank' ? `
            <div style="background:#080c14;border:1px solid #1e293b;border-radius:8px;padding:12px;margin-bottom:12px;font-size:12px;line-height:1.6;">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:6px">
                <label for="auBankCur" style="color:var(--muted)">${esc(u('bankCur'))}</label>
                <select id="auBankCur" style="padding:6px 8px;border-radius:6px;border:1px solid #334155;background:#0f1422;color:#fff;font-size:12px;">
                  <option value="TRY" ${activeBankCur === 'TRY' ? 'selected' : ''}>TRY · ${fmtTry(amtTry)}</option>
                  <option value="USD" ${activeBankCur === 'USD' ? 'selected' : ''}>USD · $${amtUsd}</option>
                </select>
              </div>
              <div style="color:#f59e0b;font-weight:700;margin-bottom:4px;">🏦 TEB — Türk Ekonomi Bankası A.Ş. · Adana Toros (446) · SWIFT TEBUTRIS</div>
              <div style="color:#e2e8f0;margin-bottom:4px;"><b>${esc(u('bankBenef'))}:</b> ITOUCH BİLİŞİM SİSTEMLERİ LTD. ŞTİ.</div>
              <div style="font-family:monospace;color:#10b981;word-break:break-all"><b>TRY IBAN:</b> TR92 0003 2000 0000 0070 5754 65</div>
              <div style="font-family:monospace;color:#38bdf8;word-break:break-all"><b>USD IBAN:</b> TR83 0003 2000 0000 0088 9467 48</div>
              <div style="color:var(--muted);margin-top:6px;">${esc(u('bankNote'))}</div>
            </div>` : ''}
            ${activeAuthPayTab === 'card' ? `
            <div style="background:#080c14;border:1px solid #1e293b;border-radius:8px;padding:12px;margin-bottom:12px;font-size:12px;">
              <div style="color:#10b981;font-weight:700;margin-bottom:4px;">${esc(u('cardTitle'))}</div>
              <p style="color:var(--muted);margin:0;font-size:12px;">${u('cardNote', { a: esc(fmtTry(amtTry)) })}</p>
            </div>` : ''}
          </div>` : ''}
          <label class="check-line"><input type="checkbox" id="auTerms" required ${prevTerms ? 'checked' : ''}><span>${t('terms')}</span></label>
          <label class="check-line"><input type="checkbox" id="auKvkk" required ${prevKvkk ? 'checked' : ''}><span>${t('kvkk')}</span></label>
          ${isPaid ? `<label class="check-line"><input type="checkbox" id="auSales" required ${prevChk('auSales') ? 'checked' : ''}><span>${t('salesOk')}</span></label>` : ''}
          <label class="check-line"><input type="checkbox" id="auMkt" ${prevMkt ? 'checked' : ''}><span>${esc(t('marketing'))}</span></label>` : ''}
          <div class="sr-only" aria-hidden="true"><label for="auWeb">Website</label><input id="auWeb" type="text" tabindex="-1" autocomplete="off"></div>
          ${tab === 'signup' && activeAuthPlan === 'kurumsal'
            ? `<a class="btn-primary" href="mailto:ask@answerr.me?subject=answerr%20Enterprise" style="text-align:center;text-decoration:none;padding:12px;">${esc(u('talk'))}</a>`
            : `<button class="btn-primary" type="submit" style="padding:12px;font-size:14px;font-weight:600;">${esc(submitLabel)}</button>`}
          <p class="small-mono" id="auStatus" role="status" style="margin:4px 0 0"></p>
        </form>
        <div id="auResultBox" style="display:none;margin-top:16px;padding:16px;border-radius:10px;border:1px solid #10b981;background:#05070c;"></div>
      </div>`;

    $$('[data-at]').forEach(b => b.addEventListener('click', () => {
      history.replaceState(null, '', location.pathname + location.search + (b.dataset.at === 'signup' ? '#signup' : ''));
      renderAuth(b.dataset.at);
    }));
    $$('[data-plan-pick]').forEach(b => b.addEventListener('click', () => renderAuth('signup', b.dataset.planPick)));
    const cm = $('#cyMonthly'), cy = $('#cyYearly');
    if (cm) cm.addEventListener('click', () => { activeAuthCycle = 'monthly'; renderAuth('signup'); });
    if (cy) cy.addEventListener('click', () => { activeAuthCycle = 'yearly'; renderAuth('signup'); });
    $$('[data-pay-m]').forEach(b => b.addEventListener('click', () => { activeAuthPayTab = b.dataset.payM; renderAuth('signup'); }));
    const bq = $('#btnQuote');
    if (bq) bq.addEventListener('click', async () => {
      const em = ($('#auEmail').value || '').trim().toLowerCase();
      const st = $('#auStatus');
      if (!em || !$('#auEmail').checkValidity()) { st.textContent = t('errs.bad_email'); $('#auEmail').focus(); return; }
      bq.disabled = true; st.textContent = u('working');
      const d = await call('POST', '/v1/checkout/crypto-quote', { email: em, plan: activeAuthPlan, cycle: activeAuthCycle, website: $('#auWeb').value }, { anon: true, recaptcha: 'access' });
      bq.disabled = false;
      if (!d.ok) { st.textContent = msg(d); return; }
      authQuote = Object.assign({}, d.data, { email: em });
      renderAuth('signup');
    });
    const bc = $('#auBankCur');
    if (bc) bc.addEventListener('change', () => { activeBankCur = bc.value; });
    const netSel = $('#auNet');
    if (netSel) netSel.addEventListener('change', () => { $('#auDepositAddr').textContent = netSel.value === 'trc20' ? TRON_DEPOSIT : EVM_DEPOSIT; });
    const cp = $('#btnCopyDep');
    if (cp) cp.addEventListener('click', () => {
      try { navigator.clipboard.writeText($('#auDepositAddr').textContent.trim()); } catch (e) { /* ignore */ }
      cp.textContent = u('copied'); setTimeout(() => { cp.textContent = u('copy'); }, 2000);
    });

    const form = $('#authForm');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const st = $('#auStatus'), btn = e.target.querySelector('button[type=submit]');
      if (btn) btn.disabled = true;
      st.textContent = u('working');
      const email = $('#auEmail').value.trim();
      const website = $('#auWeb').value;
      if (tab === 'signin') {
        const r = await call('POST', '/v1/auth/login', { email, lang: L(), website }, { anon: true, recaptcha: 'access' });
        if (btn) btn.disabled = false;
        st.textContent = r.ok ? t('sent') : msg(r);
        return;
      }
      const val = (id) => { const x = $('#' + id); return x && x.value.trim() ? x.value.trim() : null; };
      const network = val('auNet') || 'base';
      const method = isPaid ? activeAuthPayTab : 'free';
      const reqBody = {
        email, company: val('auCo'), tax_id: val('auTax'), address: val('auAddr'),
        plan: activeAuthPlan, cycle: activeAuthCycle, method,
        tx_hash: val('auTxHash'), quote_id: authQuote ? authQuote.quote_id : null, network, token: network === 'trc20' ? 'USDT' : 'USDC', currency: activeBankCur,
        accept_terms: $('#auTerms').checked, kvkk_ack: $('#auKvkk').checked, marketing: $('#auMkt').checked,
        lang: L(), website
      };
      if (method === 'crypto' && !authQuote) { if (btn) btn.disabled = false; st.textContent = t('errs.quote_required'); return; }
      const res = await call('POST', '/v1/checkout/instant', reqBody, { anon: true, recaptcha: 'access' });
      if (btn) btn.disabled = false;
      if (!res.ok) { st.textContent = msg(res); return; }
      const data = res.data || {};
      if (data.status === 'login_link_sent') {
        st.textContent = '';
        form.style.display = 'none';
        const box = $('#auResultBox');
        box.style.display = 'block';
        box.innerHTML = `<div style="color:#f59e0b;font-weight:700;margin-bottom:6px">✉️ ${esc(u('linkSent'))}</div><p class="muted" style="margin:0">${esc(data.message || t('sent'))}</p>`;
        return;
      }
      if (data.session) saveSession(data.session);
      S.firstKey = data.api_key || null;
      if (data.status === 'billing_required') {
        // card: continue in Plan & billing with this plan preselected
        S.pendingPay = { plan: data.requested_plan || activeAuthPlan, cycle: data.cycle || activeAuthCycle };
        history.replaceState(null, '', location.pathname + location.search + '#billing');
        await boot();
        return;
      }
      form.style.display = 'none';
      st.textContent = '';
      const box = $('#auResultBox');
      box.style.display = 'block';
      const invBtn = data.invoice_pdf_url
        ? `<button type="button" id="btnInv" class="btn-ghost btn-sm">${esc(String(data.invoice_no || '').startsWith('INV') ? u('invPaid') : u('invPro'))}</button>` : '';
      box.innerHTML = `
        <div style="color:#10b981;font-weight:700;font-size:16px;margin-bottom:8px;">✓ ${esc(data.message || u('ready'))}</div>
        ${data.invoice_no ? `<div style="font-size:12px;color:var(--muted);margin-bottom:10px;">${esc(u('invNo'))}: <b>${esc(data.invoice_no)}</b></div>` : ''}
        ${data.api_key ? `<p style="color:var(--muted);font-size:12px;margin:0 0 6px;">${u('keyLead')}</p>
          <div style="background:#000;border:1px solid #1e293b;padding:10px;border-radius:6px;font-family:monospace;color:#38bdf8;word-break:break-all;font-size:13px;margin-bottom:12px;">${esc(data.api_key)}</div>` : ''}
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
          ${data.api_key ? `<button type="button" id="btnCopyKey" class="btn-ghost btn-sm">${esc(u('copyKey'))}</button>` : ''}
          ${invBtn}
          <button type="button" id="btnEnterConsole" class="btn-primary btn-sm">${esc(u('enter'))}</button>
        </div>`;
      const ck = $('#btnCopyKey');
      if (ck) ck.addEventListener('click', () => { try { navigator.clipboard.writeText(data.api_key); } catch (e2) { /* ignore */ } ck.textContent = u('copied'); setTimeout(() => { ck.textContent = u('copyKey'); }, 2000); });
      const ib = $('#btnInv');
      if (ib) ib.addEventListener('click', () => downloadInvoice(data.invoice_pdf_url, ib));
      $('#btnEnterConsole').addEventListener('click', async () => { S.firstKey = null; history.replaceState(null, '', location.pathname + location.search); await boot(); });
    });
  }


  async function verifyFromHash() {
    const m = location.hash.match(/login=(ans_link_[A-Za-z0-9_\-]+)/);
    if (!m) return false;
    history.replaceState(null, '', location.pathname + location.search);
    root().innerHTML = `<p class="muted">${esc(t('verifying'))}</p>`;
    const r = await call('POST', '/v1/auth/verify', { token: m[1] }, { anon: true });
    if (!r.ok) { renderAuth('signin'); $('#auStatus').textContent = t('badLink'); return true; }
    saveSession(r.data.session);
    S.firstKey = r.data.api_key || null;
    await boot();
    return true;
  }

  /* ------------------------------------------------------------------ shell */
  const VIEWS = ['overview', 'keys', 'gates', 'decisions', 'reviews', 'shadow', 'team', 'billing', 'settings'];
  const REVIEWER_VIEWS = ['overview', 'decisions', 'reviews', 'shadow'];

  async function boot() {
    const r = await call('GET', '/v1/account');
    if (!r.ok) { if (r.status !== 401) toast(msg(r)); renderAuth(location.hash === '#signup' ? 'signup' : 'signin'); return; }
    S.account = r.data.account;
    const want = (location.hash || '').replace('#', '');
    S.view = VIEWS.includes(want) ? want : 'overview';
    renderShell();
  }

  function allowedViews() { return S.account.me.role === 'reviewer' ? REVIEWER_VIEWS : VIEWS; }

  function renderShell() {
    const a = S.account;
    document.getElementById('csWho').textContent = (a.company || a.email) + ' · ' + t('roles.' + a.me.role) + ' · ' + (a.plan_name[L()] || a.plan);
    if (!allowedViews().includes(S.view)) S.view = 'overview';
    root().innerHTML = `
      <div class="cs-shell">
        <nav class="cs-side" aria-label="Konsol">
          ${allowedViews().map(v => `<button type="button" data-v="${v}" aria-current="${v === S.view}">${esc(t('nav.' + v))}${v === 'reviews' ? '<span class="count" id="revCount" hidden></span>' : ''}</button>`).join('')}
          <button type="button" id="csLogout" style="margin-top:12px;color:var(--muted)">${esc(t('logout'))}</button>
        </nav>
        <div class="cs-main" id="csMain"></div>
      </div>`;
    $$('[data-v]').forEach(b => b.addEventListener('click', () => { S.view = b.dataset.v; history.replaceState(null, '', '#' + S.view); renderShell(); }));
    $('#csLogout').addEventListener('click', async () => { await call('POST', '/v1/auth/logout'); saveSession(null); S.account = null; renderAuth('signin'); });
    (VIEW_FN[S.view] || viewOverview)($('#csMain'));
    refreshReviewCount();
  }

  async function refreshReviewCount() {
    if (!S.account.features.review_queue) return;
    const r = await call('GET', '/v1/reviews?status=pending&limit=200');
    const el = document.getElementById('revCount');
    if (el && r.ok) { const n = r.data.reviews.length; el.hidden = !n; el.textContent = n; }
  }

  function upgradeCard(el) {
    el.innerHTML = `<div class="cs-card"><h2>${esc(t('upgrade'))}</h2><p><a class="btn-primary btn-sm" href="#billing" data-go="billing">${esc(t('seePlans'))}</a></p></div>`;
    $('[data-go]', el).addEventListener('click', (e) => { e.preventDefault(); S.view = 'billing'; renderShell(); });
  }

  function copyBtn(text) {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'btn-ghost btn-sm'; b.textContent = t('copy');
    b.addEventListener('click', async () => { try { await navigator.clipboard.writeText(text); b.textContent = t('copied'); } catch (e) { /* ignore */ } });
    return b;
  }

  /* ------------------------------------------------------------------ views */
  async function viewOverview(el) {
    const fresh = await call('GET', '/v1/account');
    if (fresh.ok) S.account = fresh.data.account;
    const a = S.account, u = a.usage;
    const pct = u.quota ? Math.min(100, u.decisions / u.quota * 100) : 0;
    el.innerHTML = `
      ${S.firstKey ? `<div class="cs-card" style="border-color:var(--amber)"><h2>${esc(t('welcomeKey'))}</h2><div class="secret" id="fk">${esc(S.firstKey)}</div><div id="fkc"></div></div>` : ''}
      <div class="cs-kpis">
        <div class="cs-kpi"><small>${esc(t('plan'))}</small><b>${esc(a.plan_name[L()] || a.plan)}</b></div>
        <div class="cs-kpi"><small>${esc(t('used'))}</small><b>${fmtN(u.decisions)}</b></div>
        <div class="cs-kpi"><small>${esc(t('remaining'))}</small><b>${u.quota == null ? esc(t('unlimited')) : fmtN(u.remaining)}</b></div>
        <div class="cs-kpi"><small>${esc(t('period'))}</small><b>${esc(u.period)}</b></div>
      </div>
      ${u.quota ? `<div class="meter ${pct >= 100 ? 'full' : pct >= 80 ? 'warn' : ''}" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${pct.toFixed(0)}"><i style="width:${pct}%"></i></div>
      <p class="small-mono" style="margin:0">${fmtN(u.decisions)} / ${fmtN(u.quota)} · %${pct.toFixed(1)}${a.overage_enabled ? ' · ' + esc(t('overageOn')) : ''}</p>` : ''}
      <div class="cs-card"><h2>${esc(t('last30'))}</h2><div class="bars-chart" id="ovChart" aria-label="${esc(t('last30'))}"></div>
        <div class="legend"><span><i style="background:var(--ice)"></i>ALLOW</span><span><i style="background:var(--amber)"></i>REVIEW</span><span><i style="background:var(--stop)"></i>DENY</span></div></div>
      <div class="cs-card"><h2>${esc(t('quick'))}</h2>
<pre class="code">curl -s ${esc(A().API)}/v1/gates/agent_mcp_guard/decide \\
  -H "Authorization: Bearer $ANSWERR_API_KEY" -H "Content-Type: application/json" \\
  -d '{"state": {"tool_name": "send_payment", "user_role": "member", "amount_usd": 7200}}'</pre>
        <p class="small-mono" style="margin:0"><a href="../docs.html">docs.html</a> · <a href="${esc(A().API)}/v1/docs" rel="noopener">/v1/docs</a></p></div>`;
    if (S.firstKey) { $('#fkc').appendChild(copyBtn(S.firstKey)); S.firstKey = null; }
    const r = await call('GET', '/v1/account/usage?days=30');
    if (!r.ok) return;
    const max = Math.max(1, ...r.data.series.map(d => d.decisions));
    $('#ovChart').innerHTML = r.data.series.map(d => `<div title="${esc(d.day)} · ${d.decisions}">
      <span style="height:${d.allow / max * 136}px;background:var(--ice)"></span><span style="height:${d.review / max * 136}px;background:var(--amber)"></span><span style="height:${d.deny / max * 136}px;background:var(--stop)"></span></div>`).join('');
  }

  async function viewKeys(el) {
    const r = await call('GET', '/v1/account/keys');
    if (!r.ok) { el.innerHTML = `<p class="note">${esc(msg(r))}</p>`; return; }
    el.innerHTML = `
      <div class="cs-card"><h2>${esc(t('nav.keys'))}</h2>
        <form id="kForm" class="cs-row"><div class="field"><label for="kLabel">${esc(t('label'))}</label><input id="kLabel" type="text" maxlength="60" value="production"></div>
          <button class="btn-primary btn-sm" type="submit">${esc(t('newKey'))}</button></form>
        <div id="kNew"></div>
        <div class="scroll-x"><table class="cs-table"><thead><tr><th>${esc(t('label'))}</th><th>${esc(t('prefix'))}</th><th>${esc(t('created'))}</th><th>${esc(t('lastUsed'))}</th><th>${esc(t('status'))}</th><th></th></tr></thead>
        <tbody>${r.data.keys.map(k => `<tr><td>${esc(k.label)}</td><td><code>${esc(k.prefix)}…</code></td><td>${fmtT(k.created_at)}</td><td>${fmtT(k.last_used_at)}</td>
          <td>${k.revoked_at ? esc(t('revoked')) : `<span class="v-allow">${esc(t('active'))}</span>`}</td>
          <td>${k.revoked_at ? '' : `<button class="btn-ghost btn-sm" data-revoke="${esc(k.id)}">${esc(t('revoke'))}</button>`}</td></tr>`).join('')}</tbody></table></div></div>`;
    $('#kForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const c = await call('POST', '/v1/account/keys', { label: $('#kLabel').value || 'key' });
      if (!c.ok) { toast(msg(c)); return; }
      await viewKeys(el);
      $('#kNew').innerHTML = `<p class="small-mono">${esc(t('welcomeKey'))}</p><div class="secret">${esc(c.data.api_key)}</div>`;
      $('#kNew').appendChild(copyBtn(c.data.api_key));
    });
    $$('[data-revoke]', el).forEach(b => b.addEventListener('click', async () => {
      if (b.dataset.armed !== '1') { b.dataset.armed = '1'; b.textContent = t('sure'); return; }
      const d = await call('DELETE', '/v1/account/keys/' + encodeURIComponent(b.dataset.revoke));
      if (!d.ok) toast(msg(d)); viewKeys(el);
    }));
  }

  async function viewGates(el) {
    const r = await call('GET', '/v1/gates');
    const own = r.ok ? r.data.gates.filter(g => !g.builtin) : [];
    let draftJson = '';
    try {
      draftJson = sessionStorage.getItem('answerr_draft_gate') || '';
      if (draftJson) sessionStorage.removeItem('answerr_draft_gate');
    } catch (e) { draftJson = ''; }
    el.innerHTML = `
      <div class="cs-card"><h2>${esc(t('nav.gates'))}</h2><p class="muted" style="margin:0">${esc(t('gatesLead'))} · ${fmtN(own.length)} / ${fmtN(S.account.limits.custom_gates)}</p>
        <div class="scroll-x"><table class="cs-table"><thead><tr><th>${esc(t('gate'))}</th><th>${esc(t('version'))}</th><th>${esc(t('seal'))}</th><th>${esc(t('rules'))}</th><th></th></tr></thead>
        <tbody>${own.length ? own.map(g => `<tr><td><code>${esc(g.gate_id)}</code><br><span class="muted">${esc(g.title || '')}</span></td><td>${esc(g.version)}</td>
          <td><code>${esc((g.policy_seal || '').slice(0, 19))}…</code></td><td>${(g.hard_rules || []).length}</td>
          <td><button class="btn-ghost btn-sm" data-editgate="${esc(g.gate_id)}">${esc(L() === 'en' ? 'Edit in compiler' : 'Derleyicide aç')}</button> <button class="btn-ghost btn-sm" data-delgate="${esc(g.gate_id)}">${esc(t('del'))}</button></td></tr>`).join('') : `<tr><td colspan="5" class="muted">${esc(t('none'))}</td></tr>`}</tbody></table></div>
        <p><a class="btn-ghost btn-sm" href="../studio.html">${esc(t('openStudio'))}</a></p></div>
      <div class="cs-card"><form id="gForm" style="display:flex;flex-direction:column;gap:10px">
        <div class="field"><label for="gJson">${esc(t('pasteGate'))}</label><textarea id="gJson" rows="8" spellcheck="false">${esc(draftJson)}</textarea></div>
        <button class="btn-primary btn-sm" type="submit" style="align-self:flex-start">${esc(t('register'))}</button></form></div>`;
    $('#gForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      let spec;
      try { spec = JSON.parse($('#gJson').value); } catch (x) { toast('JSON?'); return; }
      if (spec.policy_spec) spec = spec.policy_spec;
      const c = await call('POST', '/v1/gates', spec);
      toast(c.ok ? (c.data.gate_id + ' · ' + (c.data.policy_seal || '').slice(0, 19)) : msg(c));
      if (c.ok) viewGates(el);
    });
    $$('[data-editgate]', el).forEach(b => b.addEventListener('click', () => {
      const g = own.find(x => x.gate_id === b.dataset.editgate);
      if (g) {
        try { sessionStorage.setItem('answerr_edit_gate', JSON.stringify(g)); } catch (e) { /* ignore */ }
        window.location.href = '../studio.html';
      }
    }));
    $$('[data-delgate]', el).forEach(b => b.addEventListener('click', async () => {
      if (b.dataset.armed !== '1') { b.dataset.armed = '1'; b.textContent = t('sure'); return; }
      const d = await call('DELETE', '/v1/gates/' + encodeURIComponent(b.dataset.delgate));
      if (!d.ok) toast(msg(d)); viewGates(el);
    }));
  }

  async function viewDecisions(el, before, append) {
    const f = S.cache.df || (S.cache.df = { verdict: '', mode: '', gate_id: '' });
    const q = new URLSearchParams({ limit: '100' });
    ['verdict', 'mode', 'gate_id'].forEach(k => f[k] && q.set(k, f[k]));
    if (before) q.set('before', before);
    const r = await call('GET', '/v1/account/decisions?' + q);
    if (!r.ok) { el.innerHTML = `<p class="note">${esc(msg(r))}</p>`; return; }
    const rows = r.data.decisions.map(d => `<tr><td>${fmtT(d.ts)}</td><td>${vchip(d.verdict)}</td><td><code>${esc(d.rule_id || '')}</code><br><span class="muted">${esc(d.reason || '')}</span></td>
      <td>${esc(d.gate_id || '—')}</td><td>${esc(d.mode)}</td><td>${d.observed ? vchip(d.observed) : '—'}</td><td>${esc(d.external_id || '')}</td><td>${esc(d.latency_ms)} ms</td></tr>`).join('');
    if (append) { $('#dBody').insertAdjacentHTML('beforeend', rows); }
    else {
      el.innerHTML = `<div class="cs-card"><h2>${esc(t('nav.decisions'))}</h2>
        <div class="cs-row">
          <div class="field"><label for="fV">${esc(t('verdict'))}</label><select id="fV"><option value="">${esc(t('all'))}</option><option>ALLOW</option><option>REVIEW</option><option>DENY</option></select></div>
          <div class="field"><label for="fM">${esc(t('mode'))}</label><select id="fM"><option value="">${esc(t('all'))}</option><option>live</option><option>shadow</option></select></div>
          <div class="field"><label for="fG">${esc(t('gate'))}</label><input id="fG" type="text" value="${esc(f.gate_id)}"></div>
          <button class="btn-ghost btn-sm" id="fCsv" type="button">${esc(t('csv'))}</button>
        </div>
        <p class="small-mono" style="margin:0">${esc(t('retention'))}: ${esc(r.data.retention_days)} ${esc(t('days'))}</p>
        <div class="scroll-x"><table class="cs-table"><thead><tr><th>${esc(t('time'))}</th><th>${esc(t('verdict'))}</th><th>${esc(t('rule'))}</th><th>${esc(t('gate'))}</th><th>${esc(t('mode'))}</th><th>${esc(t('observed'))}</th><th>ID</th><th>ms</th></tr></thead>
        <tbody id="dBody">${rows || `<tr><td colspan="8" class="muted">${esc(t('none'))}</td></tr>`}</tbody></table></div>
        <button class="btn-ghost btn-sm" id="dMore" type="button" hidden>${esc(t('more'))}</button></div>`;
      $('#fV').value = f.verdict; $('#fM').value = f.mode;
      const apply = () => { f.verdict = $('#fV').value; f.mode = $('#fM').value; f.gate_id = $('#fG').value.trim(); viewDecisions(el); };
      $('#fV').addEventListener('change', apply); $('#fM').addEventListener('change', apply); $('#fG').addEventListener('change', apply);
      $('#fCsv').addEventListener('click', async () => {
        const res = await call('GET', '/v1/account/decisions.csv?days=90', null, { raw: true });
        if (!res.ok) { let d = {}; try { d = await res.json(); } catch (e) { d = {}; } toast(msg({ status: res.status, data: d })); return; }
        const blob = await res.blob(); const a = document.createElement('a');
        a.href = URL.createObjectURL(blob); a.download = 'answerr-decisions.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
      });
    }
    const more = $('#dMore');
    more.hidden = !r.data.next_before;
    more.onclick = () => viewDecisions(el, r.data.next_before, true);
  }

  async function viewReviews(el) {
    if (!S.account.features.review_queue) { upgradeCard(el); return; }
    const st = S.cache.rs || 'pending';
    const r = await call('GET', '/v1/reviews?status=' + st + '&limit=100');
    if (!r.ok) { el.innerHTML = `<p class="note">${esc(msg(r))}</p>`; return; }
    el.innerHTML = `<div class="cs-card"><h2>${esc(t('nav.reviews'))}</h2>
      <div class="tabs">${['pending', 'approved', 'rejected', 'expired'].map(s => `<button type="button" data-rs="${s}" aria-selected="${s === st}">${esc(t(s))}</button>`).join('')}</div>
      ${r.data.reviews.length ? '' : `<p class="muted">${esc(t('none'))}</p>`}
      ${r.data.reviews.map(v => `<article class="cs-card" style="background:#07090E">
        <div class="cs-row" style="justify-content:space-between"><span>${vchip('REVIEW')} <code>${esc(v.gate_id || '')}</code> · <code>${esc(v.rule_id || '')}</code></span><span class="small-mono">${fmtT(v.ts)} · ${esc(v.id)}${v.external_id ? ' · ' + esc(v.external_id) : ''}</span></div>
        <p style="margin:0">${esc(v.reason || '')}</p>
        ${v.state ? `<pre class="code" style="max-height:220px">${esc(JSON.stringify(v.state, null, 2))}</pre>` : `<p class="small-mono">${esc(t('noState'))}</p>`}
        ${v.status === 'pending' ? `<div class="cs-row"><div class="field"><label for="n_${esc(v.id)}">${esc(t('note'))}</label><input id="n_${esc(v.id)}" type="text" maxlength="500"></div>
          <button class="btn-primary btn-sm" data-act="approve" data-id="${esc(v.id)}">${esc(t('approve'))}</button>
          <button class="btn-ghost btn-sm" data-act="reject" data-id="${esc(v.id)}" style="border-color:var(--stop)">${esc(t('reject'))}</button></div>`
          : `<p class="small-mono">${esc(t(v.status))} · ${esc(v.resolved_by || '')} · ${fmtT(v.resolved_at)} ${v.note ? '· ' + esc(v.note) : ''}</p>`}
      </article>`).join('')}</div>`;
    $$('[data-rs]', el).forEach(b => b.addEventListener('click', () => { S.cache.rs = b.dataset.rs; viewReviews(el); }));
    $$('[data-act]', el).forEach(b => b.addEventListener('click', async () => {
      const note = ($('#n_' + CSS.escape(b.dataset.id)) || {}).value || null;
      const d = await call('POST', '/v1/reviews/' + encodeURIComponent(b.dataset.id) + '/resolve', { action: b.dataset.act, note });
      if (!d.ok) toast(msg(d)); viewReviews(el); refreshReviewCount();
    }));
  }

  async function viewShadow(el) {
    if (!S.account.features.shadow) { upgradeCard(el); return; }
    const days = S.cache.sd || 30;
    const r = await call('GET', '/v1/account/shadow-report?days=' + days);
    if (!r.ok) { el.innerHTML = `<p class="note">${esc(msg(r))}</p>`; return; }
    const rep = r.data.report, cols = ['ALLOW', 'REVIEW', 'DENY', 'unknown'];
    el.innerHTML = `<div class="cs-card"><h2>${esc(t('nav.shadow'))}</h2>
        <div class="cs-row"><div class="field" style="flex:0 0 160px"><label for="sd">${esc(t('days'))}</label><select id="sd">${[7, 30, 90].map(d => `<option ${d === days ? 'selected' : ''}>${d}</option>`).join('')}</select></div></div>
        <div class="cs-kpis">
          <div class="cs-kpi"><small>${esc(t('decisionsN'))}</small><b>${fmtN(rep.decisions)}</b></div>
          <div class="cs-kpi"><small>${esc(t('labelled'))}</small><b>${fmtN(rep.labelled)}</b></div>
          <div class="cs-kpi"><small>${esc(t('agreement'))}</small><b>${rep.agreement == null ? '—' : (rep.agreement * 100).toFixed(1) + '%'}</b></div>
          <div class="cs-kpi"><small>${esc(t('stricter'))}</small><b>${fmtN(rep.stricter_than_you)}</b></div>
          <div class="cs-kpi"><small>${esc(t('looser'))}</small><b>${fmtN(rep.looser_than_you)}</b></div>
        </div>
        <p class="small-mono" style="margin:0">${esc(t('rowsAre'))}</p>
        <div class="scroll-x"><table class="cs-table"><thead><tr><th></th>${cols.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead>
          <tbody>${['ALLOW', 'REVIEW', 'DENY'].map(v => `<tr><td>${vchip(v)}</td>${cols.map(c => `<td>${fmtN(rep.matrix[v][c])}</td>`).join('')}</tr>`).join('')}</tbody></table></div></div>
      <div class="cs-card"><h2>${esc(t('backtest'))}</h2><p class="muted" style="margin:0">${esc(t('btLead'))}</p>
        <form id="btForm" style="display:flex;flex-direction:column;gap:10px">
          <div class="field"><label for="btGate">${esc(t('gate'))}</label><input id="btGate" type="text" value="agent_mcp_guard"></div>
          <div class="field"><label for="btRec">${esc(t('records'))}</label><textarea id="btRec" rows="7" spellcheck="false">[{"state": {"tool_name": "drop_table", "user_role": "admin"}, "observed_outcome": "ALLOW", "id": "case-1"},
 {"state": {"tool_name": "list_orders", "user_role": "member"}, "observed_outcome": "ALLOW", "id": "case-2"}]</textarea></div>
          <button class="btn-primary btn-sm" type="submit" style="align-self:flex-start">${esc(t('run'))}</button></form><div id="btOut"></div></div>`;
    $('#sd').addEventListener('change', () => { S.cache.sd = +$('#sd').value; viewShadow(el); });
    $('#btForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      let recs;
      try { recs = JSON.parse($('#btRec').value); } catch (x) { toast('JSON?'); return; }
      const d = await call('POST', '/v1/backtest', { gate_id: $('#btGate').value.trim(), records: recs });
      if (!d.ok) { toast(msg(d)); return; }
      const b = d.data;
      $('#btOut').innerHTML = `<div class="cs-kpis"><div class="cs-kpi"><small>${esc(t('records').split(' ')[0])}</small><b>${fmtN(b.records)}</b></div>
        <div class="cs-kpi"><small>${esc(t('agreement'))}</small><b>${b.agreement == null ? '—' : (b.agreement * 100).toFixed(1) + '%'}</b></div>
        <div class="cs-kpi"><small>${esc(t('stricter'))}</small><b>${fmtN(b.stricter_than_you)}</b></div><div class="cs-kpi"><small>ms</small><b>${esc(b.elapsed_ms)}</b></div></div>
        <h3 style="margin-top:14px">${esc(t('differences'))}</h3>
        <table class="cs-table"><tbody>${b.differences.map(x => `<tr><td>${esc(x.id || '#' + x.index)}</td><td>${vchip(x.verdict)}</td><td>${vchip(x.observed)}</td><td><code>${esc(x.rule_id)}</code></td></tr>`).join('') || `<tr><td class="muted">${esc(t('none'))}</td></tr>`}</tbody></table>`;
      S.account.usage.decisions += b.records;
    });
  }

  async function viewTeam(el) {
    const r = await call('GET', '/v1/account/members');
    if (!r.ok) { el.innerHTML = `<p class="note">${esc(msg(r))}</p>`; return; }
    el.innerHTML = `<div class="cs-card"><h2>${esc(t('members'))} · ${r.data.members.length} / ${esc(r.data.seats)} ${esc(t('seats'))}</h2>
      <table class="cs-table"><thead><tr><th>${esc(t('emailCol'))}</th><th>${esc(t('role'))}</th><th>${esc(t('joined'))}</th><th></th></tr></thead>
      <tbody>${r.data.members.map(m => `<tr><td>${esc(m.email)}</td><td>${esc(t('roles.' + m.role))}</td><td>${m.joined_at ? fmtT(m.joined_at) : esc(t('invited'))}</td>
        <td>${m.role === 'owner' ? '' : `<button class="btn-ghost btn-sm" data-rm="${esc(m.email)}">${esc(t('remove'))}</button>`}</td></tr>`).join('')}</tbody></table>
      <form id="invForm" class="cs-row"><div class="field"><label for="invE">${esc(t('emailCol'))}</label><input id="invE" type="email" required></div>
        <div class="field" style="flex:0 0 180px"><label for="invR">${esc(t('role'))}</label><select id="invR"><option value="reviewer">${esc(t('roles.reviewer'))}</option><option value="admin">${esc(t('roles.admin'))}</option></select></div>
        <button class="btn-primary btn-sm" type="submit">${esc(t('invite'))}</button></form></div>`;
    $('#invForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const d = await call('POST', '/v1/account/members', { email: $('#invE').value.trim(), role: $('#invR').value });
      if (!d.ok) { toast(msg(d)); return; } viewTeam(el);
    });
    $$('[data-rm]', el).forEach(b => b.addEventListener('click', async () => {
      if (b.dataset.armed !== '1') { b.dataset.armed = '1'; b.textContent = t('sure'); return; }
      const d = await call('DELETE', '/v1/account/members/' + encodeURIComponent(b.dataset.rm)); if (!d.ok) toast(msg(d)); viewTeam(el);
    }));
  }

  async function viewBilling(el) {
    if (!S.plans) { const p = await call('GET', '/v1/plans', null, { anon: true }); S.plans = p.ok ? p.data : null; }
    const [st, acc, pays] = await Promise.all([call('GET', '/v1/account/statements'), call('GET', '/v1/account'), call('GET', '/v1/account/payments')]);
    if (acc.ok) S.account = acc.data.account;
    const a = S.account, plans = S.plans ? S.plans.plans : {}, card = Boolean(S.plans && S.plans.card_payments);
    const pend = a.pending_plan_request;
    const b = a.billing || {};
    const est = st.ok ? st.data.current_period_estimate : null;
    const tl = (v) => v == null ? '' : Number(v).toLocaleString('tr-TR', { minimumFractionDigits: Number(v) % 1 ? 2 : 0, maximumFractionDigits: 2 }) + ' ₺';
    const plist = pays.ok ? pays.data.payments : [];
    const paidPlan = ['gelistirici', 'pro'].includes(a.plan) && a.plan_expires_at;
    el.innerHTML = `
      <div class="cs-card"><h2>${esc(t('current'))}: ${esc(a.plan_name[L()] || a.plan)}${a.billing_cycle === 'yearly' ? ' · ' + esc(t('yearly')) : ''}</h2>
        ${paidPlan ? `<p class="small-mono" style="margin:0">${esc(t('paidUntil'))}: <b>${fmtT(a.plan_expires_at)}</b></p>` : ''}
        ${pend ? `<p class="note">${esc(t('pendingReq'))}: <b>${esc(pend.plan)}</b> · ${esc(pend.cycle)} · ${fmtT(pend.ts)}</p>` : ''}
        <div class="cs-row"><div class="bill" role="group"><button type="button" data-cy="monthly" aria-pressed="true">${esc(t('monthly'))}</button><button type="button" data-cy="yearly" aria-pressed="false">${esc(t('yearly'))}</button></div></div>
        <div class="plans">${Object.entries(plans).map(([id, p]) => {
          const paid = p.price_monthly_try != null;
          const isCur = id === a.plan;
          let act;
          if (id === 'kurumsal') act = `<a class="btn-ghost btn-sm" href="mailto:ask@answerr.me?subject=answerr%20Kurumsal">${esc(t('contact'))}</a>`;
          else if (paid) act = `${card ? `<button class="btn-primary btn-sm" type="button" data-pay="${esc(id)}">${esc(isCur ? t('renew') : t('payCard'))}</button>` : ''}
            <button class="btn-primary btn-sm" type="button" data-crypto="${esc(id)}" style="background:#38bdf8;border-color:#38bdf8;color:#05060a">${esc(t('payCrypto'))}</button>
            <button class="btn-ghost btn-sm" type="button" data-plan="${esc(id)}">${esc(t('payBank'))}</button>`;
          else if (isCur) act = `<span class="chip v-allow">${esc(t('current'))}</span>`;
          else act = `<button class="btn-primary btn-sm" type="button" data-plan="${esc(id)}">${esc(t('choose'))}</button>`;
          return `<article class="plan ${isCur ? 'hot' : ''}">
          <div class="pname">${esc(L() === 'en' ? p.name_en : p.name_tr)}</div>
          <div class="price" style="font-size:36px">${p.price_monthly == null ? '$' + fmtN(p.price_yearly_from) + '+' : paid
            ? `<span data-pm="${p.price_monthly_try}" data-py="${p.price_yearly_per_month_try}" data-tl="1">${tl(p.price_monthly_try)}</span>`
            : `<span>$${p.price_monthly}</span>`}<small>${p.price_monthly == null ? esc(t('perYear')) : esc(t('perMonth'))}</small></div>
          ${paid ? `<div class="small-mono">${esc(t('vatIncl'))} · <b data-pmu="${p.price_monthly}" data-pyu="${p.price_yearly_per_month}">$${p.price_monthly} USDC/USDT</b> ${esc(t('perMonth'))}</div>` : ''}
          <div class="quota">${p.quota == null ? esc(t('unlimited')) : fmtN(p.quota)} · ${esc(t('retention'))} ${p.retention_days} ${esc(t('days'))}</div>
          <div class="cs-row" style="gap:8px;flex-wrap:wrap">${act}</div></article>`; }).join('')}</div>
        <div id="cryptoBox" class="cs-card" style="display:none;margin-top:14px;border-color:#38bdf8;background:rgba(14,22,40,0.9)">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px">
            <h3 id="crTitle" style="margin:0;color:#38bdf8">${esc(t('crTitle'))}</h3>
            <button type="button" class="btn-ghost btn-sm" id="crClose" aria-label="Close">✕</button>
          </div>
          <p class="small-mono" id="crAmountInfo" style="margin:8px 0"></p>
          <div class="cs-row" style="gap:10px;flex-wrap:wrap;margin-bottom:10px">
            <button type="button" class="btn-primary btn-sm" id="crWeb3Btn" style="background:#38bdf8;border-color:#38bdf8;color:#05060a">${esc(t('crWeb3'))}</button>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-top:8px">
            <div class="field"><label for="crNet">${esc(t('crNet'))}</label>
              <select id="crNet">
                <option value="trc20">TRON (TRC20) — USDT</option>
                <option value="base">Base Mainnet — USDC / USDT</option>
                <option value="ethereum">Ethereum (ERC20) — USDT / USDC</option>
                <option value="arbitrum">Arbitrum One — USDT / USDC</option>
                <option value="bsc">BNB Smart Chain (BEP20) — USDT / USDC</option>
              </select>
            </div>
            <div class="field"><label for="crTok">Token</label>
              <select id="crTok"><option value="USDT">USDT</option><option value="USDC">USDC</option></select>
            </div>
          </div>
          <div class="small-mono" style="margin:8px 0">${esc(t('crAddr'))}: <code id="crAddr" style="color:#10b981;word-break:break-all">TLMhaDJTVYBHBSGJ9nCQGLvqnYFPsBgLJu</code></div>
          <div class="cs-row" style="gap:8px;align-items:flex-end;flex-wrap:wrap">
            <div class="field" style="flex:1 1 280px"><label for="crTx">${esc(t('crTx'))}</label><input id="crTx" type="text" placeholder="${esc(t('crTxPh'))}"></div>
            <button type="button" class="btn-primary btn-sm" id="crVerifyBtn">${esc(t('crVerify'))}</button>
          </div>
          <p class="small-mono" id="crStatus" style="margin:8px 0 0"></p>
        </div>
        <label class="check-line"><input type="checkbox" id="salesOk"><span>${t('salesOk')}</span></label>
        ${card ? `<p class="small-mono" style="margin:0">${esc(t('cardNote'))}</p>` : ''}
        <p class="small-mono" id="planStatus" aria-live="polite"></p>
        ${a.limits.overage_per_1000 ? `<label class="check-line"><input type="checkbox" id="ovr" ${a.overage_enabled ? 'checked' : ''}><span>${esc(t('overageToggle'))} ($${esc(a.limits.overage_per_1000)} ${esc(t('perThousand'))})</span></label>` : ''}
      </div>
      ${plist.length ? `<div class="cs-card"><h2>${esc(t('payments'))}</h2>
        <div class="scroll-x"><table class="cs-table"><thead><tr><th>${esc(t('when'))}</th><th>${esc(t('plan'))}</th><th>${esc(t('total'))} (${esc(t('vatIncl'))})</th><th>${esc(t('status'))}</th><th>${esc(t('paidUntil'))}</th></tr></thead>
        <tbody>${plist.map(x => `<tr><td>${fmtT(x.paid_at || x.created_at)}</td><td>${esc(x.plan || x.kind)} · ${esc(x.cycle || '')}</td><td>${(x.currency && x.currency !== 'TRY') ? esc(x.total_try + ' ' + x.currency) : tl(x.total_try)}</td><td>${esc(t('st.' + x.status) !== 'st.' + x.status ? t('st.' + x.status) : x.status)}${x.card_last4 ? ' · ' + esc(/^\d{4}$/.test(x.card_last4) ? '****' + x.card_last4 : x.card_last4) : ''}</td><td>${x.period_end ? fmtT(x.period_end) : '—'} <button type="button" class="btn-ghost btn-sm" data-inv="${esc(x.id)}" style="margin-left:6px">${esc(x.status === 'paid' ? t('invPdf') : t('proPdf'))}</button></td></tr>`).join('')}</tbody></table></div></div>` : ''}
      <div class="cs-card"><h2>${esc(t('statements'))}</h2>
        ${est ? `<p class="small-mono" style="margin:0">${esc(t('estimate'))} (${esc(est.period)}): ${esc(t('base'))} ${money(est.base_cents, est.currency)} + ${esc(t('overage'))} ${money(est.overage_cents, est.currency)} = <b>${money(est.total_cents, est.currency)}</b> · ${fmtN(est.used)} / ${est.quota == null ? '—' : fmtN(est.quota)}</p>` : ''}
        <div class="scroll-x"><table class="cs-table"><thead><tr><th>${esc(t('period'))}</th><th>${esc(t('plan'))}</th><th>${esc(t('total'))}</th><th>${esc(t('status'))}</th><th>${esc(t('einv'))}</th></tr></thead>
        <tbody>${st.ok && st.data.statements.length ? st.data.statements.map(s => `<tr><td>${esc(s.period)}</td><td>${esc(s.plan)}</td><td>${money(s.total_cents, s.currency)}</td><td>${esc(s.status)}</td><td>${esc(s.e_invoice_no || '—')}</td></tr>`).join('') : `<tr><td colspan="5" class="muted">${esc(t('none'))}</td></tr>`}</tbody></table></div>
        <p class="small-mono" style="margin:0">${esc(S.plans ? (L() === 'tr' ? S.plans.vat_note_tr : S.plans.vat_note) : '')}</p></div>
      <div class="cs-card" id="bfCard"><h2>${esc(t('billingInfo'))}</h2>
        <form id="bfForm" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">
          ${Object.keys(T.tr.bf).map(k => `<div class="field"><label for="bf_${k}">${esc(t('bf.' + k))}</label><input id="bf_${k}" type="text" maxlength="300" value="${esc(b[k] || '')}"></div>`).join('')}
          <button class="btn-primary btn-sm" type="submit" style="align-self:end">${esc(t('save'))}</button></form></div>`;
    let cycle = 'monthly';
    const pending = S.pendingPay; S.pendingPay = null;
    $$('[data-cy]', el).forEach(btn => btn.addEventListener('click', () => {
      cycle = btn.dataset.cy;
      $$('[data-cy]', el).forEach(x => x.setAttribute('aria-pressed', String(x === btn)));
      $$('[data-pm]', el).forEach(s => { const v = cycle === 'yearly' ? s.dataset.py : s.dataset.pm; s.textContent = s.dataset.tl ? tl(v) : '$' + v; });
      $$('[data-pmu]', el).forEach(s => { s.textContent = '$' + (cycle === 'yearly' ? s.dataset.pyu : s.dataset.pmu); });
      if ($('#cryptoBox') && $('#cryptoBox').style.display === 'block' && typeof getQuote === 'function') getQuote();
    }));
    if (pending) {
      const pb = $('[data-cy="' + pending.cycle + '"]', el); if (pb) pb.click();
      const pn = plans[pending.plan] ? (L() === 'en' ? plans[pending.plan].name_en : plans[pending.plan].name_tr) : pending.plan;
      $('#planStatus').textContent = t('pendingCard').replace('{p}', pn);
      const sc = $('#salesOk'); if (sc) sc.checked = true;
      setTimeout(() => { $('#bfCard').scrollIntoView({ behavior: 'smooth', block: 'start' }); const f = $('#bf_address'); if (f) f.focus(); }, 300);
    }
    const needConsent = () => {
      if ($('#salesOk').checked) return false;
      $('#planStatus').textContent = '☐ ' + t('salesOk').replace(/<[^>]+>/g, ''); $('#salesOk').focus(); return true;
    };
    $$('[data-plan]', el).forEach(btn => btn.addEventListener('click', async () => {
      const id = btn.dataset.plan;
      if (id !== 'kesif' && needConsent()) return;
      const d = await call('POST', '/v1/account/plan-request', { plan: id, cycle, note: 'mesafeli-satis onayi ' + new Date().toISOString() });
      if (d.ok && d.data.proforma_invoice_pdf_url) {
        $('#planStatus').innerHTML = '⏳ ' + t('bankReq');
        setTimeout(() => viewBilling(el), 1800);
        return;
      }
      $('#planStatus').textContent = d.ok ? (d.data.status === 'changed' ? t('saved') : d.data.status === 'scheduled' ? t('scheduled') : t('reqSent')) : msg(d);
      if (d.ok) setTimeout(() => viewBilling(el), 1200);
    }));
    $$('[data-pay]', el).forEach(btn => btn.addEventListener('click', async () => {
      if (needConsent()) return;
      btn.disabled = true; $('#planStatus').textContent = t('payOpening');
      const d = await call('POST', '/v1/account/checkout', { plan: btn.dataset.pay, cycle, accept_preinfo: true, accept_distance_sale: true, lang: L() });
      if (d.ok && d.data.payment_page_url && /^https:\/\/[a-z0-9.-]*iyzipay\.com\//i.test(d.data.payment_page_url)) { location.assign(d.data.payment_page_url); return; }
      btn.disabled = false;
      if (!d.ok && d.data && d.data.error === 'billing_incomplete') {
        $('#planStatus').textContent = t('payNeedBilling');
        const miss = (d.data.missing || [])[0]; const f = miss && $('#bf_' + miss);
        $('#bfCard').scrollIntoView({ behavior: 'smooth', block: 'start' }); if (f) f.focus();
        return;
      }
      $('#planStatus').textContent = d.ok ? t('payUnknown') : msg(d);
    }));
    let curCryptoPlan = 'pro';
    const EVM_ADDR = '0x4945ef6e124eea2176ddf050b33db42b0ae8c7f7';
    const TRON_ADDR = 'TLMhaDJTVYBHBSGJ9nCQGLvqnYFPsBgLJu';
    const BASE_USDC = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
    let curQuote = null;   // order-specific amount from POST /v1/checkout/crypto-quote (unique cents, valid 72 h)
    const getQuote = async () => {
      curQuote = null; updCrInfo();
      const d = await call('POST', '/v1/checkout/crypto-quote', { plan: curCryptoPlan, cycle });
      if (!d.ok) { $('#crStatus').textContent = msg(d); return; }
      curQuote = d.data; updCrInfo();
    };
    const updCrInfo = () => {
      const amt = curQuote ? curQuote.amount : '…';
      const pName = plans[curCryptoPlan] ? (L() === 'en' ? plans[curCryptoPlan].name_en : plans[curCryptoPlan].name_tr) : curCryptoPlan;
      if ($('#crAmountInfo')) $('#crAmountInfo').textContent = t('crAmount').replace('{p}', pName).replace('{c}', cycle === 'yearly' ? t('yearly') : t('monthly')).replace('{a}', amt);
      if ($('#crAddr') && $('#crNet')) $('#crAddr').textContent = $('#crNet').value === 'trc20' ? TRON_ADDR : EVM_ADDR;
    };
    if ($('#crNet')) $('#crNet').addEventListener('change', () => {
      if ($('#crNet').value === 'trc20' && $('#crTok')) $('#crTok').value = 'USDT';
      updCrInfo();
    });
    if ($('#crClose')) $('#crClose').addEventListener('click', () => { $('#cryptoBox').style.display = 'none'; });
    $$('[data-crypto]', el).forEach(btn => btn.addEventListener('click', () => {
      if (needConsent()) return;
      curCryptoPlan = btn.dataset.crypto;
      $('#cryptoBox').style.display = 'block';
      $('#crStatus').textContent = '';
      getQuote();
      $('#cryptoBox').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }));
    if ($('#crWeb3Btn')) $('#crWeb3Btn').addEventListener('click', async () => {
      if (needConsent()) return;
      if (!window.ethereum) { $('#crStatus').textContent = t('crNoWallet'); return; }
      try {
        $('#crStatus').textContent = t('crConnecting');
        const accs = await window.ethereum.request({ method: 'eth_requestAccounts' });
        try { await window.ethereum.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: '0x2105' }] }); }
        catch (sw) {
          if (sw.code === 4902) await window.ethereum.request({ method: 'wallet_addEthereumChain', params: [{ chainId: '0x2105', chainName: 'Base Mainnet', nativeCurrency: { name: 'ETH', symbol: 'ETH', decimals: 18 }, rpcUrls: ['https://mainnet.base.org'], blockExplorerUrls: ['https://basescan.org'] }] });
          else throw sw;
        }
        if (!curQuote) { $('#crStatus').textContent = t('errs.quote_required'); return; }
        const amt = curQuote.amount;
        const units = BigInt(Math.round(Number(amt) * 1e6)).toString(16).padStart(64, '0');
        const dataHex = '0xa9059cbb' + EVM_ADDR.toLowerCase().replace(/^0x/, '').padStart(64, '0') + units;
        $('#crStatus').textContent = t('crConfirm').replace('{a}', amt);
        const txHash = await window.ethereum.request({ method: 'eth_sendTransaction', params: [{ from: accs[0], to: BASE_USDC, data: dataHex }] });
        $('#crTx').value = txHash; $('#crNet').value = 'base'; $('#crTok').value = 'USDC';
        $('#crStatus').textContent = t('crSent');
        for (let i = 0; i < 40; i++) {
          await new Promise(r => setTimeout(r, 2000));
          const rec = await window.ethereum.request({ method: 'eth_getTransactionReceipt', params: [txHash] });
          if (rec && rec.status === '0x1') break;
        }
        $('#crVerifyBtn').click();
      } catch (e) { $('#crStatus').textContent = t('crErr') + (e.message || String(e)); }
    });
    if ($('#crVerifyBtn')) $('#crVerifyBtn').addEventListener('click', async () => {
      if (needConsent()) return;
      const txHash = ($('#crTx').value || '').trim();
      if (!txHash) { $('#crStatus').textContent = t('crNeedTx'); return; }
      $('#crVerifyBtn').disabled = true; $('#crStatus').textContent = t('crVerifying');
      if (!curQuote) { $('#crStatus').textContent = t('errs.quote_required'); return; }
      const d = await call('POST', '/v1/account/crypto-checkout', {
        plan: curCryptoPlan, cycle, quote_id: curQuote.quote_id, tx_hash: txHash, network: $('#crNet').value, token: $('#crTok').value,
        accept_preinfo: true, accept_distance_sale: true
      });
      $('#crVerifyBtn').disabled = false;
      if (!d.ok) { $('#crStatus').textContent = msg(d); return; }
      toast(t('payPaid'));
      viewBilling(el);
    });
    $$('[data-inv]', el).forEach(btn => btn.addEventListener('click', () => downloadInvoice('/v1/account/payments/' + encodeURIComponent(btn.dataset.inv) + '/invoice.pdf', btn)));

    const ovr = $('#ovr');
    if (ovr) ovr.addEventListener('change', async () => { const d = await call('PATCH', '/v1/account', { overage_enabled: ovr.checked }); toast(d.ok ? t('saved') : msg(d)); });
    $('#bfForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const billing = {}; Object.keys(T.tr.bf).forEach(k => { billing[k] = $('#bf_' + k).value.trim(); });
      const d = await call('PATCH', '/v1/account', { billing }); toast(d.ok ? t('saved') : msg(d));
    });
  }

  async function viewSettings(el) {
    const a = S.account;
    const [wh, ev] = await Promise.all([call('GET', '/v1/account/webhooks'), call('GET', '/v1/account/events?limit=50')]);
    el.innerHTML = `
      <div class="cs-card"><h2>${esc(t('nav.settings'))}</h2>
        <form id="stForm" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">
          <div class="field"><label for="stCo">${esc(t('company').replace(/ \(.*\)/, ''))}</label><input id="stCo" type="text" maxlength="120" value="${esc(a.company || '')}"></div>
          <div class="field"><label for="stLang">${esc(t('lang'))}</label><select id="stLang"><option value="tr" ${a.lang === 'tr' ? 'selected' : ''}>Türkçe</option><option value="en" ${a.lang === 'en' ? 'selected' : ''}>English</option></select></div>
          <label class="check-line" style="grid-column:1/-1"><input type="checkbox" id="stState" ${a.store_review_state ? 'checked' : ''}><span>${esc(t('storeState'))}</span></label>
          <button class="btn-primary btn-sm" type="submit" style="align-self:end">${esc(t('save'))}</button></form></div>
      <div class="cs-card"><h2>${esc(t('webhooksTitle'))}</h2>
        ${a.features.webhooks ? `
        <form id="whForm" class="cs-row"><div class="field" style="flex:3 1 320px"><label for="whUrl">${esc(t('webhook'))}</label><input id="whUrl" type="url" value="${esc(a.webhook_url || '')}" placeholder="https://"></div>
          <button class="btn-primary btn-sm" type="submit">${esc(t('save'))}</button><button class="btn-ghost btn-sm" type="button" id="whTest">${esc(t('test'))}</button></form>
        <div class="cs-row"><span class="small-mono">${esc(t('secret'))}</span><button class="btn-ghost btn-sm" type="button" id="whShow">${esc(t('show'))}</button><button class="btn-ghost btn-sm" type="button" id="whRot">${esc(t('rotate'))}</button></div>
        <div id="whSecret"></div>
        <h3>${esc(t('deliveries'))}</h3>
        <table class="cs-table"><tbody>${wh.ok && wh.data.deliveries.length ? wh.data.deliveries.map(d => `<tr><td>${fmtT(d.ts)}</td><td>${esc(d.event)}</td><td>${esc(d.status_code || '—')}</td><td>${esc(d.attempts)}</td><td>${esc(d.error || 'ok')}</td></tr>`).join('') : `<tr><td class="muted">${esc(t('none'))}</td></tr>`}</tbody></table>`
        : `<p class="muted">${esc(t('upgrade'))}</p>`}
      </div>
      <div class="cs-card"><h2>${esc(t('events'))}</h2>
        <table class="cs-table"><tbody>${ev.ok ? ev.data.events.map(e => `<tr><td>${fmtT(e.ts)}</td><td>${esc(e.action)}</td><td>${esc(e.actor || '')}</td><td class="small-mono">${esc(e.detail || '')}</td></tr>`).join('') : ''}</tbody></table></div>`;
    $('#stForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const d = await call('PATCH', '/v1/account', { company: $('#stCo').value.trim(), lang: $('#stLang').value, store_review_state: $('#stState').checked });
      if (d.ok) S.account = Object.assign(S.account, d.data.account); toast(d.ok ? t('saved') : msg(d));
    });
    if (!a.features.webhooks) return;
    $('#whForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const d = await call('PATCH', '/v1/account', { webhook_url: $('#whUrl').value.trim() });
      if (d.ok) S.account = Object.assign(S.account, d.data.account); toast(d.ok ? t('saved') : msg(d));
    });
    const showSecret = (s) => { $('#whSecret').innerHTML = `<div class="secret">${esc(s || '—')}</div>`; if (s) $('#whSecret').appendChild(copyBtn(s)); };
    $('#whShow').addEventListener('click', async () => { const d = await call('GET', '/v1/account/webhook-secret'); d.ok ? showSecret(d.data.webhook_secret) : toast(msg(d)); });
    $('#whRot').addEventListener('click', async (e) => {
      const b = e.currentTarget; if (b.dataset.armed !== '1') { b.dataset.armed = '1'; b.textContent = t('sure'); return; }
      const d = await call('POST', '/v1/account/webhook-secret'); d.ok ? showSecret(d.data.webhook_secret) : toast(msg(d));
    });
    $('#whTest').addEventListener('click', async () => { const d = await call('POST', '/v1/account/webhook-test'); toast(d.ok ? JSON.stringify(d.data.deliveries[0] || {}) : msg(d)); viewSettings(el); });
  }

  const VIEW_FN = { overview: viewOverview, keys: viewKeys, gates: viewGates, decisions: viewDecisions, reviews: viewReviews,
                    shadow: viewShadow, team: viewTeam, billing: viewBilling, settings: viewSettings };

    /* ------------------------------------------------------------------ start */
  document.addEventListener('DOMContentLoaded', async () => {
    window.addEventListener('proLanguageChanged', () => {
      if (S.account) renderShell();
      else {
        const urlP = new URLSearchParams(location.search).get('plan');
        renderAuth(location.hash.indexOf('signup') >= 0 ? 'signup' : 'signin', urlP);
      }
    });

    window.addEventListener('hashchange', () => {
      if (/login=/.test(location.hash)) { verifyFromHash(); return; }
      const v = location.hash.replace('#', '');
      const urlP = new URLSearchParams(location.search).get('plan');
      if (S.account && VIEWS.includes(v) && v !== S.view) { S.view = v; renderShell(); }
      else if (!S.account && (v.indexOf('signup') >= 0 || v === '')) renderAuth(v.indexOf('signup') >= 0 ? 'signup' : 'signin', urlP);
    });

    const pr = new URLSearchParams(location.search).get('payment');
    if (pr) {
      history.replaceState(null, '', location.pathname + (S.session ? '#billing' : ''));
      const k = { paid: 'payPaid', failed: 'payFailed', review: 'payReview' }[pr] || 'payUnknown';
      setTimeout(() => toast(t(k)), 400);
    }

    if (await verifyFromHash()) return;

    const urlPlan = new URLSearchParams(location.search).get('plan');
    if (location.hash.indexOf('signup') >= 0 || urlPlan) {
      if (S.session) {
        // If already signed in, open billing directly and scroll to the selected plan
        S.view = 'billing';
        await boot();
        return;
      }
      renderAuth('signup', urlPlan);
      return;
    }

    if (S.session) { await boot(); return; }
    renderAuth(location.hash.indexOf('signup') >= 0 ? 'signup' : 'signin');
  });
})();
