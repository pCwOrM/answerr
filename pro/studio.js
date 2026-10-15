/* Derleyici — natural language -> draft policy, tests, checks */
(function () {
  'use strict';
  const A = () => window.ProApp;

  const TEMPLATES = {
    agent: {
      tr: 'Otonom AI ajanı veritabanında drop, delete veya truncate aracı çağırmak isterse reddet. İşlem tutarı 5000 dolar üzerinde ise insana gönder. Hatalı deneme sayısı 3 üstündeyse engelle. Bilinmeyen alanlarda insana devret.',
      en: 'If the agent calls a drop, delete or truncate tool, deny it. Send amounts above 5,000 USD to a human. Block when failed attempts are more than 3. Unknown fields go to human review.',
      sample: { tool_name: 'delete_customer_ledger', amount_usd: 7200, failed_attempts: 1, auth_status: true }
    },
    pay: {
      tr: 'Tutar 25.000 TL ve üzeri ise 3D Secure incelemesine gönder. Saniyede 15 veya daha fazla deneme varsa reddet. Risk skoru 0,8 üzerindeyse insana devret.',
      en: 'Send amounts of 25,000 TRY or more to 3-D Secure review. Deny when there are 15 or more attempts per window. Hand to a human when the risk score is above 0.8.',
      sample: { amount_try: 31000, velocity: 2, risk_score: 0.42, known_device: true }
    },
    api: {
      tr: 'Misafir kullanıcıları insana devret. Saniyede 100 istek üzerinde engelle. Başarısız deneme 10 veya daha fazla ise reddet.',
      en: 'Hand guest users to review. Block above 100 requests per second. Deny when failed attempts are 10 or more.',
      sample: { user_role: 'guest', req_frequency: 12, failed_attempts: 2 }
    }
  };

  let last = null;

  function setTemplate(key) {
    const tpl = TEMPLATES[key];
    document.getElementById('nl').value = tpl[A().lang()] || tpl.tr;
    document.getElementById('sample').value = JSON.stringify(tpl.sample, null, 2);
    document.querySelectorAll('[data-tpl]').forEach(b => b.setAttribute('aria-pressed', b.dataset.tpl === key ? 'true' : 'false'));
  }

  function parseSample() {
    const raw = document.getElementById('sample').value.trim();
    if (!raw) return null;
    const v = JSON.parse(raw);
    if (!v || typeof v !== 'object' || Array.isArray(v)) throw new Error('object');
    return v;
  }

  async function compile() {
    const msg = document.getElementById('compileMsg');
    const btn = document.getElementById('compileBtn');
    let sample;
    try { sample = parseSample(); } catch (e) { msg.textContent = A().t('kkBadJson'); return; }
    const gateId = (document.getElementById('gateId').value || 'studio_draft').trim().toLowerCase();
    btn.disabled = true;
    msg.textContent = A().t('stWorking');
    const res = await A().api('/v1/policies/compile', {
      prompt: document.getElementById('nl').value, gate_id: gateId, sample_state: sample,
      schema_fields: sample ? Object.keys(sample) : null
    }, 'compile');
    btn.disabled = false;
    if (!res.ok || !res.data || !res.data.sources) {
      msg.textContent = res.status === 429 ? A().t('kk429') : (res.ok ? A().t('stOldApi') : A().t('stNoApi'));
      return;
    }
    last = res.data;
    msg.textContent = A().t('stDone') + ' · ' + A().fmtNum(res.ms, 0) + ' ms';
    render();
  }

  function effCls(e) { return e === 'DENY' ? 'deny' : e === 'REVIEW' ? 'review' : 'allow'; }

  function render() {
    if (!last) return;
    const esc = A().esc;
    const L = A().lang();
    const spec = last.policy_spec;
    const sentenceOf = {};
    (last.sources || []).forEach(s => (s.rules || []).forEach(r => { sentenceOf[r] = s.sentence; }));
    document.getElementById('rules').innerHTML = (spec.hard_rules || []).map(r => {
      const m = A().VERDICT[r.effect];
      const val = Array.isArray(r.value) ? '[' + r.value.join(', ') + ']' : JSON.stringify(r.value);
      return `<div class="rule ${effCls(r.effect)}"><div class="head"><span class="${m.cls}">${esc(r.id)} · ${esc(A().t(m.key))}</span></div>` +
        `<div>${esc(r.field)} ${esc(r.op)} ${esc(val)}</div>` +
        `<div class="src">“${esc(sentenceOf[r.id] || r.reason || '')}”</div></div>`;
    }).join('') || `<div class="empty">${esc(A().t('stNoRules'))}</div>`;

    const qs = last.questions || [];
    document.getElementById('questions').innerHTML = qs.length
      ? `<div class="note"><b>${esc(A().t('stAsks'))} · ${qs.length}</b>` +
        qs.map(q => `<div style="margin-top:8px">${esc(L === 'tr' ? (q.text_tr || q.text) : q.text)}<br><span class="muted">“${esc(q.sentence)}”</span></div>`).join('') + '</div>'
      : `<div class="small-mono">${esc(A().t('stNoQ'))}</div>`;

    const tests = last.tests || [];
    document.getElementById('tests').innerHTML =
      `<caption class="sr-only">${esc(A().t('st3'))}</caption><thead><tr><th>${esc(A().t('thInput'))}</th><th>${esc(A().t('thExpect'))}</th><th>${esc(A().t('thGot'))}</th><th></th></tr></thead><tbody>` +
      tests.map(tc => {
        const m = A().VERDICT[tc.verdict];
        return `<tr><td>${esc(JSON.stringify(tc.state))}</td><td>${esc(tc.expect)}</td><td class="${m.cls}">${esc(tc.verdict)}</td><td class="${tc.passed ? 'v-allow' : 'v-deny'}">${tc.passed ? '✓' : '✗'}</td></tr>`;
      }).join('') + '</tbody>';

    const checks = last.checks || [];
    document.getElementById('checks').innerHTML =
      `<div class="label" style="margin:6px 0">${esc(A().t('stChecks'))} · ${last.tests_passed}/${last.tests_total} ${esc(A().t('stTestsOk'))}</div>` +
      checks.filter(c => c.applies !== false).map(c =>
        `<div class="check"><span class="${c.passed ? 'ok' : 'bad'}">${c.passed ? '✓' : '✗'}</span><span><span class="mono">${esc(c.id)}</span><br><span class="muted">${esc(c.detail)}</span></span></div>`).join('');

    document.getElementById('seal').innerHTML =
      `${esc(A().t('kkSeal'))} <span title="${esc(spec.policy_seal)}">${esc(A().shortSeal(spec.policy_seal))}</span><br>` +
      `${esc(A().t('stStatus'))} ${esc(last.status === 'ready_for_review' ? A().t('stReady') : A().t('stNeeds'))}`;
    ['deployBtn', 'tryBtn', 'dlBtn', 'cpBtn'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.disabled = false;
    });
  }

  async function deployToConsole() {
    if (!last || !last.policy_spec) return;
    const out = document.getElementById('tryOut');
    const spec = Object.assign({}, last.policy_spec);
    delete spec.policy_seal;
    spec.version = spec.version || '1.0.0';
    spec.source_prompt = document.getElementById('nl').value;
    let sess = null;
    try { sess = localStorage.getItem('answerr_session'); } catch (e) { sess = null; }
    if (sess) {
      try {
        const res = await fetch(A().API + '/v1/gates', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + sess },
          body: JSON.stringify(spec)
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.gate_id) {
          out.hidden = false;
          out.innerHTML = `<b class="v-allow">✓ ${A().esc(data.gate_id)}</b> · ${A().esc(A().shortSeal(data.policy_seal))} · <a href="console/#gates">${A().esc(A().lang() === 'en' ? 'Open in Console →' : 'Konsolda aç →')}</a>`;
          return;
        }
      } catch (e) { /* fall through to console handoff */ }
    }
    try { sessionStorage.setItem('answerr_draft_gate', JSON.stringify(spec, null, 2)); } catch (e) { /* ignore */ }
    window.location.href = 'console/#gates';
  }

  async function tryIt() {
    if (!last) return;
    const out = document.getElementById('tryOut');
    let sample;
    try { sample = parseSample(); } catch (e) { out.hidden = false; out.textContent = A().t('kkBadJson'); return; }
    if (!sample) { out.hidden = false; out.textContent = A().t('stNeedSample'); return; }
    const q = A().lang() === 'en' ? 'Allow this action?' : 'Bu işleme izin verilsin mi?';
    let res = await A().api('/v1/decide', { policy: last.policy_spec, state: sample, questions: { allow: { type: 'noul', text: q } } }, 'sandbox');
    let src = A().t('kkSrcApi');
    if (!res.ok || !res.data || !res.data.trace || !res.data.trace.candidates) {
      res = A().localDecide(sample, last.policy_spec, true, q);
      src = A().t('kkSrcLocal');
    }
    const d = res.data;
    const m = A().VERDICT[d.verdict];
    out.hidden = false;
    out.innerHTML = `<b>${A().esc(A().t('stTryOut'))}</b> <span class="${m.cls}">${A().esc(A().t(m.key))}</span> · ${A().esc(d.trace.rule_id)}<br>` +
      `<span class="muted">${A().esc(d.trace.reason)}</span><br><span class="muted">${A().esc(src)}</span>`;
  }

  function download() {
    if (!last) return;
    const blob = new Blob([JSON.stringify(last.policy_spec, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = (last.policy_spec.gate_id || 'policy') + '.json';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  async function copyCmd() {
    if (!last) return;
    const spec = Object.assign({}, last.policy_spec);
    delete spec.policy_seal;
    spec.version = '1.0.0';
    const cmd = "curl -X POST https://api.answerr.me/v1/gates \\\n  -H 'Content-Type: application/json' \\\n  -H 'X-API-Key: $ANSWERR_API_KEY' \\\n  -d '" + JSON.stringify(spec).replace(/'/g, "'\\''") + "'";
    try { await navigator.clipboard.writeText(cmd); document.getElementById('compileMsg').textContent = A().t('stCopied'); }
    catch (e) { document.getElementById('compileMsg').textContent = cmd; }
  }

  document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('compileBtn')) return;
    document.querySelectorAll('[data-tpl]').forEach(b => b.addEventListener('click', () => setTemplate(b.dataset.tpl)));
    document.getElementById('compileBtn').addEventListener('click', compile);
    const depBtn = document.getElementById('deployBtn');
    if (depBtn) depBtn.addEventListener('click', deployToConsole);
    document.getElementById('tryBtn').addEventListener('click', tryIt);
    document.getElementById('dlBtn').addEventListener('click', download);
    document.getElementById('cpBtn').addEventListener('click', copyCmd);
    window.addEventListener('proLanguageChanged', render);
    let editGate = null;
    try {
      const raw = sessionStorage.getItem('answerr_edit_gate');
      if (raw) { editGate = JSON.parse(raw); sessionStorage.removeItem('answerr_edit_gate'); }
    } catch (e) { editGate = null; }
    if (editGate && editGate.gate_id) {
      document.getElementById('gateId').value = editGate.gate_id;
      if (editGate.source_prompt) {
        document.getElementById('nl').value = editGate.source_prompt;
      } else if (Array.isArray(editGate.hard_rules) && editGate.hard_rules.length) {
        document.getElementById('nl').value = editGate.hard_rules.map(r => r.reason || `${r.field} ${r.op} ${JSON.stringify(r.value)} -> ${r.effect}`).join('. ');
      }
      const sampleObj = {};
      (editGate.fields || []).forEach(f => { sampleObj[f] = 1; });
      if (Object.keys(sampleObj).length) document.getElementById('sample').value = JSON.stringify(sampleObj, null, 2);
    } else {
      setTemplate('agent');
    }
  });
})();
