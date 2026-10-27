/* answerr.me/pro — motion layer: live Mandelbrot horizon, live decision stream, Werr orbit,
   scroll reveals, counters, billing toggle and plan request form.
   Everything honours prefers-reduced-motion and pauses when off-screen or in a hidden tab. */
(function () {
  'use strict';
  const RM = false; // Live Mandelbrot horizon dive, orbit and interactive simulations active across desktop & mobile
  const t = (k) => (window.ProI18n ? window.ProI18n.t(k) : k);
  const lang = () => (window.ProI18n ? window.ProI18n.lang : 'tr');
  const SEED = { cx: -0.7436438870371587, cy: 0.1318259042053119 };   // werr "universal" seed (js/werr-engine.js)

  function onVisible(el, cb) {
    if (!('IntersectionObserver' in window)) { cb(true); return; }
    new IntersectionObserver(es => es.forEach(e => cb(e.isIntersecting)), { threshold: 0.02 }).observe(el);
  }

  /* ------------------------------------------------------------------ palette */
  function buildLUT() {
    const stops = [[5, 6, 10], [10, 34, 46], [36, 110, 128], [140, 222, 236], [244, 238, 222], [255, 176, 72], [150, 58, 26], [24, 10, 8], [5, 6, 10]];
    const N = 1024, lut = new Uint8ClampedArray(N * 3);
    for (let i = 0; i < N; i++) {
      const p = (i / N) * (stops.length - 1), k = Math.floor(p), f = p - k;
      const a = stops[k], b = stops[Math.min(k + 1, stops.length - 1)];
      const s = f * f * (3 - 2 * f);
      for (let c = 0; c < 3; c++) lut[i * 3 + c] = a[c] + (b[c] - a[c]) * s;
    }
    return lut;
  }

  /* ------------------------------------------------------------------ live horizon */
  const IN_PRO = typeof location !== 'undefined' && location.pathname.indexOf('/pro/') >= 0;
  function Horizon(host) {
    const cvs = host.querySelector('canvas.horizon');
    if (!cvs || !window.Worker) return;
    let worker;
    try { worker = new Worker((IN_PRO ? '' : 'pro/') + 'mandel-worker.js'); } catch (e) { return; }
    const ctx = cvs.getContext('2d');
    const off = document.createElement('canvas');
    const octx = off.getContext('2d');
    const lut = buildLUT();
    const SCALE0 = 1.45, F = 1.6, T = 1600, MIN = 3e-12;
    let W = 0, H = 0, ax = 0.7, ay = 0.5, img = null;
    let cur = null, next = null, pending = false, kStart = 0, offset = 0, running = false, visible = true, reqId = 0, lastDraw = 0;
    const tele = host.querySelector('[data-tele]');

    function iterFor(scale) { return Math.min(3200, Math.round(160 + 72 * Math.log2(SCALE0 / scale))); }
    function size() {
      const r = host.getBoundingClientRect();
      const wide = r.width > 760;
      W = Math.max(240, Math.min(wide ? 760 : 420, Math.round(r.width / (wide ? 2 : 1.7))));
      H = Math.max(160, Math.round(W * r.height / Math.max(1, r.width)));
      ax = wide ? 0.66 : 0.5; ay = wide ? 0.3 : 0.72;
      cvs.width = W; cvs.height = H; off.width = W; off.height = H;
      img = octx.createImageData(W, H);
    }
    function request(scale) {
      pending = true;
      worker.postMessage({ id: ++reqId, w: W, h: H, cx: SEED.cx, cy: SEED.cy, scale, ax, ay, maxIter: iterFor(scale) });
    }
    worker.onmessage = (e) => {
      const m = e.data;
      if (m.id !== reqId || m.w !== W) { pending = false; return; }
      pending = false;
      const frame = { scale: m.scale, data: m.data, maxIter: iterFor(m.scale) };
      if (!cur) { cur = frame; kStart = performance.now(); paint(); host.classList.add('live'); if (!RM) request(cur.scale / F); }
      else next = frame;
    };
    worker.onerror = () => { running = false; };

    function recolor(frame) {
      const d = img.data, src = frame.data, n = src.length;
      for (let i = 0, p = 0; i < n; i++, p += 4) {
        const v = src[i];
        if (v < 0) { d[p] = 5; d[p + 1] = 6; d[p + 2] = 10; d[p + 3] = 255; continue; }
        const k = ((Math.floor(Math.sqrt(v) * 46 + offset) % 1024) + 1024) % 1024 * 3;
        d[p] = lut[k]; d[p + 1] = lut[k + 1]; d[p + 2] = lut[k + 2]; d[p + 3] = 255;
      }
      octx.putImageData(img, 0, 0);
    }
    function paint(mag) {
      mag = mag || 1;
      recolor(cur);
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.imageSmoothingEnabled = true;
      ctx.setTransform(mag, 0, 0, mag, ax * W * (1 - mag), ay * H * (1 - mag));
      ctx.drawImage(off, 0, 0);
      if (tele) {
        const view = cur.scale / mag;
        const z = SCALE0 / view;
        tele.querySelector('[data-k="zoom"]').textContent = '×' + (z < 1e4 ? z.toFixed(z < 10 ? 2 : 0) : z.toExponential(2).replace('e+', 'e'));
        tele.querySelector('[data-k="iter"]').textContent = String(cur.maxIter);
      }
    }
    function loop(now) {
      if (!running) return;
      requestAnimationFrame(loop);
      if (!visible || document.hidden || !cur) return;
      if (now - lastDraw < 33) return;                    // ~30 fps is plenty for a slow dive
      lastDraw = now;
      let tt = (now - kStart) / T;
      if (tt >= 1) {
        if (next) {
          cur = next; next = null; kStart = now; tt = 0;
          if (cur.scale / F > MIN) request(cur.scale / F);
          else { host.classList.remove('live'); setTimeout(restart, 900); running = false; return; }
        } else tt = 1;
      }
      offset = (offset + 2.5) % 1024;
      paint(Math.pow(F, tt));
    }
    function restart() {
      cur = null; next = null; reqId++;
      size(); request(SCALE0);
      running = true; requestAnimationFrame(loop);
    }
    onVisible(host, v => { visible = v; });
    let rz = null;
    window.addEventListener('resize', () => {
      clearTimeout(rz);
      rz = setTimeout(() => {
        const keep = cur ? cur.scale : SCALE0;
        cur = null; next = null; reqId++; size(); request(RM ? 0.0035 : keep);
      }, 300);
    });
    size();
    if (RM) { request(0.0035); return; }                 // one still frame, no motion
    running = true; request(SCALE0); requestAnimationFrame(loop);
  }

  /* ------------------------------------------------------------------ live decision stream */
  const TOOLS = [
    'read_invoice_summary', 'list_orders', 'search_docs', 'send_email', 'update_customer_records', 'send_payment',
    'transfer_funds', 'deploy_to_production', 'bulk_delete_users', 'drop_table', 'get_api_key', 'read_secrets',
    'create_ticket', 'export_user_data', 'refund_order', 'query_analytics', 'kullanici_sil', 'fatura_oku',
    'odeme_gonder', 'rotate_credentials', 'grant_admin_role', 'fetch_calendar', 'post_slack_message', 'run_shell_command'
  ];
  const ROLES = ['member', 'admin', 'agent', 'support'];

  function Stream(host) {
    const list = host.querySelector('[data-stream]');
    const K = window.AnswerrPolicyKernel;
    if (!list || !K) return;
    const counts = { ALLOW: 0, REVIEW: 0, DENY: 0 };
    let policy = null, visible = true, n = 0, seed = 20261014;
    const rnd = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
    const pick = (a) => a[Math.floor(rnd() * a.length)];
    const esc = (s) => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const word = { ALLOW: 'vAllow', REVIEW: 'vReview', DENY: 'vDeny' };
    const cls = { ALLOW: 'v-allow', REVIEW: 'v-review', DENY: 'v-deny' };

    (async () => {
      for (const u of ['policies/builtin_gates.json', '../policies/builtin_gates.json', '/policies/builtin_gates.json']) {
        try {
          const r = await fetch(u);
          if (r.ok) {
            const g = await r.json();
            policy = g.agent_mcp_guard;
            for (let i = 0; i < 4; i++) addRow();
            tick();
            return;
          }
        } catch (e) { /* try next */ }
      }
    })();

    function addRow() {
      const state = { tool_name: pick(TOOLS), user_role: pick(ROLES), auth_status: rnd() > 0.08 };
      if (/payment|transfer|refund|odeme/.test(state.tool_name)) state.amount_usd = Math.round(rnd() * 9000 + 40);
      if (rnd() < 0.07) state.coffee_temp = 90;           // an unrecognised field → hand to a human
      const t0 = performance.now();
      let r = null;
      for (let i = 0; i < 50; i++) r = K.evaluate(state, policy, true);
      const us = ((performance.now() - t0) / 50) * 1000;
      counts[r.verdict]++; n++;
      const row = document.createElement('li');
      row.className = 'sr-row' + (RM ? '' : ' enter');
      const extra = state.amount_usd ? ' · $' + state.amount_usd.toLocaleString('en-US') : (state.coffee_temp ? ' · coffee_temp' : '');
      row.innerHTML = `<span class="sr-n">#${String(n).padStart(4, '0')}</span><span class="sr-tool">${esc(state.tool_name)}<small>${esc(state.user_role)}${esc(extra)}</small></span>` +
        `<span class="sr-v ${cls[r.verdict]}">${esc(t(word[r.verdict]))}</span><span class="sr-rule">${esc(r.rule_id || '')}</span><span class="sr-us">${us < 1000 ? us.toFixed(0) + ' µs' : (us / 1000).toFixed(2) + ' ms'}</span>`;
      list.prepend(row);
      while (list.children.length > 7) list.removeChild(list.lastChild);
      ['ALLOW', 'REVIEW', 'DENY'].forEach(v => { const el = host.querySelector(`[data-c="${v}"]`); if (el) el.textContent = counts[v]; });
      const tot = host.querySelector('[data-c="ALL"]'); if (tot) tot.textContent = n;
      const bar = host.querySelector('[data-mix]');
      if (bar) bar.style.setProperty('--a', (counts.ALLOW / n * 100) + '%'), bar.style.setProperty('--r', ((counts.ALLOW + counts.REVIEW) / n * 100) + '%');
    }

    function tick() {
      if (!policy) return;
      if ((visible && !document.hidden) || n < 5) addRow();
      setTimeout(tick, RM ? 3200 : 1250);
    }
    onVisible(host, v => { visible = v; });
    window.addEventListener('proLanguageChanged', () => {
      list.querySelectorAll('.sr-v').forEach(el => {
        const v = el.classList.contains('v-allow') ? 'ALLOW' : el.classList.contains('v-review') ? 'REVIEW' : 'DENY';
        el.textContent = t(word[v]);
      });
    });
  }

  /* ------------------------------------------------------------------ Werr orbit */
  function Orbit(host) {
    const planets = Array.from(host.querySelectorAll('.planet'));
    const R = [0, 150, 245, 340, 440];                     // ring radii in viewBox units (1000 × 620)
    const FL = 0.36, CX = 500, CY = 310;
    let paused = false, visible = true, last = performance.now(), phase = 0;
    const speed = [0, 0.000105, 0.00007, 0.00005, 0.000036];
    planets.forEach(p => { p._ring = +p.dataset.ring; p._a = (+p.dataset.angle || 0) * Math.PI / 180; });
    function place() {
      planets.forEach(p => {
        const a = p._a + phase * speed[p._ring] * 1000;
        const x = CX + Math.cos(a) * R[p._ring], y = CY + Math.sin(a) * R[p._ring] * FL;
        const depth = (Math.sin(a) + 1) / 2;              // 0 = behind the core, 1 = in front
        p.style.left = (x / 10) + '%';
        p.style.top = (y / 6.2) + '%';
        p.style.setProperty('--d', (0.72 + depth * 0.38).toFixed(3));
        p.style.zIndex = String(10 + Math.round(depth * 20));
      });
    }
    function loop(now) {
      requestAnimationFrame(loop);
      const dt = Math.min(64, now - last); last = now;
      if (!paused && visible && !document.hidden && !RM) { phase += dt / 1000; place(); }
    }
    host.addEventListener('mouseenter', () => { paused = true; });
    host.addEventListener('mouseleave', () => { paused = false; });
    host.addEventListener('focusin', () => { paused = true; });
    host.addEventListener('focusout', () => { paused = false; });
    planets.forEach(p => p.addEventListener('click', () => {
      const card = document.getElementById(p.dataset.target);
      if (!card) return;
      card.scrollIntoView({ behavior: RM ? 'auto' : 'smooth', block: 'center' });
      card.classList.remove('flash'); void card.offsetWidth; card.classList.add('flash');
    }));
    onVisible(host, v => { visible = v; });
    place();
    requestAnimationFrame(loop);
  }

  /* ------------------------------------------------------------------ reveal, counters, glow */
  function Reveal() {
    const els = document.querySelectorAll('.rv');
    if (RM || !('IntersectionObserver' in window)) { els.forEach(e => e.classList.add('in')); return; }
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.12 });
    els.forEach(e => io.observe(e));
  }
  function Counters() {
    document.querySelectorAll('[data-count]').forEach(el => {
      const target = +el.dataset.count, dec = +(el.dataset.dec || 0);
      const fmt = (v) => v.toLocaleString(lang() === 'tr' ? 'tr-TR' : 'en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
      if (RM) { el.textContent = fmt(target); return; }
      onVisible(el, v => {
        if (!v || el._done) return;
        el._done = true;
        const t0 = performance.now(), D = 1400;
        const step = (now) => { const k = Math.min(1, (now - t0) / D); el.textContent = fmt(target * (1 - Math.pow(1 - k, 3))); if (k < 1) requestAnimationFrame(step); };
        requestAnimationFrame(step);
      });
    });
  }
  function Glow() {
    if (RM) return;
    document.querySelectorAll('.glow').forEach(el => el.addEventListener('pointermove', (e) => {
      const r = el.getBoundingClientRect();
      el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      el.style.setProperty('--my', (e.clientY - r.top) + 'px');
    }));
  }

  /* ------------------------------------------------------------------ pricing */
  function Billing() {
    const sw = document.querySelectorAll('[data-bill]');
    if (!sw.length) return;
    let mode = 'm';
    function apply() {
      sw.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.bill === mode)));
      document.querySelectorAll('[data-price-m]').forEach(el => { el.textContent = el.dataset['price' + (mode === 'm' ? 'M' : 'Y')]; });
      document.querySelectorAll('[data-bill-note]').forEach(el => { el.hidden = mode !== 'y'; });
      document.querySelectorAll('[data-plan-btn]').forEach(a => { a.dataset.billing = mode; });
    }
    sw.forEach(b => b.addEventListener('click', () => { mode = b.dataset.bill; apply(); }));
    document.querySelectorAll('[data-plan-btn]').forEach(a => a.addEventListener('click', () => {
      const sel = document.getElementById('planSel');
      if (sel) sel.value = a.dataset.planBtn;
      const bill = document.getElementById('billSel');
      if (bill) bill.value = mode;
    }));
    apply();
  }
  function PlanForm() {
    const form = document.getElementById('planForm');
    if (!form || !window.ProApp) return;
    const A = window.ProApp;
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const status = document.getElementById('planStatus');
      const mail = document.getElementById('planMail').value.trim();
      const company = document.getElementById('planCo').value.trim();
      const plan = document.getElementById('planSel').value, bill = document.getElementById('billSel').value;
      const note = 'plan: ' + plan + ' · billing: ' + (bill === 'y' ? 'yearly' : 'monthly') + ' · ' + (document.getElementById('planNote').value.trim() || '-');
      const btn = form.querySelector('button[type="submit"]');
      btn.disabled = true; status.textContent = '…';
      const res = await A.api('/v1/access-request', {
        email: mail, company: company || null, note: note.slice(0, 1000), lang: A.lang(), source: 'answerr.me/pro/pricing',
        website: (document.getElementById('planWeb') || {}).value || ''
      }, 'access');
      btn.disabled = false;
      if (res.ok) { status.textContent = t('prOk'); form.reset(); return; }
      if (res.status === 400) { status.textContent = t('erBad'); return; }
      if (res.status === 429) { status.textContent = t('kk429'); return; }
      status.textContent = t('erFallback');
      window.location.href = 'mailto:ask@answerr.me?subject=' + encodeURIComponent('answerr Pro — ' + plan) + '&body=' + encodeURIComponent(mail + '\n' + company + '\n' + note);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-horizon]').forEach(Horizon);
    document.querySelectorAll('[data-live-stream]').forEach(Stream);
    document.querySelectorAll('[data-orbit]').forEach(Orbit);
    Reveal(); Counters(); Glow(); Billing(); PlanForm();
  });
})();
