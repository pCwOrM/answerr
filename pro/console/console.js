/* answerr console — accounts, keys, usage, decision log, reviews, shadow mode, team, plan & billing, settings.
   Talks to api.answerr.me with a session token (Authorization: Bearer ans_sess_…). Every server value is escaped. */
(function () {
  'use strict';
  const A = () => window.ProApp;
  const L = () => (window.ProI18n ? window.ProI18n.lang : 'tr');
  const SKEY = 'answerr_session';
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const $ = (sel, el) => (el || document).querySelector(sel);
  const $$ = (sel, el) => Array.from((el || document).querySelectorAll(sel));

  /* ------------------------------------------------------------------ dictionary */
  const T = {
    tr: {
      signin: 'Giriş', signup: 'Hesap aç', email: 'İş e-postası', company: 'Şirket (isteğe bağlı)',
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
      signin: 'Sign in', signup: 'Create account', email: 'Work e-mail', company: 'Company (optional)',
      terms: 'I accept the <a href="../legal/kullanim-sartlari.html" target="_blank" rel="noopener">terms of service</a> and the <a href="../legal/veri-isleme.html" target="_blank" rel="noopener">data processing agreement</a>.',
      kvkk: 'I have read the <a href="../legal/kvkk-aydinlatma.html" target="_blank" rel="noopener">KVKK privacy notice</a>.',
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
    let activeAuthPlan = 'kesif';
  let activeAuthCycle = 'monthly';
  let activeAuthPayTab = 'crypto';

  function renderAuth(tab, initialPlan) {
    tab = tab || (location.hash.indexOf('signup') >= 0 ? 'signup' : 'signin');
    if (initialPlan) activeAuthPlan = initialPlan;
    else {
      const qp = new URLSearchParams(location.search).get('plan');
      if (qp) activeAuthPlan = qp;
    }

    const prevEmail = ($('#auEmail') || {}).value || '';
    const prevCo = ($('#auCo') || {}).value || '';
    const prevTax = ($('#auTax') || {}).value || '';
    const prevAddr = ($('#auAddr') || {}).value || '';
    const prevTerms = Boolean(($('#auTerms') || {}).checked);
    const prevKvkk = Boolean(($('#auKvkk') || {}).checked);
    const prevMkt = Boolean(($('#auMkt') || {}).checked);
    const who = document.getElementById('csWho');
    if (who) who.textContent = '';

    const isPaid = ['gelistirici', 'pro'].includes(activeAuthPlan);
    const prices = {
      kesif: { usd_m: 0, try_m: 0, name: 'Keşif', desc: '10.000 Karar/ay · $0' },
      gelistirici: { usd_m: 29, usd_y: 24, try_m: '1.449 ₺', try_y: '1.199 ₺', name: 'Geliştirici', desc: '250.000 Karar/ay · 5 Anahtar' },
      pro: { usd_m: 99, usd_y: 82, try_m: '4.899 ₺', try_y: '4.049 ₺', name: 'Pro 🔥', desc: '1.000.000 Karar/ay · Gölge Mod' },
      kurumsal: { usd_m: null, name: 'Kurumsal', desc: 'Özel Hacim · 7/24 SLA' }
    };

    const curP = prices[activeAuthPlan] || prices.kesif;
    const curAmtUsd = activeAuthCycle === 'yearly' && curP.usd_y ? curP.usd_y * 12 : (curP.usd_m || 0);
    const curAmtTry = activeAuthCycle === 'yearly' && curP.try_y ? curP.try_y : (curP.try_m || '0 ₺');

    root().innerHTML = `
      <div class="auth-box cs-card" style="max-width:${tab === 'signup' && isPaid ? '620px' : '480px'};margin:0 auto;transition:max-width 0.2s ease">
        <div class="tabs" role="tablist">
          <button role="tab" type="button" data-at="signin" aria-selected="${tab === 'signin'}">${esc(t('signin'))}</button>
          <button role="tab" type="button" data-at="signup" aria-selected="${tab === 'signup'}">${esc(t('signup'))} &amp; API</button>
        </div>
        <h1 style="font-size:26px;margin:8px 0 4px">${esc(tab === 'signup' ? (isPaid ? curP.name + ' Planı & API Tahsisi' : t('signup')) : t('signin'))}</h1>
        <p class="muted" style="margin:0 0 16px;font-size:13px">${esc(tab === 'signup' ? (isPaid ? curP.desc + ' · Anında API anahtarı ve resmi ticari fatura (%0 KDV).' : t('signupLead')) : t('authLead'))}</p>

        ${tab === 'signup' ? `
        <!-- Plan Selector Pills -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:14px;">
          ${['kesif', 'gelistirici', 'pro', 'kurumsal'].map(pId => {
            const pInfo = prices[pId];
            const sel = activeAuthPlan === pId;
            return `
            <button type="button" data-plan-pick="${pId}" style="padding:8px 4px;border-radius:8px;border:1px solid ${sel ? 'var(--amber,#f59e0b)' : 'var(--line,#1e293b)'};background:${sel ? 'rgba(245,158,11,0.12)' : 'transparent'};color:${sel ? '#fff' : 'var(--muted,#94a3b8)'};cursor:pointer;text-align:center;">
              <div style="font-weight:700;font-size:12px;">${esc(pInfo.name)}</div>
              <div style="font-size:10px;margin-top:2px;">${pInfo.usd_m == null ? 'Özel' : (pInfo.usd_m === 0 ? 'Ücretsiz' : '$' + pInfo.usd_m + '/ay')}</div>
            </button>`;
          }).join('')}
        </div>

        ${isPaid ? `
        <div style="display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,0.03);border:1px solid var(--line,#1e293b);padding:8px 12px;border-radius:8px;margin-bottom:14px;font-size:12px;">
          <span style="color:var(--muted)">Faturalama Dönemi:</span>
          <div style="display:flex;gap:6px;">
            <button type="button" id="cyMonthly" style="padding:4px 8px;border-radius:6px;border:1px solid ${activeAuthCycle === 'monthly' ? 'var(--amber)' : '#334155'};background:${activeAuthCycle === 'monthly' ? 'rgba(245,158,11,0.15)' : 'transparent'};color:#fff;cursor:pointer;font-size:11px;">Aylık ($${curP.usd_m}/ay)</button>
            <button type="button" id="cyYearly" style="padding:4px 8px;border-radius:6px;border:1px solid ${activeAuthCycle === 'yearly' ? 'var(--amber)' : '#334155'};background:${activeAuthCycle === 'yearly' ? 'rgba(245,158,11,0.15)' : 'transparent'};color:#fff;cursor:pointer;font-size:11px;">Yıllık (-17% İndirim)</button>
          </div>
        </div>` : ''}
        ` : ''}

        <form id="authForm" style="display:flex;flex-direction:column;gap:12px">
          <div class="field"><label for="auEmail">${esc(t('email'))} *</label><input id="auEmail" type="email" required autocomplete="email" value="${esc(prevEmail)}" placeholder="developer@company.com"></div>

          ${tab === 'signup' ? `
          <div class="field"><label for="auCo">${esc(t('company'))} ${isPaid ? '*' : '(İsteğe bağlı)'}</label><input id="auCo" type="text" ${isPaid ? 'required' : ''} maxlength="120" autocomplete="organization" value="${esc(prevCo)}" placeholder="Şirket / Bireysel İsim"></div>

          ${isPaid ? `
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <div class="field"><label for="auTax">Vergi No / TCKN</label><input id="auTax" type="text" maxlength="50" value="${esc(prevTax)}" placeholder="Fatura için VKN/TCKN"></div>
            <div class="field"><label for="auAddr">Fatura Şehri / Ülke</label><input id="auAddr" type="text" maxlength="120" value="${esc(prevAddr)}" placeholder="Adana, Türkiye"></div>
          </div>

          <!-- Payment Method Tabs -->
          <div style="border-top:1px solid var(--line,#1e293b);padding-top:12px;margin-top:4px;">
            <label style="font-size:12px;font-weight:600;display:block;margin-bottom:8px;color:#cbd5e1;">Ödeme Yöntemi:</label>
            <div style="display:flex;gap:6px;margin-bottom:12px;">
              <button type="button" data-pay-m="crypto" style="flex:1;padding:8px;border-radius:6px;border:1px solid ${activeAuthPayTab === 'crypto' ? '#38bdf8' : '#334155'};background:${activeAuthPayTab === 'crypto' ? 'rgba(56,189,248,0.12)' : 'transparent'};color:#fff;cursor:pointer;font-size:11px;font-weight:600;">⚡ Kripto (USDC/USDT)</button>
              <button type="button" data-pay-m="bank" style="flex:1;padding:8px;border-radius:6px;border:1px solid ${activeAuthPayTab === 'bank' ? '#f59e0b' : '#334155'};background:${activeAuthPayTab === 'bank' ? 'rgba(245,158,11,0.12)' : 'transparent'};color:#fff;cursor:pointer;font-size:11px;font-weight:600;">🏦 Havale / Proforma</button>
              <button type="button" data-pay-m="card" style="flex:1;padding:8px;border-radius:6px;border:1px solid ${activeAuthPayTab === 'card' ? '#10b981' : '#334155'};background:${activeAuthPayTab === 'card' ? 'rgba(16,185,129,0.12)' : 'transparent'};color:#fff;cursor:pointer;font-size:11px;font-weight:600;">💳 Kart (iyzico 3D)</button>
            </div>

            <!-- Pane: Crypto -->
            <div id="paneCrypto" style="display:${activeAuthPayTab === 'crypto' ? 'block' : 'none'};background:#080c14;border:1px solid #1e293b;border-radius:8px;padding:12px;margin-bottom:12px;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="font-size:11px;color:var(--muted)">Yatırma Ağı &amp; Token:</span>
                <select id="auNet" style="padding:4px 8px;border-radius:6px;border:1px solid #334155;background:#0f1422;color:#fff;font-size:11px;">
                  <option value="base">Base Mainnet (USDC)</option>
                  <option value="trc20">TRON TRC20 (USDT)</option>
                  <option value="arbitrum">Arbitrum One (USDC)</option>
                  <option value="ethereum">Ethereum ERC20 (USDC/USDT)</option>
                </select>
              </div>
              <div style="background:#05070c;border:1px solid #334155;border-radius:6px;padding:8px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;gap:6px;">
                <code id="auDepositAddr" style="font-size:11px;color:#10b981;word-break:break-all;">0x4945ef6e124eea2176ddf050b33db42b0ae8c7f7</code>
                <button type="button" id="btnCopyDep" style="padding:3px 8px;font-size:10px;border-radius:4px;border:1px solid #334155;background:#1e293b;color:#fff;cursor:pointer;">Kopyala</button>
              </div>
              <div class="field" style="margin-bottom:0">
                <label for="auTxHash" style="font-size:11px">İşlem Kodu / TXID *</label>
                <input id="auTxHash" type="text" placeholder="0x... veya TRON Tx Hash" style="font-family:monospace;font-size:11px;padding:7px;">
              </div>
              <div style="font-size:10px;color:var(--muted);margin-top:6px;">Tutar: <b>$${curAmtUsd} USDC/USDT</b> (%0 KDV). İşlem onaylandığında API anahtarınız ve PAID ticari faturanız anında üretilir.</div>
            </div>

            <!-- Pane: Bank -->
            <div id="paneBank" style="display:${activeAuthPayTab === 'bank' ? 'block' : 'none'};background:#080c14;border:1px solid #1e293b;border-radius:8px;padding:12px;margin-bottom:12px;font-size:11px;line-height:1.6;">
              <div style="color:#f59e0b;font-weight:700;margin-bottom:4px;">🏦 TEB (Türk Ekonomi Bankası) — Adana Toros Şb. (446) &bull; SWIFT: TEBUTRIS</div>
              <div style="color:#e2e8f0;margin-bottom:4px;"><b>Alıcı:</b> ITOUCH BİLİŞİM SİSTEMLERİ LTD. ŞTİ.</div>
              <div style="font-family:monospace;color:#10b981;"><b>TRY IBAN:</b> TR92 0003 2000 0000 0070 5754 65</div>
              <div style="font-family:monospace;color:#38bdf8;"><b>USD IBAN:</b> TR83 0003 2000 0000 0088 9467 48</div>
              <div style="color:var(--muted);margin-top:6px;">Butona bastığınızda kurumsal proforma faturanız (PDF) anında indirilecek ve deneme API anahtarınız teslim edilecektir.</div>
            </div>

            <!-- Pane: Card -->
            <div id="paneCard" style="display:${activeAuthPayTab === 'card' ? 'block' : 'none'};background:#080c14;border:1px solid #1e293b;border-radius:8px;padding:12px;margin-bottom:12px;font-size:12px;">
              <div style="color:#10b981;font-weight:700;margin-bottom:4px;">💳 iyzico 3D Secure ile Güvenli Kart Ödemesi</div>
              <p style="color:var(--muted);margin:0 0 6px;font-size:11px;">Tutar: <b>${curAmtTry}</b> (%0 KDV Teknokent Muafiyeti). Ödeme tamamlandığında API anahtarınız ve faturanız anında aktifleşir.</p>
            </div>
          </div>` : ''}

          <label class="check-line"><input type="checkbox" id="auTerms" required ${prevTerms ? 'checked' : ''}><span>${t('terms')}</span></label>
          <label class="check-line"><input type="checkbox" id="auKvkk" required ${prevKvkk ? 'checked' : ''}><span>${t('kvkk')}</span></label>
          <label class="check-line"><input type="checkbox" id="auMkt" ${prevMkt ? 'checked' : ''}><span>${esc(t('marketing'))}</span></label>` : ''}

          <div class="sr-only" aria-hidden="true"><label for="auWeb">Website</label><input id="auWeb" type="text" tabindex="-1" autocomplete="off"></div>

          ${activeAuthPlan === 'kurumsal' ? `
          <a class="btn-primary" href="mailto:ask@answerr.me?subject=answerr%20Kurumsal%20Plan%20Talebi" style="text-align:center;text-decoration:none;padding:12px;">✉️ Kurumsal Görüşme Planla</a>`
          : `<button class="btn-primary" type="submit" style="padding:12px;font-size:14px;font-weight:600;">
              ${esc(tab === 'signup' ? (isPaid ? (activeAuthPayTab === 'crypto' ? '✓ Ödemeyi Doğrula & API Anahtarını Al' : (activeAuthPayTab === 'bank' ? '📄 Proforma Fatura Oluştur & API Al' : '💳 Kartla Güvenli Öde')) : '🚀 Anında Ücretsiz API Anahtarını Al') : t('sendLink'))}
            </button>`}

          <p class="small-mono" id="auStatus" role="status" style="margin:4px 0 0"></p>
        </form>

        <div id="auResultBox" style="display:none;margin-top:16px;padding:16px;border-radius:10px;border:1px solid #10b981;background:#05070c;"></div>
      </div>`;

    // Event listeners for tabs and plan selector
    $$('[data-at]').forEach(b => b.addEventListener('click', () => {
      history.replaceState(null, '', b.dataset.at === 'signup' ? '#signup' : '#');
      renderAuth(b.dataset.at);
    }));

    $$('[data-plan-pick]').forEach(b => b.addEventListener('click', () => {
      renderAuth('signup', b.dataset.planPick);
    }));

    const btnMonthly = $('#cyMonthly'), btnYearly = $('#cyYearly');
    if (btnMonthly) btnMonthly.addEventListener('click', () => { activeAuthCycle = 'monthly'; renderAuth('signup'); });
    if (btnYearly) btnYearly.addEventListener('click', () => { activeAuthCycle = 'yearly'; renderAuth('signup'); });

    $$('[data-pay-m]').forEach(b => b.addEventListener('click', () => {
      activeAuthPayTab = b.dataset.payM;
      renderAuth('signup');
    }));

    const netSel = $('#auNet');
    if (netSel) {
      netSel.addEventListener('change', () => {
        const addrBox = $('#auDepositAddr');
        if (addrBox) {
          addrBox.textContent = netSel.value === 'trc20' ? 'TLMhaDJTVYBHBSGJ9nCQGLvqnYFPsBgLJu' : '0x4945ef6e124eea2176ddf050b33db42b0ae8c7f7';
        }
      });
    }

    const btnCopyDep = $('#btnCopyDep');
    if (btnCopyDep) {
      btnCopyDep.addEventListener('click', () => {
        const addrBox = $('#auDepositAddr');
        if (addrBox) {
          navigator.clipboard.writeText(addrBox.textContent.trim());
          btnCopyDep.textContent = 'Kopyalandı!';
          setTimeout(() => { btnCopyDep.textContent = 'Kopyala'; }, 2000);
        }
      });
    }

    // Form submission
    const form = $('#authForm');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const st = $('#auStatus'), btn = e.target.querySelector('button[type=submit]');
        if (btn) btn.disabled = true;
        st.textContent = 'İşlem yapılıyor…';

        const email = $('#auEmail').value.trim();
        const website = $('#auWeb').value;

        if (tab === 'signin') {
          const r = await call('POST', '/v1/auth/login', { email, lang: L(), website }, { anon: true, recaptcha: 'access' });
          if (btn) btn.disabled = false;
          st.textContent = r.ok ? t('sent') : msg(r);
          return;
        }

        // Signup / Instant checkout
        const company = ($('#auCo') || {}).value ? $('#auCo').value.trim() : null;
        const tax_id = ($('#auTax') || {}).value ? $('#auTax').value.trim() : null;
        const address = ($('#auAddr') || {}).value ? $('#auAddr').value.trim() : null;
        const terms = ($('#auTerms') || {}).checked;
        const kvkk = ($('#auKvkk') || {}).checked;
        const mkt = Boolean(($('#auMkt') || {}).checked);

        const method = isPaid ? activeAuthPayTab : 'free';
        const tx_hash = ($('#auTxHash') || {}).value ? $('#auTxHash').value.trim() : null;
        const network = ($('#auNet') || {}).value || 'base';

        const reqBody = {
          email, company, tax_id, address,
          plan: activeAuthPlan, cycle: activeAuthCycle,
          method, tx_hash, network, token: network === 'trc20' ? 'USDT' : 'USDC',
          accept_terms: terms, kvkk_ack: kvkk, marketing: mkt,
          lang: L(), website
        };

        const res = await call('POST', '/v1/checkout/instant', reqBody, { anon: true, recaptcha: 'access' });
        if (btn) btn.disabled = false;

        if (!res.ok) {
          st.textContent = msg(res);
          return;
        }

        const data = res.data;

        // If card checkout, redirect to iyzico
        if (data.status === 'checkout' && data.form && data.form.payment_page_url) {
          st.textContent = 'Ödeme sayfası açılıyor…';
          location.href = data.form.payment_page_url;
          return;
        }

        // Store session if provided
        if (data.session) {
          S.session = data.session;
          localStorage.setItem('ans_session', data.session);
        }

        // Render success card
        form.style.display = 'none';
        st.textContent = '';
        const resBox = $('#auResultBox');
        resBox.style.display = 'block';

        const invLink = data.invoice_pdf_url
          ? `<a href="${esc(data.invoice_pdf_url)}" target="_blank" class="btn btn-primary" style="text-decoration:none;font-size:12px;">📄 ${data.invoice_no && data.invoice_no.startsWith('INV') ? 'Resmi Faturayı İndir (PAID PDF)' : 'Proforma Faturayı İndir (PDF)'}</a>`
          : '';

        resBox.innerHTML = `
          <div style="color:#10b981;font-weight:700;font-size:16px;margin-bottom:8px;">✓ ${esc(data.message || 'API Anahtarınız Tahsis Edildi!')}</div>
          ${data.invoice_no ? `<div style="font-size:12px;color:var(--muted);margin-bottom:10px;">Fatura No: <b>${esc(data.invoice_no)}</b></div>` : ''}
          ${data.api_key ? `
          <p style="color:var(--muted);font-size:12px;margin:0 0 6px;">Tahsis edilen API anahtarınız (isteklerinize <code>Authorization: Bearer</code> ile ekleyin):</p>
          <div style="background:#000;border:1px solid #1e293b;padding:10px;border-radius:6px;font-family:monospace;color:#38bdf8;word-break:break-all;font-size:13px;margin-bottom:12px;">${esc(data.api_key)}</div>
          ` : ''}
          <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
            ${data.api_key ? `<button type="button" id="btnCopyProvisionedKey" class="btn" style="cursor:pointer;font-size:12px;">📋 Anahtarı Kopyala</button>` : ''}
            ${invLink}
            <button type="button" id="btnEnterConsole" class="btn btn-primary" style="cursor:pointer;font-size:12px;">➡️ Konsola Gir</button>
          </div>`;

        if (data.api_key && $('#btnCopyProvisionedKey')) {
          $('#btnCopyProvisionedKey').addEventListener('click', () => {
            navigator.clipboard.writeText(data.api_key);
            $('#btnCopyProvisionedKey').textContent = 'Kopyalandı!';
            setTimeout(() => { $('#btnCopyProvisionedKey').textContent = '📋 Anahtarı Kopyala'; }, 2000);
          });
        }

        if ($('#btnEnterConsole')) {
          $('#btnEnterConsole').addEventListener('click', async () => {
            await boot();
          });
        }
      });
    }
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
            <h3 id="crTitle" style="margin:0;color:#38bdf8">⚡ USDC / USDT Kripto Ödeme (%0 KDV)</h3>
            <button type="button" class="btn-ghost btn-sm" id="crClose">✕</button>
          </div>
          <p class="small-mono" id="crAmountInfo" style="margin:8px 0"></p>
          <div class="cs-row" style="gap:10px;flex-wrap:wrap;margin-bottom:10px">
            <button type="button" class="btn-primary btn-sm" id="crWeb3Btn" style="background:#38bdf8;border-color:#38bdf8;color:#05060a">⚡ 1-Tık Base USDC Cüzdan ile Öde (MetaMask / Rabby)</button>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-top:8px">
            <div class="field"><label for="crNet">Ağ (Network)</label>
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
          <div class="small-mono" style="margin:8px 0">Hazine Adresi: <code id="crAddr" style="color:#10b981;word-break:break-all">TLMhaDJTVYBHBSGJ9nCQGLvqnYFPsBgLJu</code></div>
          <div class="cs-row" style="gap:8px;align-items:flex-end;flex-wrap:wrap">
            <div class="field" style="flex:1 1 280px"><label for="crTx">İşlem Hash (TXID)</label><input id="crTx" type="text" placeholder="0x... veya 64 karakter TRON TXID"></div>
            <button type="button" class="btn-primary btn-sm" id="crVerifyBtn">✓ Doğrula &amp; Planı Etkinleştir</button>
          </div>
          <p class="small-mono" id="crStatus" style="margin:8px 0 0"></p>
        </div>
        <label class="check-line"><input type="checkbox" id="salesOk"><span>${t('salesOk')}</span></label>
        ${card ? `<p class="small-mono" style="margin:0">${esc(t('cardNote'))}</p>` : ''}
        <p class="small-mono" id="planStatus" aria-live="polite"></p>
        ${a.limits.overage_per_1000 ? `<label class="check-line"><input type="checkbox" id="ovr" ${a.overage_enabled ? 'checked' : ''}><span>${esc(t('overageToggle'))} ($${esc(a.limits.overage_per_1000)} / 1.000)</span></label>` : ''}
      </div>
      ${plist.length ? `<div class="cs-card"><h2>${esc(t('payments'))}</h2>
        <div class="scroll-x"><table class="cs-table"><thead><tr><th>${esc(t('when'))}</th><th>${esc(t('plan'))}</th><th>${esc(t('total'))} (${esc(t('vatIncl'))})</th><th>${esc(t('status'))}</th><th>${esc(t('paidUntil'))}</th></tr></thead>
        <tbody>${plist.map(x => `<tr><td>${fmtT(x.paid_at || x.created_at)}</td><td>${esc(x.plan || x.kind)} · ${esc(x.cycle || '')}</td><td>${(x.currency && x.currency !== 'TRY') ? esc(x.total_try + ' ' + x.currency) : tl(x.total_try)}</td><td>${esc(x.status)}${x.card_last4 ? ' · ' + esc(x.card_last4) : ''}</td><td>${x.period_end ? fmtT(x.period_end) : '—'} <button type="button" class="btn-ghost btn-sm" data-inv="${esc(x.id)}" style="margin-left:6px">📄 ${x.status === 'paid' ? 'Fatura (PDF)' : 'Proforma (PDF)'}</button></td></tr>`).join('')}</tbody></table></div></div>` : ''}
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
    $$('[data-cy]', el).forEach(btn => btn.addEventListener('click', () => {
      cycle = btn.dataset.cy;
      $$('[data-cy]', el).forEach(x => x.setAttribute('aria-pressed', String(x === btn)));
      $$('[data-pm]', el).forEach(s => { const v = cycle === 'yearly' ? s.dataset.py : s.dataset.pm; s.textContent = s.dataset.tl ? tl(v) : '$' + v; });
      $$('[data-pmu]', el).forEach(s => { s.textContent = '$' + (cycle === 'yearly' ? s.dataset.pyu : s.dataset.pmu); });
    }));
    const needConsent = () => {
      if ($('#salesOk').checked) return false;
      $('#planStatus').textContent = '☐ ' + t('salesOk').replace(/<[^>]+>/g, ''); $('#salesOk').focus(); return true;
    };
    $$('[data-plan]', el).forEach(btn => btn.addEventListener('click', async () => {
      const id = btn.dataset.plan;
      if (id !== 'kesif' && needConsent()) return;
      const d = await call('POST', '/v1/account/plan-request', { plan: id, cycle, note: 'mesafeli-satis onayi ' + new Date().toISOString() });
      if (d.ok && d.data.proforma_invoice_pdf_url) {
        $('#planStatus').innerHTML = `⏳ Havale/EFT Talebi Alındı — <b>TEB TL IBAN:</b> <code>TR92 0003 2000 0000 0070 5754 65</code> · <b>USD IBAN:</b> <code>TR83 0003 2000 0000 0088 9467 48</code> · <b>EUR IBAN:</b> <code>TR28 0003 2000 0000 0088 9467 68</code> (Alıcı: ITouch Bilişim Sistemleri Ltd. Şti.). Ödeme sonrası faturanız PAID damgalanır. Aşağıdaki Ödemeler tablosundan <b>UNPAID Proforma (PDF)</b> faturanızı indirebilirsiniz.`;
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
    const usdFor = (pl, cy) => { const p = plans[pl] || {}; return cy === 'yearly' ? (p.price_yearly_per_month * 12) : p.price_monthly; };
    const updCrInfo = () => {
      const amt = usdFor(curCryptoPlan, cycle);
      const pName = plans[curCryptoPlan] ? (L() === 'en' ? plans[curCryptoPlan].name_en : plans[curCryptoPlan].name_tr) : curCryptoPlan;
      if ($('#crAmountInfo')) $('#crAmountInfo').textContent = `${pName} (${cycle === 'yearly' ? t('yearly') : t('monthly')}) — Ödenecek Tutar: ${amt} USDC / USDT (%0 KDV · Teknopark Muafiyetli)`;
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
      updCrInfo();
      $('#cryptoBox').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }));
    if ($('#crWeb3Btn')) $('#crWeb3Btn').addEventListener('click', async () => {
      if (needConsent()) return;
      if (!window.ethereum) { $('#crStatus').textContent = 'Web3 cüzdanı (MetaMask / Rabby) bulunamadı. Aşağıdan ağ seçip TXID ile doğrulayabilirsiniz.'; return; }
      try {
        $('#crStatus').textContent = 'Base Mainnet (Chain ID 8453) cüzdanına bağlanılıyor…';
        const accs = await window.ethereum.request({ method: 'eth_requestAccounts' });
        try { await window.ethereum.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: '0x2105' }] }); }
        catch (sw) {
          if (sw.code === 4902) await window.ethereum.request({ method: 'wallet_addEthereumChain', params: [{ chainId: '0x2105', chainName: 'Base Mainnet', nativeCurrency: { name: 'ETH', symbol: 'ETH', decimals: 18 }, rpcUrls: ['https://mainnet.base.org'], blockExplorerUrls: ['https://basescan.org'] }] });
          else throw sw;
        }
        const amt = usdFor(curCryptoPlan, cycle);
        const units = (BigInt(amt) * 1000000n).toString(16).padStart(64, '0');
        const dataHex = '0xa9059cbb' + EVM_ADDR.toLowerCase().replace(/^0x/, '').padStart(64, '0') + units;
        $('#crStatus').textContent = `Cüzdanınızda ${amt} USDC transferini onaylayın…`;
        const txHash = await window.ethereum.request({ method: 'eth_sendTransaction', params: [{ from: accs[0], to: BASE_USDC, data: dataHex }] });
        $('#crTx').value = txHash; $('#crNet').value = 'base'; $('#crTok').value = 'USDC';
        $('#crStatus').textContent = 'Transfer gönderildi, blok onayı bekleniyor…';
        for (let i = 0; i < 40; i++) {
          await new Promise(r => setTimeout(r, 2000));
          const rec = await window.ethereum.request({ method: 'eth_getTransactionReceipt', params: [txHash] });
          if (rec && rec.status === '0x1') break;
        }
        $('#crVerifyBtn').click();
      } catch (e) { $('#crStatus').textContent = 'Hata: ' + (e.message || String(e)); }
    });
    if ($('#crVerifyBtn')) $('#crVerifyBtn').addEventListener('click', async () => {
      if (needConsent()) return;
      const txHash = ($('#crTx').value || '').trim();
      if (!txHash) { $('#crStatus').textContent = 'Lütfen işlem hash (TXID) girin.'; return; }
      $('#crVerifyBtn').disabled = true; $('#crStatus').textContent = 'Blokzincir üzerinde doğrulanıyor…';
      const d = await call('POST', '/v1/account/crypto-checkout', {
        plan: curCryptoPlan, cycle, tx_hash: txHash, network: $('#crNet').value, token: $('#crTok').value,
        accept_preinfo: true, accept_distance_sale: true
      });
      $('#crVerifyBtn').disabled = false;
      if (!d.ok) { $('#crStatus').textContent = msg(d); return; }
      toast(t('payPaid'));
      viewBilling(el);
    });
    $$('[data-inv]', el).forEach(btn => btn.addEventListener('click', async () => {
      const res = await call('GET', '/v1/account/payments/' + encodeURIComponent(btn.dataset.inv) + '/invoice.pdf', null, { raw: true });
      if (!res.ok) { toast(t('err')); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
    }));

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
