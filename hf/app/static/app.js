/* ============================================================
   Agent Generator Wizard – Client-Side Application
   4-step wizard: Home → Plan → Configure → Result
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  checkInferenceStatus();
  initStep1();
  initStep2();
  initStep3();
  initStep4();
  initGlobalShortcuts();
});

/* ----------------------------------------------------------
   Inference Status Indicator (all pages)
   ---------------------------------------------------------- */
function checkInferenceStatus() {
  fetch('/api/inference-status')
    .then(r => r.json())
    .then(data => {
      const dot = document.getElementById('statusDot');
      if (dot) {
        dot.style.background = data.available ? '#22c55e' : '#3f3f50';
        dot.style.boxShadow = data.available ? '0 0 8px rgba(34,197,94,0.5)' : 'none';
      }
    })
    .catch(() => {});
}

/* ----------------------------------------------------------
   Global Keyboard Shortcuts
   ---------------------------------------------------------- */
function initGlobalShortcuts() {
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      const form = document.querySelector('form');
      if (form) form.requestSubmit();
    }
  });
}

/* ----------------------------------------------------------
   Step 1 – Home (Prompt Input)
   ---------------------------------------------------------- */
function initStep1() {
  const textarea = document.getElementById('promptInput');
  const charCount = document.getElementById('charCount');
  const submitBtn = document.getElementById('submitBtn');
  if (!textarea || !charCount || !submitBtn) return;

  function updateCharCount() {
    const len = textarea.value.length;
    charCount.textContent = len + ' / 2000';

    // Yellow warning above 1800
    if (len > 1800) {
      charCount.classList.add('text-yellow-500');
    } else {
      charCount.classList.remove('text-yellow-500');
    }

    // Minimum 10 chars to enable submit
    const valid = len >= 10;
    submitBtn.disabled = !valid;
    submitBtn.classList.toggle('opacity-50', !valid);
    submitBtn.classList.toggle('cursor-not-allowed', !valid);
    submitBtn.classList.toggle('pointer-events-none', !valid);
  }

  textarea.addEventListener('input', updateCharCount);
  updateCharCount();

  // Example chips populate the textarea
  document.querySelectorAll('.example-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      textarea.value = btn.dataset.prompt || btn.textContent.trim();
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
      textarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
      textarea.focus();
    });
  });

  // Form submit loading state
  const form = textarea.closest('form');
  if (form) {
    form.addEventListener('submit', () => {
      setLoading(submitBtn, 'Planning...');
    });
  }
}

/* ----------------------------------------------------------
   Step 2 – Plan (Agents & Tasks Editor)
   ---------------------------------------------------------- */
