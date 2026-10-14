/**
 * answerr policy kernel (JavaScript) — deterministic verdict layer.
 *
 * Mirrors policy_kernel.py. Both are checked against tests/policy_vectors.json
 * so the same state + policy yields the same verdict in the browser, in Node
 * and on the server.
 *
 * Verdicts: ALLOW, REVIEW (hand to a human), DENY. The most severe candidate
 * wins. The question text never changes the verdict; it only decides how the
 * verdict is expressed as a boolean.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.AnswerrPolicyKernel = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const KERNEL_VERSION = '1.0.0';
  const SEVERITY = { ALLOW: 0, REVIEW: 1, DENY: 2 };
  const LABELS = { ALLOW: 'ALLOWED', REVIEW: 'ABSTAIN_REVIEW', DENY: 'DENIED' };
  const RISK_ALLOW_MAX = 0.2;
  const RISK_DENY_MIN = 1.4;

  const TOOL_FIELDS = ['tool', 'tool_name', 'action', 'command', 'operation', 'method',
    'endpoint', 'function', 'function_name'];

  const TOOL_CLASSES = {
    destructive: ['drop', 'delete', 'del', 'remove', 'rm', 'rmdir', 'unlink', 'truncate',
      'destroy', 'purge', 'wipe', 'erase', 'kill', 'terminate', 'shutdown',
      'revoke', 'sil', 'silme', 'kaldir', 'yoket'],
    privileged: ['exec', 'execute', 'shell', 'bash', 'sudo', 'eval', 'spawn', 'chmod',
      'chown', 'grant', 'escalate', 'impersonate', 'su', 'ssh', 'private',
      'secret', 'secrets', 'credential', 'credentials', 'password', 'passwd',
      'calistir'],
    financial: ['transfer', 'wire', 'withdraw', 'pay', 'payment', 'payout', 'refund',
      'charge', 'swap', 'trade', 'buy', 'sell', 'order', 'purchase', 'mint',
      'burn', 'approve', 'sign', 'odeme', 'ode', 'aktar', 'havale', 'eft', 'satin'],
    write: ['update', 'write', 'insert', 'create', 'add', 'put', 'patch', 'set', 'modify',
      'edit', 'upload', 'deploy', 'publish', 'release', 'merge', 'push', 'commit',
      'send', 'email', 'mail', 'post', 'invite', 'rename', 'move', 'migrate',
      'install', 'import', 'export', 'restart', 'reboot', 'scale', 'enable',
      'disable', 'assign', 'reset', 'guncelle', 'yaz', 'ekle', 'olustur', 'gonder',
      'yayinla'],
    read: ['read', 'get', 'list', 'search', 'query', 'view', 'fetch', 'ping', 'status',
      'describe', 'show', 'count', 'find', 'lookup', 'inspect', 'check', 'health',
      'summary', 'summarize', 'preview', 'oku', 'listele', 'ara', 'sorgula',
      'goruntule']
  };
  const TOOL_COMBOS = [['format', ['disk', 'drive', 'volume', 'partition'], 'destructive']];
  const DEFAULT_TOOL_POLICY = {
    destructive: 'DENY', privileged: 'DENY', financial: 'REVIEW',
    write: 'REVIEW', read: 'ALLOW', unknown: 'REVIEW'
  };
  const CLASS_ORDER = ['destructive', 'privileged', 'financial', 'write', 'read'];
  const AMBIGUOUS_NOUNS = ['order', 'orders', 'status', 'payment', 'payments', 'post', 'posts',
    'email', 'emails', 'mail', 'release', 'trade', 'trades', 'charge',
    'charges', 'transfer', 'transfers', 'update', 'updates', 'export',
    'import', 'sign', 'set', 'count', 'summary', 'health', 'preview',
    'check', 'view'];

  const SIG_FAILURE = ['fail', 'failed', 'failure', 'failures', 'error', 'errors', 'attempt',
    'attempts', 'retry', 'retries', 'hata', 'hatali', 'deneme', 'basarisiz'];
  const SIG_RATE = ['rate', 'freq', 'frequency', 'velocity', 'rps', 'qps', 'hiz', 'burst'];
  const SIG_AMOUNT = ['amount', 'tutar', 'price', 'total', 'exposure', 'borrow', 'value'];
  const SIG_TRUST_BOOL = ['auth', 'authenticated', 'verified', 'valid', 'known', 'biometric',
    'mfa', 'dogrulandi', 'dogrulanmis', 'safe'];
  const SIG_HAZARD_BOOL = ['suspicious', 'anomaly', 'attack', 'threat', 'exploit', 'mismatch',
    'blacklisted', 'supheli', 'anomali', 'sandwich', 'burst'];
  const SIG_ROLE = ['role', 'rol', 'actor'];
  const SIG_RISK_SCORE = ['risk', 'fraud', 'anomaly', 'drift'];
  const SIG_TRUST_SCORE = ['trust', 'reputation', 'guven'];
  const SIG_TEMP = ['temp', 'temperature', 'sicaklik'];
  const SIG_LOAD = ['torque', 'tork', 'load', 'yuk'];
  const SIG_VIBRATION = ['vibration', 'titresim'];
  const SIG_PROXIMITY = ['proximity', 'distance', 'mesafe'];
  const QUALIFIERS = ['user', 'tool', 'name', 'action', 'command', 'operation', 'method', 'endpoint',
    'function', 'status', 'count', 'usd', 'try', 'tl', 'eur', 'ms', 'pct',
    'percent', 'sec', 'per', 'min', 'score', 'id', 'uuid', 'tenant', 'req',
    'request', 'requests', 'num', 'number', 'level', 'cart', 'card', 'device',
    'geo', 'ip', 'country', 'account', 'session', 'time', 'window', 'transaction',
    'kmh', 'celsius', 'nm', 'g', 'm', 'joint', 'motor', 'cpu', 'core', 'actuator',
    'ratio', 'kullanici', 'islem', 'sayisi', 'is', 'has'];
  const KNOWN_VOCAB = new Set([].concat(SIG_FAILURE, SIG_RATE, SIG_AMOUNT, SIG_TRUST_BOOL,
    SIG_HAZARD_BOOL, SIG_ROLE, SIG_RISK_SCORE, SIG_TRUST_SCORE, SIG_TEMP, SIG_LOAD,
    SIG_VIBRATION, SIG_PROXIMITY, QUALIFIERS, TOOL_FIELDS));

  const ROLE_RISK = [
    [['admin', 'root', 'superuser', 'owner', 'yonetici', 'kurucu'], -1.5],
    [['member', 'user', 'kullanici', 'uye', 'employee', 'staff'], -0.8],
    [['service', 'internal', 'system', 'sistem'], -0.5],
    [['agent', 'bot_agent', 'assistant', 'ajan'], 0.3],
    [['guest', 'anonymous', 'anonim', 'misafir', 'unverified', 'visitor'], 0.9],
    [['suspicious', 'supheli'], 1.8],
    [['attacker', 'malicious', 'hacker', 'bot', 'saldirgan', 'zararli'], 2.5]
  ];

  const DENY_POLARITY = /\b(block|deny|reject|refuse|forbid|halt|stop|quarantine|shutdown|revert|engelle|reddet|durdur|blokla|kapat|karantina|yasakla)/;
  const META_KEYS = new Set(['_task_id', 'presetId', 'warmup', 'ping']);

  // ------------------------------------------------------------ helpers
  function normalizeText(s) {
    return String(s).replace(/İ/g, 'i').toLowerCase().replace(/̇/g, '')
      .replace(/ı/g, 'i').replace(/ş/g, 's').replace(/ğ/g, 'g').replace(/ü/g, 'u')
      .replace(/ö/g, 'o').replace(/ç/g, 'c').replace(/â/g, 'a').replace(/î/g, 'i').replace(/û/g, 'u');
  }
  function tokenize(s) {
    const raw = normalizeText(String(s).replace(/([a-z0-9])([A-Z])/g, '$1_$2'));
    return raw.split(/[^a-z0-9]+/).filter(Boolean);
  }
  function round4(x) { return Math.floor(x * 10000 + 0.5) / 10000; }
  function isNumber(v) { return typeof v === 'number' && Number.isFinite(v); }
  function anyIn(tokens, vocab) { return tokens.some(t => vocab.includes(t)); }
  function eq(a, b) {
    if (isNumber(a) && isNumber(b)) return a === b;
    if (typeof a === 'boolean' || typeof b === 'boolean') return typeof a === 'boolean' && typeof b === 'boolean' && a === b;
    if (typeof a === 'string' && typeof b === 'string') return a === b;
    return false;
  }
  function has(o, k) { return o != null && Object.prototype.hasOwnProperty.call(o, k); }

  // canonical JSON (sorted keys, compact) — matches Python canonical_json
  function canonicalJson(o) {
    if (o === null || typeof o !== 'object') return JSON.stringify(o);
    if (Array.isArray(o)) return '[' + o.map(canonicalJson).join(',') + ']';
    return '{' + Object.keys(o).sort().map(k => JSON.stringify(k) + ':' + canonicalJson(o[k])).join(',') + '}';
  }

  // SHA-256 (synchronous, UTF-8) — small reference implementation
  function sha256Hex(str) {
    const bytes = unescape(encodeURIComponent(str));
    const K = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
      0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
      0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
      0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
      0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
      0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
      0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
      0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2];
    let H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    const l = bytes.length;
    const words = [];
    for (let i = 0; i < l; i++) words[i >> 2] |= bytes.charCodeAt(i) << (24 - (i % 4) * 8);
    words[l >> 2] |= 0x80 << (24 - (l % 4) * 8);
    const nBlocks = (((l + 8) >> 6) + 1) * 16;
    for (let i = words.length; i < nBlocks; i++) words[i] = words[i] | 0;
    words[nBlocks - 1] = (l * 8) >>> 0;
    words[nBlocks - 2] = Math.floor((l * 8) / 0x100000000);
    const W = new Array(64);
    const rotr = (x, n) => (x >>> n) | (x << (32 - n));
    for (let j = 0; j < nBlocks; j += 16) {
      let [a, b, c, d, e, f, g, h] = H;
      for (let i = 0; i < 64; i++) {
        if (i < 16) W[i] = words[j + i] | 0;
        else {
          const s0 = rotr(W[i - 15], 7) ^ rotr(W[i - 15], 18) ^ (W[i - 15] >>> 3);
          const s1 = rotr(W[i - 2], 17) ^ rotr(W[i - 2], 19) ^ (W[i - 2] >>> 10);
          W[i] = (W[i - 16] + s0 + W[i - 7] + s1) | 0;
        }
        const S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        const ch = (e & f) ^ (~e & g);
        const t1 = (h + S1 + ch + K[i] + W[i]) | 0;
        const S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        const maj = (a & b) ^ (a & c) ^ (b & c);
        const t2 = (S0 + maj) | 0;
        h = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
      }
      H = [(H[0] + a) | 0, (H[1] + b) | 0, (H[2] + c) | 0, (H[3] + d) | 0,
        (H[4] + e) | 0, (H[5] + f) | 0, (H[6] + g) | 0, (H[7] + h) | 0];
    }
    return H.map(x => (x >>> 0).toString(16).padStart(8, '0')).join('');
  }

  function policySeal(policy) {
    const body = {};
    Object.keys(policy || {}).forEach(k => { if (k !== 'policy_seal' && k !== 'seal') body[k] = policy[k]; });
    return 'sha256:' + sha256Hex(canonicalJson(body));
  }

  // ------------------------------------------------------------ tool class
  function classifyTool(value) {
    const tokens = tokenize(value);
    let classes = [];
    let firstVerb = null;
    tokens.forEach(t => {
      const hit = CLASS_ORDER.filter(c => TOOL_CLASSES[c].includes(t));
      if (!hit.length) return;
      if (firstVerb === 'read' && AMBIGUOUS_NOUNS.includes(t) && !hit.some(c => c === 'destructive' || c === 'privileged')) return;
      if (firstVerb === null) firstVerb = hit.includes('read') ? hit[hit.length - 1] : hit[0];
      hit.forEach(c => { if (!classes.includes(c)) classes.push(c); });
    });
    classes = CLASS_ORDER.filter(c => classes.includes(c));
    TOOL_COMBOS.forEach(([verb, objs, cls]) => {
      if (tokens.includes(verb) && objs.some(o => tokens.includes(o)) && !classes.includes(cls)) classes.unshift(cls);
    });
    let primary = null;
    for (const cls of CLASS_ORDER) { if (classes.includes(cls)) { primary = cls; break; } }
    return { tokens, classes, primary: primary || 'unknown' };
  }

  // ------------------------------------------------------------ policy schema
  function policyFields(policy) {
    if (!policy) return [];
    const out = [];
    (policy.fields || []).forEach(f => out.push(f));
    (policy.required_fields || []).forEach(f => out.push(f));
    Object.keys(policy.feature_weights || {}).forEach(f => out.push(f));
    (policy.hard_rules || []).forEach(r => { if (r.field) out.push(r.field); });
    Object.entries(policy.field_aliases || {}).forEach(([f, al]) => { out.push(f); (al || []).forEach(a => out.push(a)); });
    return Array.from(new Set(out));
  }
  function resolveField(state, field, policy) {
    if (has(state, field)) return [true, state[field], field];
    const aliases = ((policy || {}).field_aliases || {})[field] || [];
    for (const a of aliases) if (has(state, a)) return [true, state[a], a];
    return [false, null, null];
  }

  // ------------------------------------------------------------ hard rules
  const NUMERIC_OPS = ['>', '>=', '<', '<='];
  function evalRule(rule, state, policy) {
    const [present, val, used] = resolveField(state, rule.field || '', policy);
    if (!present) return null;
    const op = rule.op;
    const target = rule.value;
    let effect = String(rule.effect || 'DENY').toUpperCase();
    if (!has(SEVERITY, effect)) effect = 'REVIEW';
    const rid = rule.id || ('rule_' + rule.field);
    const reason = rule.reason || `${rule.field} ${op} ${JSON.stringify(target)}`;
    let hit;
    if (NUMERIC_OPS.includes(op)) {
      if (!isNumber(val) || !isNumber(target)) {
        return { effect: 'REVIEW', rule_id: 'type_mismatch:' + rid,
          reason: `Field '${used}' is not numeric; rule ${rid} cannot be evaluated.` };
      }
      hit = (op === '>' && val > target) || (op === '>=' && val >= target) || (op === '<' && val < target) || (op === '<=' && val <= target);
    } else if (op === '==' || op === '=') hit = eq(val, target);
    else if (op === '!=') hit = !eq(val, target);
    else if (op === 'in') hit = Array.isArray(target) && target.some(t => eq(val, t));
    else if (op === 'not_in') hit = Array.isArray(target) && !target.some(t => eq(val, t));
    else if (op === 'has_token') {
      const toks = typeof val === 'string' ? tokenize(val) : [];
      const want = (Array.isArray(target) ? target : [target]).map(normalizeText);
      hit = want.some(t => toks.includes(t));
    } else {
      return { effect: 'REVIEW', rule_id: 'unknown_op:' + rid, reason: `Unsupported operator '${op}' in rule ${rid}.` };
    }
    return hit ? { effect, rule_id: rid, reason } : null;
  }

  // ------------------------------------------------------------ risk signals
  function signalContribution(key, v) {
    const toks = tokenize(key);
    if (typeof v === 'boolean') {
      if (anyIn(toks, SIG_HAZARD_BOOL)) return v ? 2.5 : -0.5;
      if (anyIn(toks, SIG_TRUST_BOOL)) return v ? -0.8 : 1.2;
      return null;
    }
    if (isNumber(v)) {
      const x = v;
      if (anyIn(toks, SIG_RISK_SCORE) && anyIn(toks, ['score', 'ratio', 'index'])) return x >= 0.7 ? 2.4 : (x >= 0.4 ? 1.1 : -0.6);
      if (anyIn(toks, SIG_TRUST_SCORE)) return x >= 0.7 ? -1.2 : (x < 0.4 ? 1.8 : 0.2);
      if (anyIn(toks, SIG_FAILURE)) return (x / 5.0) * 1.5;
      if (anyIn(toks, SIG_RATE)) return x / 50.0;
      if (anyIn(toks, SIG_AMOUNT)) return x > 2000 ? Math.min(3.0, Math.log10(x / 1000.0) * 1.2) : -0.3;
      if (anyIn(toks, SIG_TEMP)) return x > 75 ? ((x - 75.0) / 10.0) * 2.2 : (x < 5 ? 1.5 : -0.5);
      if (anyIn(toks, SIG_LOAD)) return x > 85 ? ((x - 85.0) / 10.0) * 1.8 : -0.4;
      if (anyIn(toks, SIG_VIBRATION)) return x > 1.8 ? (x - 1.0) * 1.8 : -0.5;
      if (anyIn(toks, SIG_PROXIMITY)) return x < 10 ? 0.8 : -0.3;
      return null;
    }
    if (typeof v === 'string' && anyIn(toks, SIG_ROLE)) {
      const vt = tokenize(v);
      const vn = normalizeText(v);
      for (const [words, r] of ROLE_RISK) {
        if (words.some(w => vt.includes(w)) || words.includes(vn)) return r;
      }
      return 0.0;
    }
    return null;
  }
  function ruleOwnedFields(policy) {
    const owned = new Set();
    const aliases = (policy || {}).field_aliases || {};
    ((policy || {}).hard_rules || []).forEach(r => {
      if (r.field) { owned.add(r.field); (aliases[r.field] || []).forEach(a => owned.add(a)); }
    });
    return owned;
  }
  function keyRecognized(key, pfieldSet) {
    if (pfieldSet.has(key)) return true;
    const toks = tokenize(key);
    return toks.length > 0 && toks.every(t => KNOWN_VOCAB.has(t));
  }

  // ------------------------------------------------------------ main
  function evaluate(stateIn, policyIn, strictIn) {
    const state = Object.assign({}, stateIn || {});
    const policy = policyIn || null;
    const strict = Boolean(strictIn || (policy && policy.unknown_fallback === 'abstain_review'));
    const keys = Object.keys(state).filter(k => !META_KEYS.has(k)).sort();
    const pfields = new Set(policyFields(policy));
    const candidates = [];
    const contributions = {};
    const recognized = [];
    const unrecognized = [];

    if (!keys.length) candidates.push({ effect: 'REVIEW', rule_id: 'empty_state', reason: 'No state fields were provided.' });

    const missing = [];
    ((policy || {}).required_fields || []).forEach(rf => { if (!resolveField(state, rf, policy)[0]) missing.push(rf); });
    if (missing.length) candidates.push({ effect: 'REVIEW', rule_id: 'missing_required', reason: 'Required field(s) missing: ' + missing.join(', ') });

    let toolInfo = null;
    const toolPolicy = Object.assign({}, DEFAULT_TOOL_POLICY, (policy || {}).tool_policy || {});
    for (const tf of TOOL_FIELDS) {
      if (has(state, tf) && typeof state[tf] === 'string') {
        const info = classifyTool(state[tf]);
        const eff = toolPolicy[info.primary] || 'REVIEW';
        toolInfo = { field: tf, value: state[tf], tokens: info.tokens, classes: info.classes, class: info.primary, effect: eff };
        candidates.push({ effect: eff, rule_id: 'tool_class:' + info.primary, reason: `Tool '${state[tf]}' classified as ${info.primary}.` });
        break;
      }
    }

    ((policy || {}).hard_rules || []).forEach(rule => { const hit = evalRule(rule, state, policy); if (hit) candidates.push(hit); });

    const weights = (policy || {}).feature_weights || {};
    const owned = ruleOwnedFields(policy);
    let risk = 0.0;
    let hasSignal = false;
    for (const k of keys) {
      const v = state[k];
      const rec = keyRecognized(k, pfields);
      let contrib = null;
      if (has(weights, k)) {
        const w = weights[k] || {};
        if (isNumber(v)) {
          const scale = w.scale || 1.0;
          contrib = ((v - (w.threshold || 0.0)) / scale) * (w.weight ?? 1.0);
        } else if (typeof v === 'boolean') {
          contrib = (v ? 1.0 : -1.0) * (w.weight ?? 1.0);
        }
      }
      if (contrib === null && rec && !TOOL_FIELDS.includes(k) && !owned.has(k)) contrib = signalContribution(k, v);
      if (contrib !== null) { hasSignal = true; risk += contrib; contributions[k] = round4(contrib); }
      else contributions[k] = 0.0;
      (rec ? recognized : unrecognized).push(k);
    }
    risk = round4(risk);
    const ood = unrecognized.length > 0;
    if (ood && strict) candidates.push({ effect: 'REVIEW', rule_id: 'ood_unrecognized_fields', reason: 'Unrecognized field(s): ' + unrecognized.join(', ') });

    if (risk >= RISK_DENY_MIN) candidates.push({ effect: 'DENY', rule_id: 'risk_high', reason: `Risk score ${fmt(risk)} >= ${fmt(RISK_DENY_MIN)}.` });
    else if (risk > RISK_ALLOW_MAX) candidates.push({ effect: 'REVIEW', rule_id: 'risk_mid', reason: `Risk score ${fmt(risk)} is between ${fmt(RISK_ALLOW_MAX)} and ${fmt(RISK_DENY_MIN)}.` });
    else if (hasSignal || toolInfo) candidates.push({ effect: 'ALLOW', rule_id: 'risk_low', reason: `Risk score ${fmt(risk)} <= ${fmt(RISK_ALLOW_MAX)}.` });
    else if (!candidates.length) candidates.push({ effect: 'REVIEW', rule_id: 'no_signal', reason: 'No recognized risk signal; nothing to decide on.' });

    let best = candidates[0];
    for (const c of candidates.slice(1)) if (SEVERITY[c.effect] > SEVERITY[best.effect]) best = c;
    const verdict = best.effect;
    const ruleBased = !best.rule_id.startsWith('risk_');
    let confidence;
    if (verdict === 'REVIEW') confidence = 0.0;
    else if (ruleBased) confidence = 1.0;
    else {
      const edge = verdict === 'ALLOW' ? (RISK_ALLOW_MAX - risk) : (risk - RISK_DENY_MIN);
      confidence = round4(Math.min(1.0, 0.5 + edge / 2.0));
    }
    if (ood && !strict) confidence = Math.min(confidence, 0.5);
    // noul = probability that the action may proceed, consistent with the verdict
    let noul;
    if (verdict === 'REVIEW') noul = 0.5;
    else if (ruleBased) noul = verdict === 'ALLOW' ? 1.0 : 0.0;
    else noul = round4(1.0 / (1.0 + Math.exp((risk - RISK_ALLOW_MAX) * 2.0)));

    return {
      kernel_version: KERNEL_VERSION,
      verdict, label: LABELS[verdict], rule_id: best.rule_id, reason: best.reason,
      confidence, risk_score: risk, noul, candidates, tool: toolInfo,
      recognized_fields: recognized, unrecognized_fields: unrecognized,
      missing_required_fields: missing, feature_contributions: contributions,
      ood_detected: ood, strict,
      policy_id: (policy && (policy.gate_id || policy.id)) || 'universal_default',
      policy_version: (policy && policy.version) || KERNEL_VERSION
    };
  }

  // Python's str(float) for the numbers used in reasons (e.g. 1.4, 0.2, -2.3, 0.0)
  function fmt(x) {
    if (Number.isInteger(x)) return x.toFixed(1);
    return String(x);
  }

  function questionPolarity(text) { return DENY_POLARITY.test(normalizeText(text || '')) ? 'deny' : 'allow'; }

  function answerQuestion(result, text) {
    const pol = questionPolarity(text);
    const v = result.verdict;
    const decision = v === 'REVIEW' ? null : (pol === 'deny' ? v === 'DENY' : v === 'ALLOW');
    return {
      type: 'noul', decision, boolean: decision, verdict: v, label: result.label, status: result.label,
      question_polarity: pol, noul: pol === 'allow' ? result.noul : round4(1.0 - result.noul),
      confidence: result.confidence, matched_rule: result.rule_id, reason: result.reason
    };
  }

  return {
    KERNEL_VERSION, evaluate, answerQuestion, questionPolarity, classifyTool, tokenize,
    normalizeText, policySeal, canonicalJson, sha256Hex, policyFields, DEFAULT_TOOL_POLICY
  };
});
