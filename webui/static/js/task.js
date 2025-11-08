// Task Visualization JavaScript

let network = null;
let websocket = null;
let currentTaskData = null;

// Load task data on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadTaskDetails();
    initializeTree();
    connectWebSocket();
    setupControls();

    // Refresh task details based on status
    startAutoRefresh();
});

function formatCost(amount) {
    if (amount === 0 || amount === null || amount === undefined) return '$0.00';
    if (amount < 0.01) return `$${amount.toFixed(4)}`;
    return `$${amount.toFixed(2)}`;
}

function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString();
}

async function loadTaskDetails() {
    try {
        const response = await fetch(`/api/tasks/${TASK_ID}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const task = await response.json();

        // Handle error response from backend
        if (task.error) {
            console.error('API Error:', task.error);
            document.getElementById('task-title').textContent = 'Error loading task';
            document.getElementById('task-status').textContent = 'error';
            document.getElementById('task-status').className = 'status-badge failed';
            return;
        }

        // Store for later use
        currentTaskData = task;

        // Update task details
        const taskTitle = task.context?.title || task.task || 'Untitled Task';
        document.getElementById('task-title').textContent = taskTitle;

        // Update status badge with indicator
        const statusBadge = document.getElementById('task-status');
        const statusClass = task.status || 'processing';
        statusBadge.className = `status-badge ${statusClass}`;
        statusBadge.innerHTML = `
            <span class="status-indicator ${statusClass}"></span>
            ${task.status || 'processing'}
        `;

        // Show/hide live indicator based on status
        const liveIndicator = document.getElementById('live-indicator');
        if (task.status === 'processing') {
            liveIndicator.style.display = 'inline-flex';
        } else {
            liveIndicator.style.display = 'none';
        }

        // Update details with flash animation on change
        updateDetailWithFlash('detail-status', task.status);
        updateDetailWithFlash('detail-agents', task.metrics?.total_agents || '-');
        updateDetailWithFlash('detail-depth', task.metrics?.max_depth || '-');
        updateDetailWithFlash('detail-time',
            task.metrics?.execution_time_seconds ?
            `${task.metrics.execution_time_seconds.toFixed(2)}s` : '-');

        // Update cost metrics with flash animation
        const totalCost = task.metrics?.cost_usd || 0;
        const totalAgents = task.metrics?.total_agents || 0;
        const avgCost = totalAgents > 0 ? totalCost / totalAgents : 0;

        updateDetailWithFlash('detail-cost', formatCost(totalCost));
        updateDetailWithFlash('detail-tokens', formatNumber(task.metrics?.total_tokens));
        updateDetailWithFlash('detail-avg-cost', formatCost(avgCost));

        // Show error section if task failed
        if (task.status === 'failed' || task.status === 'timeout') {
            const errorSection = document.getElementById('error-section');
            errorSection.style.display = 'block';

            if (task.error) {
                document.getElementById('error-type-text').textContent = task.error.type || 'Error';
                document.getElementById('error-message').textContent = task.error.message || 'Unknown error';
                document.getElementById('error-timestamp').textContent =
                    `Occurred at: ${new Date(task.error.timestamp).toLocaleString()}`;

                if (task.error.traceback) {
                    document.getElementById('error-traceback').textContent = task.error.traceback;
                }
            }
        } else {
            document.getElementById('error-section').style.display = 'none';
        }

        // Show budget pause section if budget exceeded
        if (task.status === 'paused_budget') {
            const budgetSection = document.getElementById('budget-pause-section');
            budgetSection.style.display = 'block';

            if (task.error && task.error.message) {
                document.getElementById('budget-pause-message').textContent = task.error.message;
            }

            const currentCost = task.metrics?.cost_usd || 0;
            const budgetLimit = task.metrics?.budget_limit || 0;
            document.getElementById('budget-current-cost').textContent = formatCost(currentCost);
            document.getElementById('budget-limit').textContent = formatCost(budgetLimit);
        } else {
            const budgetSection = document.getElementById('budget-pause-section');
            if (budgetSection) {
                budgetSection.style.display = 'none';
            }
        }

        // Update result if completed
        if (task.result) {
            const resultBox = document.getElementById('task-result');
            resultBox.className = 'result-box-modern';
            resultBox.innerHTML = `<pre>${JSON.stringify(task.result, null, 2)}</pre>`;
        } else if (task.status === 'completed') {
            const resultBox = document.getElementById('task-result');
            resultBox.className = 'result-box-modern';
            resultBox.innerHTML = `<p style="color: #9ca3af;">No result data available</p>`;
        }

        // Load and update tree
        await loadTree();
    } catch (error) {
        console.error('Error loading task details:', error);
    }
}

async function loadTree() {
    try {
        const response = await fetch(`/api/tasks/${TASK_ID}/tree`);
        const data = await response.json();

        if (data.tree && data.tree.nodes) {
            updateTree(data.tree);
        } else {
            // Create demo tree structure for visualization
            createDemoTree();
        }
    } catch (error) {
        console.error('Error loading tree:', error);
        createDemoTree();
    }
}

function initializeTree() {
    const container = document.getElementById('tree-container');

    // Initial empty network
    const data = {
        nodes: new vis.DataSet([]),
        edges: new vis.DataSet([])
    };

    const options = {
        layout: {
            hierarchical: {
                direction: 'UD',
                sortMethod: 'directed',
                nodeSpacing: 150,
                levelSeparation: 120
            }
        },
        physics: {
            enabled: false
        },
        nodes: {
            shape: 'box',
            margin: 10,
            widthConstraint: {
                maximum: 200
            },
            font: {
                size: 14,
                face: 'Arial'
            },
            borderWidth: 2,
            shadow: true
        },
        edges: {
            arrows: 'to',
            smooth: {
                type: 'cubicBezier',
                forceDirection: 'vertical'
            },
            color: {
                color: '#848484',
                highlight: '#6366f1'
            },
            width: 2
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true
        }
    };

    network = new vis.Network(container, data, options);

    // Handle node selection
    network.on('selectNode', (params) => {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            showAgentDetails(nodeId);
        }
    });
}

function updateTree(treeData) {
    if (!network) return;

    const nodes = treeData.nodes.map(node => ({
        id: node.id,
        label: node.label || `Agent ${node.id.substring(0, 6)}`,
        title: node.task || 'No task description',
        color: getNodeColor(node.status),
        font: {
            color: node.status === 'running' ? '#ffffff' : '#000000'
        }
    }));

    const edges = treeData.edges.map(edge => ({
        from: edge.from,
        to: edge.to
    }));

    network.setData({
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges)
    });

    network.fit();
}

function createDemoTree() {
    // Create a demo tree to show how it looks
    const demoNodes = [
        {
            id: 'root',
            label: 'Root Agent',
            task: 'Main task: ' + TASK_ID.substring(0, 8),
            status: 'running'
        },
        {
            id: 'agent-1',
            label: 'Agent 1.1',
            task: 'Subtask 1',
            status: 'completed'
        },
        {
            id: 'agent-2',
            label: 'Agent 1.2',
            task: 'Subtask 2',
            status: 'running'
        },
        {
            id: 'agent-3',
            label: 'Agent 1.3',
            task: 'Subtask 3',
            status: 'waiting'
        }
    ];

    const demoEdges = [
        { from: 'root', to: 'agent-1' },
        { from: 'root', to: 'agent-2' },
        { from: 'root', to: 'agent-3' }
    ];

    updateTree({ nodes: demoNodes, edges: demoEdges });
}

function getNodeColor(status) {
    const colors = {
        running: { background: '#3b82f6', border: '#2563eb' },
        completed: { background: '#10b981', border: '#059669' },
        failed: { background: '#ef4444', border: '#dc2626' },
        timeout: { background: '#f59e0b', border: '#d97706' },
        waiting: { background: '#9ca3af', border: '#6b7280' },
        created: { background: '#9ca3af', border: '#6b7280' }
    };

    return colors[status] || colors.created;
}

async function showAgentDetails(nodeId) {
    try {
        const response = await fetch(`/api/tasks/${TASK_ID}/agents/${nodeId}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const agent = await response.json();

        if (agent.error || !agent.agent_id) {
            document.getElementById('agent-details').innerHTML = `
                <div class="empty-state-dashboard" style="padding: 2rem; border: none;">
                    <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="40" cy="40" r="30" stroke="#E5E7EB" stroke-width="3"/>
                        <path d="M40 20V40M40 50H40.01" stroke="#E5E7EB" stroke-width="3" stroke-linecap="round"/>
                    </svg>
                    <p style="margin-top: 1rem; margin-bottom: 0;">Unable to load agent details</p>
                </div>
            `;
            return;
        }

        // Build tool calls section
        let toolCallsHtml = '';
        if (agent.tool_calls && agent.tool_calls.length > 0) {
            toolCallsHtml = `
                <div class="mt-2">
                    <strong style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M14 7L8 13L4 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        Tool Calls (${agent.tool_calls.length})
                    </strong>
                    ${agent.tool_calls.map(tc => `
                        <div class="tool-call-item">
                            <div class="tool-call-header">
                                <span class="tool-name">${tc.tool || 'Unknown'}</span>
                                <span class="tool-time">${tc.timestamp ? new Date(tc.timestamp).toLocaleTimeString() : 'N/A'}</span>
                            </div>
                            <details class="tool-call-details">
                                <summary>Parameters & Result</summary>
                                <div class="tool-call-content">
                                    <strong>Input:</strong>
                                    <pre>${JSON.stringify(tc.input || {}, null, 2)}</pre>
                                    <strong>Output:</strong>
                                    <pre>${JSON.stringify(tc.result || {}, null, 2)}</pre>
                                </div>
                            </details>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        const detailsHtml = `
            <div>
                <div class="detail-item-modern">
                    <span class="detail-label">Agent ID:</span>
                    <span class="detail-value" title="${agent.agent_id || 'N/A'}">${agent.agent_id ? agent.agent_id.substring(0, 8) + '...' : 'N/A'}</span>
                </div>
                <div class="detail-item-modern">
                    <span class="detail-label">Status:</span>
                    <span class="status-badge ${agent.status || 'unknown'}">
                        <span class="status-indicator ${agent.status || 'unknown'}"></span>
                        ${agent.status || 'unknown'}
                    </span>
                </div>
                <div class="detail-item-modern">
                    <span class="detail-label">Depth:</span>
                    <span class="detail-value">${agent.depth !== undefined ? agent.depth : 'N/A'}</span>
                </div>
                <div class="detail-item-modern">
                    <span class="detail-label">Tool Calls:</span>
                    <span class="detail-value">${agent.tool_calls ? agent.tool_calls.length : 0}</span>
                </div>
                <div class="detail-item-modern">
                    <span class="detail-label">Cost:</span>
                    <span class="detail-value cost-value">${formatCost(agent.metrics?.cost_usd || 0)}</span>
                </div>
                <div class="detail-item-modern">
                    <span class="detail-label">Tokens:</span>
                    <span class="detail-value">${formatNumber((agent.metrics?.prompt_tokens || 0) + (agent.metrics?.completion_tokens || 0))}</span>
                </div>
            </div>
            <div class="mt-2">
                <strong style="display: block; margin-bottom: 0.5rem; color: var(--dark);">Task:</strong>
                <p style="color: var(--gray); line-height: 1.6;">${agent.assigned_task || 'No task description available'}</p>
            </div>
            ${agent.thoughts ? `
                <div class="mt-2">
                    <strong style="display: block; margin-bottom: 0.5rem; color: var(--dark);">Thoughts:</strong>
                    <p style="color: var(--gray); line-height: 1.6;">${agent.thoughts}</p>
                </div>
            ` : ''}
            ${agent.result ? `
                <div class="mt-2">
                    <strong style="display: block; margin-bottom: 0.5rem; color: var(--dark);">Result:</strong>
                    <div class="result-box-modern" style="max-height: 300px;">
                        <pre>${JSON.stringify(agent.result, null, 2)}</pre>
                    </div>
                </div>
            ` : ''}
            ${toolCallsHtml}
        `;

        document.getElementById('agent-details').innerHTML = detailsHtml;
    } catch (error) {
        console.error('Error loading agent details:', error);
        document.getElementById('agent-details').innerHTML = `
            <div class="empty-state-dashboard" style="padding: 2rem; border: none;">
                <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="40" cy="40" r="30" stroke="#E5E7EB" stroke-width="3"/>
                    <path d="M40 20V40M40 50H40.01" stroke="#E5E7EB" stroke-width="3" stroke-linecap="round"/>
                </svg>
                <p style="margin-top: 1rem; margin-bottom: 0;">Error loading agent details</p>
            </div>
        `;
    }
}

function connectWebSocket() {
    const wsUrl = `ws://${window.location.host}/ws/tasks/${TASK_ID}`;

    try {
        websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            console.log('WebSocket connected');
        };

        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);

            // Handle different message types
            if (data.type === 'agent_created') {
                // Add new node to tree
                console.log('New agent created:', data.agent_id);
            } else if (data.type === 'agent_completed') {
                // Update node status
                console.log('Agent completed:', data.agent_id);
            } else if (data.type === 'tool_called') {
                console.log('Tool called:', data.tool);
            }

            // Reload tree on updates
            loadTree();
        };

        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        websocket.onclose = () => {
            console.log('WebSocket closed, reconnecting...');
            setTimeout(connectWebSocket, 5000);
        };
    } catch (error) {
        console.error('Failed to connect WebSocket:', error);
    }
}

