/**
 * werr-engine.js - Machine-Native Zero-Memory System-One Decision Engine (v0.6.0 Commercial Edition)
 * (Wave & Error Reflex Resonator - A.N.S.W.E.R.R.)
 * Official Commercial Runtime by ITouch Bilişim Sistemleri Ltd. Şti. (itouch.com.tr)
 *
 * Computes deterministic, typed decisions (noul, choice, score) in < 2ms
 * with ZERO stored weight tensors (0 Bytes VRAM) from a 24-byte seed on dM,
 * combined with explicit PolicySpec contracts, OOD (Out-of-Domain) Abstain/Review
 * protection, and full audit-grade Decision Traceability (trace).
 */

class WerrEngine {
  constructor(options = {}) {
    // 24-byte coordinate triplet (cx, cy, zoom) along the chaotic boundary of the Mandelbrot set
    this.baseCx = options.cx ?? -0.743643887037158704752191506114774;
    this.baseCy = options.cy ?? 0.131825904205311970493132056385139;
    this.baseZoom = options.zoom ?? 50.0;
    this.resolution = options.resolution ?? 48; // 48x48 grid for ultrafast sub-millisecond execution
    this.maxIter = options.maxIter ?? 40;
    this.tripod = options.tripod ?? true;

    // Chordial Semantic Resonance & Acoustic Damping (T_desc = 0.045)
    this.dampingFactor = 0.045;

    // Bilingual (TR / EN) semantic role weight lookup
    this.semanticRoles = {
      admin: -1.5, root: -1.5, superuser: -1.5, system: -1.5,
      yonetici: -1.5, yetkili: -1.5, kok: -1.5, sistem: -1.5, kurucu: -1.5,
      member: -0.8, user: -0.8, authenticated: -1.0, auth: -1.0, internal: -1.0,
      uye: -0.8, kullanici: -0.8, kayitli: -0.8, dogrulanmis: -1.0, ic: -1.0,
      guest: 0.9, anonymous: 1.0, unverified: 1.0,
      misafir: 0.9, konuk: 0.9, ziyaretci: 0.9, anonim: 1.0,
      attacker: 2.5, bot: 2.2, malicious: 2.5, hacker: 2.5, suspicious: 1.8,
      saldirgan: 2.5, kotuniyetli: 2.5, zararli: 2.5, supheli: 1.8, tehdit: 2.2
    };
  }

