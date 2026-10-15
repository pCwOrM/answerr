/* answerr.me/pro — shared client: API calls, reCAPTCHA, local kernel fallback, rendering helpers */
(function () {
  'use strict';

  // ?api=... override is honoured only on a local development host
  const LOCAL = /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
  const OVERRIDE = LOCAL ? new URLSearchParams(location.search).get('api') : null;
  const API = OVERRIDE && /^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(OVERRIDE) ? OVERRIDE : 'https://api.answerr.me';
  const SITE_KEY = '6LdP-JgqAAAAAJLdy_W8uowqstSa4XKlJTOkVAux';
  const t = (k) => (window.ProI18n ? window.ProI18n.t(k) : k);
  const lang = () => (window.ProI18n ? window.ProI18n.lang : 'tr');

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function recaptchaToken(action) {
    return new Promise(resolve => {
      const done = (v) => resolve(v || null);
      const timer = setTimeout(() => done(null), 1500);
      try {
        if (typeof grecaptcha === 'undefined' || !grecaptcha.ready) { clearTimeout(timer); return done(null); }
        grecaptcha.ready(() => {
          grecaptcha.execute(SITE_KEY, { action }).then(tok => { clearTimeout(timer); done(tok); }, () => { clearTimeout(timer); done(null); });
        });
      } catch (e) { clearTimeout(timer); done(null); }
    });
  }

  async function api(path, body, action) {
    const headers = { 'Content-Type': 'application/json' };
    if (body) {
      const tok = await recaptchaToken(action || 'decide');
      if (tok) headers['X-Recaptcha-Token'] = tok;
    }
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    const t0 = performance.now();
    try {
      const res = await fetch(API + path, {
        method: body ? 'POST' : 'GET', headers, body: body ? JSON.stringify(body) : undefined, signal: ctrl.signal
      });
      const ms = performance.now() - t0;
      let data = null;
      try { data = await res.json(); } catch (e) { data = null; }
      return { ok: res.ok, status: res.status, data, ms };
    } catch (e) {
      return { ok: false, status: 0, data: null, ms: performance.now() - t0, error: String(e) };
    } finally { clearTimeout(timer); }
  }

  // Same response shape as POST /v1/decide, computed in the browser with the shared kernel.
  function localDecide(state, policy, strict, question) {
    const K = window.AnswerrPolicyKernel;
    const t0 = performance.now();
    const r = K.evaluate(state, policy, strict);
    const a = K.answerQuestion(r, question);
    const ms = performance.now() - t0;
    return {
      source: 'local', ms,
      data: {
        verdict: r.verdict, label: r.label, decision: a.decision, answers: { allow: a },
        trace: {
          policy_id: r.policy_id, policy_version: r.policy_version,
          policy_seal: policy ? (policy.policy_seal || K.policySeal(policy)) : null,
          verdict: r.verdict, rule_id: r.rule_id, reason: r.reason, risk_score: r.risk_score,
          candidates: r.candidates, tool: r.tool, feature_contributions: r.feature_contributions,
          recognized_fields: r.recognized_fields, unrecognized_fields: r.unrecognized_fields,
          missing_required_fields: r.missing_required_fields, ood_detected: r.ood_detected
        },
        latency_ms: ms
      }
    };
  }

  const VERDICT = {
    ALLOW: { cls: 'v-allow', color: '#8CDEEC', key: 'vAllow', code: 'ALLOW' },
    REVIEW: { cls: 'v-review', color: '#FFB048', key: 'vReview', code: 'REVIEW' },
    DENY: { cls: 'v-deny', color: '#FF6B5B', key: 'vDeny', code: 'DENY' }
  };

  function fmtNum(x, d) {
    if (x == null || Number.isNaN(x)) return '—';
    return Number(x).toLocaleString(lang() === 'tr' ? 'tr-TR' : 'en-US', { maximumFractionDigits: d == null ? 2 : d });
  }

  function shortSeal(s) {
    if (!s) return '—';
    return s.length > 30 ? s.slice(0, 19) + '…' + s.slice(-6) : s;
  }

  async function health() {
    const r = await api('/v1/health');
    return r.ok && r.data ? r.data : null;
  }

  function setupNav() {
    const btn = document.querySelector('.nav-toggle');
    const links = document.querySelector('.nav-links');
    if (btn && links) {
      btn.addEventListener('click', () => {
        const open = links.classList.toggle('open');
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
      links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
        if (links.classList.contains('open')) {
          links.classList.remove('open');
          btn.setAttribute('aria-expanded', 'false');
        }
      }));
    }
  }

  async function setupHud() {
    const el = document.getElementById('hudStatus');
    if (!el) return;
    const h = await health();
    const render = () => {
      if (h) {
        el.innerHTML = `<span class="dot on"></span>${esc(t('hudOnline'))} · API ${esc(h.api_version)} · ${esc(t('hudKernel'))} ${esc(h.kernel_version || '—')}`;
      } else {
        el.innerHTML = `<span class="dot off"></span>${esc(t('hudOffline'))}`;
      }
    };
    render();
    window.addEventListener('proLanguageChanged', render);
    window.ProApp.apiOnline = Boolean(h);
  }

  window.ProApp = { API, api, recaptchaToken, localDecide, VERDICT, esc, t, lang, fmtNum, shortSeal, health, apiOnline: null };
  document.addEventListener('DOMContentLoaded', () => { setupNav(); setupHud(); });
})();
