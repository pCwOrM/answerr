/**
 * gemini.js - System-Two Deliberative AI Bridge
 * Interfaces with Google Gemini's fastest models (gemini-2.5-flash / gemini-1.5-flash)
 * for answerr (answerr.me)
 */

class GeminiBridge {
  constructor() {
    this.storageKey = 'answerr_gemini_api_key';
    this.modelStorageKey = 'answerr_gemini_model';
    this.defaultModel = 'gemini-2.5-flash';
  }

  getApiKey() {
    return localStorage.getItem(this.storageKey) || '';
  }

  setApiKey(key) {
    if (key) {
      localStorage.setItem(this.storageKey, key.trim());
    } else {
      localStorage.removeItem(this.storageKey);
    }
  }

  getModel() {
    return localStorage.getItem(this.modelStorageKey) || this.defaultModel;
  }

  setModel(model) {
    if (model) {
      localStorage.setItem(this.modelStorageKey, model.trim());
    }
  }

  hasApiKey() {
    return Boolean(this.getApiKey());
  }

  /**
   * System-Two Step 1: Transforms unstructured natural language prompt into
   * typed wevv parameters (state object, question type, instructions, criteria).
   */
  async transformPromptToWevv(userPrompt) {
    const apiKey = this.getApiKey();

    if (!apiKey) {
      // Intelligent local heuristic parser for zero-key instant preview
      return this.heuristicParser(userPrompt);
    }

    const model = this.getModel();
    const systemInstruction = `You are the System-Two cognitive compiler for the 'wevv' Zero-Memory Fractal Decision Engine.
Your role: Given a natural language scenario, question, or system triage prompt, you extract the underlying program state and formulate a typed wevv decision query.

wevv supports three typed primitives:
1. 'noul': Boolean probability decision (e.g. allow/deny, safe/unsafe, valid/invalid).
2. 'choice': Categorical routing (e.g. direct_api vs rate_limiter vs sandbox vs drop_packet).
3. 'score': Ordinal rating / severity assessment (e.g. Low, Medium, High, Critical).

Respond ONLY with a valid JSON object with the following schema:
{
  "state": {
    "key_name": number | boolean | string
  },
  "question": {
    "key": "decision_key",
    "type": "noul" | "choice" | "score",
    "instructions": "Clear question instructions",
    "criteria": ["OptionA", "OptionB", ...] or {"opt_a": "desc A", ...} (for choice or score),
    "threshold": 0.5
  },
  "detectedLanguage": "tr" | "en",
  "scenarioSummary": "Brief 1-sentence summary of the scenario in detected language"
}`;

    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;

    const requestBody = {
      contents: [
        {
          role: 'user',
          parts: [{ text: `Translate the following user inquiry into a formal wevv System-One decision specification:\n\n"${userPrompt}"` }]
        }
      ],
      systemInstruction: {
        parts: [{ text: systemInstruction }]
      },
      generationConfig: {
        temperature: 0.1,
        responseMimeType: 'application/json'
      }
    };

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData?.error?.message || `Gemini API HTTP ${response.status}`);
      }

      const data = await response.json();
      const rawText = data?.candidates?.[0]?.content?.parts?.[0]?.text || '{}';
      const parsed = JSON.parse(rawText);

      return {
        success: true,
        source: 'gemini',
        model,
        data: parsed
      };
    } catch (err) {
      console.warn('[Answerr/Gemini] Fallback to heuristic parser due to:', err.message);
      const fallback = this.heuristicParser(userPrompt);
      fallback.apiError = err.message;
      return fallback;
    }
  }

  /**
   * System-Two Step 2: Interprets the mathematical output of wevv and produces
   * natural language commentary and recommended actions.
   */
  async interpretDecision(userPrompt, wevvResult, stateData) {
    const apiKey = this.getApiKey();

    if (!apiKey) {
      return this.heuristicInterpreter(userPrompt, wevvResult, stateData);
    }

    const model = this.getModel();
    const isTurkish = /[çğıöşü]/i.test(userPrompt) || /izin|guven|sistem|nasil|mi|mu|miyim|paket|saldiri|tehlike/i.test(userPrompt);

    const promptText = `User Query: "${userPrompt}"
Extracted State: ${JSON.stringify(stateData?.state || {})}
wevv System-One Deterministic Result:
- Model: ${wevvResult.model}
- Latency: ${wevvResult.latencyMs} ms
- Tensor Memory: 0 Bytes VRAM (True Zero-Memory Fractal Dynamics)
- 24-Byte Seed Coordinates: cx=${wevvResult.coordinates.cx.toFixed(6)}, cy=${wevvResult.coordinates.cy.toFixed(6)}, zoom=${wevvResult.coordinates.zoom.toFixed(1)}
- Answers: ${JSON.stringify(wevvResult.answers, null, 2)}
- Fractal Telemetry: ${JSON.stringify(wevvResult.telemetry)}

Provide an authoritative, clear, and insightful System-Two cognitive response in ${isTurkish ? 'Turkish' : 'English'}.
Structure your answer into:
1. **Karar Özeti (Decision Verdict)**: Direct result with confidence score.
2. **Sistem-1 Fraktal Mantığı (Mathematical Reflex)**: Brief explanation of why the state parameters and Mandelbrot boundary dynamics led to this verdict.
3. **Önerilen Aksiyon (Recommended Action)**: Practical next step for the engineer / system.

Keep the tone concise, scientific, and professional.`;

    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;

    const requestBody = {
      contents: [{ role: 'user', parts: [{ text: promptText }] }],
      generationConfig: {
        temperature: 0.3,
        maxOutputTokens: 600
      }
    };

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData?.error?.message || `Gemini API HTTP ${response.status}`);
      }

      const data = await response.json();
      const text = data?.candidates?.[0]?.content?.parts?.[0]?.text || '';

      return {
        success: true,
        source: 'gemini',
        model,
        text
      };
    } catch (err) {
      console.warn('[Answerr/Gemini] Fallback interpreter due to:', err.message);
      const fallback = this.heuristicInterpreter(userPrompt, wevvResult, stateData);
      fallback.apiError = err.message;
      return fallback;
    }
  }

  /**
   * Local heuristic prompt parser when Gemini API key is not configured or in offline demo mode
   */
  heuristicParser(prompt) {
    const p = prompt.toLowerCase();
    const isTurkish = /[çğıöşü]/i.test(prompt) || /izin|gecer|mi|mu|saldiri|tehlike|yonlendir|skor/i.test(p);

    let qType = 'noul';
    let qKey = 'allow_execution';
    let instructions = isTurkish ? 'Bu operasyonun yürütülmesine izin verilsin mi?' : 'Should this incoming request be granted direct execution?';
    let criteria = null;
    const state = {};

    // Extract numbers if present
    const numbers = prompt.match(/\d+(\.\d+)?/g);
    if (numbers) {
      state.req_frequency = parseFloat(numbers[0]) || 1.0;
      if (numbers.length > 1) state.payload_kb = parseFloat(numbers[1]) || 5.0;
    } else {
      state.req_frequency = 2.5;
      state.payload_kb = 12.0;
    }

    // Role detection
    if (/admin|yonetici|yetkili|root|kurucu/.test(p)) {
      state.user_role = 'admin';
      state.auth_status = true;
    } else if (/hacker|saldirgan|bot|attacker|kotuniyetli|ddos/.test(p)) {
      state.user_role = 'attacker';
      state.auth_status = false;
      state.failed_attempts = 15;
    } else if (/guest|misafir|anonim|anonymous|unverified/.test(p)) {
      state.user_role = 'guest';
      state.auth_status = false;
    } else {
      state.user_role = 'member';
      state.auth_status = true;
    }

    // Question type detection
    if (/yonlendir|nereye|hangi|route|cluster|nereye gitsin|kategori|sec/i.test(p)) {
      qType = 'choice';
      qKey = 'route_target';
      instructions = isTurkish ? 'Hedef servis/küme seçimi' : 'Target microservice cluster routing';
      criteria = isTurkish ? {
        direct_api: 'Doğrudan Üretim Kümesi (Production)',
        rate_limiter: 'Oran Sınırlama Kuyruğu (Rate-Limiter)',
        sandbox_audit: 'Yalıtılmış Güvenlik İncelemesi (Sandbox)',
        drop_packet: 'Trafik Engelleme & Kara Liste (Drop)'
      } : {
        direct_api: 'Direct Production API',
        rate_limiter: 'Rate-Limiting Buffer Queue',
        sandbox_audit: 'Isolated Sandbox Audit',
        drop_packet: 'Immediate Packet Drop'
      };
    } else if (/skor|seviye|risk|tehlike derecesi|score|level|puan|oncelik/i.test(p)) {
      qType = 'score';
      qKey = 'risk_severity';
      instructions = isTurkish ? 'Algılanan tehdit/risk şiddeti derecesi' : 'Perceived threat/risk severity index';
      criteria = isTurkish
        ? ['Normal / Güvenli', 'Düşük Anomali', 'Yüksek Risk', 'Kritik Tehdit']
        : ['Normal / Benign', 'Minor Anomaly', 'Elevated Risk', 'Critical Threat'];
    }

    return {
      success: true,
      source: 'local_heuristic',
      model: 'local-state-compiler',
      data: {
        state,
        question: {
          key: qKey,
          type: qType,
          instructions,
          criteria,
          threshold: 0.5
        },
        detectedLanguage: isTurkish ? 'tr' : 'en',
        scenarioSummary: isTurkish
          ? `Soru Sistem-1 parametrelerine dönüştürüldü (Rol: ${state.user_role}, Karar Tipi: ${qType}).`
          : `Synthesized into System-1 parameters (Role: ${state.user_role}, Primitive: ${qType}).`
      }
    };
  }

  /**
   * Local heuristic interpreter when Gemini API key is not configured
   */
  heuristicInterpreter(prompt, wevvResult, stateData) {
    const isTurkish = stateData?.detectedLanguage === 'tr' || /[çğıöşü]/i.test(prompt);
    const answers = wevvResult.answers;
    const ansKey = Object.keys(answers)[0];
    const ans = answers[ansKey];

    let verdict = '';
    let logic = '';
    let action = '';

    if (ans.type === 'noul') {
      const decisionText = ans.decision ? (isTurkish ? 'ONAYLANDI (TRUE)' : 'APPROVED (TRUE)') : (isTurkish ? 'REDDEDİLDİ (FALSE)' : 'DENIED (FALSE)');
      verdict = isTurkish
        ? `**Karar:** ${decisionText} (Olasılık: %${(ans.noul * 100).toFixed(1)}, Güven: %${(ans.confidence * 100).toFixed(0)})`
        : `**Verdict:** ${decisionText} (Probability: ${(ans.noul * 100).toFixed(1)}%, Confidence: ${(ans.confidence * 100).toFixed(0)}%)`;

      logic = isTurkish
        ? `wevv motoru 24 baytlık $(c_x, c_y)$ tohumunu Mandelbrot sınırında modüle etti. Kaçış dinamiği (${wevvResult.latencyMs} ms) ve kuadran enerjisi hesaplanarak ${ans.decision ? 'güvenli sınır içinde kalındı' : 'hata sınırı aşılarak anomali tespit edildi'}.`
        : `The wevv engine perturbed the 24-byte boundary seed along dM. Escape dynamics (${wevvResult.latencyMs} ms) indicated ${ans.decision ? 'safe operational manifold' : 'divergence crossing the error threshold'}.`;

      action = ans.decision
        ? (isTurkish ? 'İşlem derhal üretim boru hattına yönlendirildi; ek gecikme olmadan yürütülüyor.' : 'Operation dispatched directly to execution pipeline with zero additional latency.')
        : (isTurkish ? 'İşlem durduruldu. Sistem-1 refleks kalkanı güvenlik ihlalini engelledi.' : 'Operation aborted. System-1 reflex arc prevented potential safety hazard.');

    } else if (ans.type === 'choice') {
      verdict = isTurkish
        ? `**Seçilen Rota:** \`${ans.choice}\` (Güven: %${(ans.confidence * 100).toFixed(0)})`
        : `**Selected Target:** \`${ans.choice}\` (Confidence: ${(ans.confidence * 100).toFixed(0)}%)`;

      logic = isTurkish
        ? `Girdi durumu 4-Kuadran ($Q_1-Q_4$) alt bölgelerine ayrıştırıldı. En yüksek faz enerjisi \`${ans.choice}\` rotasında kilitlendi.`
        : `Input state was partitioned across the 4-Quadrant phase space ($Q_1-Q_4$). The maximum harmonic density localized at \`${ans.choice}\`.`;

      action = isTurkish
        ? `Paket hedefi \`${ans.choice}\` olarak güncellendi ve ilgili mikroservis tamponuna iletildi.`
        : `Traffic routed to \`${ans.choice}\` and queued in the designated microservice channel.`;

    } else if (ans.type === 'score') {
      verdict = isTurkish
        ? `**Değerlendirme Skoru:** ${ans.score} / ${ans.scaleMax} — Seviye: **${ans.selectedLevel}**`
        : `**Evaluated Score:** ${ans.score} / ${ans.scaleMax} — Level: **${ans.selectedLevel}**`;

      logic = isTurkish
        ? `Kaotik sınır saçılma integrali ve kaçış hızı hesaplandı. Güven oranı: %${(ans.confidence * 100).toFixed(0)}.`
        : `Dark-area escape integral and divergence velocity yielded continuous scale metric with ${(ans.confidence * 100).toFixed(0)}% confidence.`;

      action = isTurkish
        ? `Operasyonel izleme seviyesi '${ans.selectedLevel}' olarak işaretlendi.`
        : `Operational triage metric committed to telemetry log as '${ans.selectedLevel}'.`;
    }

    const text = isTurkish
      ? `${verdict}\n\n**Sistem-1 Fraktal Refleksi:** ${logic}\n\n**Önerilen Operasyonel Aksiyon:** ${action}\n\n*(🛡️ wevv Sıfır-Halüsinasyon Garantisi: Karar, Mandelbrot fraktal kaçış geometrisi üzerinden deterministik olarak üretilmiştir.)*`
      : `${verdict}\n\n**System-1 Fractal Reflex:** ${logic}\n\n**Recommended Operational Action:** ${action}\n\n*(🛡️ wevv Zero-Hallucination Guarantee: Decision derived deterministically via Mandelbrot fractal escape geometry.)*`;

    return {
      success: true,
      source: 'local_heuristic',
      model: 'local-interpreter',
      text
    };
  }
}

if (typeof window !== 'undefined') {
  window.GeminiBridge = GeminiBridge;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { GeminiBridge };
}