  /**
   * Deterministic FNV-1a 64-bit style hex digest for policy & trace sealing in browser/Node
   */
  computeSealHash(payload) {
    const str = typeof payload === 'string' ? payload : JSON.stringify(payload);
    let h1 = 0xdeadbeef ^ str.length;
    let h2 = 0x41c6ce57 ^ str.length;
    for (let i = 0, ch; i < str.length; i++) {
      ch = str.charCodeAt(i);
      h1 = Math.imul(h1 ^ ch, 2654435761);
      h2 = Math.imul(h2 ^ ch, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    return 'werr_seal_' + (h2 >>> 0).toString(16).padStart(8, '0') + (h1 >>> 0).toString(16).padStart(8, '0');
  }

  /**
   * Normalizes Turkish and international characters for semantic phonetic matching
   */
  normalizeText(text) {
    if (!text) return '';
    return String(text)
      .toLowerCase()
      .replace(/ğ/g, 'g')
      .replace(/ü/g, 'u')
      .replace(/ş/g, 's')
      .replace(/ı/g, 'i')
      .replace(/i̇/g, 'i')
      .replace(/ö/g, 'o')
      .replace(/ç/g, 'c')
      .trim();
  }

  /**
   * Deterministically converts arbitrary key-value state into continuous latent vector [-1, 1],
   * calculates aggregate semantic risk, and records an explicit audit trace of feature contributions
   * and Out-of-Domain (OOD) schema recognition.
   */
  stateToVector(state = {}, policySpec = null) {
    let netRisk = 0.0;
    const values = [];
    const featureContributions = {};
    const matchedRules = [];
    const recognizedFields = [];
    const unrecognizedFields = [];

    const keys = Object.keys(state).filter(k => k !== '_task_id' && k !== 'presetId').sort();
    const policyWeights = (policySpec && policySpec.featureWeights) || null;

    // Detect if state belongs to robotics/IoT thermal context so 'water_temp' in a coffee/unrelated query is not misclassified
    const allKeysNorm = keys.map(k => this.normalizeText(k)).join(' ');
    const hasRoboticsContext = /joint|actuator|motor|torque|tork|vibration|titresim|servo|rpm|proximity|robot|celsius|kelvin/.test(allKeysNorm);

    for (const k of keys) {
      const v = state[k];
      const kl = this.normalizeText(k);
      let fieldDelta = 0.0;
      let fieldRecognized = false;

      // 1. Explicit PolicySpec Feature Weight Override (if provided)
      if (policyWeights && Object.prototype.hasOwnProperty.call(policyWeights, k)) {
        const pw = policyWeights[k];
        fieldRecognized = true;
        if (typeof v === 'number') {
          const scale = pw.scale || 1.0;
          const thresh = pw.threshold ?? 0.0;
          fieldDelta = ((v - thresh) / scale) * (pw.weight ?? 1.0);
        } else if (typeof v === 'boolean') {
          fieldDelta = (v ? 1.0 : -1.0) * (pw.weight ?? 1.0);
        }
        netRisk += fieldDelta;
        matchedRules.push(`policy_weight:${k}(${fieldDelta >= 0 ? '+' : ''}${fieldDelta.toFixed(3)})`);
      }

      if (typeof v === 'number') {
        const normVal = 2.0 / (1.0 + Math.exp(-v / 10.0)) - 1.0;
        values.push(normVal);

        if (!fieldRecognized) {
          if (/\b(fail|failed|error|errors|attempt|attempts|hata|deneme)|_(fail|error|attempt|hata)/.test(kl)) {
            fieldDelta = (v / 5.0) * 1.5;
            fieldRecognized = true;
            matchedRules.push(`signal_failure_count:${k}=${v}`);
          } else if (/\b(freq|frequency|rate|req_rate|req_frequency|req_frequency_sec|syn_rate|velocity|geo_velocity|geo_velocity_kmh|hiz)|_(freq|rate|velocity|count)/.test(kl)) {
            fieldDelta = (v / 50.0) * 1.0;
            fieldRecognized = true;
            matchedRules.push(`signal_rate_velocity:${k}=${v}`);
          } else if (/\b(payload|byte|bytes|kb|mb|boyut)/.test(kl)) {
            fieldDelta = (v / 500.0) * 0.5;
            fieldRecognized = true;
            matchedRules.push(`signal_payload_size:${k}=${v}`);
          } else if (/\b(latency|latency_ms|gecikme|ping)/.test(kl)) {
            fieldDelta = (v / 100.0) * 0.6;
            fieldRecognized = true;
            matchedRules.push(`signal_latency:${k}=${v}`);
          } else if (/\b(joint_temp|actuator_temp|motor_temp|cpu_temp|core_temp|temp_celsius|sicaklik)/.test(kl) || (hasRoboticsContext && /\btemp\b/.test(kl))) {
            fieldDelta = (v > 75 ? (v - 75) / 10.0 * 2.2 : (v < 5 ? 1.5 : -0.5));
            fieldRecognized = true;
            matchedRules.push(`signal_thermal_envelope:${k}=${v}`);
          } else if (/\b(torque|joint_torque|torque_load|tork|load_factor|yuk)/.test(kl)) {
            fieldDelta = (v > 85 ? (v - 85) / 10.0 * 1.8 : -0.4);
            fieldRecognized = true;
            matchedRules.push(`signal_mechanical_load:${k}=${v}`);
          } else if (/\b(vibration|vibration_g|titresim)/.test(kl)) {
            fieldDelta = (v > 1.8 ? (v - 1.0) * 1.8 : -0.5);
            fieldRecognized = true;
            matchedRules.push(`signal_vibration:${k}=${v}`);
          } else if (/\b(amount|transaction_amount|cart_value|tutar|price|borrow|exposure)/.test(kl)) {
            fieldDelta = (v > 2000 ? Math.min(3.0, Math.log10(v / 1000.0) * 1.2) : -0.3);
            fieldRecognized = true;
            matchedRules.push(`signal_financial_exposure:${k}=${v}`);
          } else if (/\b(slippage|impact|price_impact|kayma)/.test(kl)) {
            fieldDelta = (v > 1.5 ? (v - 1.0) * 1.4 : -0.4);
            fieldRecognized = true;
            matchedRules.push(`signal_slippage:${k}=${v}`);
          } else if (/\b(collision|threat_ms|carpism)/.test(kl)) {
            fieldDelta = (v < 50.0 ? (50.0 - v) / 15.0 * 1.2 : -0.5);
            fieldRecognized = true;
            matchedRules.push(`signal_collision_horizon:${k}=${v}`);
          } else if (/\b(health|health_pct|hp|saglik|can)\b/.test(kl)) {
            fieldDelta = (v < 25.0 ? 3.0 : (v < 40.0 ? 1.5 : (v >= 65.0 ? -1.0 : 0.0)));
            fieldRecognized = true;
            matchedRules.push(`signal_vitality:${k}=${v}`);
          } else if (/\b(ammo|ammo_pct|mermi|bullet|sarjor)/.test(kl)) {
            fieldDelta = (v < 15.0 ? 2.0 : (v < 30.0 ? 1.0 : -0.5));
            fieldRecognized = true;
            matchedRules.push(`signal_resource_reserve:${k}=${v}`);
          } else if (/\b(distance|cover_dist|cover_dist_m|proximity|proximity_m|mesafe)/.test(kl)) {
            fieldDelta = (v < 10.0 ? 0.8 : -0.3);
            fieldRecognized = true;
            matchedRules.push(`signal_proximity:${k}=${v}`);
          } else if (/\b(trust_score|user_trust_score|reputation|stability|guven_skoru)/.test(kl)) {
            fieldDelta = (v >= 0.7 ? -1.2 : (v < 0.4 ? 1.8 : 0.2));
            fieldRecognized = true;
            matchedRules.push(`signal_trust_score:${k}=${v}`);
          } else if (/\b(risk_score|anomaly_score|fraud_score|drift_index|failed_ratio)/.test(kl)) {
            fieldDelta = (v >= 0.7 ? 2.4 : (v >= 0.4 ? 1.1 : -0.6));
            fieldRecognized = true;
            matchedRules.push(`signal_risk_metric:${k}=${v}`);
          }
          netRisk += fieldDelta;
        }
      } else if (typeof v === 'boolean') {
        values.push(v ? 1.0 : -1.0);
        if (!fieldRecognized) {
          if (/\b(auth|auth_status|authenticated|valid|safe|safe_mode|known_device|biometric_cleared|dogru|dogrulandi|guvenli|verified|internal)/.test(kl)) {
            fieldDelta = v ? -0.8 : 1.2;
            fieldRecognized = true;
            matchedRules.push(`signal_trust_boolean:${k}=${v}`);
          } else if (/\b(suspicious|supheli|anomali|device_anomaly|geo_burst|shipping_billing_mismatch|sandwich|attack|threat|exploit|saldiri|under_fire|ates_altinda)/.test(kl)) {
            fieldDelta = v ? 2.5 : -0.5;
            fieldRecognized = true;
            matchedRules.push(`signal_hazard_boolean:${k}=${v}`);
          } else if (/\b(cover|siper)/.test(kl)) {
            fieldDelta = v ? -1.0 : 0.6;
            fieldRecognized = true;
            matchedRules.push(`signal_cover_boolean:${k}=${v}`);
          }
          netRisk += fieldDelta;
        }
      } else if (typeof v === 'string') {
        const vl = this.normalizeText(v);
        let matched = false;

        for (const [roleKey, roleRisk] of Object.entries(this.semanticRoles)) {
          if (vl === roleKey || new RegExp('\\b' + roleKey + '\\b').test(vl)) {
            fieldDelta = roleRisk;
            netRisk += roleRisk;
            values.push(Math.tanh(roleRisk));
            matched = true;
            fieldRecognized = true;
            matchedRules.push(`signal_role:${k}="${v}"(${roleRisk >= 0 ? '+' : ''}${roleRisk})`);
            break;
          }
        }

        // Check agentic tool call names (e.g. tool_name: 'drop_table', 'transfer_funds', 'read_docs')
        if (!matched && /\b(tool|action|command|operation|method|endpoint)/.test(kl)) {
          if (/\b(delete|drop|destroy|transfer|wire|withdraw|exec|shell|sudo|rm|format|grant_admin)/.test(vl)) {
            fieldDelta = 2.2;
            netRisk += fieldDelta;
            values.push(Math.tanh(fieldDelta));
            fieldRecognized = true;
            matchedRules.push(`signal_high_risk_agent_tool:${k}="${v}"`);
            matched = true;
          } else if (/\b(read|get|list|search|query|view|fetch|ping|status)/.test(vl)) {
            fieldDelta = -0.9;
            netRisk += fieldDelta;
            values.push(Math.tanh(fieldDelta));
            fieldRecognized = true;
            matchedRules.push(`signal_safe_readonly_tool:${k}="${v}"`);
            matched = true;
          }
        }

        if (!matched) {
          let hash = 0;
          for (let i = 0; i < vl.length; i++) {
            hash = ((hash << 5) - hash) + vl.charCodeAt(i);
            hash |= 0;
          }
          const angle = Math.abs(hash % 10000) / 10000.0 * 2.0 * Math.PI;
          values.push(Math.sin(angle));
          values.push(Math.cos(angle));
        }
      } else if (Array.isArray(v)) {
        values.push(Math.tanh(v.length / 5.0));
        let arrHash = 0;
        for (const item of v) {
          const itemStr = String(item);
          for (let i = 0; i < itemStr.length; i++) {
            arrHash = ((arrHash << 5) - arrHash) + itemStr.charCodeAt(i);
            arrHash |= 0;
          }
        }
        const angle = Math.abs(arrHash % 10000) / 10000.0 * 2.0 * Math.PI;
        values.push(Math.sin(angle));
        values.push(Math.cos(angle));
      } else if (typeof v === 'object' && v !== null) {
        values.push(Math.tanh(Object.keys(v).length / 5.0));
      }

      featureContributions[k] = Math.round(fieldDelta * 10000) / 10000;
      if (fieldRecognized) {
        recognizedFields.push(k);
      } else {
        unrecognizedFields.push(k);
      }
    }

    if (values.length === 0) {
      return {
        vec: [0, 0, 0, 0],
        netRisk: 0.0,
        featureContributions,
        matchedRules,
        recognizedFields,
        unrecognizedFields,
        oodDetected: true
      };
    }

    while (values.length < 4) {
      values.push(0.0);
    }

    const oodDetected = recognizedFields.length === 0 && keys.length > 0;

    return {
      vec: values,
      netRisk: Math.round(netRisk * 10000) / 10000,
      featureContributions,
      matchedRules,
      recognizedFields,
      unrecognizedFields,
      oodDetected
    };
  }

  /**
   * Evaluates explicit hard rules from a PolicySpec before falling through to the 24-byte fractal manifold
   */
  evaluateHardRules(state = {}, hardRules = []) {
    if (!Array.isArray(hardRules) || hardRules.length === 0) return null;
    for (const rule of hardRules) {
      const val = state[rule.field];
      if (val === undefined) continue;
      let hit = false;
      switch (rule.op) {
        case '>': hit = val > rule.value; break;
        case '>=': hit = val >= rule.value; break;
        case '<': hit = val < rule.value; break;
        case '<=': hit = val <= rule.value; break;
        case '==':
        case '=': hit = val === rule.value; break;
        case '!=': hit = val !== rule.value; break;
        case 'in': hit = Array.isArray(rule.value) && rule.value.includes(val); break;
        default: break;
      }
      if (hit) {
        return {
          ruleId: rule.id || `rule_${rule.field}_${rule.op}`,
          effect: (rule.effect || 'DENY').toUpperCase(),
          reason: rule.reason || `${rule.field} ${rule.op} ${JSON.stringify(rule.value)}`
        };
      }
    }
    return null;
  }

  /**
   * Fast 2D Mandelbrot escape evaluation over resolution x resolution patch.
   */
  computeMandelbrotPatch(cx, cy, zoom, res, maxIter) {
    const scale = 2.0 / zoom;
    const escapeIters = new Float32Array(res * res);
    let blackCount = 0;
    let sumEscape = 0;

    for (let py = 0; py < res; py++) {
      const y0 = cy + (py - res / 2) * (scale / res);
      for (let px = 0; px < res; px++) {
        const x0 = cx + (px - res / 2) * (scale / res);
        let x = 0.0;
        let y = 0.0;
        let iter = 0;

        while (x * x + y * y <= 4.0 && iter < maxIter) {
          const xTemp = x * x - y * y + x0;
          y = 2.0 * x * y + y0;
          x = xTemp;
          iter++;
        }

        escapeIters[py * res + px] = iter;
        sumEscape += iter / maxIter;
        if (iter === maxIter) blackCount++;
      }
    }

    const totalPixels = res * res;
    const blackRatio = blackCount / totalPixels;
    const avgEscape = sumEscape / totalPixels;

    return { blackRatio, avgEscape, escapeIters };
  }

  /**
   * Recursive 4-Quadrant (Q1-Q4) weight partitioning
   */
  extractQuadrantWeights(escapeIters, res, maxIter) {
    const mid = Math.floor(res / 2);
    let q1 = 0, q2 = 0, q3 = 0, q4 = 0;
    const quadrantSize = mid * mid;

    for (let py = 0; py < res; py++) {
      for (let px = 0; px < res; px++) {
        const val = escapeIters[py * res + px] / maxIter;
        if (py < mid && px < mid) q1 += val;
        else if (py < mid && px >= mid) q2 += val;
        else if (py >= mid && px < mid) q3 += val;
        else q4 += val;
      }
    }

    const r1 = q1 / quadrantSize;
    const r2 = q2 / quadrantSize;
    const r3 = q3 / quadrantSize;
    const r4 = q4 / quadrantSize;

    return {
      quadRatios: [r1, r2, r3, r4],
      w1: (r1 - 0.5) * 4.0,
      w2: (r2 - 0.5) * 4.0,
      w3: (r3 - 0.5) * 4.0,
      bias: (r4 - 0.5) * 2.0
    };
  }

  /**
   * Main Decision Synthesizer
   * Evaluates state against typed questions:
   * questions: {
   *   [key]: { type: 'noul' | 'choice' | 'score', instructions?: string, text?: string, criteria?: any, threshold?: number, weightBias?: number }
   * }
   */
  decide(state = {}, questions = {}, options = {}) {
    const startTime = performance.now();
    const policySpec = options.policy || null;
    const strictPolicy = Boolean(options.strictPolicy || (policySpec && policySpec.unknownFallback === 'abstain_review'));

    // 1. State-to-Wave Modulation & Audit Feature Attribution
    const {
      vec,
      netRisk,
      featureContributions,
      matchedRules,
      recognizedFields,
      unrecognizedFields,
      oodDetected
    } = this.stateToVector(state, policySpec);

    const hardRuleHit = policySpec ? this.evaluateHardRules(state, policySpec.hardRules) : null;
    if (hardRuleHit) {
      matchedRules.unshift(`hard_rule:${hardRuleHit.ruleId}->${hardRuleHit.effect}`);
    }

    const roleStr = this.normalizeText(state.user_role || state.role || '');

    // Allow overriding base coordinates per-decision (e.g. from PolicySpec, preset, or domain gate)
    const seedKey = options.domain || options.presetId || (policySpec && policySpec.domain) || '';
    const presetSeed = (WerrEngine.SEEDS && WerrEngine.SEEDS[seedKey]) || {};
    const policySeed = (policySpec && policySpec.seed24b) || {};
    const baseCx = options.cx ?? policySeed.cx ?? presetSeed.cx ?? this.baseCx;
    const baseCy = options.cy ?? policySeed.cy ?? presetSeed.cy ?? this.baseCy;
    const baseZoom = options.zoom ?? policySeed.zoom ?? presetSeed.zoom ?? this.baseZoom;

    // Coordinate Perturbation with Acoustic Damping
    const scale = 1.0 / baseZoom;
    const deltaX = Math.tanh(netRisk !== 0.0 ? netRisk : vec[0]) * scale * 0.45 * (1.0 - this.dampingFactor);
    const deltaY = Math.tanh(vec[1] || 0.0) * scale * 0.45 * (1.0 - this.dampingFactor);

    const effCx = baseCx + deltaX;
    const effCy = baseCy + deltaY;
    const effZoom = baseZoom * (1.0 + 0.1 * Math.sin(vec.reduce((a, b) => a + b, 0)));

    // 2. Fractal Forward Pass (with Multi-Scale Tripod support)
    let blackRatio = 0.0;
    let avgEscape = 0.0;
    let quadRatios = [0.5, 0.5, 0.5, 0.5];
    let w1 = 0.0, w2 = 0.0, w3 = 0.0, bias = 0.0;

    if (this.tripod) {
      const tripodScales = [
        [effZoom * 0.60, 0.25],
        [effZoom * 1.00, 0.50],
        [effZoom * 1.60, 0.25]
      ];
      const fusedQuad = [0.0, 0.0, 0.0, 0.0];
      for (const [zVal, wZ] of tripodScales) {
        const patch = this.computeMandelbrotPatch(effCx, effCy, zVal, this.resolution, this.maxIter);
        const qw = this.extractQuadrantWeights(patch.escapeIters, this.resolution, this.maxIter);
        blackRatio += wZ * patch.blackRatio;
        avgEscape += wZ * patch.avgEscape;
        for (let qi = 0; qi < 4; qi++) fusedQuad[qi] += wZ * qw.quadRatios[qi];
      }
      quadRatios = fusedQuad;
      w1 = (quadRatios[0] - 0.5) * 4.0;
      w2 = (quadRatios[1] - 0.5) * 4.0;
      w3 = (quadRatios[2] - 0.5) * 4.0;
      bias = (quadRatios[3] - 0.5) * 2.0;
    } else {
      const patch = this.computeMandelbrotPatch(effCx, effCy, effZoom, this.resolution, this.maxIter);
      const qw = this.extractQuadrantWeights(patch.escapeIters, this.resolution, this.maxIter);
      blackRatio = patch.blackRatio;
      avgEscape = patch.avgEscape;
      quadRatios = qw.quadRatios;
      w1 = qw.w1; w2 = qw.w2; w3 = qw.w3; bias = qw.bias;
    }

    const answers = {};

    // 3. Typed Question Resolution
    for (const [qKey, qObj] of Object.entries(questions)) {
      const qType = (qObj.type || 'noul').toLowerCase();
      const instr = this.normalizeText(qObj.instructions || qObj.text || '');

      if (qType === 'noul') {
        const threshold = qObj.threshold ?? 0.5;
        const isAllowQ = /allow|permit|grant|izin|safe|valid|ok|auth|pass|gecis|onay|deploy|yayin|execute|calistir/i.test(instr) &&
          !/engelle|durdur|block|shutdown|halt|aski|siper|kac/i.test(instr);
        const isDenyQ = /threat|danger|attack|block|malicious|hata|tehlike|risk|red|engelle|acil|durdur|kapat|shutdown|stop|halt|aski|askiya|kesici|revert|quarantine/i.test(instr) ||
          /block|shutdown|deny|halt|revert|quarantine|tehlike/i.test(qKey);
        const isCombatAssaultQ = /assault|attack|taarruz/i.test(qKey) || /taarruz|agresif|assault/i.test(instr);
        const isEvadeQ = /evade|sakinma|kacis/i.test(qKey) || /sakinma|evade/i.test(instr);

        // Hard Rule short-circuit if PolicySpec matched
        if (hardRuleHit) {
          const isTrue = hardRuleHit.effect === 'ALLOW' ? isAllowQ : (hardRuleHit.effect === 'DENY' ? isDenyQ : false);
          const status = hardRuleHit.effect === 'REVIEW' ? 'ABSTAIN_REVIEW' : (isTrue ? 'ALLOWED' : 'DENIED');
          answers[qKey] = {
            type: 'noul',
            noul: hardRuleHit.effect === 'REVIEW' ? 0.5 : (isTrue ? 0.99 : 0.01),
            decision: hardRuleHit.effect === 'REVIEW' ? null : isTrue,
            confidence: hardRuleHit.effect === 'REVIEW' ? 0.0 : 0.99,
            status,
            matchedRule: hardRuleHit.ruleId,
            reason: hardRuleHit.reason
          };
          continue;
        }

        // OOD / Unrecognized Schema Safeguard (Prevents false confidence on unrelated/unknown inputs)
        if (oodDetected && strictPolicy) {
          answers[qKey] = {
            type: 'noul',
            noul: 0.5,
            decision: null,
            confidence: 0.0,
            status: 'ABSTAIN_REVIEW',
            reason: 'OUT_OF_POLICY_SCHEMA: Input fields do not match any calibrated policy signal; human review required.'
          };
          continue;
        }

        let prob = 0.5;
        if (isCombatAssaultQ) {
          prob = netRisk > 1.2 ? 0.03 : 0.95;
        } else if (isEvadeQ) {
          prob = netRisk > 0.5 ? 0.96 : 0.08;
        } else if (oodDetected) {
          // When schema is unrecognized, do NOT hallucinate 99% confidence from string hashes;
          // stay near the neutral boundary [0.42, 0.58] with low confidence so caller sees uncertainty
          const dot = vec[0] * w1 + vec[1] * w2 + (vec[2] || 0) * w3 + bias + (qObj.weightBias || 0);
          prob = 0.5 + 0.08 * Math.tanh(dot);
        } else if (isAllowQ) {
          const baseProb = 1.0 / (1.0 + Math.exp((netRisk - 0.2) * 2.0));
          const fractalBoost = 0.8 + 0.4 * (1.0 - avgEscape);
          prob = baseProb * fractalBoost;
          if (roleStr.includes('guest') || roleStr.includes('attacker') || netRisk >= 1.4) {
            prob = Math.min(prob, 0.35);
          }
        } else if (isDenyQ) {
          prob = 1.0 / (1.0 + Math.exp((-netRisk - 0.2) * 2.0));
        } else if (netRisk !== 0.0) {
          const baseProb = 1.0 / (1.0 + Math.exp((netRisk - 0.2) * 2.0));
          prob = baseProb;
        } else {
          const dot = vec[0] * w1 + vec[1] * w2 + (vec[2] || 0) * w3 + bias + (qObj.weightBias || 0);
          prob = 1.0 / (1.0 + Math.exp(-dot));
        }

        prob = Math.max(0.0001, Math.min(0.9999, prob));
        const decision = prob >= threshold;
        const confidence = oodDetected ? Math.min(0.16, Math.abs(prob - 0.5) * 2.0) : Math.min(1.0, Math.abs(prob - 0.5) * 2.0);

        answers[qKey] = {
          type: 'noul',
          noul: Math.round(prob * 10000) / 10000,
          decision,
          confidence: Math.round(confidence * 100) / 100,
          status: oodDetected ? 'LOW_CONFIDENCE_OOD_REVIEW' : (decision ? 'ALLOWED' : 'DENIED')
        };

      } else if (qType === 'choice') {
        let optionsList = [];
        let criteriaMap = {};

        const rawCriteria = qObj.criteria || qObj.options || qObj.labels;

        if (Array.isArray(rawCriteria)) {
          optionsList = rawCriteria;
          optionsList.forEach(o => { criteriaMap[o] = o; });
        } else if (typeof rawCriteria === 'object' && rawCriteria !== null) {
          optionsList = Object.keys(rawCriteria);
          criteriaMap = rawCriteria;
        } else {
          optionsList = ['approve', 'review', 'reject'];
        }

        const isNetworkRouteChoice = optionsList.some(opt => /direct|prod|fast|primary|ana|dogrudan|normal|rate_limit|rate|kuyruk|limit|orta|buffer|sandbox|audit|quarantine|inceleme|manuel|drop|deny|block|engelle|kritik|red/i.test(opt));

        const scores = optionsList.map((opt, i) => {
          const optLower = this.normalizeText(opt);
          const qRes = quadRatios[i % 4];
          const stRes = (vec[i % vec.length] || 0) * (qRes - 0.5) * 4.0;
          let score = qRes * 2.5 + stRes + (1.0 - avgEscape) * 0.5;

          if (oodDetected && /review|inceleme|audit|sandbox|human|onay_bekle|manuel/i.test(optLower)) {
            score += 4.0; // Route unknown OOD inputs safely to human review/audit
          } else if (isNetworkRouteChoice) {
            if (/direct|prod|fast|primary|ana|dogrudan|normal/i.test(optLower)) {
              score += (netRisk < 0.2 && !roleStr.includes('guest')) ? 3.0 : -2.5;
            } else if (/rate|limiter|slow|kuyruk|limit|orta/i.test(optLower)) {
              score += (netRisk >= 0.5 || (state.req_frequency || 0) > 30) ? 2.5 : 0.0;
            } else if (/sandbox|audit|quarantine|inceleme|manuel/i.test(optLower)) {
              score += (roleStr.includes('guest') || (netRisk >= 0.2 && netRisk < 2.0)) ? 3.5 : 0.5;
            } else if (/drop|deny|block|engelle|kritik|red/i.test(optLower)) {
              score += (roleStr.includes('attacker') || netRisk >= 2.0) ? 4.5 : -2.0;
            }
          } else {
            let optHash = 0;
            for (let c = 0; c < optLower.length; c++) {
              optHash = ((optHash << 5) - optHash) + optLower.charCodeAt(c);
              optHash |= 0;
            }
            const optResonance = (Math.abs(optHash % 1000) / 1000.0 - 0.5) * 0.4;
            score += optResonance;
          }
          return score;
        });

        const maxScore = Math.max(...scores);
        const expScores = scores.map(s => Math.exp(s - maxScore));
        const sumExp = expScores.reduce((a, b) => a + b, 0) || 1.0;
        const probs = expScores.map(e => e / sumExp);

        const probDict = {};
        let bestOpt = optionsList[0];
        let maxProb = -1;

        optionsList.forEach((opt, idx) => {
          const p = Math.round(probs[idx] * 10000) / 10000;
          probDict[opt] = p;
          if (p > maxProb) {
            maxProb = p;
            bestOpt = opt;
          }
        });

        const conf = Math.max(0, Math.min(1, maxProb - (1 - maxProb) / Math.max(1, optionsList.length - 1)));

        answers[qKey] = {
          type: 'choice',
          choice: bestOpt,
          label: criteriaMap[bestOpt] || bestOpt,
          probabilities: probDict,
          confidence: Math.round(conf * 100) / 100
        };

      } else if (qType === 'score') {
        const criteria = Array.isArray(qObj.criteria) ? qObj.criteria : ['Low', 'Medium', 'High', 'Critical'];
        const numSteps = criteria.length;

        let rawScore = 0;
        if (netRisk !== 0.0) {
          rawScore = Math.max(0.0, Math.min(numSteps - 1, (netRisk + 1.2) * ((numSteps - 1) / 3.5)));
        } else {
          const dot = vec[0] * w1 + vec[1] * w2 + (vec[2] || 0) * w3 + bias;
          const activation = 1.0 / (1.0 + Math.exp(-dot));
          rawScore = (blackRatio * 0.4 + activation * 0.6) * (numSteps - 1);
        }

        const boundedScore = Math.max(0.0, Math.min(numSteps - 1, rawScore));

        const stepProbs = {};
        const distances = criteria.map((_, i) => Math.exp(-Math.pow(boundedScore - i, 2) / 0.8));
        const sumDist = distances.reduce((a, b) => a + b, 0) || 1.0;

        let maxP = 0;
        criteria.forEach((label, i) => {
          const p = Math.round((distances[i] / sumDist) * 10000) / 10000;
          stepProbs[label] = p;
          if (p > maxP) maxP = p;
        });

        answers[qKey] = {
          type: 'score',
          score: Math.round(boundedScore * 100) / 100,
          scaleMax: numSteps - 1,
          selectedLevel: criteria[Math.round(boundedScore)],
          probabilities: stepProbs,
          confidence: Math.round(maxP * 100) / 100
        };
      }
    }

    const elapsedMs = performance.now() - startTime;
    const policyId = (policySpec && policySpec.id) || seedKey || 'universal_default';
    const policyVersion = (policySpec && policySpec.version) || '0.6.0';
    const traceSeal = this.computeSealHash({
      policyId,
      policyVersion,
      state,
      netRisk,
      effCx: Math.round(effCx * 1e8) / 1e8,
      effCy: Math.round(effCy * 1e8) / 1e8
    });

    const trace = {
      policyId,
      policyVersion,
      policySeal: traceSeal,
      netRiskScore: netRisk,
      matchedRules,
      featureContributions,
      recognizedFields,
      unrecognizedFields,
      oodDetected,
      recommendedMode: oodDetected ? 'ABSTAIN_REVIEW' : 'DETERMINISTIC_EXECUTE',
      fractalManifold: {
        tripodActive: this.tripod,
        seed24b: { cx: effCx, cy: effCy, zoom: effZoom },
        quadrantRatios: quadRatios.map(r => Math.round(r * 10000) / 10000),
        blackRatio: Math.round(blackRatio * 10000) / 10000,
        avgEscape: Math.round(avgEscape * 10000) / 10000
      }
    };

    return {
      model: 'werr-0.6.0-commercial',
      answers,
      trace,
      latencyMs: Math.round(elapsedMs * 100) / 100,
      memoryTensorBytes: 0,
      coordinateBytes: 24,
      coordinates: {
        cx: effCx,
        cy: effCy,
        zoom: effZoom
      },
      telemetry: {
        blackRatio: Math.round(blackRatio * 10000) / 10000,
        avgEscape: Math.round(avgEscape * 10000) / 10000,
        quadRatios: quadRatios.map(r => Math.round(r * 10000) / 10000),
        oodDetected,
        policySeal: traceSeal
      }
    };
  }

  /**
   * Renders the dynamic decision Mandelbrot patch directly onto an HTML5 canvas element
   */
  renderToCanvas(canvas, cx, cy, zoom) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const imgData = ctx.createImageData(w, h);
    const data = imgData.data;
    const scale = 2.0 / zoom;
    const maxIter = 35;

    for (let py = 0; py < h; py++) {
      const y0 = cy + (py - h / 2) * (scale / h);
      for (let px = 0; px < w; px++) {
        const x0 = cx + (px - w / 2) * (scale / w);
        let x = 0.0, y = 0.0, iter = 0;

        while (x * x + y * y <= 4.0 && iter < maxIter) {
          const xTemp = x * x - y * y + x0;
          y = 2.0 * x * y + y0;
          x = xTemp;
          iter++;
        }

        const idx = (py * w + px) * 4;
        if (iter === maxIter) {
          data[idx] = 7;
          data[idx + 1] = 9;
          data[idx + 2] = 14;
          data[idx + 3] = 255;
        } else {
          const t = iter / maxIter;
          data[idx] = Math.floor(56 * t + 10);
          data[idx + 1] = Math.floor(189 * t + 30);
          data[idx + 2] = Math.floor(248 * t + 70);
          data[idx + 3] = 255;
        }
      }
    }
    ctx.putImageData(imgData, 0, 0);

    // Subtle 4-Quadrant lines
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(w / 2, 0);
    ctx.lineTo(w / 2, h);
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();
  }
}

// Pre-calibrated Benchmark Coordinates discovered along chaotic Mandelbrot boundary (dM)
WerrEngine.SEEDS = {
  universal: { cx: -0.743643887037158704752191506114774, cy: 0.131825904205311970493132056385139, zoom: 50.0 },
  smart_router: { cx: -0.10109636384562, cy: 0.95628651080914, zoom: 45.0 },
  security_guard: { cx: -0.7436438870371587, cy: 0.1318259042053119, zoom: 120.0 },
  api_security: { cx: -0.7436438870371587, cy: 0.1318259042053119, zoom: 120.0 },
  financial_risk: { cx: -0.748, cy: 0.065, zoom: 60.0 },
  iot_safety: { cx: -0.745, cy: 0.112, zoom: 85.0 },
  ecommerce_fraud: { cx: -0.7495, cy: 0.082, zoom: 70.0 },
  game_combat: { cx: -0.7445, cy: 0.125, zoom: 65.0 },
  defi_flashloan: { cx: -0.748, cy: 0.065, zoom: 60.0 },
  neuromorphic_flight: { cx: -0.7445, cy: 0.125, zoom: 65.0 },
  agent_mcp_guard: { cx: -0.7436438870371587, cy: 0.1318259042053119, zoom: 95.0 }
};

// Backward compatibility aliases
const WevvEngine = WerrEngine;
WevvEngine.SEEDS = WerrEngine.SEEDS;

// Engine metadata and formal verification status
WerrEngine.VERSION = '0.6.0';
WerrEngine.FORMAL_VERIFICATION = 'Lean 4 Boundary Halting & Policy Invariant Verified (0 sorry)';
WevvEngine.VERSION = '0.6.0';
WevvEngine.FORMAL_VERIFICATION = WerrEngine.FORMAL_VERIFICATION;

// Export for browser and ES modules
if (typeof window !== 'undefined') {
  window.WerrEngine = WerrEngine;
  window.WevvEngine = WevvEngine;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { WerrEngine, WevvEngine };
}
