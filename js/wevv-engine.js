/**
 * wevv-engine.js - Machine-Native Zero-Memory System-One Decision Engine
 * Client-Side JavaScript implementation for answerr.me
 * Derived from: "Universal Fractal Natural Language Decision Map" (Dağlı et al., 2026)
 *
 * Computes deterministic, typed decisions (noul, choice, score) in < 2ms
 * with ZERO stored weight tensors (0 Bytes VRAM) from a 24-byte seed on dM.
 */

class WevvEngine {
  constructor(options = {}) {
    // 24-byte coordinate triplet (cx, cy, zoom) along the chaotic boundary of the Mandelbrot set
    this.baseCx = options.cx ?? -0.743643887037158704752191506114774;
    this.baseCy = options.cy ?? 0.131825904205311970493132056385139;
    this.baseZoom = options.zoom ?? 50.0;
    this.resolution = options.resolution ?? 48; // 48x48 grid for ultrafast sub-millisecond execution
    this.maxIter = options.maxIter ?? 40;
    
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
      .replace(/ö/g, 'o')
      .replace(/ç/g, 'c')
      .trim();
  }

  /**
   * Deterministically converts arbitrary key-value state into continuous latent vector [-1, 1]
   * and calculates aggregate semantic risk.
   */
  stateToVector(state = {}) {
    let netRisk = 0.0;
    const values = [];

    const keys = Object.keys(state).sort();
    for (const k of keys) {
      const v = state[k];
      const kl = this.normalizeText(k);

      if (typeof v === 'number') {
        const normVal = 2.0 / (1.0 + Math.exp(-v / 10.0)) - 1.0;
        values.push(normVal);

        if (kl.includes('fail') || kl.includes('error') || kl.includes('attempt') || kl.includes('hata')) {
          netRisk += (v / 5.0) * 1.5;
        } else if (kl.includes('freq') || kl.includes('rate') || kl.includes('speed') || kl.includes('hiz')) {
          netRisk += (v / 50.0) * 1.0;
        } else if (kl.includes('payload') || kl.includes('byte') || kl.includes('kb') || kl.includes('mb') || kl.includes('boyut')) {
          netRisk += (v / 500.0) * 0.5;
        } else if (kl.includes('latency') || kl.includes('gecikme') || kl.includes('ping')) {
          netRisk += (v / 100.0) * 0.6;
        }
      } else if (typeof v === 'boolean') {
        values.push(v ? 1.0 : -1.0);
        if (kl.includes('auth') || kl.includes('valid') || kl.includes('safe') || kl.includes('dogru') || kl.includes('guvenli')) {
          netRisk += v ? -0.8 : 1.2;
        } else if (kl.includes('suspicious') || kl.includes('supheli') || kl.includes('anomali')) {
          netRisk += v ? 1.8 : -0.5;
        }
      } else if (typeof v === 'string') {
        const vl = this.normalizeText(v);
        let matched = false;

        for (const [roleKey, roleRisk] of Object.entries(this.semanticRoles)) {
          if (vl.includes(roleKey)) {
            netRisk += roleRisk;
            values.push(Math.tanh(roleRisk));
            matched = true;
            break;
          }
        }

        if (!matched) {
          // Acoustic phonetic hash projection
          let hash = 0;
          for (let i = 0; i < vl.length; i++) {
            hash = ((hash << 5) - hash) + vl.charCodeAt(i);
            hash |= 0;
          }
          const angle = Math.abs(hash % 10000) / 10000.0 * 2.0 * Math.PI;
          values.push(Math.sin(angle));
          values.push(Math.cos(angle));
        }
      }
    }

    if (values.length === 0) {
      return { vec: [0, 0, 0, 0], netRisk: 0.0 };
    }

    while (values.length < 4) {
      values.push(0.0);
    }

    return { vec: values, netRisk };
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
   *   [key]: { type: 'noul' | 'choice' | 'score', instructions: string, criteria?: any, threshold?: number, weightBias?: number }
   * }
   */
  decide(state = {}, questions = {}) {
    const startTime = performance.now();

    // 1. State-to-Wave Modulation
    const { vec, netRisk } = this.stateToVector(state);
    const roleStr = this.normalizeText(state.user_role || state.role || '');

    // Coordinate Perturbation with Acoustic Damping
    const scale = 1.0 / this.baseZoom;
    const deltaX = Math.tanh(netRisk !== 0.0 ? netRisk : vec[0]) * scale * 0.45 * (1.0 - this.dampingFactor);
    const deltaY = Math.tanh(vec[1] || 0.0) * scale * 0.45 * (1.0 - this.dampingFactor);

    const effCx = this.baseCx + deltaX;
    const effCy = this.baseCy + deltaY;
    const effZoom = this.baseZoom * (1.0 + 0.1 * Math.sin(vec.reduce((a, b) => a + b, 0)));

    // 2. Fractal Forward Pass
    const { blackRatio, avgEscape, escapeIters } = this.computeMandelbrotPatch(
      effCx, effCy, effZoom, this.resolution, this.maxIter
    );

    const { quadRatios, w1, w2, w3, bias } = this.extractQuadrantWeights(
      escapeIters, this.resolution, this.maxIter
    );

    const answers = {};

    // 3. Typed Question Resolution
    for (const [qKey, qObj] of Object.entries(questions)) {
      const qType = (qObj.type || 'noul').toLowerCase();
      const instr = this.normalizeText(qObj.instructions || '');

      if (qType === 'noul') {
        const threshold = qObj.threshold ?? 0.5;
        const isAllowQ = /allow|permit|grant|izin|safe|valid|ok|auth|pass|gecis|onay/i.test(instr);
        const isDenyQ = /threat|danger|attack|block|malicious|hata|tehlike|risk|red|engelle/i.test(instr);

        let prob = 0.5;
        if (isAllowQ || (netRisk !== 0.0 && !isDenyQ)) {
          const baseProb = 1.0 / (1.0 + Math.exp((netRisk - 0.2) * 2.0));
          const fractalBoost = 0.8 + 0.4 * (1.0 - avgEscape);
          prob = baseProb * fractalBoost;
          if (roleStr.includes('guest') || roleStr.includes('attacker') || netRisk >= 1.4) {
            prob = Math.min(prob, 0.35);
          }
        } else if (isDenyQ) {
          prob = 1.0 / (1.0 + Math.exp((-netRisk - 0.2) * 2.0));
        } else {
          const dot = vec[0] * w1 + vec[1] * w2 + (vec[2] || 0) * w3 + bias + (qObj.weightBias || 0);
          prob = 1.0 / (1.0 + Math.exp(-dot));
        }

        prob = Math.max(0.0001, Math.min(0.9999, prob));
        const decision = prob >= threshold;
        const confidence = Math.min(1.0, Math.abs(prob - 0.5) * 2.0);

        answers[qKey] = {
          type: 'noul',
          noul: Math.round(prob * 10000) / 10000,
          decision,
          confidence: Math.round(confidence * 100) / 100
        };

      } else if (qType === 'choice') {
        let options = [];
        let criteriaMap = {};

        if (Array.isArray(qObj.criteria)) {
          options = qObj.criteria;
          options.forEach(o => { criteriaMap[o] = o; });
        } else if (typeof qObj.criteria === 'object' && qObj.criteria !== null) {
          options = Object.keys(qObj.criteria);
          criteriaMap = qObj.criteria;
        } else {
          options = ['approve', 'review', 'reject'];
        }

        const scores = options.map((opt, i) => {
          const optLower = this.normalizeText(opt);
          const qRes = quadRatios[i % 4];
          const stRes = (vec[i % vec.length] || 0) * (qRes - 0.5) * 4.0;
          let score = qRes * 2.5 + stRes + (1.0 - avgEscape) * 0.5;

          if (/direct|prod|fast|primary|ana|dogrudan|normal/i.test(optLower)) {
            score += (netRisk < 0.2 && !roleStr.includes('guest')) ? 3.0 : -2.5;
          } else if (/rate|limiter|slow|kuyruk|limit|orta/i.test(optLower)) {
            score += (netRisk >= 0.5 || (state.req_frequency || 0) > 30) ? 2.5 : 0.0;
          } else if (/sandbox|audit|quarantine|inceleme|manuel/i.test(optLower)) {
            score += (roleStr.includes('guest') || (netRisk >= 0.2 && netRisk < 2.0)) ? 3.5 : 0.5;
          } else if (/drop|deny|block|engelle|kritik|red/i.test(optLower)) {
            score += (roleStr.includes('attacker') || netRisk >= 2.0) ? 4.5 : -2.0;
          }
          return score;
        });

        // Softmax normalization
        const maxScore = Math.max(...scores);
        const expScores = scores.map(s => Math.exp(s - maxScore));
        const sumExp = expScores.reduce((a, b) => a + b, 0) || 1.0;
        const probs = expScores.map(e => e / sumExp);

        const probDict = {};
        let bestOpt = options[0];
        let maxProb = -1;

        options.forEach((opt, idx) => {
          const p = Math.round(probs[idx] * 10000) / 10000;
          probDict[opt] = p;
          if (p > maxProb) {
            maxProb = p;
            bestOpt = opt;
          }
        });

        const conf = Math.max(0, Math.min(1, maxProb - (1 - maxProb) / Math.max(1, options.length - 1)));

        answers[qKey] = {
          type: 'choice',
          choice: bestOpt,
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

        // Gaussian distribution over score steps
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

    return {
      model: 'wevv-0.1.0-fractal',
      answers,
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
        quadRatios: quadRatios.map(r => Math.round(r * 10000) / 10000)
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

// Export for browser and ES modules
if (typeof window !== 'undefined') {
  window.WevvEngine = WevvEngine;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { WevvEngine };
}
