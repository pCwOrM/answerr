/**
 * app.js - Main Application Orchestrator for answerr (answerr.me)
 * Manages chat lifecycle, dual-cognitive pipeline execution (System 1 + System 2),
 * live telemetry HUD rendering, and UI interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Core Engines
  const wevv = new WevvEngine();
  const gemini = new GeminiBridge();

  // 2. DOM Elements
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

  // Settings Modal
  const settingsModalEl = document.getElementById('settings-modal');
  const btnCloseModalEl = document.getElementById('btn-close-modal');
  const btnCancelModalEl = document.getElementById('btn-cancel-modal');
  const btnSaveSettingsEl = document.getElementById('btn-save-settings');
  const inputApiKeyEl = document.getElementById('input-api-key');
  const selectModelEl = document.getElementById('select-model');
  const btnClearHistoryEl = document.getElementById('btn-clear-history');

  // 3. Application State
  let currentSessionId = generateId();
  let conversationSessions = loadSessions();
  let isGenerating = false;

  // Initialize UI
  updateModelBadge();
  renderPresetCards();
  renderHistoryList();

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

  btnSendEl.addEventListener('click', handleSendMessage);

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
      if (confirm('Tüm konuşma geçmişi silinsin mi? / Clear all conversation history?')) {
        conversationSessions = {};
        saveSessions();
        renderHistoryList();
        startNewChat();
        closeModal();
      }
    });
  }

  function updateModelBadge() {
    const hasKey = gemini.hasApiKey();
    const model = gemini.getModel();
    if (activeModelBadgeEl) {
      activeModelBadgeEl.innerHTML = hasKey
        ? `<span class="model-sparkle">✨</span> ${model}`
        : `<span class="model-sparkle">⚡</span> ${model} (Demo Keyless)`;
    }
  }

  // 4. Send Message Lifecycle
  async function handleSendMessage(presetPromptText) {
    const prompt = (presetPromptText || chatInputEl.value).trim();
    if (!prompt || isGenerating) return;

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
      // Step 1: System-2 Decomposition (Gemini / Heuristic)
      updateStepper(stepperEl, '1/3 Gemini Flash: Doğal dil durum matrisine dönüştürülüyor...');
      const step1Result = await gemini.transformPromptToWevv(prompt);

      const stateData = step1Result.data;
      const stateObj = stateData.state || {};
      const questionObj = stateData.question || {
        key: 'decision',
        type: 'noul',
        instructions: prompt
      };

      // Step 2: System-1 Instant Execution (wevv Fractal Engine)
      updateStepper(stepperEl, '2/3 wevv: Mandelbrot ∂M kaçış dinamikleri hesaplanıyor (< 2ms)...');
      
      // Artificial micro-pause for smooth cognitive visualization
      await new Promise(r => setTimeout(r, 150));

      const wevvResult = wevv.decide(stateObj, {
        [questionObj.key || 'decision']: questionObj
      });

      // Step 3: System-2 Commentary Synthesis (Gemini / Heuristic)
      updateStepper(stepperEl, '3/3 Gemini Flash: Sistem-1 telemetrisi ve aksiyon yorumlanıyor...');
      const step3Result = await gemini.interpretDecision(prompt, wevvResult, stateData);

      // Remove stepper and render rich cards
      stepperEl.remove();

      // Render wevv System-1 Telemetry HUD Card
      const hudCard = renderWevvHudCard(wevv, wevvResult, stateData);
      contentEl.appendChild(hudCard);

      // Render Gemini System-2 Commentary Card
      const commentaryCard = renderGeminiCommentaryCard(step3Result, stateData);
      contentEl.appendChild(commentaryCard);

      // Save assistant message to session
      session.messages.push({
        role: 'assistant',
        wevvResult,
        stateData,
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

  // 5. Render wevv Telemetry HUD Card
  function renderWevvHudCard(wevvInstance, result, stateData) {
    const card = document.createElement('div');
    card.className = 'wevv-hud-card';

    const ansKey = Object.keys(result.answers)[0];
    const ans = result.answers[ansKey];

    let verdictClass = 'approved';
    let verdictTitle = '';
    let verdictSub = '';

    if (ans.type === 'noul') {
      verdictClass = ans.decision ? 'approved' : 'denied';
      verdictTitle = ans.decision ? 'ONAYLANDI (TRUE)' : 'ENGELLE / RET (FALSE)';
      verdictSub = `p=${ans.noul} • Güven: %${(ans.confidence * 100).toFixed(0)}`;
    } else if (ans.type === 'choice') {
      verdictClass = 'routed';
      verdictTitle = `ROTA: ${ans.choice.toUpperCase()}`;
      verdictSub = `Olasılık Dağılımı • Güven: %${(ans.confidence * 100).toFixed(0)}`;
    } else if (ans.type === 'score') {
      verdictClass = 'scored';
      verdictTitle = `SKOR: ${ans.score} / ${ans.scaleMax} (${ans.selectedLevel})`;
      verdictSub = `Derece Dağılımı • Güven: %${(ans.confidence * 100).toFixed(0)}`;
    }

    const cxStr = result.coordinates.cx.toFixed(6);
    const cyStr = result.coordinates.cy.toFixed(6);
    const zoomStr = result.coordinates.zoom.toFixed(1);

    const qRatios = result.telemetry.quadRatios || [0.25, 0.25, 0.25, 0.25];

    card.innerHTML = `
      <div class="hud-header">
        <div class="hud-title">
          <span>🌊 wevv Sistem-1 Fraktal Refleksi</span>
        </div>
        <div class="hud-badges">
          <span class="telemetry-pill fast">⚡ ${result.latencyMs} ms</span>
          <span class="telemetry-pill zero-mem">💾 0B Tensör VRAM</span>
          <span class="telemetry-pill" title="Mandelbrot Boundary Seed Coordinates">📍 24B Tohum</span>
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
        </div>
      </div>
    `;

    // Render fractal canvas
    const canvas = card.querySelector('.fractal-canvas');
    setTimeout(() => {
      wevvInstance.renderToCanvas(canvas, result.coordinates.cx, result.coordinates.cy, result.coordinates.zoom);
    }, 20);

    return card;
  }

  // 6. Render Gemini System-2 Commentary Card
  function renderGeminiCommentaryCard(commentaryResult, stateData) {
    const card = document.createElement('div');
    card.className = 'gemini-commentary-card';

    const modelName = commentaryResult.model || 'Gemini Flash';
    const sourceLabel = commentaryResult.source === 'gemini' ? 'Gemini 2.5 Flash (Sistem-2)' : 'Answerr Derleyici (Demo Modu)';

    card.innerHTML = `
      <div class="gemini-card-header">
        <span>💬 ${sourceLabel}</span>
        <span class="gemini-model-tag">${modelName}</span>
      </div>
      <div class="gemini-text">${formatMarkdown(commentaryResult.text)}</div>
    `;

    return card;
  }

  // 7. Presets Grid Rendering
  function renderPresetCards() {
    if (!presetGridEl || typeof SCENARIO_PRESETS === 'undefined') return;
    presetGridEl.innerHTML = '';

    SCENARIO_PRESETS.forEach(preset => {
      const card = document.createElement('div');
      card.className = 'preset-card';
      card.innerHTML = `
        <div class="preset-header">
          <span class="preset-icon">${preset.icon}</span>
          <span class="preset-category">${preset.categoryTr || preset.category}</span>
        </div>
        <div class="preset-title">${preset.titleTr || preset.title}</div>
        <div class="preset-prompt-snippet">${preset.prompt}</div>
      `;
      card.addEventListener('click', () => {
        handleSendMessage(preset.prompt);
      });
      presetGridEl.appendChild(card);
    });
  }

  // 8. Session & History Management
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
      historyListEl.innerHTML = '<div style="font-size:0.75rem; color:var(--text-muted); padding:0.5rem 0.75rem;">Geçmiş bulunmuyor.</div>';
      return;
    }

    sessions.forEach(sess => {
      const item = document.createElement('div');
      item.className = `history-item ${sess.id === currentSessionId ? 'active' : ''}`;
      item.innerHTML = `<span>💬</span><span style="overflow:hidden;text-overflow:ellipsis;">${escapeHtml(sess.title)}</span>`;
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
          const hud = renderWevvHudCard(wevv, msg.wevvResult, msg.stateData);
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

  function scrollToBottom() {
    chatScrollAreaEl.scrollTop = chatScrollAreaEl.scrollHeight;
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
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
    return formatted;
  }
});