function initStep2() {
  const planForm = document.getElementById('planForm');
  const addAgentBtn = document.getElementById('addAgentBtn');
  const addTaskBtn = document.getElementById('addTaskBtn');
  const continueBtn = document.getElementById('continueBtn');
  if (!planForm) return;

  let agentCounter = document.querySelectorAll('.agent-card').length;
  let taskCounter = document.querySelectorAll('.task-card').length;

  // Delegated click handler for remove buttons
  planForm.addEventListener('click', (e) => {
    const removeAgent = e.target.closest('.remove-agent-btn');
    if (removeAgent) {
      removeAgent.closest('.agent-card').remove();
      refreshAgentDropdowns();
      return;
    }
    const removeTask = e.target.closest('.remove-task-btn');
    if (removeTask) {
      removeTask.closest('.task-card').remove();
    }
  });

  // Add new agent card
  if (addAgentBtn) {
    addAgentBtn.addEventListener('click', () => {
      agentCounter++;
      const container = document.getElementById('agentsContainer') || addAgentBtn.parentElement;
      const card = document.createElement('div');
      card.className = 'agent-card border rounded-lg p-4 mb-4';
      card.innerHTML =
        '<div class="flex justify-between items-center mb-2">' +
          '<h3 class="font-semibold">New Agent</h3>' +
          '<button type="button" class="remove-agent-btn text-red-500 hover:text-red-700 text-sm">Remove Agent</button>' +
        '</div>' +
        '<label class="block mb-1 text-sm font-medium">Role</label>' +
        '<input type="text" class="agent-role w-full border rounded px-3 py-2 mb-2" placeholder="Agent role" />' +
        '<label class="block mb-1 text-sm font-medium">Goal</label>' +
        '<input type="text" class="agent-goal w-full border rounded px-3 py-2 mb-2" placeholder="Agent goal" />' +
        '<label class="block mb-1 text-sm font-medium">Backstory</label>' +
        '<textarea class="agent-backstory w-full border rounded px-3 py-2 mb-2" rows="2" placeholder="Agent backstory"></textarea>';
      container.appendChild(card);
      refreshAgentDropdowns();
    });
  }

  // Add new task card
  if (addTaskBtn) {
    addTaskBtn.addEventListener('click', () => {
      taskCounter++;
      const container = document.getElementById('tasksContainer') || addTaskBtn.parentElement;
      const card = document.createElement('div');
      card.className = 'task-card border rounded-lg p-4 mb-4';
      card.innerHTML =
        '<div class="flex justify-between items-center mb-2">' +
          '<h3 class="font-semibold">New Task</h3>' +
          '<button type="button" class="remove-task-btn text-red-500 hover:text-red-700 text-sm">Remove Task</button>' +
        '</div>' +
        '<label class="block mb-1 text-sm font-medium">Description</label>' +
        '<textarea class="task-description w-full border rounded px-3 py-2 mb-2" rows="2" placeholder="Task description"></textarea>' +
        '<label class="block mb-1 text-sm font-medium">Expected Output</label>' +
        '<input type="text" class="task-expected-output w-full border rounded px-3 py-2 mb-2" placeholder="Expected output" />' +
        '<label class="block mb-1 text-sm font-medium">Assigned Agent</label>' +
        '<select class="task-agent-select w-full border rounded px-3 py-2 mb-2"></select>';
      container.appendChild(card);
      refreshAgentDropdowns();
    });
  }

  // Refresh dropdowns when agent roles change
  planForm.addEventListener('input', (e) => {
    if (e.target.classList.contains('agent-role')) {
      refreshAgentDropdowns();
    }
  });

  // Intercept submit: serialize plan to hidden JSON field
  planForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const agents = collectAgents();
    const tasks = collectTasks();
    const plan = { agents, tasks };
    const hidden = document.getElementById('planJsonInput');
    if (hidden) hidden.value = JSON.stringify(plan);
    if (continueBtn) setLoading(continueBtn, 'Continuing...');
    planForm.submit();
  });
}

function slugify(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
}

function collectAgents() {
  const agents = [];
  document.querySelectorAll('.agent-card').forEach(card => {
    const role = (card.querySelector('.agent-role') || {}).value || '';
    const goal = (card.querySelector('.agent-goal') || {}).value || '';
    const backstory = (card.querySelector('.agent-backstory') || {}).value || '';
    agents.push({
      id: slugify(role) || 'agent_' + agents.length,
      role, goal, backstory
    });
  });
  return agents;
}

function collectTasks() {
  const tasks = [];
  document.querySelectorAll('.task-card').forEach(card => {
    const description = (card.querySelector('.task-description') || {}).value || '';
    const expected_output = (card.querySelector('.task-expected-output') || {}).value || '';
    const agent = (card.querySelector('.task-agent-select') || {}).value || '';
    tasks.push({ description, expected_output, agent });
  });
  return tasks;
}

function refreshAgentDropdowns() {
  const agents = collectAgents();
  document.querySelectorAll('.task-agent-select').forEach(select => {
    const current = select.value;
    select.innerHTML = agents.map(a =>
      '<option value="' + a.id + '"' +
      (a.id === current ? ' selected' : '') + '>' +
      (a.role || a.id) + '</option>'
    ).join('');
  });
}

/* ----------------------------------------------------------
   Step 3 – Configure (Framework, Mode, Tools, Options)
   ---------------------------------------------------------- */