function setupControls() {
    document.getElementById('zoom-in').onclick = () => {
        const scale = network.getScale();
        network.moveTo({ scale: scale * 1.2 });
    };

    document.getElementById('zoom-out').onclick = () => {
        const scale = network.getScale();
        network.moveTo({ scale: scale * 0.8 });
    };

    document.getElementById('fit-view').onclick = () => {
        network.fit({ animation: true });
    };

    // Budget continue button
    const continueBtn = document.getElementById('continue-budget-btn');
    if (continueBtn) {
        continueBtn.onclick = async () => {
            await continueTaskBudget();
        };
    }
}

async function continueTaskBudget() {
    const continueBtn = document.getElementById('continue-budget-btn');
    if (!continueBtn) return;

    try {
        // Disable button and show loading state
        continueBtn.disabled = true;
        const originalText = continueBtn.textContent;
        continueBtn.textContent = 'Continuing...';

        const response = await fetch(`/api/tasks/${TASK_ID}/continue`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ additional_budget: 2.00 })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to continue task');
        }

        const result = await response.json();
        console.log('Task resumed:', result);

        // Reload task details to update UI
        await loadTaskDetails();

    } catch (error) {
        console.error('Error continuing task:', error);
        alert('Failed to continue task: ' + error.message);

        // Re-enable button on error
        continueBtn.disabled = false;
        continueBtn.textContent = 'Continue for $2 more';
    }
}

