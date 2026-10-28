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

  let gates = null;
  let current = { gate: 'agent_mcp_guard', scenario: 'del' };
  let last = null;
  const latencies = [];

  async function loadGates() {
    try {
      const r = await fetch('../../../policies/builtin_gates.json', { cache: 'no-cache' });
      gates = await r.json();
    } catch (e) { gates = null; }
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

  async function run() {
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
    const body = { gate_id: current.gate, strict_policy: true, state, questions: { allow: { type: 'noul', text: question } } };
    let res = await A().api('/v1/decide', body, 'decide');
    let source = 'api';
    // An API older than 1.2.0 has no kernel trace; fall back to the same kernel locally.
    if (!res.ok || !res.data || !res.data.trace || !res.data.trace.candidates) {
      if (res.status === 429) { renderError(A().t('kk429')); btn.disabled = false; reactor.classList.remove('busy'); return; }
      if (gates && gates[current.gate] && window.AnswerrPolicyKernel) {
        res = A().localDecide(state, gates[current.gate], true, question);
        source = 'local';
      } else {
        renderError(A().t('kkNoApi'));
        btn.disabled = false; reactor.classList.remove('busy'); return;
      }
    } else {
      latencies.push(res.ms);
      renderMetrics();
    }
    last = { data: res.data, ms: res.ms, source };
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
    document.getElementById('vSub').textContent = tr.reason || '';
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
        `<span class="why">${esc(c.reason)}</span></div>`;
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
    document.getElementById('sealLine').innerHTML =
      `${esc(A().t('kkPolicy'))} ${esc(tr.policy_id || '—')} v${esc(tr.policy_version || '—')}<br>` +
      `${esc(A().t('kkSeal'))} <span title="${esc(tr.policy_seal || '')}">${esc(A().shortSeal(tr.policy_seal))}</span>`;
  }

  document.addEventListener('DOMContentLoaded', async () => {
    const sel = document.getElementById('gateSel');
    if (!sel) return;
    sel.addEventListener('change', () => { current.gate = sel.value; current.scenario = SCENARIOS[sel.value][0].id; loadScenario(); run(); });
    document.getElementById('runBtn').addEventListener('click', run);
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
    window.addEventListener('proLanguageChanged', () => { renderScenarios(); render(); renderMetrics(); });
    await loadGates();
    loadScenario();
    run();
  });
})();