const FILE_TREES = {
  crewai: {
    code_and_yaml: [
      'config/agents.yaml', 'config/tasks.yaml',
      'src/crew.py', 'src/main.py', 'src/tools/',
      'tests/', 'pyproject.toml', 'README.md'
    ],
    code_only: ['src/main.py', 'requirements.txt', 'README.md']
  },
  langgraph: {
    code_only: ['src/main.py', 'requirements.txt', 'README.md']
  },
  watsonx_orchestrate: {
    yaml_only: ['agent.yaml', 'README.md']
  },
  crewai_flow: {
    code_only: ['src/main.py', 'requirements.txt', 'README.md']
  },
  react: {
    code_only: ['src/main.py', 'requirements.txt', 'README.md']
  }
};

function initStep3() {
  const configForm = document.getElementById('configForm');
  if (!configForm) return;

  // Advanced options toggle
  const advancedToggle = document.getElementById('toggleAdvanced');
  const advancedPanel = document.getElementById('advancedPanel');
  if (advancedToggle && advancedPanel) {
    advancedToggle.addEventListener('click', () => {
      advancedPanel.classList.toggle('hidden');
      advancedToggle.setAttribute('aria-expanded',
        !advancedPanel.classList.contains('hidden'));
    });
  }

  // Temperature slider live display
  const tempSlider = document.getElementById('temperature');
  const tempValue = document.getElementById('temperatureValue');
  if (tempSlider && tempValue) {
    tempSlider.addEventListener('input', () => {
      tempValue.textContent = tempSlider.value;
    });
  }

  // Framework radio change
  document.querySelectorAll('.framework-radio').forEach(radio => {
    radio.addEventListener('change', () => {
      applyFrameworkConstraints(radio.value);
      const mode = getSelectedMode();
      updateFileTreePreview(radio.value, mode);
    });
  });

  // Mode radio change
  document.querySelectorAll('.mode-radio').forEach(radio => {
    radio.addEventListener('change', () => {
      const framework = getSelectedFramework();
      updateFileTreePreview(framework, radio.value);
    });
  });

  // Initialize state from current selections
  const framework = getSelectedFramework();
  const mode = getSelectedMode();
  if (framework) {
    applyFrameworkConstraints(framework);
    updateFileTreePreview(framework, mode);
  }

  // Pre-check tools that appeared in the plan
  preCheckPlanTools();

  // Form submit loading state
  configForm.addEventListener('submit', () => {
    const btn = configForm.querySelector('button[type="submit"]');
    if (btn) setLoading(btn, 'Generating...');
  });
}

function getSelectedFramework() {
  const el = document.querySelector('.framework-radio:checked');
  return el ? el.value : '';
}

function getSelectedMode() {
  const el = document.querySelector('.mode-radio:checked');
  return el ? el.value : '';
}

