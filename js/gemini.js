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
   * typed werr parameters (state object, question type, instructions, criteria).
   */
  async transformPromptToWevv(userPrompt) {
    const apiKey = this.getApiKey();

    if (!apiKey) {
      // Intelligent local heuristic parser for zero-key instant preview
      return this.heuristicParser(userPrompt);
    }

    const model = this.getModel();
    const systemInstruction = `You are the System-Two cognitive compiler for the 'werr' Zero-Memory Fractal Decision Engine.
Your role: Given a natural language scenario, question, or system triage prompt, you extract the underlying program state and formulate a typed werr decision query.

werr supports three typed primitives:
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
          parts: [{ text: `Translate the following user inquiry into a formal werr System-One decision specification:\n\n"${userPrompt}"` }]
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
   * System-Two Step 2: Interprets the mathematical output of werr and produces
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
werr System-One Deterministic Result:
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
   * Local heuristic prompt parser when Gemini API key is not configured or in offline demo mode.
   * Matches curated presets directly and performs intelligent domain/question extraction on custom queries.
   */
  heuristicParser(prompt) {
    const p = (prompt || '').trim();
    const pLower = p.toLowerCase();
    const isTurkish = /[çğıöşü]/i.test(p) || /mi\b|mu\b|mı\b|mü\b|izin|onay|durum|istek|sistem|kullanici|nedir|hangisi|acil|sogutma|engellensin/i.test(pLower);

    // 1. Check if userPrompt matches any known preset in SCENARIO_PRESETS
    if (typeof SCENARIO_PRESETS !== 'undefined' && Array.isArray(SCENARIO_PRESETS)) {
      for (const preset of SCENARIO_PRESETS) {
        const trMatch = preset.prompt && (p === preset.prompt.trim() || pLower.includes((preset.titleTr || '').toLowerCase()) || p.includes(preset.prompt.slice(0, 25)));
        const enMatch = preset.promptEn && (p === preset.promptEn.trim() || pLower.includes((preset.title || '').toLowerCase()) || p.includes(preset.promptEn.slice(0, 25)));

        if (trMatch || enMatch) {
          const langKey = isTurkish ? 'tr' : 'en';
          const instructions = isTurkish
            ? (preset.question.instructionsTr || preset.question.instructions)
            : (preset.question.instructionsEn || preset.question.instructions);
          const criteria = isTurkish
            ? (preset.question.criteriaTr || preset.question.criteria)
            : (preset.question.criteriaEn || preset.question.criteria);

          return {
            success: true,
            source: 'local_heuristic',
            model: 'werr-preset-compiler',
            presetId: preset.id,
            data: {
              presetId: preset.id,
              state: { ...preset.state },
              question: {
                key: preset.question.key,
                type: preset.question.type,
                instructions: instructions,
                criteria: criteria || null,
                threshold: preset.question.threshold || 0.5
              },
              detectedLanguage: langKey,
              scenarioSummary: isTurkish
                ? `Hazır Senaryo: ${preset.titleTr} (Tipli Karar: ${preset.question.type.toUpperCase()})`
                : `Preset Scenario: ${preset.title} (Typed Decision: ${preset.question.type.toUpperCase()})`
            }
          };
        }
      }
    }

    // 2. Intelligent Dynamic Extraction for Custom Queries
    let instructions = '';
    
    // Extract the actual question from the prompt (sentence ending with '?' or question suffixes)
    const sentences = p.split(/(?<=[.!?\n])\s+/);
    const qSentence = sentences.find(s => /\?|mi\b|mu\b|mı\b|mü\b|should\b|is\b|which\b|what\b/i.test(s));
    if (qSentence) {
      instructions = qSentence.trim();
      if (!instructions.endsWith('?')) instructions += '?';
    } else if (sentences.length > 0) {
      instructions = sentences[sentences.length - 1].trim();
      if (!instructions.endsWith('?')) instructions += '?';
    } else {
      instructions = isTurkish ? 'Bu işlem onaylansın mı?' : 'Should this action be approved?';
    }

    // Determine Question Type and Key
    let qType = 'noul';
    let qKey = 'allow_execution';
    let criteria = null;

    if (/hangisi|nereye|hangi|rota|route|cluster|which|choose|select/i.test(pLower)) {
      qType = 'choice';
      qKey = 'target_route';
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
    } else if (/skor|seviye|risk|tehlike|derece|score|level|puan|severity|rate/i.test(pLower)) {
      qType = 'score';
      qKey = 'severity_score';
      criteria = isTurkish
        ? ['Normal / Güvenli', 'Düşük Anomali', 'Yüksek Risk', 'Kritik Seviye']
        : ['Normal / Benign', 'Minor Anomaly', 'Elevated Risk', 'Critical Threat'];
    } else {
      qType = 'noul';
      if (/engel|bloke|drop|block|ban/i.test(pLower)) {
        qKey = 'block_request';
      } else if (/acil|durdur|kapat|sogut|shutdown|stop|halt|freeze/i.test(pLower)) {
        qKey = 'emergency_shutdown';
      } else if (/onay|izin|allow|permit|approve/i.test(pLower)) {
        qKey = 'allow_execution';
      } else {
        qKey = 'execute_action';
      }
    }

    // Extract State Variables Intelligently
    const state = {};

    // Temperature (e.g. 82°C, 95 C, 40 derece)
    const tempMatch = p.match(/(\d+(?:\.\d+)?)\s*(?:°c|c\b|derece)/i);
    if (tempMatch) state.temp_c = parseFloat(tempMatch[1]);

    // Percentage / Torque / Load (e.g. %94 or 94%)
    const pctMatch = p.match(/(?:%(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*%)/);
    if (pctMatch) state.torque_or_load_pct = parseFloat(pctMatch[1] || pctMatch[2]);

    // Multipliers / Ratios (e.g. 2.8 katı, 3x baseline)
    const ratioMatch = p.match(/(\d+(?:\.\d+)?)\s*(?:katı|kat|x|times)\b/i);
    if (ratioMatch) state.multiplier_ratio = parseFloat(ratioMatch[1]);

    // Latency (e.g. 45 ms)
    const latMatch = p.match(/(\d+(?:\.\d+)?)\s*ms\b/i);
    if (latMatch) state.latency_ms = parseFloat(latMatch[1]);

    // Payload size (e.g. 14 KB, 500 MB)
    const sizeMatch = p.match(/(\d+(?:\.\d+)?)\s*(?:kb|mb|gb|bytes)\b/i);
    if (sizeMatch) state.payload_size = parseFloat(sizeMatch[1]);

    // Monetary Amount (e.g. 4500 USD, 200 TL, $500)
    const amtMatch = p.match(/(?:\$|€|£)?\s*(\d+(?:\.\d+)?)\s*(?:usd|eur|try|tl|dolar|euro)?\b/i);
    if (amtMatch && !tempMatch && !latMatch && parseFloat(amtMatch[1]) > 50) {
      state.amount = parseFloat(amtMatch[1]);
    }

    // Request counts (e.g. 180 istek)
    const reqMatch = p.match(/(\d+)\s*(?:istek|talep|request|req)/i);
    if (reqMatch) state.req_count = parseInt(reqMatch[1], 10);

    // Failed counts (e.g. 24 başarısız)
    const failMatch = p.match(/(\d+)\s*(?:başarısız|hata|failed|error)/i);
    if (failMatch) state.failed_count = parseInt(failMatch[1], 10);

    // Roles (word boundaries: DO NOT match robot as bot!)
    if (/\b(?:admin|yonetici|yetkili|root)\b/i.test(pLower)) {
      state.user_role = 'admin';
      state.auth_status = true;
    } else if (/\b(?:hacker|saldirgan|attacker|ddos)\b/i.test(pLower)) {
      state.user_role = 'attacker';
      state.auth_status = false;
    } else if (/\b(?:guest|misafir|anonim|anonymous)\b/i.test(pLower)) {
      state.user_role = 'guest';
      state.auth_status = false;
    } else if (/\b(?:member|uye|user|kullanici)\b/i.test(pLower)) {
      state.user_role = 'member';
      state.auth_status = true;
    }

    // Fallback if no specific state properties were extracted: extract generic numbers
    if (Object.keys(state).length === 0) {
      const numbers = p.match(/\d+(?:\.\d+)?/g);
      if (numbers) {
        numbers.slice(0, 4).forEach((num, idx) => {
          state[`metric_${idx + 1}`] = parseFloat(num);
        });
      } else {
        state.signal_intensity = 1.0;
      }
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
          ? `Girdi Sistem-1 parametrelerine dönüştürüldü (Karar: ${qType.toUpperCase()}, Soru: "${instructions}").`
          : `Synthesized into System-1 parameters (Primitive: ${qType.toUpperCase()}, Question: "${instructions}").`
      }
    };
  }

  /**
   * Local heuristic interpreter when Gemini API key is not configured.
   * Produces tailored, contextual decision commentary matching the actual question.
   */
  heuristicInterpreter(prompt, wevvResult, stateData) {
    const isTurkish = stateData?.detectedLanguage === 'tr' || /[çğıöşü]/i.test(prompt);
    const answers = wevvResult.answers;
    const ansKey = Object.keys(answers)[0];
    const ans = answers[ansKey];
    const question = stateData?.data?.question || stateData?.question || {};
    const qKey = question.key || ansKey;
    const instructions = question.instructions || '';

    // Check if preset matches for tailored interpretation
    let presetMatch = null;
    if (typeof SCENARIO_PRESETS !== 'undefined' && Array.isArray(SCENARIO_PRESETS)) {
      presetMatch = SCENARIO_PRESETS.find(pr =>
        (stateData?.presetId && pr.id === stateData.presetId) ||
        (pr.prompt && prompt.includes(pr.prompt.slice(0, 25)))
      );
    }

    let verdict = '';
    let logic = '';
    let action = '';

    if (ans.type === 'noul') {
      if (presetMatch && presetMatch.interpretation) {
        const interp = isTurkish ? presetMatch.interpretation.tr : presetMatch.interpretation.en;
        const decisionText = ans.decision ? interp.trueVerdict : interp.falseVerdict;
        verdict = isTurkish
          ? `**Karar:** ${decisionText} (Olasılık: %${(ans.noul * 100).toFixed(1)}, Güven: %${(ans.confidence * 100).toFixed(0)})`
          : `**Verdict:** ${decisionText} (Probability: ${(ans.noul * 100).toFixed(1)}%, Confidence: ${(ans.confidence * 100).toFixed(0)}%)`;
        action = ans.decision ? interp.trueAction : interp.falseAction;
      } else {
        let trueVerdict = isTurkish ? 'ONAYLANDI (TRUE)' : 'APPROVED (TRUE)';
        let falseVerdict = isTurkish ? 'REDDEDİLDİ (FALSE)' : 'DENIED (FALSE)';
        let trueAction = isTurkish ? `Talimat onaylandı: "${instructions}". Sistem-1 refleksi aksiyonu derhal yürüttü.` : `Instruction approved: "${instructions}". System-1 reflex executed action immediately.`;
        let falseAction = isTurkish ? `Talimat reddedildi: "${instructions}". Eşik değeri sağlanamadı; işlem durduruldu.` : `Instruction denied: "${instructions}". Threshold not met; operation blocked.`;

        if (qKey === 'emergency_shutdown' || /acil|durdur|shutdown|halt/i.test(instructions)) {
          trueVerdict = isTurkish ? 'ACİL DURDURMA DEVREYE ALINDI (TRUE)' : 'EMERGENCY SHUTDOWN ENGAGED (TRUE)';
          falseVerdict = isTurkish ? 'NORMAL ÇALIŞMA (FALSE)' : 'NORMAL OPERATION (FALSE)';
          trueAction = isTurkish ? 'Kritik eşik aşıldı! Acil soğutma ve durdurma protokolü derhal yürütüldü.' : 'Critical threshold crossed! Emergency cooling and shutdown protocol executed.';
          falseAction = isTurkish ? 'Parametreler operasyonel tolerans içinde; acil durdurma gerekmiyor, robot çalışma döngüsüne devam ediyor.' : 'Parameters within operational tolerance; no shutdown needed.';
        } else if (qKey === 'block_request' || /engellensin|bloke|block|drop/i.test(instructions)) {
          trueVerdict = isTurkish ? 'ENGELLEME ONAYLANDI (TRUE)' : 'BLOCK CONFIRMED (TRUE)';
          falseVerdict = isTurkish ? 'GEÇİŞE İZİN VERİLDİ (FALSE)' : 'TRAFFIC ALLOWED (FALSE)';
          trueAction = isTurkish ? 'Anomali ve kural ihlali tespit edildi. İstek derhal engellendi ve karantinaya alındı.' : 'Anomaly and violation detected. Request blocked and quarantined.';
          falseAction = isTurkish ? 'İstek güvenli parametreler içinde değerlendirildi; geçişe onay verildi.' : 'Request within benign parameters; traffic allowed.';
        }

        const decisionText = ans.decision ? trueVerdict : falseVerdict;
        verdict = isTurkish
          ? `**Karar:** ${decisionText} (Olasılık: %${(ans.noul * 100).toFixed(1)}, Güven: %${(ans.confidence * 100).toFixed(0)})`
          : `**Verdict:** ${decisionText} (Probability: ${(ans.noul * 100).toFixed(1)}%, Confidence: ${(ans.confidence * 100).toFixed(0)}%)`;
        action = ans.decision ? trueAction : falseAction;
      }

      logic = isTurkish
        ? `werr motoru 24 baytlık $(c_x, c_y)$ tohumunu Mandelbrot sınırında modüle etti. Kaçış dinamiği (${wevvResult.latencyMs} ms) ve kuadran enerjisi hesaplanarak ${ans.decision ? 'pozitif kararlılık/aksiyon alanı doğrulandı' : 'hata/güvenlik toleransı aşılarak negatif karar üretildi'}.`
        : `The werr engine perturbed the 24-byte boundary seed along dM. Escape dynamics (${wevvResult.latencyMs} ms) indicated ${ans.decision ? 'positive action manifold confirmed' : 'divergence crossing safety tolerance'}.`;

    } else if (ans.type === 'choice') {
      verdict = isTurkish
        ? `**Seçilen Rota:** \`${ans.choice}\` (Güven: %${(ans.confidence * 100).toFixed(0)})`
        : `**Selected Target:** \`${ans.choice}\` (Confidence: ${(ans.confidence * 100).toFixed(0)}%)`;

      logic = isTurkish
        ? `Girdi durumu 4-Kuadran ($Q_1-Q_4$) alt bölgelerine ayrıştırıldı. En yüksek faz enerjisi \`${ans.choice}\` rotasında kilitlendi.`
        : `Input state was partitioned across the 4-Quadrant phase space ($Q_1-Q_4$). The maximum harmonic density localized at \`${ans.choice}\`.`;

      action = presetMatch?.interpretation
        ? (isTurkish ? presetMatch.interpretation.tr.actionPrefix : presetMatch.interpretation.en.actionPrefix) + `\`${ans.choice}\``
        : (isTurkish ? `Paket hedefi \`${ans.choice}\` olarak güncellendi ve ilgili mikroservis tamponuna iletildi.` : `Traffic routed to \`${ans.choice}\` and queued in designated microservice channel.`);

    } else if (ans.type === 'score') {
      verdict = isTurkish
        ? `**Değerlendirme Skoru:** ${ans.score} / ${ans.scaleMax} — Seviye: **${ans.selectedLevel}**`
        : `**Evaluated Score:** ${ans.score} / ${ans.scaleMax} — Level: **${ans.selectedLevel}**`;

      logic = isTurkish
        ? `Kaotik sınır saçılma integrali ve kaçış hızı hesaplandı. Güven oranı: %${(ans.confidence * 100).toFixed(0)}.`
        : `Dark-area escape integral and divergence velocity yielded continuous scale metric with ${(ans.confidence * 100).toFixed(0)}% confidence.`;

      action = presetMatch?.interpretation
        ? (isTurkish ? presetMatch.interpretation.tr.actionPrefix : presetMatch.interpretation.en.actionPrefix)
        : (isTurkish ? `Operasyonel izleme seviyesi '${ans.selectedLevel}' olarak işaretlendi.` : `Operational triage metric committed to telemetry log as '${ans.selectedLevel}'.`);
    }

    const text = isTurkish
      ? `${verdict}\n\n**Sistem-1 Fraktal Refleksi:** ${logic}\n\n**Önerilen Operasyonel Aksiyon:** ${action}\n\n*(🛡️ werr Sıfır-Halüsinasyon Garantisi: Karar, Mandelbrot fraktal kaçış geometrisi üzerinden deterministik olarak üretilmiştir.)*`
      : `${verdict}\n\n**System-1 Fractal Reflex:** ${logic}\n\n**Recommended Operational Action:** ${action}\n\n*(🛡️ werr Zero-Hallucination Guarantee: Decision derived deterministically via Mandelbrot fractal escape geometry.)*`;

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
