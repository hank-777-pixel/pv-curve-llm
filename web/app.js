class PVCurveChat {
    constructor() {
        this.chatEl = document.getElementById('chat');
        this.formEl = document.getElementById('chat-form');
        this.inputEl = document.getElementById('message-input');
        this.sessionId = localStorage.getItem('pv-session-id') || null;
        this.modelProvider = localStorage.getItem('pv-model-provider') || 'ollama';
        this.graphs = [];
        this.pendingTraceEl = null;
        
        this.setupEventListeners();
        this.initializeUI();
        this.showWelcomeMessage();
        this.refreshGraphs();
        this.updateModelStatus();
    }
    
    setupEventListeners() {
        // Chat form submission
        this.formEl.addEventListener('submit', async (e) => {
  e.preventDefault();
            const message = this.inputEl.value.trim();
  if (!message) return;
            
            this.appendMessage('user', message);
            this.inputEl.value = '';
            this.inputEl.disabled = true;
            const traceEl = this.createThinkingPlaceholder();
            this.pendingTraceEl = traceEl;
            
            try {
                const data = await this.sendMessage(message);
                this.displayResponse(data);
            } catch (err) {
                this.appendMessage('assistant', `Error: ${err.message}`);
            } finally {
                this.inputEl.disabled = false;
                this.inputEl.focus();
                this.pendingTraceEl = null;
            }
        });

        // Model provider selection
        document.getElementById('model-provider').addEventListener('change', (e) => {
            this.modelProvider = e.target.value;
            localStorage.setItem('pv-model-provider', this.modelProvider);
            this.updateModelStatus();
            this.appendMessage('system', `Switched to ${this.modelProvider === 'ollama' ? 'Ollama (Local)' : 'OpenAI (API)'} model`);
        });

        // Header controls
        document.getElementById('new-session').addEventListener('click', () => {
            this.startNewSession();
        });

        document.getElementById('export-session').addEventListener('click', () => {
            this.exportSession();
        });

        // Graph controls
        document.getElementById('refresh-graphs').addEventListener('click', () => {
            this.refreshGraphs();
        });

        document.getElementById('clear-graphs').addEventListener('click', () => {
            this.clearGraphs();
        });

        // Close modal on click outside
        document.getElementById('graph-modal').addEventListener('click', (e) => {
            if (e.target.id === 'graph-modal') {
                this.closeGraphModal();
            }
        });

        // ESC key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeGraphModal();
            }
        });
    }
    
    initializeUI() {
        // Set model provider
        document.getElementById('model-provider').value = this.modelProvider;
        
        // Initialize parameters display with defaults
        this.updateParametersDisplay({
            grid: 'ieee39',
            bus_id: 5,
            power_factor: 0.95,
            step_size: 0.01,
            max_scale: 3.0,
            capacitive: false
        });
    }
    
    async sendMessage(message) {
        const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message, 
                session_id: this.sessionId,
                model_provider: this.modelProvider
            })
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Request failed');
        
        if (data.conversation_id) {
            this.sessionId = data.conversation_id;
            localStorage.setItem('pv-session-id', this.sessionId);
        }
        
        return data;
    }
    
    displayResponse(data) {
        // Replace placeholder with collapsible trace and then show final answer
        if (this.pendingTraceEl) {
            this.replaceThinkingWithTrace(this.pendingTraceEl, data.progress_messages || [], data.node_responses || []);
        } else if (data.progress_messages) {
            this.displayProgressMessages(data.progress_messages);
        }
        
        // Show multi-step plan steps list if detected, but render each step result as its own answer message
        if (data.updated_state && data.updated_state.is_compound) {
            this.displayMultiStepPlan(data);
            const stepResults = (data.updated_state.step_results || []);
            let plotPath = this.extractPlotPath(data);
            stepResults.forEach(async (step, idx) => {
                const content = typeof step.result === 'string' ? step.result : JSON.stringify(step.result, null, 2);
                const el = this.appendMessage('assistant', content);
                // If this step corresponds to generation or analysis and a plot exists, show it as its own block
                if ((step.action === 'generation' || step.action === 'analysis')) {
                    if (!plotPath) {
                        plotPath = await this.fetchLatestGraphFilename();
                    }
                    if (plotPath) {
                        this.appendStandalonePlot(plotPath);
                    }
                }
            });
        }
        
        // Display main response after the trace section, unless it's the compound summary line
        const isCompound = !!(data.updated_state && data.updated_state.is_compound);
        const isSummaryLine = typeof data.response_text === 'string' && data.response_text.trim().toLowerCase().startsWith('completed multi-step request');
        const hasCompoundSummary = Array.isArray(data.node_responses) && data.node_responses.some(n => n.node_type === 'compound_summary');
        if (!(isCompound && (isSummaryLine || hasCompoundSummary))) {
            const el = this.appendMessage('assistant', data.response_text);
            // If this final response corresponds to analysis, embed plot as well
            let plotPath = this.extractPlotPath(data);
            const hasAnalysis = Array.isArray(data.node_responses) && data.node_responses.some(n => n.node_type === 'analysis');
            if (hasAnalysis) {
                const tryEmbed = (p) => { if (p) this.appendStandalonePlot(p); };
                if (plotPath) tryEmbed(plotPath); else this.fetchLatestGraphFilename().then(tryEmbed);
            }
        }
        
        // Handle node responses
        if (data.node_responses) {
            data.node_responses.forEach(nodeResp => {
                this.handleNodeResponse(nodeResp);
            });
        }
        
        // Show suggestions
        if (data.next_suggestions && data.next_suggestions.length > 0) {
            this.displaySuggestions(data.next_suggestions);
        }
        
        // Update parameters display
        if (data.updated_state && data.updated_state.inputs) {
            this.updateParametersDisplay(data.updated_state.inputs);
        }

        // Refresh graphs if new PV curve was generated
        if (data.node_responses && data.node_responses.some(r => r.node_type === 'generation' && r.success)) {
            setTimeout(() => this.refreshGraphs(), 1000);
        }
    }
    
    handleNodeResponse(nodeResponse) {
        switch (nodeResponse.node_type) {
            case 'generation':
                this.displayPVCurve(nodeResponse.data);
                break;
            case 'parameter':
                this.displayParameterUpdate(nodeResponse.data);
                break;
            case 'analysis':
                this.displayAnalysis(nodeResponse.data);
                break;
        }
    }
    
    displayPVCurve(data) {
        if (!data.pv_results) return;
        
        const container = document.createElement('div');
        container.className = 'pv-curve-result';
        
        const results = data.pv_results;
        const plotPath = results.save_path ? this.getBasename(results.save_path) : null;
        
        container.innerHTML = `
            <div class="result-header">
                📊 PV Curve Generated
            </div>
            ${plotPath ? `<img src="/api/pv-curves/${plotPath}" alt="PV Curve" class="pv-plot" />` : ''}
            <div class="metrics">
                <div class="metric">
                    <span class="label">Grid System</span>
                    <span class="value">${data.grid_system?.toUpperCase()}</span>
                </div>
                <div class="metric">
                    <span class="label">Bus ID</span>
                    <span class="value">${data.bus_monitored}</span>
                </div>
                ${data.load_margin_mw ? `
                <div class="metric">
                    <span class="label">Load Margin</span>
                    <span class="value">${data.load_margin_mw.toFixed(2)} MW</span>
                </div>
                ` : ''}
                ${data.nose_point_voltage_pu ? `
                <div class="metric">
                    <span class="label">Nose Voltage</span>
                    <span class="value">${data.nose_point_voltage_pu.toFixed(3)} pu</span>
                </div>
                ` : ''}
            </div>
        `;
        
        this.chatEl.appendChild(container);
        this.chatEl.scrollTop = this.chatEl.scrollHeight;
    }
    
    displayParameterUpdate(data) {
        if (!data.updated_parameters) return;
        
        const container = document.createElement('div');
        container.className = 'parameter-update';
        container.innerHTML = `
            <div class="update-header">⚙️ Parameters Updated</div>
            <div class="updated-params">
                ${data.updated_parameters.map(param => `<span class="param-tag">${param}</span>`).join('')}
            </div>
        `;
        
        this.chatEl.appendChild(container);
        this.chatEl.scrollTop = this.chatEl.scrollHeight;
    }
    
    displayAnalysis(data) {
        // Analysis content is shown in the main message
    }
    
    displaySuggestions(suggestions) {
        const container = document.createElement('div');
        container.className = 'suggestions';
        container.innerHTML = `
            <div class="suggestions-header">💡 Suggested Actions:</div>
            <div class="suggestion-buttons">
                ${suggestions.map(suggestion => 
                    `<button class="suggestion-btn" onclick="window.chat.sendSuggestion('${suggestion.replace(/'/g, "\\'")}')">${suggestion}</button>`
                ).join('')}
            </div>
        `;
        
        this.chatEl.appendChild(container);
        this.chatEl.scrollTop = this.chatEl.scrollHeight;
    }
    
    updateParametersDisplay(inputs) {
        document.getElementById('param-grid').textContent = inputs.grid?.toUpperCase() || 'N/A';
        document.getElementById('param-bus').textContent = inputs.bus_id || 'N/A';
        document.getElementById('param-pf').textContent = inputs.power_factor || 'N/A';
        document.getElementById('param-step').textContent = inputs.step_size || 'N/A';
        document.getElementById('param-scale').textContent = inputs.max_scale || 'N/A';
        document.getElementById('param-load').textContent = inputs.capacitive ? 'Capacitive' : 'Inductive';
    }
    
    async refreshGraphs() {
        try {
            const response = await fetch('/api/graphs');
            if (response.ok) {
                this.graphs = await response.json();
                this.updateGraphDirectory();
            }
        } catch (err) {
            console.error('Failed to refresh graphs:', err);
        }
    }
    
    updateGraphDirectory() {
        const directory = document.getElementById('graph-directory');
        
        if (this.graphs.length === 0) {
            directory.innerHTML = '<div class="no-graphs">No graphs generated yet</div>';
            return;
        }
        
        directory.innerHTML = this.graphs.map(graph => `
            <div class="graph-item" onclick="window.chat.openGraph('${graph.filename}', '${graph.title}')">
                <div class="graph-item-header">${graph.title}</div>
                <div class="graph-item-details">
                    ${graph.grid} • Bus ${graph.bus} • ${graph.timestamp}
                </div>
            </div>
        `).join('');
    }
    
    openGraph(filename, title) {
        const modal = document.getElementById('graph-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalImage = document.getElementById('modal-image');
        const modalDetails = document.getElementById('modal-details');
        
        modalTitle.textContent = title;
        modalImage.src = `/api/pv-curves/${filename}`;
        
        // Find graph details
        const graph = this.graphs.find(g => g.filename === filename);
        if (graph) {
            modalDetails.innerHTML = `
                <div class="metric">
                    <span class="label">Grid System</span>
                    <span class="value">${graph.grid}</span>
                </div>
                <div class="metric">
                    <span class="label">Bus ID</span>
                    <span class="value">${graph.bus}</span>
                </div>
                <div class="metric">
                    <span class="label">Generated</span>
                    <span class="value">${graph.timestamp}</span>
                </div>
                ${graph.load_margin ? `
                <div class="metric">
                    <span class="label">Load Margin</span>
                    <span class="value">${graph.load_margin} MW</span>
                </div>
                ` : ''}
            `;
        }
        
        modal.classList.add('show');
    }
    
    closeGraphModal() {
        document.getElementById('graph-modal').classList.remove('show');
    }
    
    async clearGraphs() {
        if (!confirm('Are you sure you want to clear all generated graphs?')) return;
        
        try {
            const response = await fetch('/api/graphs', { method: 'DELETE' });
            if (response.ok) {
                this.graphs = [];
                this.updateGraphDirectory();
                this.appendMessage('system', 'All graphs cleared');
            }
  } catch (err) {
            this.appendMessage('system', 'Failed to clear graphs');
        }
    }
    
    startNewSession() {
        this.sessionId = null;
        localStorage.removeItem('pv-session-id');
        this.chatEl.innerHTML = '';
        this.showWelcomeMessage();
        this.appendMessage('system', 'Started new session');
    }
    
    exportSession() {
        // Get all messages
        const messages = Array.from(this.chatEl.children).map(el => ({
            role: el.classList.contains('user') ? 'user' : 'assistant',
            content: el.textContent,
            timestamp: new Date().toISOString()
        }));
        
        const sessionData = {
            sessionId: this.sessionId,
            modelProvider: this.modelProvider,
            messages: messages,
            exportedAt: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(sessionData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `pv-curve-session-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        this.appendMessage('system', 'Session exported successfully');
    }
    
    updateModelStatus() {
        const statusEl = document.getElementById('model-status');
        const indicator = statusEl.querySelector('.status-indicator');
        const text = statusEl.querySelector('span:last-child');
        
        // Show connecting status
        indicator.className = 'status-indicator offline';
        text.textContent = 'Connecting...';
        
        // Test connection (simplified - just assume it works for now)
        setTimeout(() => {
            indicator.className = 'status-indicator online';
            text.textContent = `Connected (${this.modelProvider})`;
        }, 1000);
    }
    
    appendMessage(role, text) {
        const item = document.createElement('div');
        item.className = `msg ${role}`;
        
        if (role === 'system') {
            item.style.alignSelf = 'center';
            item.style.background = 'var(--bg-tertiary)';
            item.style.color = 'var(--text-muted)';
            item.style.fontSize = '0.9rem';
            item.style.fontStyle = 'italic';
            item.style.maxWidth = '60%';
        }
        
        item.textContent = text;
        this.chatEl.appendChild(item);
        this.chatEl.scrollTop = this.chatEl.scrollHeight;
    }
    
    sendSuggestion(suggestion) {
        this.inputEl.value = suggestion;
        this.formEl.dispatchEvent(new Event('submit'));
    }
    
    sendQuickMessage(message) {
        this.inputEl.value = message;
        this.formEl.dispatchEvent(new Event('submit'));
    }
    
    displayProgressMessages(progressMessages) {
        let currentSpinners = new Map();
        
        // Group messages by timestamp for better organization
        progressMessages.forEach((msg, index) => {
            switch (msg.type) {
                case 'info':
                    this.appendProgressMessage('info', msg.message, false, msg.timestamp);
                    break;
                case 'spinner_start':
                    const spinnerEl = this.appendProgressMessage('spinner', msg.message, true, msg.timestamp);
                    currentSpinners.set(msg.spinner_id, spinnerEl);
                    break;
                case 'spinner_update':
                    const existingSpinner = currentSpinners.get(msg.spinner_id);
                    if (existingSpinner) {
                        this.updateSpinnerMessage(existingSpinner, msg.message);
                    }
                    break;
                case 'spinner_end':
                    const completedSpinner = currentSpinners.get(msg.spinner_id);
                    if (completedSpinner) {
                        this.completeSpinner(completedSpinner, msg.message);
                        currentSpinners.delete(msg.spinner_id);
                    }
                    break;
                case 'answer':
                    // Answer messages are shown as regular assistant messages
                    break;
            }
        });
    }
    
    appendProgressMessage(type, text, isSpinner = false, timestamp = null) {
        const item = document.createElement('div');
        item.className = `msg progress ${type}`;
        
        // Add thinking indicator and enhanced styling with context-aware icons
        const icon = this.getProgressIcon(type, isSpinner, text);
        const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString() : '';
        
        if (isSpinner) {
            item.innerHTML = `
                <div class="progress-header">
                    <div class="progress-icon spinner">${icon}</div>
                    <div class="progress-content">
                        <div class="progress-text">${text}</div>
                        ${timeStr ? `<div class="progress-time">${timeStr}</div>` : ''}
                    </div>
                </div>
            `;
        } else {
            item.innerHTML = `
                <div class="progress-header">
                    <div class="progress-icon">${icon}</div>
                    <div class="progress-content">
                        <div class="progress-text">${text}</div>
                        ${timeStr ? `<div class="progress-time">${timeStr}</div>` : ''}
                    </div>
                </div>
            `;
        }
        
        this.chatEl.appendChild(item);
        this.chatEl.scrollTop = this.chatEl.scrollHeight;
        return item;
    }

    createThinkingPlaceholder() {
        const container = document.createElement('div');
        container.className = 'trace-container thinking';
        container.innerHTML = `
            <div class="trace-header">
                <div class="trace-title"><span class="spinner-dot"></span> Thinking...</div>
            </div>
            <div class="trace-body" hidden></div>
        `;
        this.chatEl.appendChild(container);
        this.chatEl.scrollTop = this.chatEl.scrollHeight;
        return container;
    }

    replaceThinkingWithTrace(container, progressMessages, nodeResponses) {
        container.classList.remove('thinking');
        const titleEl = container.querySelector('.trace-title');
        titleEl.innerHTML = 'Reasoning trace';
        const body = container.querySelector('.trace-body');
        body.innerHTML = '';
        const list = document.createElement('div');
        list.className = 'trace-list';
        (progressMessages || []).forEach(msg => {
            const row = document.createElement('div');
            row.className = `trace-row ${msg.type}`;
            const timeStr = (msg.timestamp || msg.ts) ? new Date(msg.timestamp || msg.ts).toLocaleTimeString() : '';
            const text = msg.message || msg.text || '';
            row.innerHTML = `
                <div class="trace-meta">${timeStr}${msg.node ? ` • ${msg.node}` : ''}${Number.isInteger(msg.step) ? ` • step ${msg.step}` : ''}</div>
                <div class="trace-text">${this.escapeHtml(text)}</div>
            `;
            list.appendChild(row);
        });
        body.appendChild(list);
        // Only add details toggle if there are details
        const hasDetails = list.children.length > 0;
        if (hasDetails) {
            const header = container.querySelector('.trace-header');
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'trace-toggle';
            toggleBtn.setAttribute('aria-expanded', 'false');
            toggleBtn.setAttribute('aria-label', 'Toggle details');
            toggleBtn.textContent = 'Show details';
            header.appendChild(toggleBtn);
            toggleBtn.addEventListener('click', () => {
                const expanded = toggleBtn.getAttribute('aria-expanded') === 'true';
                toggleBtn.setAttribute('aria-expanded', String(!expanded));
                toggleBtn.textContent = expanded ? 'Show details' : 'Hide details';
                body.hidden = expanded;
            });
        }
    }

    escapeHtml(s) {
        return String(s)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;');
    }

    extractPlotPath(data) {
        if (!data || !Array.isArray(data.node_responses)) return null;
        // Prefer latest generation node
        for (let i = data.node_responses.length - 1; i >= 0; i--) {
            const n = data.node_responses[i];
            if (n.node_type === 'generation') {
                const path = (n.data && n.data.pv_results && n.data.pv_results.save_path) || (n.metadata && n.metadata.plot_path);
                if (path) return this.getBasename(String(path));
            }
        }
        // Fallback to analysis payload if present
        for (let i = data.node_responses.length - 1; i >= 0; i--) {
            const n = data.node_responses[i];
            if (n.node_type === 'analysis') {
                const res = n.data && n.data.results_analyzed;
                const path = res && res.save_path;
                if (path) return this.getBasename(String(path));
            }
        }
        return null;
    }

    async fetchLatestGraphFilename() {
        try {
            const resp = await fetch('/api/graphs');
            if (!resp.ok) return null;
            const graphs = await resp.json();
            if (Array.isArray(graphs) && graphs.length > 0) {
                // First item is most recent by server sort
                return graphs[0].filename;
            }
        } catch (_) {
            return null;
        }
        return null;
    }

    appendStandalonePlot(plotFilename) {
        if (!plotFilename) return;
        const container = document.createElement('div');
        container.className = 'pv-curve-result';
        container.innerHTML = `
            <div class="result-header">📊 PV Curve</div>
            <img src="/api/pv-curves/${plotFilename}" alt="PV Curve" class="pv-plot" />
        `;
        this.chatEl.appendChild(container);
        this.chatEl.scrollTop = this.chatEl.scrollHeight;
    }

    getBasename(path) {
        const normalized = String(path).replace(/\\/g, '/');
        const parts = normalized.split('/');
        return parts[parts.length - 1];
    }
    
    getProgressIcon(type, isSpinner = false, message = '') {
        if (isSpinner) return '⟳';
        
        // Enhanced icon mapping based on message content
        if (type === 'info') {
            const lowerMsg = message.toLowerCase();
            if (lowerMsg.includes('plan') || lowerMsg.includes('multi-step')) return '🧠';
            if (lowerMsg.includes('generat')) return '⚡';
            if (lowerMsg.includes('analyz') || lowerMsg.includes('analysis')) return '🔍';
            if (lowerMsg.includes('retriev') || lowerMsg.includes('context')) return '📚';
            if (lowerMsg.includes('parameter') || lowerMsg.includes('chang')) return '⚙️';
            if (lowerMsg.includes('error') || lowerMsg.includes('fail')) return '⚠️';
            return '💭'; // Default thinking bubble
        }
        
        return type === 'spinner' ? '⟳' : '•';
    }
    
    displayMultiStepPlan(data) {
        const container = document.createElement('div');
        container.className = 'multi-step-plan';
        
        const planInfo = this.extractPlanInfo(data);
        
        container.innerHTML = `
            <div class="plan-header">
                🧠 Multi-Step Analysis Plan
            </div>
            <div class="plan-content">
                <div class="plan-description">${planInfo.description}</div>
                ${planInfo.steps.length > 0 ? `
                    <div class="plan-steps">
                        <div class="steps-title">Planned Steps:</div>
                        ${planInfo.steps.map((step, i) => `
                            <div class="plan-step ${step.completed ? 'completed' : ''}">
                                <div class="step-number">${i + 1}</div>
                                <div class="step-content">
                                    <div class="step-action">${step.action}</div>
                                    ${step.description ? `<div class="step-description">${step.description}</div>` : ''}
                                </div>
                                <div class="step-status">${step.completed ? '✅' : '⏳'}</div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
        
        this.chatEl.appendChild(container);
        this.chatEl.scrollTop = this.chatEl.scrollHeight;
    }
    
    extractPlanInfo(data) {
        // Extract plan information from the response data
        let description = "Complex multi-step request detected";
        let steps = [];
        
        // Check if there's plan data in the state
        if (data.updated_state && data.updated_state.plan) {
            const plan = data.updated_state.plan;
            description = plan.description || description;
            steps = plan.steps || [];
        }
        
        // Infer steps from progress messages if no explicit plan
        if (steps.length === 0 && data.progress_messages) {
            const inferredSteps = [];
            data.progress_messages.forEach(msg => {
                if (msg.message && msg.message.toLowerCase().includes('plan')) {
                    inferredSteps.push({
                        action: msg.message,
                        completed: msg.type === 'spinner_end'
                    });
                }
            });
            steps = inferredSteps;
        }
        
        return { description, steps };
    }
    
    updateSpinnerMessage(spinnerEl, newText) {
        const textEl = spinnerEl.querySelector('.progress-text');
        if (textEl) {
            textEl.textContent = newText;
        }
    }
    
    completeSpinner(spinnerEl, completionMessage = null) {
        const iconEl = spinnerEl.querySelector('.progress-icon');
        const textEl = spinnerEl.querySelector('.progress-text');
        
        if (iconEl) {
            iconEl.textContent = '✅';
            iconEl.classList.add('completed');
            iconEl.classList.remove('spinner');
        }
        
        if (completionMessage && textEl) {
            textEl.textContent = completionMessage;
        }
        
        spinnerEl.classList.add('completed');
    }

    showWelcomeMessage() {
        this.appendMessage('assistant', 'Welcome to the PV Curve Analysis Platform! 🔌⚡\n\nI can help you:\n• Generate PV curves for different power systems\n• Analyze voltage stability and load margins\n• Modify system parameters\n• Compare different grid configurations\n\nTry clicking one of the quick action buttons below or ask me anything about power system analysis!');
    }
}

// Initialize the enhanced chat
window.chat = new PVCurveChat();