function applyFrameworkConstraints(framework) {
  const modes = FILE_TREES[framework] || {};
  const availableModes = Object.keys(modes);

  // Enable/disable mode radios based on framework compatibility
  document.querySelectorAll('.mode-radio').forEach(radio => {
    const compatible = availableModes.includes(radio.value);
    radio.disabled = !compatible;
    const label = radio.closest('label') || radio.parentElement;
    if (label) label.classList.toggle('opacity-50', !compatible);
    if (!compatible && radio.checked) radio.checked = false;
  });

  // Auto-select first compatible mode if nothing selected
  if (!getSelectedMode() && availableModes.length) {
    const first = document.querySelector(
      '.mode-radio[value="' + availableModes[0] + '"]');
    if (first) {
      first.checked = true;
      first.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  // Show/hide framework-specific warnings
  document.querySelectorAll('.framework-warning').forEach(el => {
    el.classList.toggle('hidden', el.dataset.framework !== framework);
  });
}

function updateFileTreePreview(framework, mode) {
  const preview = document.getElementById('fileTreePreview');
  if (!preview) return;

  const tree = (FILE_TREES[framework] || {})[mode] || [];
  if (!tree.length) {
    preview.innerHTML =
      '<p class="text-gray-400 italic">Select a framework and output mode to preview.</p>';
    return;
  }

  preview.innerHTML = '<ul class="font-mono text-sm space-y-1">' +
    tree.map(f => {
      const isDir = f.endsWith('/');
      const icon = isDir ? '&#128193;' : '&#128196;';
      return '<li>' + icon + ' ' + f + '</li>';
    }).join('') + '</ul>';
}

function preCheckPlanTools() {
  const planInput = document.getElementById('planJsonInput');
  if (!planInput || !planInput.value) return;
  try {
    const plan = JSON.parse(planInput.value);
    const planTools = (plan.tools || []).map(
      t => (typeof t === 'string') ? t : (t.name || ''));
    document.querySelectorAll('.tool-checkbox').forEach(cb => {
      if (planTools.includes(cb.value)) cb.checked = true;
    });
  } catch (_) { /* ignore parse errors */ }
}

/* ----------------------------------------------------------
   Step 4 – Result (File Viewer & Editor)
   ---------------------------------------------------------- */
function initStep4() {
  const codeContent = document.getElementById('codeContent');
  if (!codeContent) return;

  // Copy button
  const copyBtn = document.getElementById('copyBtn');
  if (copyBtn) {
    copyBtn.addEventListener('click', copyCode);
  }

  // Edit form loading state
  const editForm = document.getElementById('editForm');
  if (editForm) {
    editForm.addEventListener('submit', () => {
      const btn = editForm.querySelector('button[type="submit"]');
      if (btn) setLoading(btn, 'Applying...');
    });
  }
}

/** Select and display a file in the code viewer (called from template). */
function selectFile(filepath) {
  if (typeof fileData === 'undefined' || !fileData[filepath]) return;

  // Update active state in file tree
  document.querySelectorAll('.file-tree-item').forEach(function(item) {
    var isActive = item.getAttribute('data-filepath') === filepath;
    if (isActive) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Update filename display
  var filenameEl = document.getElementById('currentFileName');
  if (filenameEl) filenameEl.textContent = filepath;

  // Show code block, hide placeholder
  var placeholder = document.getElementById('codePlaceholder');
  var codeBlock = document.getElementById('codeBlock');
  var codeContent = document.getElementById('codeContent');

  if (placeholder) placeholder.style.display = 'none';
  if (codeBlock) codeBlock.classList.remove('hidden');

  // Set content and highlight
  if (codeContent) {
    var lang = getLanguage(filepath);
    codeContent.className = 'language-' + lang;
    codeContent.textContent = fileData[filepath];
    if (typeof Prism !== 'undefined') {
      Prism.highlightElement(codeContent);
    }
  }
}

/** Map file extensions to Prism.js language identifiers. */
function getLanguage(filepath) {
  const name = filepath.split('/').pop();
  if (name === 'Dockerfile') return 'docker';

  const ext = name.includes('.') ? name.split('.').pop().toLowerCase() : '';
  const map = {
    py: 'python',
    yaml: 'yaml',
    yml: 'yaml',
    md: 'markdown',
    html: 'markup',
    js: 'javascript',
    css: 'css',
    sh: 'bash',
    toml: 'text',
    cfg: 'text',
    txt: 'text',
    json: 'json',
    dockerfile: 'docker'
  };
  return map[ext] || 'text';
}

/** Copy the currently displayed code to clipboard with visual feedback. */
function copyCode() {
  const codeContent = document.getElementById('codeContent');
  const copyBtn = document.getElementById('copyBtn');
  if (!codeContent) return;

  navigator.clipboard.writeText(codeContent.textContent).then(() => {
    if (!copyBtn) return;
    const original = copyBtn.textContent;
    copyBtn.textContent = 'Copied!';
    setTimeout(() => { copyBtn.textContent = original; }, 2000);
  }).catch(() => {
    // Silently fail if clipboard unavailable
  });
}

/* ----------------------------------------------------------
   Shared Utilities
   ---------------------------------------------------------- */

/** Put a button into loading state: disable it, show spinner, change label. */
function setLoading(btn, text) {
  btn.disabled = true;
  btn.classList.add('opacity-50', 'cursor-not-allowed');

  const spinner = btn.querySelector('.spinner');
  if (spinner) spinner.classList.remove('hidden');

  const label = btn.querySelector('.btn-label');
  if (label) {
    label.textContent = text;
  } else if (spinner) {
    // Button has a spinner but no .btn-label wrapper — update text node
    const textNode = Array.from(btn.childNodes)
      .find(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim());
    if (textNode) {
      textNode.textContent = ' ' + text;
    } else {
      btn.appendChild(document.createTextNode(' ' + text));
    }
  } else {
    btn.textContent = text;
  }
}


/* ============================================================
   Settings Modal
   ============================================================ */

function openSettings() {
  const modal = document.getElementById('settingsModal');
  if (!modal) return;
  modal.style.display = 'flex';
  loadSettings();
}

function closeSettings() {
  const modal = document.getElementById('settingsModal');
  if (modal) modal.style.display = 'none';
}

// Close on backdrop click
document.addEventListener('click', function(e) {
  const modal = document.getElementById('settingsModal');
  if (modal && e.target === modal) closeSettings();
});

// Close on Escape
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeSettings();
});

function onAuthModeChange(mode) {
  ['Local', 'Pairing', 'ApiKey'].forEach(m => {
    const el = document.getElementById('auth' + m);
    if (el) el.classList.toggle('selected', m.toLowerCase() === mode.replace('_', '').toLowerCase()
      || (m === 'ApiKey' && mode === 'api_key')
      || (m === 'Local' && mode === 'local')
      || (m === 'Pairing' && mode === 'pairing'));
  });
  const pairSection = document.getElementById('pairingSection');
  const keySection = document.getElementById('apiKeySection');
  if (pairSection) pairSection.style.display = mode === 'pairing' ? 'block' : 'none';
  if (keySection) keySection.style.display = mode === 'api_key' ? 'block' : 'none';
}

function showAuthModeSection(provider) {
  const section = document.getElementById('authModeSection');
  if (section) section.style.display = provider === 'ollabridge' ? 'block' : 'none';
  if (provider !== 'ollabridge') {
    const pairSection = document.getElementById('pairingSection');
    const keySection = document.getElementById('apiKeySection');
    if (pairSection) pairSection.style.display = 'none';
    if (keySection) keySection.style.display = 'block';
  }
}

function doPairing() {
  const base = document.getElementById('settingsBaseUrl')?.value?.trim();
  const code = document.getElementById('pairingCode')?.value?.trim();
  const btn = document.getElementById('pairBtn');
  const text = document.getElementById('pairBtnText');
  const spin = document.getElementById('pairSpinner');
  const result = document.getElementById('pairingResult');

  if (!base) { if (result) { result.style.display = 'block'; result.style.color = 'var(--red)'; result.textContent = 'Enter OllaBridge URL first'; } return; }
  if (!code || code.length < 4) { if (result) { result.style.display = 'block'; result.style.color = 'var(--red)'; result.textContent = 'Enter the pairing code from OllaBridge console'; } return; }

  if (btn) btn.disabled = true;
  if (text) text.textContent = 'Pairing...';
  if (spin) spin.style.display = 'inline-block';
  if (result) result.style.display = 'none';

  fetch('/api/ollabridge/pair', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ base_url: base, code: code }),
  })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        if (result) { result.style.display = 'block'; result.style.color = 'var(--green)'; result.textContent = 'Paired successfully!'; }
        const badge = document.getElementById('pairedBadge');
        const devId = document.getElementById('pairedDeviceId');
        if (badge) badge.style.display = 'block';
        if (devId) devId.textContent = data.device_id || 'connected';
        updateSettingsStatus(true);
        checkInferenceStatus();
        // Refresh models after pairing
        setTimeout(refreshModels, 500);
      } else {
        if (result) { result.style.display = 'block'; result.style.color = 'var(--red)'; result.textContent = data.error || 'Pairing failed'; }
      }
    })
    .catch(e => {
      if (result) { result.style.display = 'block'; result.style.color = 'var(--red)'; result.textContent = 'Error: ' + e.message; }
    })
    .finally(() => {
      if (btn) btn.disabled = false;
      if (text) text.textContent = 'Pair';
      if (spin) spin.style.display = 'none';
    });
}