// Auto-refresh management
let refreshInterval = null;

function startAutoRefresh() {
    // Clear existing interval if any
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }

    // Set refresh interval based on task status
    const refreshRate = getRefreshRate();
    refreshInterval = setInterval(async () => {
        await loadTaskDetails();
        // Adjust refresh rate dynamically
        const newRate = getRefreshRate();
        if (newRate !== refreshRate) {
            startAutoRefresh();
        }
    }, refreshRate);
}

function getRefreshRate() {
    // Faster refresh for running tasks, slower for completed
    if (!currentTaskData) return 3000;

    const status = currentTaskData.status;
    if (status === 'processing' || status === 'paused_budget') {
        return 2000; // 2 seconds for active tasks
    } else if (status === 'completed' || status === 'failed' || status === 'timeout') {
        return 10000; // 10 seconds for finished tasks
    }
    return 3000;
}

// Helper function to update detail with flash animation
function updateDetailWithFlash(elementId, newValue) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const currentValue = element.textContent;
    if (currentValue !== String(newValue)) {
        // Value changed, flash the parent
        const parent = element.closest('.detail-item-modern');
        if (parent) {
            parent.classList.remove('update-flash');
            // Force reflow
            void parent.offsetWidth;
            parent.classList.add('update-flash');
        }
    }
    element.textContent = newValue;
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (websocket) {
        websocket.close();
    }
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
