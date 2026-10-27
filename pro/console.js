/* Kara Kutu — live decision console on /pro */
(function () {
  'use strict';
  const A = () => window.ProApp;

  const SCENARIOS = {
    agent_mcp_guard: [
      { id: 'del', tr: 'Toplu silme · yönetici', en: 'Bulk delete · admin', state: { tool_name: 'bulk_delete_users', user_role: 'admin', auth_status: true, failed_attempts: 0 } },
      { id: 'read', tr: 'Fatura özeti okuma', en: 'Read invoice summary', state: { tool_name: 'read_invoice_summary', user_role: 'admin', auth_status: true, failed_attempts: 0 } },
      { id: 'pay', tr: 'Ödeme · 7.200 $', en: 'Payment · $7,200', state: { tool_name: 'send_payment', user_role: 'member', auth_status: true, amount_usd: 7200 } },
      { id: 'key', tr: 'API anahtarı isteği', en: 'API key request', state: { tool_name: 'get_api_key', user_role: 'admin', auth_status: true } },
      { id: 'ood', tr: 'Bilinmeyen alan', en: 'Unknown field', state: { tool_name: 'read_invoice_summary', user_role: 'admin', coffee_temp: 90 } }
    ],
    fintech_payment_tr: [
      { id: 'ok', tr: 'Bilinen cihaz · 450 TL', en: 'Known device · 450', state: { amount: 450, velocity: 1, known_device: true, device_anomaly: false } },
      { id: 'travel', tr: 'İmkânsız yolculuk', en: 'Impossible travel', state: { amount: 1200, geo_velocity_kmh: 920, known_device: true } },
      { id: 'card', tr: 'Kart denemesi', en: 'Card testing', state: { amount: 40, velocity: 22, device_anomaly: true } },
      { id: 'big', tr: 'Yüksek tutar · 30.000', en: 'High amount · 30,000', state: { tutar: 30000, velocity: 1, known_device: true } }
    ],
    api_zero_trust_waf: [
      { id: 'clean', tr: 'Temiz yönetici isteği', en: 'Clean admin request', state: { user_role: 'admin', failed_attempts: 0, req_frequency: 3, authenticated: true } },
      { id: 'flood', tr: 'Saniyede 240 istek', en: '240 requests / second', state: { user_role: 'guest', failed_attempts: 0, req_frequency: 240 } },
      { id: 'att', tr: 'Saldırgan profili', en: 'Attacker profile', state: { user_role: 'attacker', failed_attempts: 2, req_frequency: 12 } }
    ]
  };
  const QUESTIONS = {
    agent_mcp_guard: { tr: 'Bu araç çağrısına izin verilsin mi?', en: 'Should this tool call be allowed?' },
    fintech_payment_tr: { tr: 'Bu ödeme onaylansın mı?', en: 'Approve this payment?' },
    api_zero_trust_waf: { tr: 'Bu istek geçsin mi?', en: 'Let this request through?' }
  };

  const WERR_PRESETS = {
    smart_router: {
      cx: -0.101096, cy: 0.956287, zoom: 45, max_iter: 36, cadence_lambda: 0.10, cadence_alpha: 0.50,
      enable_domain: true, enable_lexical: true, enable_resonance: true, tripod: true,
      tr: 'Optimal: AI ajan kapısı ve çok alanlı orkestrasyon için 4-kadran dengeli hibrit kurgu [1,1,1].',
      en: 'Optimal: Balanced 4-quadrant hybrid setup [1,1,1] for AI agent gates and multi-domain routing.'
    },
    security_guard: {
      cx: -0.743644, cy: 0.131826, zoom: 120, max_iter: 48, cadence_lambda: 0.08, cadence_alpha: 0.60,
      enable_domain: true, enable_lexical: true, enable_resonance: true, tripod: true,
      tr: 'Optimal: Sıfır güven API/WAF ve DDoS engelleme için Seahorse Vadisi keskin sınır kurgusu [1,1,1].',
      en: 'Optimal: Seahorse Valley sharp boundary setup [1,1,1] for zero-trust API WAF & DDoS defense.'
    },
    risk_evaluator: {
      cx: -0.750000, cy: 0.100000, zoom: 25, max_iter: 48, cadence_lambda: 0.12, cadence_alpha: 0.55,
      enable_domain: true, enable_lexical: true, enable_resonance: true, tripod: true,
      tr: 'Optimal: Ödeme ve finansal risk puanlaması (fintech_payment_tr) için yumuşak kaçış gradyanı [1,1,1].',
      en: 'Optimal: Smooth escape gradient setup [1,1,1] for payment and checkout risk scoring.'
    },
    crown_core: {
      cx: -0.122561, cy: 0.744862, zoom: 64, max_iter: 64, cadence_lambda: 0.10, cadence_alpha: 0.50,
      enable_domain: true, enable_lexical: true, enable_resonance: true, tripod: true,
      tr: 'Optimal: Endüstriyel robotik, IoT emniyet kilidi ve Werracle Z/9Z rezonans uyumlu üçayak kurgusu [1,1,1].',
      en: 'Optimal: Period-3 tripod resonance setup [1,1,1] for robotics, IoT safety & Werracle Z/9Z.'
    },
    universal_cusp: {
      cx: -0.743644, cy: 0.131826, zoom: 50, max_iter: 36, cadence_lambda: 0.10, cadence_alpha: 0.50,
      enable_domain: false, enable_lexical: false, enable_resonance: false, tripod: true,
      tr: 'Saf Fraktal: Alan sözlükleri kapalı [0,0,0]; yalnızca 24B Mandelbrot sınırı (∂M) geometrisi çalışır.',
      en: 'Pure Fractal: Domain ontologies off [0,0,0]; evaluates pure 24B Mandelbrot boundary (∂M) geometry.'
    }
  };
  const GATE_PROFILES = {
    agent_mcp_guard: 'smart_router',
    fintech_payment_tr: 'risk_evaluator',
    api_zero_trust_waf: 'security_guard'
  };

  let gates = null;
  let current = { gate: 'agent_mcp_guard', scenario: 'del', preset: 'auto' };
  let last = null;
  const latencies = [];

  async function loadGates() {
    for (const url of ['policies/builtin_gates.json', '../policies/builtin_gates.json', '/policies/builtin_gates.json']) {
      try {
        const r = await fetch(url);
        if (r.ok) { gates = await r.json(); return; }
      } catch (e) { /* try next */ }
    }
    gates = null;
  }

  function effectivePresetKey() {
    return current.preset === 'auto' ? (GATE_PROFILES[current.gate] || 'smart_router') : current.preset;
  }

  function syncWerrInputsFromPreset() {
    const pSel = document.getElementById('werrPresetSel');
    if (!pSel) return;
    const key = effectivePresetKey();
    const p = WERR_PRESETS[key];
    const desc = document.getElementById('werrPresetDesc');
    const L = A().lang();
    if (p) {
      document.getElementById('wpDomain').checked = p.enable_domain;
      document.getElementById('wpLexical').checked = p.enable_lexical;
      document.getElementById('wpResonance').checked = p.enable_resonance;
      document.getElementById('wpTripod').checked = p.tripod;
      document.getElementById('wpCx').value = p.cx;
      document.getElementById('wpCy').value = p.cy;
      document.getElementById('wpZoom').value = p.zoom;
      document.getElementById('wpIter').value = p.max_iter;
      document.getElementById('wpLambda').value = p.cadence_lambda;
      document.getElementById('wpAlpha').value = p.cadence_alpha;
      if (desc) {
        const autoTag = current.preset === 'auto' ? `[auto → ${key}] ` : '';
        desc.textContent = autoTag + (p[L] || p.tr);
      }
    } else if (desc) {
      desc.textContent = L === 'en'
        ? 'Custom configuration: your manual 8-state cube and 24B seed parameters are active.'
        : 'Özel kurgu: seçtiğiniz 8-durum küpü ve 24B tohum parametreleri doğrudan uygulanır.';
    }
  }

  function readWerrParams() {
    const pSel = document.getElementById('werrPresetSel');
    if (!pSel) return { preset: 'auto' };
    const enable_domain = document.getElementById('wpDomain').checked;
    const enable_lexical = enable_domain ? document.getElementById('wpLexical').checked : false;
    const enable_resonance = enable_domain ? document.getElementById('wpResonance').checked : false;
    const tripod = document.getElementById('wpTripod').checked;
    const cx = parseFloat(document.getElementById('wpCx').value);
    const cy = parseFloat(document.getElementById('wpCy').value);
    const zoom = parseFloat(document.getElementById('wpZoom').value);
    const max_iter = parseInt(document.getElementById('wpIter').value, 10) || 36;
    const cadence_lambda = parseFloat(document.getElementById('wpLambda').value);
    const cadence_alpha = parseFloat(document.getElementById('wpAlpha').value);
    let mode = 'pure_fractal';
    if (enable_domain) {
      if (enable_lexical && enable_resonance) mode = 'hybrid';
      else if (enable_lexical) mode = 'lexical';
      else if (enable_resonance) mode = 'resonance';
    }
    return {
      preset: current.preset === 'custom' ? effectivePresetKey() : current.preset,
      mode,
      domain_mode: enable_domain ? 'multi' : 'none',
      enable_domain,
      enable_lexical,
      enable_resonance,
      tripod,
      cx: Number.isFinite(cx) ? cx : -0.101096,
      cy: Number.isFinite(cy) ? cy : 0.956287,
      zoom: Number.isFinite(zoom) && zoom > 0 ? zoom : 45,
      max_iter: Math.max(8, Math.min(256, max_iter)),
      cadence_lambda: Number.isFinite(cadence_lambda) ? cadence_lambda : 0.10,
      cadence_alpha: Number.isFinite(cadence_alpha) ? cadence_alpha : 0.50
    };
  }

  function renderScenarios() {
    const list = document.getElementById('scnList');
    const L = A().lang();
    list.innerHTML = SCENARIOS[current.gate].map(s =>
      `<button type="button" class="scn" data-id="${s.id}" aria-pressed="${s.id === current.scenario}">${A().esc(s[L] || s.tr)}</button>`).join('');
    list.querySelectorAll('.scn').forEach(b => b.addEventListener('click', () => {
      current.scenario = b.dataset.id;
      loadScenario();
      run();
    }));
    document.getElementById('qLine').textContent = (L === 'en' ? 'question: ' : 'soru: ') + QUESTIONS[current.gate][L];
  }

  function loadScenario() {
    const s = SCENARIOS[current.gate].find(x => x.id === current.scenario) || SCENARIOS[current.gate][0];
    current.scenario = s.id;
    document.getElementById('stateBox').value = JSON.stringify(s.state, null, 2);
    renderScenarios();
  }

  async function run(opts) {
    const autoInit = Boolean(opts && opts.autoInit === true);
    const btn = document.getElementById('runBtn');
    const reactor = document.getElementById('reactor');
    let state;
    try {
      state = JSON.parse(document.getElementById('stateBox').value || '{}');
      if (!state || typeof state !== 'object' || Array.isArray(state)) throw new Error('object');
    } catch (e) {
      renderError(A().t('kkBadJson'));
      return;
    }
    btn.disabled = true;
    reactor.classList.add('busy');
    const question = QUESTIONS[current.gate][A().lang()];
    const wp = readWerrParams();
    wp.telemetry_opt_in = !autoInit;
    const body = {
      gate_id: current.gate, strict_policy: true, state,
      questions: { allow: { type: 'noul', text: question } },
      werr_preset: current.preset === 'custom' ? null : current.preset,
      werr_params: wp
    };
    let res = await A().api('/v1/decide', body, 'decide');
    let source = 'api';
    // An API older than 1.2.0 has no kernel trace; fall back to the same kernel locally.
    if (!res.ok || !res.data || !res.data.trace || !res.data.trace.candidates) {
      if (res.status === 429) { renderError(A().t('kk429')); btn.disabled = false; reactor.classList.remove('busy'); return; }
      if (gates && gates[current.gate] && window.AnswerrPolicyKernel) {
        res = A().localDecide(state, gates[current.gate], true, question);
        res.data.werr_config = {
          selection_mode: current.preset === 'auto' ? 'auto_optimal' : 'user_custom',
          preset: effectivePresetKey(),
          state_cube: [wp.enable_domain ? 1 : 0, wp.enable_lexical ? 1 : 0, wp.enable_resonance ? 1 : 0],
          mode: wp.mode, tripod: wp.tripod,
          seed_24b: { cx: wp.cx, cy: wp.cy, zoom: wp.zoom },
          max_iter: wp.max_iter, cadence_lambda: wp.cadence_lambda, cadence_alpha: wp.cadence_alpha
        };
        source = 'local';
      } else {
        renderError(A().t('kkNoApi'));
        btn.disabled = false; reactor.classList.remove('busy'); return;
      }
    } else {
      latencies.push(res.ms);
      renderMetrics();
    }
    last = { data: res.data, ms: res.ms, source, wp };
    render();
    btn.disabled = false;
    reactor.classList.remove('busy');
  }

  function renderMetrics() {
    if (!latencies.length) return;
    const s = latencies.slice().sort((a, b) => a - b);
    const med = s[Math.floor(s.length / 2)];
    document.getElementById('mLat').textContent = A().fmtNum(med, 0) + ' ms';
    document.getElementById('mLatN').textContent = (A().lang() === 'en' ? 'requests this session: ' : 'bu oturumdaki istek: ') + latencies.length;
  }

  function renderError(msg) {
    document.getElementById('vCode').textContent = 'ERR';
    const w = document.getElementById('vWord');
    w.textContent = '—'; w.className = 'verdict';
    document.getElementById('vSub').textContent = msg;
  }

  function localizeReason(s) {
    if (!s || A().lang() !== 'tr') return s || '';
    return String(s)
      .replace(/^Tool '([^']+)' is in class 'destructive' -> DENY$/, "Araç '$1' yıkıcı ('destructive') sınıfında → DUR")
      .replace(/^Tool '([^']+)' is in class 'privileged' -> DENY$/, "Araç '$1' ayrıcalıklı ('privileged') sınıfında → DUR")
      .replace(/^Tool '([^']+)' is in class 'mutating' -> REVIEW$/, "Araç '$1' değiştirici ('mutating') sınıfında → İNSANA DEVRET")
      .replace(/^Tool '([^']+)' is in class 'readonly' \(read-only\)\.$/, "Araç '$1' salt okunur ('readonly') sınıfında.")
      .replace(/^Tool '([^']+)' is not in the known tool registry\.$/, "Araç '$1' bilinen araç kayıtlarında yer almıyor.")
      .replace(/^Strict mode: unrecognized field\(s\): (.+)$/, 'Sıkı mod: tanınmayan alan(lar): $1')
      .replace(/^Missing required field\(s\): (.+)$/, 'Eksik zorunlu alan(lar): $1')
      .replace(/^All (\d+) fields recognized; risk score ([0-9.\-]+) within bounds\.$/, 'Tüm $1 alan tanındı; risk puanı ($2) güvenli sınırlar içinde.')
      .replace(/^Risk score ([0-9.\-]+) >= deny threshold ([0-9.\-]+)\.$/, 'Risk puanı ($1) ≥ reddetme eşiği ($2).')
      .replace(/^Risk score ([0-9.\-]+) >= review threshold ([0-9.\-]+)\.$/, 'Risk puanı ($1) ≥ inceleme eşiği ($2).')
      .replace(/^Destructive tool class \(delete\/drop\/wipe\/shell\/truncate\)\.$/, 'Yıkıcı araç sınıfı (silme/drop/wipe/kabuk/truncate).')
      .replace(/^Credential\/secret\/privilege tool requires explicit break-glass\.$/, 'Kimlik bilgisi/sır/yetki aracı açık acil durum (break-glass) onayı gerektirir.')
      .replace(/^Unauthenticated caller cannot invoke agent tools\.$/, 'Kimliği doğrulanmamış çağrıcı ajan araçlarını çalıştıramaz.')
      .replace(/^Repeated authentication or tool failures\.$/, 'Tekrarlayan kimlik doğrulama veya araç hataları.')
      .replace(/^High-value transaction requires human approval\.$/, 'Yüksek tutarlı işlem insan onayı gerektirir.')
      .replace(/^Impossible-travel velocity anomaly \(>800 km\/h\)\.$/, 'İmkânsız yolculuk hız anomalisi (>800 km/s).')
      .replace(/^Card-testing velocity spike\.$/, 'Kart denemesi hız sıçraması.')
      .replace(/^High-value payment requires 3DS \/ manual review\.$/, 'Yüksek tutarlı ödeme 3D Secure / insan incelemesi gerektirir.')
      .replace(/^Device integrity anomaly requires step-up verification\.$/, 'Cihaz bütünlüğü anomalisi ek doğrulama gerektirir.')
      .replace(/^Request frequency exceeds DDoS ceiling \(100 rps\)\.$/, 'İstek sıklığı DDoS tavanını aşıyor (100 istek/sn).')
      .replace(/^Brute-force authentication threshold exceeded\.$/, 'Kaba kuvvet kimlik doğrulama eşiği aşıldı.')
      .replace(/^Caller role flagged as adversarial\.$/, 'Çağrıcı rolü saldırgan olarak işaretlendi.')
      .replace(/^Guest caller in elevated request regime\.$/, 'Misafir çağrıcı yüksek istek rejiminde.');
  }

  function render() {
    if (!last) return;
    const d = last.data;
    const tr = d.trace || {};
    const v = d.verdict || tr.verdict || 'REVIEW';
    const meta = A().VERDICT[v] || A().VERDICT.REVIEW;
    const esc = A().esc;
    document.getElementById('vCode').textContent = (A().lang() === 'en' ? 'VERDICT · ' : 'HÜKÜM · ') + meta.code;
    const w = document.getElementById('vWord');
    w.textContent = A().t(meta.key); w.className = 'verdict ' + meta.cls;
    document.getElementById('vSub').textContent = localizeReason(tr.reason || '');
    document.getElementById('ringA').setAttribute('stroke', meta.color);
    document.getElementById('ringB').setAttribute('stroke', meta.color);

    const ans = (d.answers && (d.answers.allow || Object.values(d.answers)[0])) || {};
    document.getElementById('sConf').textContent = v === 'REVIEW' ? '—' : Number(ans.confidence || 0).toFixed(2);
    document.getElementById('sRule').textContent = tr.rule_id || '—';
    document.getElementById('sLat').textContent = A().fmtNum(last.source === 'api' ? last.ms : (d.latency_ms || 0), last.source === 'api' ? 0 : 2) + ' ms';
    document.getElementById('sSource').textContent = last.source === 'api'
      ? A().t('kkSrcApi') + ' · ' + A().t('kkSrvMs') + ' ' + A().fmtNum(d.latency_ms, 2) + ' ms'
      : A().t('kkSrcLocal');

    const cands = tr.candidates || [];
    let winIdx = 0;
    const sev = { ALLOW: 0, REVIEW: 1, DENY: 2 };
    cands.forEach((c, i) => { if (sev[c.effect] > sev[cands[winIdx].effect]) winIdx = i; });
    document.getElementById('candList').innerHTML = cands.map((c, i) => {
      const m = A().VERDICT[c.effect];
      return `<div class="trace-row${i === winIdx ? ' win' : ''}"><span class="${i === winIdx ? m.cls : ''}">${i === winIdx ? '▶' : '·'}</span>` +
        `<span>${esc(c.rule_id)}</span><span class="${m.cls}" style="text-align:right">${esc(c.effect)}</span>` +
        `<span class="why">${esc(localizeReason(c.reason))}</span></div>`;
    }).join('') || `<div class="empty">—</div>`;

    const contrib = tr.feature_contributions || {};
    const vals = Object.entries(contrib);
    const maxAbs = Math.max(1, ...vals.map(([, x]) => Math.abs(x)));
    const unk = new Set(tr.unrecognized_fields || []);
    document.getElementById('barList').innerHTML = vals.map(([k, x]) => {
      const pct = Math.min(50, Math.abs(x) / maxAbs * 50);
      const color = unk.has(k) ? '#FFB048' : (x > 0 ? '#FF6B5B' : '#8CDEEC');
      const left = x >= 0 ? 50 : 50 - pct;
      const label = unk.has(k) ? '?' : (x > 0 ? '+' : '') + A().fmtNum(x, 2);
      return `<div class="bar"><span class="n" title="${esc(k)}">${esc(k)}</span>` +
        `<span class="t"><span class="f" style="left:${left}%;width:${unk.has(k) ? 3 : pct}%;background:${color}"></span>` +
        `<span class="f" style="left:50%;width:1px;background:rgba(140,222,236,0.35)"></span></span>` +
        `<span class="v" style="color:${color}">${esc(label)}</span></div>`;
    }).join('') + `<div class="small-mono">${esc(A().t('kkRisk'))} ${A().fmtNum(tr.risk_score, 2)}</div>`;

    const unknown = tr.unrecognized_fields || [];
    const missing = tr.missing_required_fields || [];
    document.getElementById('unkNote').innerHTML =
      `<b>${esc(A().t('kkUnk'))}</b> ${unknown.length ? esc(unknown.join(', ')) : esc(A().t('kkNone'))}` +
      (missing.length ? `<br><b>${esc(A().t('kkMissing'))}</b> ${esc(missing.join(', '))}` : '');

    const fm = tr.fractal_manifold || {};
    const wc = d.werr_config || fm.werr_config || (last.wp ? {
      preset: effectivePresetKey(),
      state_cube: [last.wp.enable_domain ? 1 : 0, last.wp.enable_lexical ? 1 : 0, last.wp.enable_resonance ? 1 : 0],
      mode: last.wp.mode, tripod: last.wp.tripod,
      seed_24b: { cx: last.wp.cx, cy: last.wp.cy, zoom: last.wp.zoom }
    } : null);
    const mfEl = document.getElementById('werrManifoldLine');
    if (mfEl && wc) {
      const cube = Array.isArray(wc.state_cube) ? `[${wc.state_cube.join(',')}]` : '[1,1,1]';
      const coords = fm.active_coordinates || wc.seed_24b || {};
      const cxStr = coords.cx != null ? Number(coords.cx).toFixed(4) : '—';
      const cyStr = coords.cy != null ? Number(coords.cy).toFixed(4) : '—';
      const zmStr = coords.zoom != null ? Number(coords.zoom).toFixed(1) : '—';
      const wr = fm.werr_reflex && (fm.werr_reflex.allow || Object.values(fm.werr_reflex)[0]);
      const wrTxt = wr && wr.noul != null ? ` · noul=${Number(wr.noul).toFixed(3)}` : '';
      mfEl.innerHTML = `werr: <b>${esc(wc.preset || 'auto')}</b> ${esc(cube)} (${esc(wc.mode || 'hybrid')}${wc.tripod ? '+tripod' : ''}) · c=(${esc(cxStr)}, ${esc(cyStr)}) ×${esc(zmStr)}${esc(wrTxt)}`;
    }

    document.getElementById('sealLine').innerHTML =
      `${esc(A().t('kkPolicy'))} ${esc(tr.policy_id || '—')} v${esc(tr.policy_version || '—')}<br>` +
      `${esc(A().t('kkSeal'))} <span title="${esc(tr.policy_seal || '')}">${esc(A().shortSeal(tr.policy_seal))}</span>`;
  }

  document.addEventListener('DOMContentLoaded', async () => {
    const sel = document.getElementById('gateSel');
    if (!sel) return;
    sel.addEventListener('change', () => {
      current.gate = sel.value;
      current.scenario = SCENARIOS[sel.value][0].id;
      if (current.preset === 'auto') syncWerrInputsFromPreset();
      loadScenario();
      run();
    });
    const pSel = document.getElementById('werrPresetSel');
    if (pSel) {
      pSel.addEventListener('change', () => {
        current.preset = pSel.value;
        syncWerrInputsFromPreset();
        if (current.preset === 'custom') {
          const adv = document.getElementById('werrAdvBox');
          if (adv) adv.open = true;
        }
        run();
      });
      ['wpDomain', 'wpLexical', 'wpResonance', 'wpTripod', 'wpCx', 'wpCy', 'wpZoom', 'wpIter', 'wpLambda', 'wpAlpha'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', () => {
          if (id === 'wpDomain' && !el.checked) {
            document.getElementById('wpLexical').checked = false;
            document.getElementById('wpResonance').checked = false;
          }
          current.preset = 'custom';
          pSel.value = 'custom';
          syncWerrInputsFromPreset();
          run();
        });
      });
    }
    document.getElementById('runBtn').addEventListener('click', () => run());
    const form = document.getElementById('accessForm');
    if (form) form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const mail = document.getElementById('eposta').value.trim();
      const status = document.getElementById('erStatus');
      const btn = form.querySelector('button[type="submit"]');
      btn.disabled = true;
      status.textContent = A().t('erSending');
      const res = await A().api('/v1/access-request', {
        email: mail, lang: A().lang(), source: 'answerr.me/pro',
        website: (document.getElementById('erWeb') || {}).value || ''
      }, 'access');
      btn.disabled = false;
      if (res.ok) { status.textContent = A().t('erOk'); form.reset(); return; }
      if (res.status === 400) { status.textContent = A().t('erBad'); return; }
      if (res.status === 429) { status.textContent = A().t('kk429'); return; }
      // API unavailable or older than 1.2.0: hand over to the visitor's mail client
      const subject = encodeURIComponent('answerr Pro — tasarım ortaklığı / design partner');
      const bodyTxt = encodeURIComponent((A().lang() === 'en' ? 'Work e-mail: ' : 'İş e-postası: ') + mail);
      status.textContent = A().t('erFallback');
      window.location.href = `mailto:ask@answerr.me?subject=${subject}&body=${bodyTxt}`;
    });
    window.addEventListener('proLanguageChanged', () => { syncWerrInputsFromPreset(); renderScenarios(); render(); renderMetrics(); });
    await loadGates();
    syncWerrInputsFromPreset();
    loadScenario();
    run({ autoInit: true });
  });
})();