function loadSettings() {
  fetch('/api/settings')
    .then(r => r.json())
    .then(data => {
      // Set provider radio
      const radio = document.querySelector(`input[name="s_provider"][value="${data.provider}"]`);
      if (radio) { radio.checked = true; highlightProviderCard(data.provider); }
      // Set fields
      const url = document.getElementById('settingsBaseUrl');
      const model = document.getElementById('settingsModel');
      const key = document.getElementById('settingsApiKey');
      const temp = document.getElementById('settingsTemp');
      const tempVal = document.getElementById('settingsTempValue');
      if (url) url.value = data.base_url || '';
      if (model) model.value = data.model || '';
      if (key) key.value = data.api_key === '***' ? '' : (data.api_key || '');
      if (temp) temp.value = data.temperature || 0.7;
      if (tempVal) tempVal.textContent = data.temperature || '0.7';
      // Status
      updateSettingsStatus(data.available);
      // Model suggestions
      showModelSuggestions(data.available_models || [], data.model);
      // Auth mode (OllaBridge)
      showAuthModeSection(data.provider);
      if (data.auth_mode) {
        const authRadio = document.querySelector(`input[name="s_auth_mode"][value="${data.auth_mode}"]`);
        if (authRadio) authRadio.checked = true;
        onAuthModeChange(data.auth_mode);
      }
      // Show paired badge if already paired
      if (data.paired) {
        const badge = document.getElementById('pairedBadge');
        const devId = document.getElementById('pairedDeviceId');
        if (badge) badge.style.display = 'block';
        if (devId) devId.textContent = data.device_id || 'connected';
      }
    })
    .catch(() => updateSettingsStatus(false));
}

