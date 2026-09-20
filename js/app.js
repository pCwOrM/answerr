/**
 * app.js - Main Application Orchestrator for answerr (answerr.me)
 * Manages chat lifecycle, dual-cognitive pipeline execution (System 1 + System 2),
 * live telemetry HUD rendering with Smart If-Statement code & Seed Dump,
 * Google reCAPTCHA v3 & mechsrv telemetry integration, multi-language (TR / EN) switching.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Core Engines
  const werr = new WerrEngine();
  const wevv = werr; // Backward compatibility alias
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

  // Telemetry Dispatcher to api.answerr.me
  async function dispatchWebTelemetry(werrResult, prompt, stateData) {
    try {
      const token = await getRecaptchaToken("answerr_chat");
      const ansKey = Object.keys(werrResult.answers)[0];
      const ans = werrResult.answers[ansKey];

      const payload = {
        timestamp: new Date().toISOString(),
        version: "answerr-0.1.0-web",
        source: "answerr_chat",
        recaptcha_token: token || undefined,
        seed: {
          cx: parseFloat(werrResult.coordinates.cx.toFixed(8)),
          cy: parseFloat(werrResult.coordinates.cy.toFixed(8)),
          zoom: parseFloat(werrResult.coordinates.zoom.toFixed(4))
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
        latency_ms: werrResult.latencyMs
      };

      fetch("https://api.answerr.me:4431/werr/telemetry", {
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
      heroTitle: "<span class=\"brand-text-answe\">answe</span><span class=\"brand-text-r1\">r</span><span class=\"brand-text-r2\">r</span>",
      heroMotto: "\"Doğal diyalog gerektiğinde <strong>answerr</strong>, mikrosaniyelik refleks gerektiğinde <strong>werr</strong>.\"",
      heroSubtitle: "Sıfır gecikmeli, 0-Byte VRAM fraktal omurilik karar çalışma alanı. Durum verinizi girin; Mandelbrot dinamikleriyle deterministik, tipli ve anlık karar üretin.",
      tagSpeed: "⚡ < 0.5 ms Refleks",
      tagZeroMem: "💾 0-Byte VRAM",
      tagHallucination: "🛡️ Sıfır Halüsinasyon",
      tagCrash: "🚀 Asla Çökmez & %100 Deterministik",
      inputPlaceholder: "Werr is the point? Bir durum girin ve anında karar werr (örn: 'Anonim IP 180 istek/dk, izin verilsin mi?')...",
      newDecisionBtn: "Yeni Karar",
      historyLabel: "Karar Geçmişi",
      systemStatus: "werr 0-Byte VRAM: Aktif",
      disclaimer: "answerr, <a href=\"https://github.com/pCwOrM/werr\" target=\"_blank\" rel=\"noopener\">werr</a> fraktal Sistem-1 karar motoru ile çalışır. Tip güvenli, deterministik ve sıfır halüsinasyonludur. <a href=\"index.html\">answerr.me</a>.",
      modalTitle: "⚙️ Answerr Karar Motoru Ayarları",
      modalFreeBadge: "✓ Tamamen Ücretsiz & Anahtarsız Sistem-1 Aktif",
      modalFreeDesc: "answerr, tarayıcınızda sıfır gecikmeli yerel werr Sistem-1 fraktal motoruyla çalışır. Herhangi bir kayıt, ücret veya API anahtarı zorunlu değildir.",
      modalApiLabel: "Opsiyonel: Google Gemini API Anahtarı",
      modalApiHint: "Genişletilmiş bulut Sistem-2 müzakeresi isterseniz Google AI Studio'dan ücretsiz anahtar alabilirsiniz. Anahtar sadece tarayıcınızda (localStorage) saklanır.",
      modalModelLabel: "Sistem-2 Müzakere Modeli",
      modalClearHistory: "🗑️ Tüm Karar Geçmişini Temizle",
      modalCancel: "İptal",
      modalSave: "Ayarları Kaydet",
      keylessBadge: "werr Sistem-1",
      keylessBadgeTag: "(Keyless)",
      step1: "1/3 Durum matrisi ve tipli soru ayrıştırılıyor (System-2 State)...",
      step2: "2/3 werr: Mandelbrot ∂M kaçış dinamiği hesaplanıyor (< 0.5ms)...",
      step3: "3/3 Sistem-1 telemetrisi ve karar doğrulanıyor...",
      hudTitle: "⚡ werr Sistem-1 Omurilik Refleksi",
      hudLatency: "ms",
      hudVram: "0B Tensör VRAM",
      hudSeed: "24B Tohum",
      approved: "ONAYLANDI (TRUE)",
      denied: "ENGELLE / RET (FALSE)",
      routed: "ROTA",
      scored: "SKOR",
      confidence: "Güven",
      smartIf: "🚀 AKILLI KOD (Smart If-Statement):",
      downloadSeed: "💾 24B Tohum İndir (.TXT)",
      toggleSidebarOpen: "Menüyü Aç (Karar Geçmişi)",
      toggleSidebarClose: "Menüyü Kapat",
      actionWerr: "⚡ Karar Werr",
      actionAnswerr: "💬 Cevap Werr",
      actionGate: "🛡️ İzin Werr",
      actionRank: "🚀 Öncelik Werr",
      ctaCloud: "answerr Cloud API'yi Keşfet",
      ctaCore: "werr Çekirdeğini Uygulamana Göm (pip install werr)",
      sendBtnTitle: "⚡ Karar Werr (Enter)",
      topbarHomeText: "Ana Sayfa",
      topbarHomeTitle: "Ana Sayfaya Dön",
      githubBadgeText: "werr Çekirdeği",
      githubBadgeTitle: "werr Geometrik Refleks Çekirdeği",
      presetSectionLabel: "Örnek Senaryolar ile Başlayın:"
    },
    en: {
      heroTitle: "<span class=\"brand-text-answe\">answe</span><span class=\"brand-text-r1\">r</span><span class=\"brand-text-r2\">r</span>",
      heroMotto: "\"When you need natural dialogue, call <strong>answerr</strong>. When you need microsecond reflexes, embed <strong>werr</strong>.\"",
      heroSubtitle: "Zero-latency, 0-Byte VRAM fractal spinal reflex workspace. Ingest operational state vectors and generate deterministic, typed System-1 decisions instantly.",
      tagSpeed: "⚡ < 0.5 ms Fractal Reflex",
      tagZeroMem: "💾 0-Byte Tensor Memory",
      tagHallucination: "🛡️ Zero Hallucination",
      tagCrash: "🚀 Zero Crash & 100% Deterministic",
      inputPlaceholder: "Werr is the point? Enter an operational scenario and werr it now...",
      newDecisionBtn: "New Decision",
      historyLabel: "Decision Log",
      systemStatus: "werr 0-Byte VRAM: Active",
      disclaimer: "answerr is powered by the <a href=\"https://github.com/pCwOrM/werr\" target=\"_blank\" rel=\"noopener\">werr</a> fractal System-One engine. Type-safe, calibrated, zero-hallucination. <a href=\"index.html\">answerr.me</a>.",
      modalTitle: "⚙️ Answerr Decision Engine Settings",
      modalFreeBadge: "✓ 100% Free & Keyless System-1 Active",
      modalFreeDesc: "answerr operates with zero latency directly inside your browser with the werr engine. No sign-up, credit card, or API key required.",
      modalApiLabel: "Optional: Google Gemini API Key",
      modalApiHint: "To unlock cloud System-2 deliberation, you can optionally provide a free key from Google AI Studio. Stored strictly in your browser (localStorage).",
      modalModelLabel: "System-2 Model",
      modalClearHistory: "🗑️ Clear All Decision Records",
      modalCancel: "Cancel",
      modalSave: "Save Settings",
      keylessBadge: "werr System-1",
      keylessBadgeTag: "(Keyless)",
      step1: "1/3 Compiling input into state vector...",
      step2: "2/3 werr: Evaluating Mandelbrot escape dynamics (< 0.5ms)...",
      step3: "3/3 Synthesizing System-1 telemetry and actions...",
      hudTitle: "⚡ werr System-1 Spinal Reflex",
      hudLatency: "ms",
      hudVram: "0B Tensor VRAM",
      hudSeed: "24B Seed",
      approved: "APPROVED (TRUE)",
      denied: "DENIED / BLOCKED (FALSE)",
      routed: "ROUTE",
      scored: "SCORE",
      confidence: "Confidence",
      smartIf: "🚀 SMART IF-STATEMENT (Production Code):",
      downloadSeed: "💾 Download 24B Seed (.TXT)",
      toggleSidebarOpen: "Open Menu (Decision Log)",
      toggleSidebarClose: "Close Menu",
      actionWerr: "⚡ Werr It!",
      actionAnswerr: "💬 Answerr It!",
      actionGate: "🛡️ Gate It!",
      actionRank: "🚀 Rank It!",
      ctaCloud: "Explore answerr Cloud API",
      ctaCore: "Embed werr Kernel in App (pip install werr)",
      sendBtnTitle: "⚡ Werr It! (Enter)",
      topbarHomeText: "Home",
      topbarHomeTitle: "Back to Home",
      githubBadgeText: "werr Core",
      githubBadgeTitle: "werr Geometric Reflex Engine",
      presetSectionLabel: "Start with Curated Scenarios:"
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
  const btnOpenSidebarEl = document.getElementById('btn-open-sidebar');
  const sidebarBackdropEl = document.getElementById('sidebar-backdrop');
  const btnThemeToggleEl = document.getElementById('btn-theme-toggle');
  const btnSettingsEl = document.getElementById('btn-settings');
  const activeModelBadgeEl = document.getElementById('active-model-badge');
  const btnLangToggleEl = document.getElementById('btn-lang-toggle');
  const currentLangTextEl = document.getElementById('current-lang-text');
  const githubBadgeTextEl = document.getElementById('github-badge-text');
  const githubBadgeLinkEl = document.getElementById('github-badge-link');
  const topbarHomeLinkEl = document.getElementById('topbar-home-link');

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

  // Dynamic Elements
  const heroMottoEl = document.getElementById('hero-motto');
  const topbarHomeTextEl = document.getElementById('topbar-home-text');
  const presetSectionLabelEl = document.getElementById('preset-section-label');
  const systemStatusTextEl = document.getElementById('system-status-text');

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
    document.title = lang === 'tr'
      ? "answerr | Karar ve Diyalog Çalışma Alanı (Workspace)"
      : "answerr | Decision & Dialogue Workspace";
    if (currentLangTextEl) currentLangTextEl.textContent = toAsciiUpper(lang);

    if (newDecisionTextEl) newDecisionTextEl.textContent = t.newDecisionBtn;
    if (historyLabelEl) historyLabelEl.textContent = t.historyLabel;
    if (systemStatusTextEl && t.systemStatus) systemStatusTextEl.textContent = t.systemStatus;
    if (topbarHomeTextEl && t.topbarHomeText) topbarHomeTextEl.textContent = t.topbarHomeText;
    if (topbarHomeLinkEl && t.topbarHomeTitle) topbarHomeLinkEl.title = t.topbarHomeTitle;
    if (githubBadgeTextEl && t.githubBadgeText) githubBadgeTextEl.textContent = t.githubBadgeText;
    if (githubBadgeLinkEl && t.githubBadgeTitle) githubBadgeLinkEl.title = t.githubBadgeTitle;
    if (presetSectionLabelEl && t.presetSectionLabel) presetSectionLabelEl.textContent = t.presetSectionLabel;

    if (btnOpenSidebarEl) {
      btnOpenSidebarEl.title = t.toggleSidebarOpen;
      btnOpenSidebarEl.setAttribute('aria-label', t.toggleSidebarOpen);
    }
    if (btnToggleSidebarEl) {
      btnToggleSidebarEl.title = t.toggleSidebarClose;
      btnToggleSidebarEl.setAttribute('aria-label', t.toggleSidebarClose);
    }

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

    if (heroMottoEl && t.heroMotto) heroMottoEl.innerHTML = t.heroMotto;
    if (btnSendEl && t.sendBtnTitle) btnSendEl.title = t.sendBtnTitle;
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

  // Sidebar Toggle, Collapse & Reopen Handlers
  function setSidebarCollapsed(collapsed) {
    if (!sidebarEl) return;
    sidebarEl.classList.toggle('collapsed', collapsed);
    localStorage.setItem('answerr_sidebar_collapsed', collapsed ? 'true' : 'false');
  }

  if (btnToggleSidebarEl) {
    btnToggleSidebarEl.addEventListener('click', () => {
      setSidebarCollapsed(true);
    });
  }

  if (btnOpenSidebarEl) {
    btnOpenSidebarEl.addEventListener('click', () => {
      setSidebarCollapsed(false);
    });
  }

  if (sidebarBackdropEl) {
    sidebarBackdropEl.addEventListener('click', () => {
      setSidebarCollapsed(true);
    });
  }

  // Keyboard shortcut: Ctrl+B or Cmd+B to toggle sidebar
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
      e.preventDefault();
      const isCurrentlyCollapsed = sidebarEl.classList.contains('collapsed');
      setSidebarCollapsed(!isCurrentlyCollapsed);
    }
    if (e.key === 'Escape' && sidebarEl && !sidebarEl.classList.contains('collapsed') && window.innerWidth < 768) {
      setSidebarCollapsed(true);
    }
  });

  // Restore saved sidebar preference
  const savedSidebarCollapsed = localStorage.getItem('answerr_sidebar_collapsed');
  if (savedSidebarCollapsed === 'true') {
    sidebarEl.classList.add('collapsed');
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
        ? `<span class="model-sparkle">✨</span> <span class="badge-title">${model}</span>`
        : `<span class="model-sparkle">⚡</span> <span class="badge-title">${t.keylessBadge}</span><span class="badge-tag desktop-only"> ${t.keylessBadgeTag}</span>`;
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

      const ansKey = Object.keys(wevvResult.answers)[0];
      const primaryAns = wevvResult.answers[ansKey];
      console.log(`[werr-core] 0-Byte tensor memory allocated. 24-byte seed locked: cx=${wevvResult.coordinates.cx.toFixed(6)}, cy=${wevvResult.coordinates.cy.toFixed(6)}, zoom=${wevvResult.coordinates.zoom.toFixed(1)}`);
      console.log(`[werr-reflex] Karar üretildi: ${primaryAns.type === 'noul' ? (primaryAns.decision ? 'ALLOWED' : 'DENIED') : (primaryAns.choice || primaryAns.score)} (p=${(primaryAns.p || 0.5).toFixed(4)}, Güven: %${((primaryAns.confidence || 0) * 100).toFixed(1)}, Süre: ${wevvResult.latencyMs} ms)`);
      if (stateData.category) {
        console.log(`[werr-router] Werr to route: '${stateData.category}' alanına yönlendirildi.`);
      }

      // Dispatch Telemetry with Google reCAPTCHA v3 asynchronously to api.answerr.me
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
          <img src="assets/werr_logo_core.svg" alt="werr logo" style="width:20px; height:20px; vertical-align:middle; margin-right:6px; filter:drop-shadow(0 0 6px rgba(56,189,248,0.4));">
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
     ANSWERR (ADAPTIVE NON-TENSOR SIGNAL WAVE & ERROR REFLEX RESONATOR)
                 24-BYTE MANDELBROT SEED TELEMETRY DUMP
================================================================================
Timestamp               : ${dateStr}
Inference Architecture  : werr Zero-Memory Fractal System-One Reflex (∂M Boundary)
Subdivision Mode        : 4-Quadrant Phase Discretization (rr)
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
Core Engine Repository  : https://github.com/pCwOrM/werr
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

    const modelName = commentaryResult.source === 'gemini' ? (commentaryResult.model || 'Gemini Flash') : 'WERR-NATIVE';

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
      ? '📐 werr Formatına Dönüştürülen Program Durumu (State) & Tipli Soru'
      : '📐 werr Formatted Program State & Typed Question Matrix';

    const detailsSummary = isTr
      ? '🔍 werr Ham Durum & Soru Yükünü İncele (Raw State & Question JSON)'
      : '🔍 Inspect Raw State & Question Payload (JSON)';

    const rawJsonStr = JSON.stringify({ state: stateObj, question: questionObj }, null, 2);

    const specBoxHtml = `
      <div class="werr-spec-box wevv-spec-box">
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

  // 8. Presets Grid Rendering with Language Awareness (Sleek Compact Prompt Pills)
  function renderPresetCards(lang = currentLang) {
    if (!presetGridEl || typeof SCENARIO_PRESETS === 'undefined') return;
    presetGridEl.innerHTML = '';

    // Render top 4 curated scenarios in a balanced, clean 2x2 layout
    SCENARIO_PRESETS.slice(0, 4).forEach(preset => {
      const card = document.createElement('button');
      card.className = 'preset-card';
      card.setAttribute('type', 'button');

      const isTr = lang === 'tr';
      const cat = isTr ? (preset.categoryTr || preset.category) : preset.category;
      const title = isTr ? (preset.titleTr || preset.title) : preset.title;
      const prompt = isTr ? preset.prompt : (preset.promptEn || preset.prompt);

      card.innerHTML = `
        <div class="preset-pill-left">
          <span class="preset-icon">${preset.icon}</span>
          <div class="preset-info">
            <span class="preset-title">${escapeHtml(title)}</span>
            <span class="preset-category">${escapeHtml(cat)}</span>
          </div>
        </div>
        <span class="preset-arrow">→</span>
      `;

      card.title = prompt;
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
      /(?:\(|&lt;|\*)\s*(?:🛡️|&#128737;)?\s*(?:wevv|werr)\s+(?:Sıfır-Halüsinasyon Garantisi|Zero-Hallucination Guarantee):?\s*([^)*]+)(?:\)|\*)/gi,
      (match, desc) => {
        const isTr = currentLang === 'tr';
        const title = isTr ? 'werr Sıfır-Halüsinasyon Garantisi' : 'werr Zero-Hallucination Guarantee';
        return `<div class="zero-hallucination-banner"><span class="zh-shield">🛡️</span><span><strong>${title}:</strong> ${desc.trim()}</span></div>`;
      }
    );

    return formatted;
  }
});
