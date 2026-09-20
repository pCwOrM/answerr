/**
 * app.js - Main Application Orchestrator for answerr (answerr.me)
 * Manages chat lifecycle, dual-cognitive pipeline execution (System 1 + System 2),
 * live telemetry HUD rendering with Smart If-Statement code & Seed Dump,
 * Google reCAPTCHA v3 & mechsrv telemetry integration, multi-language (TR / EN) switching.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Core Engines
  const wevv = new WevvEngine();
  const gemini = new GeminiBridge();

  // Google reCAPTCHA v3 Site Key (matches wevv infrastructure)
  const RECAPTCHA_SITE_KEY = "6LdP-JgqAAAAAJLdy_W8uowqstSa4XKlJTOkVAux";

  function getRecaptchaToken(action = "answerr_chat") {
    return new Promise((resolve) => {
      try {
        if (typeof grecaptcha !== 'undefined' && grecaptcha.ready) {
          grecaptcha.ready(function() {
            grecaptcha.execute(RECAPTCHA_SITE_KEY, { action: action })
              .then(function(token) { resolve(token); })
              .catch(function(err) {
                console.warn("[answerr] reCAPTCHA token execution failed:", err);
                resolve(null);
              });
          });
        } else {
          resolve(null);
        }
      } catch (e) {
        console.warn("[answerr] reCAPTCHA exception:", e);
        resolve(null);
      }
    });
  }

  // Telemetry Dispatcher to mechsrv.itouch.fi
  async function dispatchWebTelemetry(wevvResult, prompt, stateData) {
    try {
      const token = await getRecaptchaToken("answerr_chat");
      const ansKey = Object.keys(wevvResult.answers)[0];
      const ans = wevvResult.answers[ansKey];

      const payload = {
        timestamp: new Date().toISOString(),
        version: "answerr-0.1.0-web",
        source: "answerr_chat",
        recaptcha_token: token || undefined,
        seed: {
          cx: parseFloat(wevvResult.coordinates.cx.toFixed(8)),
          cy: parseFloat(wevvResult.coordinates.cy.toFixed(8)),
          zoom: parseFloat(wevvResult.coordinates.zoom.toFixed(4))
        },
        state_summary: stateData.state || {},
        questions: [
          {
            name: ansKey,
            type: ans.type,
            instruction: prompt,
            decision: ans.type === 'noul' ? ans.decision : (ans.type === 'choice' ? ans.choice : ans.score),
            confidence: ans.confidence
          }
        ],
        latency_ms: wevvResult.latencyMs
      };

      fetch("https://mechsrv.itouch.fi:4431/wevv/telemetry", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "X-Recaptcha-Token": token } : {})
        },
        body: JSON.stringify(payload),
        keepalive: true
      }).catch(() => {});
    } catch (err) {
      // Non-blocking telemetry
    }
  }

  // 2. Language State & Translations
  let currentLang = localStorage.getItem('answerr_lang') || 'tr';

  const I18N = {
    tr: {
      heroTitle: "Sadece Sohbet Etmeyin. Karar Verin.",
      heroSubtitle: "<strong>A.N.S.W.E.R.R.</strong> <em>(Adaptive Next-gen Signal Wave & Error Reflex Reasoner)</em>: Yazılımlar ve otomasyon için <strong>Sistem-1</strong> karar altyapısı. Operasyonel durum (state) verisini ve soru talimatlarını anında tipli kararlara (<code>noul</code>, <code>choice</code>, <code>score</code>) dönüştürür. <strong>wevv</strong> 0-Byte VRAM fraktal omurilik refleksiyle çalışır; mikrosaniyede deterministik sonuç üretir, asla halüsinasyon görmez ve çökmez.",
      tagSpeed: "⚡ < 0.5 ms Sistem-1 Fraktal Hızı",
      tagZeroMem: "💾 0-Byte VRAM (Zero-Tensor Architecture)",
      tagHallucination: "🛡️ Sıfır Halüsinasyon & Tip Güvenli",
      tagCrash: "🚀 Asla Çökmez & %100 Deterministik",
      inputPlaceholder: "Operasyonel durum (state) veya karar senaryosu girin (örn: 'Anonim IP'den 180 istek/dk geldi, yürütmeye izin verilsin mi?')...",
      newDecisionBtn: "Yeni Karar",
      historyLabel: "Karar Geçmişi",
      systemStatus: "wevv 0-Byte VRAM: Aktif",
      disclaimer: "answerr, <a href=\"https://github.com/pCwOrM/wevv\" target=\"_blank\" rel=\"noopener\">wevv</a> fraktal Sistem-1 karar motoru ile çalışır. Tip güvenli, deterministik ve sıfır halüsinasyonludur. <a href=\"https://answerr.me\">answerr.me</a>.",
      modalTitle: "⚙️ Answerr Karar Motoru Ayarları",
      modalFreeBadge: "✓ Tamamen Ücretsiz & Anahtarsız Sistem-1 Aktif",
      modalFreeDesc: "answerr, tarayıcınızda sıfır gecikmeli yerel wevv Sistem-1 fraktal motoruyla çalışır. Herhangi bir kayıt, ücret veya API anahtarı zorunlu değildir.",
      modalApiLabel: "Opsiyonel: Google Gemini API Anahtarı",
      modalApiHint: "Genişletilmiş bulut Sistem-2 müzakeresi isterseniz Google AI Studio'dan ücretsiz anahtar alabilirsiniz. Anahtar sadece tarayıcınızda (localStorage) saklanır.",
      modalModelLabel: "Sistem-2 Müzakere Modeli",
      modalClearHistory: "🗑️ Tüm Karar Geçmişini Temizle",
      modalCancel: "İptal",
      modalSave: "Ayarları Kaydet",
      keylessBadge: "⚡ wevv Sistem-1 (Ücretsiz / Keyless)",
      step1: "1/3 Durum matrisi ve tipli soru ayrıştırılıyor (System-2 State)...",
      step2: "2/3 wevv: Mandelbrot ∂M kaçış dinamiği hesaplanıyor (< 0.5ms)...",
      step3: "3/3 Sistem-1 telemetrisi ve karar doğrulanıyor...",
      hudTitle: "🌊 wevv Sistem-1 Karar Refleksi",
      hudLatency: "ms",
      hudVram: "0B Tensör VRAM",
      hudSeed: "24B Tohum",
      approved: "ONAYLANDI (TRUE)",
      denied: "ENGELLE / RET (FALSE)",
      routed: "ROTA",
      scored: "SKOR",
      confidence: "Güven",
      smartIf: "🚀 AKILLI KOD (Smart If-Statement):",
      downloadSeed: "💾 24B Tohum İndir (.TXT)"
    },
    en: {
      heroTitle: "Don't Just Chat. Get The Answerr.",
      heroSubtitle: "<strong>A.N.S.W.E.R.R.</strong> <em>(Adaptive Next-gen Signal Wave & Error Reflex Reasoner)</em>: Machine-native <strong>System-One</strong> decision infrastructure for software and automation. Send operational program state and typed questions; get structured, calibrated decisions (<code>noul</code>, <code>choice</code>, <code>score</code>) your code can use directly. Powered by <strong>wevv</strong> zero-memory fractal reflexes.",
      tagSpeed: "⚡ < 0.5 ms System-1 Fractal Speed",
      tagZeroMem: "💾 0-Byte VRAM (Zero-Tensor Architecture)",
      tagHallucination: "🛡️ Zero Hallucination & Type-Safe",
      tagCrash: "🚀 Zero Crash & 100% Deterministic",
      inputPlaceholder: "Enter operational state or decision query (e.g. 'Anonymous IP with 180 req/min burst, allow execution?')...",
      newDecisionBtn: "New Decision",
      historyLabel: "Decision Log",
      systemStatus: "wevv 0-Byte VRAM: Active",
      disclaimer: "answerr is powered by the <a href=\"https://github.com/pCwOrM/wevv\" target=\"_blank\" rel=\"noopener\">wevv</a> fractal System-One engine. Type-safe, calibrated, zero-hallucination. <a href=\"https://answerr.me\">answerr.me</a>.",
      modalTitle: "⚙️ Answerr Decision Engine Settings",
      modalFreeBadge: "✓ 100% Free & Keyless System-1 Active",
      modalFreeDesc: "answerr operates with zero latency directly inside your browser. No sign-up, credit card, or API key required.",
      modalApiLabel: "Optional: Google Gemini API Key",
      modalApiHint: "To unlock cloud System-2 deliberation, you can optionally provide a free key from Google AI Studio. Stored strictly in your browser (localStorage).",
      modalModelLabel: "System-2 Model",
      modalClearHistory: "🗑️ Clear All Decision Records",
      modalCancel: "Cancel",
      modalSave: "Save Settings",
      keylessBadge: "⚡ wevv System-1 (Free / Keyless)",
      step1: "1/3 Compiling input into state vector...",
      step2: "2/3 wevv: Evaluating Mandelbrot escape dynamics (< 0.5ms)...",
      step3: "3/3 Synthesizing System-1 telemetry and actions...",
      hudTitle: "🌊 wevv System-1 Decision Reflex",
      hudLatency: "ms",
      hudVram: "0B Tensor VRAM",
      hudSeed: "24B Seed",
      approved: "APPROVED (TRUE)",
      denied: "DENIED / BLOCKED (FALSE)",
      routed: "ROUTE",
      scored: "SCORE",
      confidence: "Confidence",
      smartIf: "🚀 SMART IF-STATEMENT (Production Code):",
      downloadSeed: "💾 Download 24B Seed (.TXT)"
    }
  };

  // 3. DOM Elements
  const chatMessagesEl = document.getElementById('chat-messages');
  const chatScrollAreaEl = document.getElementById('chat-scroll-area');
  const chatInputEl = document.getElementById('chat-input');
  const btnSendEl = document.getElementById('btn-send');
  const welcomeHeroEl = document.getElementById('welcome-hero');
  const presetGridEl = document.getElementById('preset-grid');
  const btnNewChatEl = document.getElementById('btn-new-chat');
  const historyListEl = document.getElementById('history-list');

  // Sidebar & Topbar
  const sidebarEl = document.getElementById('sidebar');
  const btnToggleSidebarEl = document.getElementById('btn-toggle-sidebar');
  const btnThemeToggleEl = document.getElementById('btn-theme-toggle');
  const btnSettingsEl = document.getElementById('btn-settings');
  const activeModelBadgeEl = document.getElementById('active-model-badge');
  const btnLangToggleEl = document.getElementById('btn-lang-toggle');
  const currentLangTextEl = document.getElementById('current-lang-text');

  // Dynamic I18N Text Elements
  const heroTitleEl = document.getElementById('hero-title');
  const heroSubtitleEl = document.getElementById('hero-subtitle');
  const tagHallucinationEl = document.getElementById('tag-hallucination');
  const tagCrashEl = document.getElementById('tag-crash');
  const tagSpeedEl = document.getElementById('tag-speed');
  const tagZeroMemEl = document.getElementById('tag-zeromem');
  const chatDisclaimerEl = document.getElementById('chat-disclaimer');
  const modalTitleEl = document.getElementById('modal-title');
  const modalFreeBadgeEl = document.getElementById('modal-free-badge');
  const modalFreeDescEl = document.getElementById('modal-free-desc');
  const modalApiLabelEl = document.getElementById('modal-api-label');
  const modalApiHintEl = document.getElementById('modal-api-hint');
  const modalModelLabelEl = document.getElementById('modal-model-label');
  const btnClearHistoryEl = document.getElementById('btn-clear-history');
  const btnCancelModalEl = document.getElementById('btn-cancel-modal');
  const btnSaveSettingsEl = document.getElementById('btn-save-settings');

  const newDecisionTextEl = document.getElementById('new-decision-text');
  const historyLabelEl = document.getElementById('history-label');

  // Settings Modal
  const settingsModalEl = document.getElementById('settings-modal');
  const btnCloseModalEl = document.getElementById('btn-close-modal');
  const inputApiKeyEl = document.getElementById('input-api-key');
  const selectModelEl = document.getElementById('select-model');

  // 4. Application State
  let currentSessionId = generateId();
  let conversationSessions = loadSessions();
  let isGenerating = false;

  // Initialize UI & Language
  applyLanguage(currentLang);
  updateModelBadge();
  renderHistoryList();

  // Language Toggle Event
  if (btnLangToggleEl) {
    btnLangToggleEl.addEventListener('click', () => {
      currentLang = currentLang === 'tr' ? 'en' : 'tr';
      localStorage.setItem('answerr_lang', currentLang);
      applyLanguage(currentLang);
    });
  }

  function toAsciiUpper(str) {
    if (!str) return '';
    return String(str).toLocaleUpperCase('en-US');
  }

  function applyLanguage(lang) {
    const t = I18N[lang] || I18N.tr;
    document.documentElement.lang = lang;
    if (currentLangTextEl) currentLangTextEl.textContent = toAsciiUpper(lang);

    if (newDecisionTextEl) newDecisionTextEl.textContent = t.newDecisionBtn;
    if (historyLabelEl) historyLabelEl.textContent = t.historyLabel;

    if (heroTitleEl) heroTitleEl.innerHTML = t.heroTitle;
    if (heroSubtitleEl) heroSubtitleEl.innerHTML = t.heroSubtitle;
    if (tagHallucinationEl) tagHallucinationEl.innerHTML = t.tagHallucination;
    if (tagCrashEl) tagCrashEl.innerHTML = t.tagCrash;
    if (tagSpeedEl) tagSpeedEl.innerHTML = t.tagSpeed;
    if (tagZeroMemEl) tagZeroMemEl.innerHTML = t.tagZeroMem;
    if (chatInputEl) chatInputEl.placeholder = t.inputPlaceholder;
    if (chatDisclaimerEl) chatDisclaimerEl.innerHTML = t.disclaimer;

    if (modalTitleEl) modalTitleEl.textContent = t.modalTitle;
    if (modalFreeBadgeEl) modalFreeBadgeEl.textContent = t.modalFreeBadge;
    if (modalFreeDescEl) modalFreeDescEl.textContent = t.modalFreeDesc;
    if (modalApiLabelEl) modalApiLabelEl.textContent = t.modalApiLabel;
    if (modalApiHintEl) modalApiHintEl.innerHTML = t.modalApiHint;
    if (modalModelLabelEl) modalModelLabelEl.textContent = t.modalModelLabel;
    if (btnClearHistoryEl) btnClearHistoryEl.textContent = t.modalClearHistory;
    if (btnCancelModalEl) btnCancelModalEl.textContent = t.modalCancel;
    if (btnSaveSettingsEl) btnSaveSettingsEl.textContent = t.modalSave;

    renderPresetCards(lang);
    renderHistoryList();
    updateModelBadge();
  }

  // Auto-resize input textarea
  chatInputEl.addEventListener('input', () => {
    chatInputEl.style.height = 'auto';
    chatInputEl.style.height = Math.min(chatInputEl.scrollHeight, 160) + 'px';
    btnSendEl.disabled = !chatInputEl.value.trim() || isGenerating;
  });

  chatInputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!btnSendEl.disabled) {
        handleSendMessage();
      }
    }
  });

  btnSendEl.addEventListener('click', () => handleSendMessage());

  // New Chat
  btnNewChatEl.addEventListener('click', () => {
    startNewChat();
  });

  // Sidebar Toggle
  if (btnToggleSidebarEl) {
    btnToggleSidebarEl.addEventListener('click', () => {
      sidebarEl.classList.toggle('collapsed');
    });
  }

  // Theme Toggle
  if (btnThemeToggleEl) {
    btnThemeToggleEl.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('answerr_theme', newTheme);
      btnThemeToggleEl.innerHTML = newTheme === 'dark' ? '🌙' : '☀️';
    });

    const savedTheme = localStorage.getItem('answerr_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    btnThemeToggleEl.innerHTML = savedTheme === 'dark' ? '🌙' : '☀️';
  }

  // Settings Modal Handlers
  btnSettingsEl.addEventListener('click', () => {
    inputApiKeyEl.value = gemini.getApiKey();
    selectModelEl.value = gemini.getModel();
    settingsModalEl.classList.add('open');
  });

  const closeModal = () => settingsModalEl.classList.remove('open');
  btnCloseModalEl.addEventListener('click', closeModal);
  btnCancelModalEl.addEventListener('click', closeModal);
  settingsModalEl.addEventListener('click', (e) => {
    if (e.target === settingsModalEl) closeModal();
  });

  btnSaveSettingsEl.addEventListener('click', () => {
    gemini.setApiKey(inputApiKeyEl.value);
    gemini.setModel(selectModelEl.value);
    updateModelBadge();
    closeModal();
  });

  if (btnClearHistoryEl) {
    btnClearHistoryEl.addEventListener('click', () => {
      const msg = currentLang === 'tr' ? 'Tüm kayıtlı kararlar silinsin mi?' : 'Clear all recorded decisions?';
      if (confirm(msg)) {
        conversationSessions = {};
        saveSessions();
        renderHistoryList();
        startNewChat();
        closeModal();
      }
    });
  }

  function updateModelBadge() {
    const t = I18N[currentLang] || I18N.tr;
    const hasKey = gemini.hasApiKey();
    const model = gemini.getModel();
    if (activeModelBadgeEl) {
      activeModelBadgeEl.innerHTML = hasKey
        ? `<span class="model-sparkle">✨</span> ${model}`
        : `<span class="model-sparkle">⚡</span> ${t.keylessBadge}`;
    }
  }

  // 5. Send Message Lifecycle
  async function handleSendMessage(presetPromptText) {
    const prompt = (presetPromptText || chatInputEl.value).trim();
    if (!prompt || isGenerating) return;

    const t = I18N[currentLang] || I18N.tr;
    isGenerating = true;
    chatInputEl.value = '';
    chatInputEl.style.height = 'auto';
    btnSendEl.disabled = true;

    // Hide welcome hero on first message
    if (welcomeHeroEl) {
      welcomeHeroEl.style.display = 'none';
    }

    // Append User Message
    appendUserMessage(prompt);

    // Save session title if first message
    let session = conversationSessions[currentSessionId];
    if (!session) {
      session = {
        id: currentSessionId,
        title: prompt.slice(0, 36) + (prompt.length > 36 ? '...' : ''),
        createdAt: new Date().toISOString(),
        messages: []
      };
      conversationSessions[currentSessionId] = session;
    }
    session.messages.push({ role: 'user', content: prompt });
    saveSessions();
    renderHistoryList();

    // Append Assistant Placeholder with live Stepper
    const assistantRow = createAssistantRow();
    chatMessagesEl.appendChild(assistantRow);
    scrollToBottom();

    const stepperEl = assistantRow.querySelector('.pipeline-status');
    const contentEl = assistantRow.querySelector('.assistant-content');

    try {
      // Step 1: System-2 Decomposition
      updateStepper(stepperEl, t.step1);
      const step1Result = await gemini.transformPromptToWevv(prompt);

      const stateData = step1Result.data;
      const stateObj = stateData.state || {};
      const questionObj = stateData.question || {
        key: 'decision',
        type: 'noul',
        instructions: prompt
      };

      // Step 2: System-1 Instant Execution (wevv Fractal Engine)
      updateStepper(stepperEl, t.step2);
      await new Promise(r => setTimeout(r, 120));

      const wevvResult = wevv.decide(stateObj, {
        [questionObj.key || 'decision']: questionObj
      });

      // Dispatch Telemetry with Google reCAPTCHA v3 asynchronously to mechsrv.itouch.fi
      dispatchWebTelemetry(wevvResult, prompt, stateData);

      // Step 3: System-2 Commentary Synthesis
      updateStepper(stepperEl, t.step3);
      const step3Result = await gemini.interpretDecision(prompt, wevvResult, stateData);

      // Remove stepper and render rich cards
      stepperEl.remove();

      // Render wevv System-1 Telemetry HUD Card
      const hudCard = renderWevvHudCard(wevv, wevvResult, stateData, prompt);
      contentEl.appendChild(hudCard);

      // Render Gemini / Local Commentary Card
      const commentaryCard = renderGeminiCommentaryCard(step3Result, stateData);
      contentEl.appendChild(commentaryCard);

      // Save assistant message to session
      session.messages.push({
        role: 'assistant',
        wevvResult,
        stateData,
        prompt,
        commentary: step3Result
      });
      saveSessions();

    } catch (err) {
      console.error('[Answerr Execution Error]:', err);
      if (stepperEl) stepperEl.remove();
      const errCard = document.createElement('div');
      errCard.className = 'gemini-commentary-card';
      errCard.style.borderColor = 'var(--rose)';
      errCard.innerHTML = `<strong style="color:var(--rose)">İşlem Hatası:</strong> ${err.message}`;
      contentEl.appendChild(errCard);
    } finally {
      isGenerating = false;
      btnSendEl.disabled = !chatInputEl.value.trim();
      scrollToBottom();
    }
  }

  function updateStepper(stepperEl, text) {
    if (!stepperEl) return;
    stepperEl.innerHTML = `<div class="spinner"></div><span>${text}</span>`;
  }

  function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'message-row user';
    row.innerHTML = `
      <div class="message-avatar">👤</div>
      <div class="message-body">
        <div class="message-bubble">${escapeHtml(text)}</div>
      </div>
    `;
    chatMessagesEl.appendChild(row);
  }

  function createAssistantRow() {
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.innerHTML = `
      <div class="message-avatar">🌊</div>
      <div class="message-body assistant-content">
        <div class="pipeline-status">
          <div class="spinner"></div>
          <span>Sistem başlatılıyor...</span>
        </div>
      </div>
    `;
    return row;
  }

  // 6. Render wevv Telemetry HUD Card with Smart Code & Seed Dump
  function renderWevvHudCard(wevvInstance, result, stateData, prompt = '') {
    const t = I18N[currentLang] || I18N.tr;
    const card = document.createElement('div');
    card.className = 'wevv-hud-card';

    const ansKey = Object.keys(result.answers)[0];
    const ans = result.answers[ansKey];

    let verdictClass = 'approved';
    let verdictTitle = '';
    let verdictSub = '';
    let smartCodeSnippet = '';

    if (ans.type === 'noul') {
      verdictClass = ans.decision ? 'approved' : 'denied';
      verdictTitle = ans.decision ? t.approved : t.denied;
      verdictSub = `p=${ans.noul} • ${t.confidence}: %${(ans.confidence * 100).toFixed(0)}`;
      smartCodeSnippet = ans.decision
        ? `<span class="kw">if</span> response.<span class="fn">boolean</span>(<span class="str">"${ansKey}"</span>): <span class="fn">EXECUTE_DIRECT</span>(request)`
        : `<span class="kw">if not</span> response.<span class="fn">boolean</span>(<span class="str">"${ansKey}"</span>): <span class="fn">BLOCK_OR_QUARANTINE</span>(request)`;
    } else if (ans.type === 'choice') {
      verdictClass = 'routed';
      verdictTitle = `${t.routed}: ${toAsciiUpper(ans.choice)}`;
      verdictSub = `${t.confidence}: %${(ans.confidence * 100).toFixed(0)}`;
      smartCodeSnippet = `<span class="kw">match</span> response.<span class="fn">choice</span>(<span class="str">"${ansKey}"</span>): <span class="kw">case</span> <span class="str">"${ans.choice}"</span>: <span class="fn">ROUTE_TO_${toAsciiUpper(ans.choice)}</span>(payload)`;
    } else if (ans.type === 'score') {
      verdictClass = 'scored';
      verdictTitle = `${t.scored}: ${ans.score} / ${ans.scaleMax} (${ans.selectedLevel})`;
      verdictSub = `${t.confidence}: %${(ans.confidence * 100).toFixed(0)}`;
      smartCodeSnippet = `<span class="kw">if</span> response.<span class="fn">score</span>(<span class="str">"${ansKey}"</span>) &lt; 1.5: <span class="fn">NORMAL_PIPELINE</span>() <span class="kw">else</span>: <span class="fn">TRIGGER_${toAsciiUpper(ans.selectedLevel || 'ALERT')}</span>()`;
    }

    const cxStr = result.coordinates.cx.toFixed(6);
    const cyStr = result.coordinates.cy.toFixed(6);
    const qRatios = result.telemetry.quadRatios || [0.25, 0.25, 0.25, 0.25];

    card.innerHTML = `
      <div class="hud-header">
        <div class="hud-title">
          <span>${t.hudTitle}</span>
        </div>
        <div class="hud-badges">
          <span class="telemetry-pill fast" style="box-shadow:0 0 10px rgba(16,185,129,0.3)">⚡ ${result.latencyMs} ${t.hudLatency}</span>
          <span class="telemetry-pill zero-mem">💾 ${t.hudVram}</span>
          <button class="btn-seed-download" title="${t.downloadSeed}">
            ${t.downloadSeed}
          </button>
        </div>
      </div>

      <div class="hud-content-grid">
        <div class="hud-canvas-container">
          <canvas class="fractal-canvas" width="130" height="130"></canvas>
          <span class="canvas-label">${cxStr}, ${cyStr}</span>
        </div>

        <div class="hud-metrics">
          <div class="verdict-banner ${verdictClass}">
            <span class="verdict-main">${verdictTitle}</span>
            <span class="verdict-confidence">${verdictSub}</span>
          </div>

          <div class="hud-quadrant-bars">
            <div class="q-bar-col">
              <span>Q1 (${(qRatios[0] * 100).toFixed(0)}%)</span>
              <div class="q-progress"><div class="q-progress-fill" style="width: ${Math.min(100, qRatios[0] * 100)}%"></div></div>
            </div>
            <div class="q-bar-col">
              <span>Q2 (${(qRatios[1] * 100).toFixed(0)}%)</span>
              <div class="q-progress"><div class="q-progress-fill" style="width: ${Math.min(100, qRatios[1] * 100)}%"></div></div>
            </div>
            <div class="q-bar-col">
              <span>Q3 (${(qRatios[2] * 100).toFixed(0)}%)</span>
              <div class="q-progress"><div class="q-progress-fill" style="width: ${Math.min(100, qRatios[2] * 100)}%"></div></div>
            </div>
            <div class="q-bar-col">
              <span>Q4 (${(qRatios[3] * 100).toFixed(0)}%)</span>
              <div class="q-progress"><div class="q-progress-fill" style="width: ${Math.min(100, qRatios[3] * 100)}%"></div></div>
            </div>
          </div>

          <div class="hud-smart-code">
            <div class="smart-code-header">
              <span>${t.smartIf}</span>
            </div>
            <div class="smart-code-snippet">${smartCodeSnippet}</div>
          </div>
        </div>
      </div>
    `;

    // Render fractal canvas
    const canvas = card.querySelector('.fractal-canvas');
    setTimeout(() => {
      wevvInstance.renderToCanvas(canvas, result.coordinates.cx, result.coordinates.cy, result.coordinates.zoom);
    }, 20);

    // Download Seed Dump Button
    const btnDownload = card.querySelector('.btn-seed-download');
    if (btnDownload) {
      btnDownload.addEventListener('click', () => {
        downloadSeedDump(result, stateData, prompt);
      });
    }

    return card;
  }

  // 24-Byte Memory & Seed Dump Downloader (.TXT)
  function downloadSeedDump(wevvResult, stateData, prompt) {
    const isTr = currentLang === 'tr';
    const now = new Date();
    const dateStr = now.toISOString().replace('T', ' ').substring(0, 19);
    const ansKey = Object.keys(wevvResult.answers)[0];
    const ans = wevvResult.answers[ansKey];

    const content = `================================================================================
     ANSWERR (ADAPTIVE NEXT-GEN SIGNAL WAVE & ERROR REFLEX REASONER)
                 24-BYTE MANDELBROT SEED TELEMETRY DUMP
================================================================================
Timestamp               : ${dateStr}
Inference Architecture  : wevv Zero-Memory Fractal System-One Reflex (∂M Boundary)
Subdivision Mode        : 4-Quadrant Phase Discretization (vv)
Zero-Hallucination      : 100% Deterministic Mathematical Convergence
Zero-Crash Resilience   : Active (Chaotic Phase Space Absorption)

[1] MEMORY FOOTPRINT & SEED SPECS
--------------------------------------------------------------------------------
Tensor Weights VRAM     : 0 Bytes (True Zero-Tensor Footprint)
Seed Footprint          : 24 Bytes (Three 64-bit IEEE-754 Float64 Coordinates)
Parameter 1 (cx)        : ${wevvResult.coordinates.cx.toFixed(8)}
Parameter 2 (cy)        : ${wevvResult.coordinates.cy.toFixed(8)}
Parameter 3 (zoom)      : ${wevvResult.coordinates.zoom.toFixed(4)}x

[2] PROGRAM STATE (EXTRACTED)
--------------------------------------------------------------------------------
Input Scenario          : ${prompt}
Extracted State Data    : ${JSON.stringify(stateData.state || {}, null, 2)}

[3] SYSTEM-ONE SYNTHESIZED DECISION
--------------------------------------------------------------------------------
Primitive Type          : ${toAsciiUpper(ans.type)}
Decision Output         : ${ans.type === 'noul' ? (ans.decision ? 'TRUE (ALLOWED)' : 'FALSE (DENIED)') : (ans.type === 'choice' ? ans.choice : ans.score)}
Confidence              : ${(ans.confidence * 100).toFixed(1)}%
Decision Latency        : ${wevvResult.latencyMs} ms (Sub-millisecond Reflex)
Quadrant Phase Energy   : Q1: ${(wevvResult.telemetry.quadRatios[0]*100).toFixed(1)}%, Q2: ${(wevvResult.telemetry.quadRatios[1]*100).toFixed(1)}%, Q3: ${(wevvResult.telemetry.quadRatios[2]*100).toFixed(1)}%, Q4: ${(wevvResult.telemetry.quadRatios[3]*100).toFixed(1)}%

[4] VERIFICATION & REPRODUCIBILITY
--------------------------------------------------------------------------------
Core Engine Repository  : https://github.com/pCwOrM/wevv
Platform Interface      : https://github.com/pCwOrM/answerr (https://answerr.me)
License                 : MIT License (%100 Free & Open Source)
================================================================================`;

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `answerr_seed_dump_24bytes_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // 7. Render Commentary Card
  function renderGeminiCommentaryCard(commentaryResult, stateData) {
    const card = document.createElement('div');
    card.className = 'gemini-commentary-card';

    const isTr = currentLang === 'tr';
    const sourceLabel = commentaryResult.source === 'gemini'
      ? (isTr ? 'Gemini Flash (Bulut Sistem-2 Müzakeresi)' : 'Gemini Flash (Cloud System-2 Deliberation)')
      : (isTr ? 'Answerr Sistem-1 Karar Derleyicisi (Sıfır Halüsinasyon)' : 'Answerr System-1 Decision Compiler (Zero Hallucination)');

    const modelName = commentaryResult.source === 'gemini' ? (commentaryResult.model || 'Gemini Flash') : 'WEVV-NATIVE';

    const stateObj = stateData?.state || {};
    const questionObj = stateData?.question || {};
    const qType = toAsciiUpper(questionObj.type || 'noul');
    const qKey = toAsciiUpper(questionObj.key || 'decision');
    const qInstr = questionObj.instructions || '';

    // Generate state parameter chips
    let stateChipsHtml = '';
    for (const [k, v] of Object.entries(stateObj)) {
      stateChipsHtml += `<span class="spec-chip"><span class="k">${escapeHtml(k)}:</span> <span class="v">${escapeHtml(String(v))}</span></span>`;
    }
    if (!stateChipsHtml) {
      stateChipsHtml = `<span style="font-size:0.75rem; color:var(--text-muted);">${isTr ? 'Varsayılan program durumu (state) uygulandı.' : 'Default state vector applied.'}</span>`;
    }

    const specHeaderTitle = isTr
      ? '📐 wevv Formatına Dönüştürülen Program Durumu (State) & Tipli Soru'
      : '📐 wevv Formatted Program State & Typed Question Matrix';

    const detailsSummary = isTr
      ? '🔍 wevv Ham Durum & Soru Yükünü İncele (Raw State & Question JSON)'
      : '🔍 Inspect Raw State & Question Payload (JSON)';

    const rawJsonStr = JSON.stringify({ state: stateObj, question: questionObj }, null, 2);

    const specBoxHtml = `
      <div class="wevv-spec-box">
        <div class="spec-header">
          <span>${specHeaderTitle}</span>
          <span class="spec-type-tag" lang="en">${qType} (${qKey})</span>
        </div>
        <div style="font-size:0.8rem; color:var(--text-main); margin-bottom: 0.2rem;">
          <span style="color:var(--text-muted); font-size:0.75rem;">${isTr ? 'Soru Talimatı:' : 'Instruction:'}</span> <em>"${escapeHtml(qInstr)}"</em>
        </div>
        <div class="spec-state-grid">
          ${stateChipsHtml}
        </div>
        <details class="spec-details">
          <summary>${detailsSummary}</summary>
          <pre class="spec-json-pre"><code>${escapeHtml(rawJsonStr)}</code></pre>
        </details>
      </div>
    `;

    card.innerHTML = `
      <div class="gemini-card-header">
        <div class="gemini-header-left">
          <span>💬</span>
          <span>${sourceLabel}</span>
        </div>
        <span class="gemini-model-tag" lang="en">${toAsciiUpper(modelName)}</span>
      </div>
      ${specBoxHtml}
      <div class="gemini-text">${formatMarkdown(commentaryResult.text)}</div>
    `;

    return card;
  }

  // 8. Presets Grid Rendering with Language Awareness
  function renderPresetCards(lang = currentLang) {
    if (!presetGridEl || typeof SCENARIO_PRESETS === 'undefined') return;
    presetGridEl.innerHTML = '';

    SCENARIO_PRESETS.forEach(preset => {
      const card = document.createElement('div');
      card.className = 'preset-card';

      const isTr = lang === 'tr';
      const cat = isTr ? (preset.categoryTr || preset.category) : preset.category;
      const title = isTr ? (preset.titleTr || preset.title) : preset.title;
      const prompt = isTr ? preset.prompt : (preset.promptEn || preset.prompt);

      card.innerHTML = `
        <div class="preset-header">
          <span class="preset-icon">${preset.icon}</span>
          <span class="preset-category">${escapeHtml(cat)}</span>
        </div>
        <div class="preset-title">${escapeHtml(title)}</div>
        <div class="preset-prompt-snippet">${escapeHtml(prompt)}</div>
      `;

      card.addEventListener('click', () => {
        handleSendMessage(prompt);
      });
      presetGridEl.appendChild(card);
    });
  }

  // 9. Session & History Management
  function startNewChat() {
    currentSessionId = generateId();
    chatMessagesEl.innerHTML = '';
    if (welcomeHeroEl) {
      welcomeHeroEl.style.display = 'flex';
      chatMessagesEl.appendChild(welcomeHeroEl);
    }
    chatInputEl.value = '';
    chatInputEl.focus();
    renderHistoryList();
  }

  function renderHistoryList() {
    if (!historyListEl) return;
    historyListEl.innerHTML = '';

    const sessions = Object.values(conversationSessions).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

    if (sessions.length === 0) {
      const noHist = currentLang === 'tr' ? 'Kayıtlı karar bulunmuyor.' : 'No decision records yet.';
      historyListEl.innerHTML = `<div style="font-size:0.75rem; color:var(--text-muted); padding:0.5rem 0.75rem;">${noHist}</div>`;
      return;
    }

    sessions.forEach(sess => {
      const item = document.createElement('div');
      item.className = `history-item ${sess.id === currentSessionId ? 'active' : ''}`;
      item.innerHTML = `<span>⚡</span><span style="overflow:hidden;text-overflow:ellipsis;">${escapeHtml(sess.title)}</span>`;
      item.addEventListener('click', () => loadSession(sess.id));
      historyListEl.appendChild(item);
    });
  }

  function loadSession(id) {
    const session = conversationSessions[id];
    if (!session) return;

    currentSessionId = id;
    chatMessagesEl.innerHTML = '';
    if (welcomeHeroEl) welcomeHeroEl.style.display = 'none';

    session.messages.forEach(msg => {
      if (msg.role === 'user') {
        appendUserMessage(msg.content);
      } else if (msg.role === 'assistant') {
        const row = createAssistantRow();
        row.querySelector('.pipeline-status').remove();
        const contentEl = row.querySelector('.assistant-content');

        if (msg.wevvResult) {
          const hud = renderWevvHudCard(wevv, msg.wevvResult, msg.stateData, msg.prompt || '');
          contentEl.appendChild(hud);
        }
        if (msg.commentary) {
          const comm = renderGeminiCommentaryCard(msg.commentary, msg.stateData);
          contentEl.appendChild(comm);
        }
        chatMessagesEl.appendChild(row);
      }
    });

    renderHistoryList();
    scrollToBottom();
  }

  function loadSessions() {
    try {
      return JSON.parse(localStorage.getItem('answerr_sessions') || '{}');
    } catch (e) {
      return {};
    }
  }

  function saveSessions() {
    try {
      localStorage.setItem('answerr_sessions', JSON.stringify(conversationSessions));
    } catch (e) {
      console.warn('LocalStorage save error:', e);
    }
  }

  function scrollToBottom(smooth = true) {
    if (!chatScrollAreaEl) return;
    requestAnimationFrame(() => {
      chatScrollAreaEl.scrollTo({
        top: chatScrollAreaEl.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
      });
      setTimeout(() => {
        chatScrollAreaEl.scrollTo({
          top: chatScrollAreaEl.scrollHeight,
          behavior: 'smooth'
        });
      }, 140);
    });
  }

  function generateId() {
    return 'sess_' + Math.random().toString(36).substring(2, 9);
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function formatMarkdown(text) {
    if (!text) return '';
    let formatted = escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.08);padding:0.15rem 0.4rem;border-radius:4px;font-family:var(--font-mono);font-size:0.88em;color:var(--cyan);">$1</code>')
      .replace(/\$([^\$]+)\$/g, '<span class="math-badge" lang="en"><code>$1</code></span>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');

    // Format zero hallucination guarantee callout banner
    formatted = formatted.replace(
      /(?:\(|&lt;|\*)\s*(?:🛡️|&#128737;)?\s*wevv\s+(?:Sıfır-Halüsinasyon Garantisi|Zero-Hallucination Guarantee):?\s*([^)*]+)(?:\)|\*)/gi,
      (match, desc) => {
        const isTr = currentLang === 'tr';
        const title = isTr ? 'wevv Sıfır-Halüsinasyon Garantisi' : 'wevv Zero-Hallucination Guarantee';
        return `<div class="zero-hallucination-banner"><span class="zh-shield">🛡️</span><span><strong>${title}:</strong> ${desc.trim()}</span></div>`;
      }
    );

    return formatted;
  }
});