function highlightProviderCard(provider) {
  ['Ollama', 'Ollabridge', 'Openai'].forEach(p => {
    const el = document.getElementById('prov' + p);
    if (el) el.classList.toggle('selected', p.toLowerCase() === provider);
  });
}

function onProviderChange(provider) {
  highlightProviderCard(provider);
  const defaults = {
    ollama: { url: 'http://localhost:11434', model: 'qwen2.5:1.5b' },
    ollabridge: { url: 'https://ruslanmv-ollabridge.hf.space', model: 'qwen2.5:1.5b' },
    openai: { url: 'https://api.openai.com', model: 'gpt-4o' },
  };
  const d = defaults[provider] || defaults.ollama;
  const url = document.getElementById('settingsBaseUrl');
  const model = document.getElementById('settingsModel');
  if (url) url.value = d.url;
  if (model) model.value = d.model;
  // Show/hide auth mode section
  showAuthModeSection(provider);
  if (provider === 'ollabridge') {
    onAuthModeChange('pairing');
    const r = document.querySelector('input[name="s_auth_mode"][value="pairing"]');
    if (r) r.checked = true;
  }
}

function updateSettingsStatus(available) {
  const dot = document.getElementById('settingsStatusDot');
  const text = document.getElementById('settingsStatusText');
  if (dot) {
    dot.style.background = available ? '#22c55e' : '#ef4444';
    dot.style.boxShadow = available ? '0 0 8px rgba(34,197,94,0.5)' : '0 0 8px rgba(239,68,68,0.3)';
  }
  if (text) {
    text.textContent = available ? 'Connected' : 'Not connected';
    text.style.color = available ? '#22c55e' : '#ef4444';
  }
}

function showModelSuggestions(models, current) {
  const container = document.getElementById('modelSuggestions');
  if (!container) return;
  container.innerHTML = '';
  models.forEach(m => {
    if (!m) return;
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'tag-chip';
    chip.textContent = m;
    if (m === current) chip.style.borderColor = 'var(--cyan)';
    chip.onclick = function() {
      document.getElementById('settingsModel').value = m;
      container.querySelectorAll('.tag-chip').forEach(c => c.style.borderColor = '');
      chip.style.borderColor = 'var(--cyan)';
    };
    container.appendChild(chip);
  });
}

