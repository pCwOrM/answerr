/* answerr.me/pro/research — live determinism check.
   Runs the same policy kernel the API uses, in this browser, on one state 10,000 times.
   Nothing here is simulated: the verdict count, the order test and the timing are measured. */
(function () {
  'use strict';
  var K = window.AnswerrPolicyKernel;
  var btn = document.getElementById('dtRun');
  if (!btn || !K) return;
  var $ = function (id) { return document.getElementById(id); };
  var t = function (k, d) { try { var v = window.ProI18n && window.ProI18n.t(k); return v && v !== k ? v : d; } catch (e) { return d; } };
  var N = 10000, BATCH = 100;
  var STATE = { tool_name: 'transfer_funds', user_role: 'agent', auth_status: true, amount_usd: 1924 };
  var STATE_REORDERED = { amount_usd: 1924, auth_status: true, user_role: 'agent', tool_name: 'transfer_funds' };
  var policy = null;

  function loadPolicy() {
    if (policy) return Promise.resolve(policy);
    var urls = ['../policies/builtin_gates.json', '/policies/builtin_gates.json'];
    return urls.reduce(function (p, u) {
      return p.catch(function () { return fetch(u).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }); });
    }, Promise.reject()).then(function (g) { policy = g.agent_mcp_guard; return policy; });
  }
  function key(r) { return r.verdict + '|' + r.rule_id; }
  function fmtUs(us) { return us < 1000 ? us.toFixed(us < 10 ? 1 : 0) + ' µs' : (us / 1000).toFixed(2) + ' ms'; }
  function verdictLabel(v) { return v === 'ALLOW' ? t('vAllow', 'GEÇ') : v === 'DENY' ? t('vDeny', 'DUR') : t('vReview', 'İNSANA DEVRET'); }

  function run() {
    btn.disabled = true;
    $('dtStatus').textContent = t('rs2Running', 'Çalışıyor…');
    loadPolicy().then(function (p) {
      var seen = {}, perBatch = [], first = null;
      var i = 0;
      (function step() {
        var t0 = performance.now(), r;
        for (var j = 0; j < BATCH; j++) { r = K.evaluate(STATE, p, true); seen[key(r)] = 1; }
        perBatch.push(((performance.now() - t0) / BATCH) * 1000);
        if (!first) first = r;
        i += BATCH;
        if (i < N) { setTimeout(step, 0); return; }
        var re = K.evaluate(STATE_REORDERED, p, true);
        perBatch.sort(function (a, b) { return a - b; });
        var median = perBatch[Math.floor(perBatch.length / 2)];
        $('dtCalls').textContent = N.toLocaleString(document.documentElement.lang === 'tr' ? 'tr-TR' : 'en-US');
        $('dtDistinct').textContent = String(Object.keys(seen).length);
        $('dtOrder').textContent = key(re) === key(first) ? t('rs2Same', 'aynı hüküm') : t('rs2Diff', 'farklı hüküm');
        $('dtMedian').textContent = fmtUs(median);
        $('dtVerdict').textContent = verdictLabel(first.verdict);
        var rule = document.createElement('small'); rule.textContent = first.rule_id || ''; $('dtVerdict').appendChild(rule);
        $('dtSeal').textContent = K.policySeal(p);
        $('dtStatus').textContent = t('rs2TestFoot', 'Rakamlar bu tarayıcıda ölçülür; cihazınıza göre değişir.');
        btn.disabled = false;
      })();
    }).catch(function () {
      $('dtStatus').textContent = t('rs2Fail', 'Politika dosyası yüklenemedi.');
      btn.disabled = false;
    });
  }
  btn.addEventListener('click', run);
  // Run once when the section scrolls into view so the numbers are there without a click.
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { io.disconnect(); run(); } }, { threshold: 0.4 });
    io.observe($('dogrulama'));
  }
})();