function refreshModels() {
  fetch('/api/models')
    .then(r => r.json())
    .then(data => {
      showModelSuggestions(data.models || [], data.current);
    })
    .catch(() => {});
}

function saveSettings() {
  const provider = document.querySelector('input[name="s_provider"]:checked');
  const authMode = document.querySelector('input[name="s_auth_mode"]:checked');
  const body = {
    provider: provider ? provider.value : undefined,
    base_url: document.getElementById('settingsBaseUrl')?.value || undefined,
    model: document.getElementById('settingsModel')?.value || undefined,
    temperature: parseFloat(document.getElementById('settingsTemp')?.value || '0.7'),
    auth_mode: authMode ? authMode.value : undefined,
  };
  const apiKey = document.getElementById('settingsApiKey')?.value;
  if (apiKey) body.api_key = apiKey;

  fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    .then(r => r.json())
    .then(data => {
      updateSettingsStatus(data.available);
      checkInferenceStatus();
      closeSettings();
    })
    .catch(() => alert('Failed to save settings'));
}

function testConnection() {
  const btn = document.getElementById('testBtn');
  const text = document.getElementById('testBtnText');
  const spin = document.getElementById('testSpinner');
  if (btn) btn.disabled = true;
  if (text) text.textContent = 'Testing...';
  if (spin) spin.style.display = 'inline-block';

  // Save first, then test
  const provider = document.querySelector('input[name="s_provider"]:checked');
  const body = {
    provider: provider ? provider.value : undefined,
    base_url: document.getElementById('settingsBaseUrl')?.value || undefined,
    model: document.getElementById('settingsModel')?.value || undefined,
    temperature: parseFloat(document.getElementById('settingsTemp')?.value || '0.7'),
  };
  const apiKey = document.getElementById('settingsApiKey')?.value;
  if (apiKey) body.api_key = apiKey;

  fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    .then(() => fetch('/api/settings/test', { method: 'POST' }))
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        updateSettingsStatus(true);
        if (text) text.textContent = 'Connected!';
        setTimeout(() => { if (text) text.textContent = 'Test Connection'; }, 2000);
      } else {
        updateSettingsStatus(false);
        if (text) text.textContent = data.error ? 'Failed' : 'Not reachable';
        setTimeout(() => { if (text) text.textContent = 'Test Connection'; }, 3000);
      }
    })
    .catch(() => {
      updateSettingsStatus(false);
      if (text) text.textContent = 'Error';
      setTimeout(() => { if (text) text.textContent = 'Test Connection'; }, 2000);
    })
    .finally(() => {
      if (btn) btn.disabled = false;
      if (spin) spin.style.display = 'none';
      checkInferenceStatus();
    });
}


/* ============================================================
   Sandbox Verification (Step 4 result page)
   ============================================================ */

var _sandboxOpen = false;

function toggleSandbox() {
  _sandboxOpen = !_sandboxOpen;
  var content = document.getElementById('sandboxContent');
  var dot = document.getElementById('sandboxToggleDot');
  var toggle = document.getElementById('sandboxToggle');
  if (content) content.style.display = _sandboxOpen ? 'block' : 'none';
  if (dot) {
    dot.style.left = _sandboxOpen ? '24px' : '4px';
    dot.style.background = _sandboxOpen ? '#06b6d4' : '#71717a';
  }
  if (toggle) toggle.style.background = _sandboxOpen ? 'rgba(6,182,212,0.3)' : 'rgba(255,255,255,0.1)';
}

function runSandbox(projectId) {
  var btn = document.getElementById('sandboxRunBtn');
  var text = document.getElementById('sandboxRunText');
  var spin = document.getElementById('sandboxSpinner');
  var idle = document.getElementById('sandboxIdle');
  var results = document.getElementById('sandboxResults');

  if (btn) btn.disabled = true;
  if (text) text.textContent = 'Verifying...';
  if (spin) spin.classList.remove('hidden');

  // Update check icons to running
  ['syntax', 'security', 'deps', 'import'].forEach(function(c) {
    var icon = document.getElementById('check-' + c + '-icon');
    if (icon) icon.innerHTML = '<div class="spinner" style="width:12px;height:12px;border-width:1.5px;"></div>';
  });

  fetch('/api/verify/' + projectId, { method: 'POST' })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (idle) idle.style.display = 'none';
      if (results) results.style.display = 'block';

      // Overall status
      var overall = document.getElementById('sandboxOverall');
      if (overall) {
        if (data.status === 'success') {
          overall.className = 'p-4 rounded-xl text-sm flex items-center gap-3 bg-emerald-900/20 border border-emerald-500/20 text-emerald-300';
          overall.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>' + (data.summary || 'All checks passed');
        } else if (data.status === 'warning') {
          overall.className = 'p-4 rounded-xl text-sm flex items-center gap-3 bg-yellow-900/20 border border-yellow-500/20 text-yellow-300';
          overall.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01"/></svg>' + (data.summary || 'Completed with warnings');
        } else {
          overall.className = 'p-4 rounded-xl text-sm flex items-center gap-3 bg-red-900/20 border border-red-500/20 text-red-300';
          overall.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>' + (data.summary || 'Verification failed');
        }
      }

      // Steps
      var stepsEl = document.getElementById('sandboxSteps');
      if (stepsEl && data.steps) {
        stepsEl.innerHTML = '';
        var allLogs = '';
        data.steps.forEach(function(step) {
          var icon = step.status === 'success' ? '✓' : step.status === 'warning' ? '⚠' : step.status === 'skipped' ? '○' : '✗';
          var color = step.status === 'success' ? 'text-emerald-400' : step.status === 'warning' ? 'text-yellow-400' : step.status === 'skipped' ? 'text-zinc-500' : 'text-red-400';
          stepsEl.innerHTML += '<div class="flex items-center gap-3 p-2 rounded-lg bg-dark-900/30"><span class="w-5 text-center ' + color + ' font-bold text-xs">' + icon + '</span><span class="text-xs text-dark-300 capitalize font-medium">' + step.name + '</span><span class="text-xs text-dark-500 flex-1">' + step.message + '</span></div>';
          if (step.logs) allLogs += '--- ' + step.name + ' ---\n' + step.logs + '\n\n';
        });
        // Show logs section if there are any
        if (allLogs) {
          var logSection = document.getElementById('sandboxLogSection');
          var logEl = document.getElementById('sandboxLog');
          if (logSection) logSection.style.display = 'block';
          if (logEl) logEl.textContent = allLogs;
        }
      }

      // Update check icons
      var checkMap = { syntax: 'syntax', security: 'security', dependencies: 'deps', import_test: 'import' };
      (data.steps || []).forEach(function(step) {
        var key = checkMap[step.name];
        if (!key) return;
        var icon = document.getElementById('check-' + key + '-icon');
        if (!icon) return;
        if (step.status === 'success') {
          icon.innerHTML = '<svg class="w-3 h-3 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>';
          icon.className = 'w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center';
        } else if (step.status === 'error') {
          icon.innerHTML = '<svg class="w-3 h-3 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>';
          icon.className = 'w-5 h-5 rounded-full bg-red-500/20 flex items-center justify-center';
        } else {
          icon.innerHTML = '<svg class="w-3 h-3 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01"/></svg>';
          icon.className = 'w-5 h-5 rounded-full bg-yellow-500/20 flex items-center justify-center';
        }
      });
    })
    .catch(function(e) {
      if (idle) idle.style.display = 'block';
      if (results) results.style.display = 'none';
      alert('Verification failed: ' + e.message);
    })
    .finally(function() {
      if (btn) btn.disabled = false;
      if (text) text.textContent = 'Run Again';
      if (spin) spin.classList.add('hidden');
    });
}
