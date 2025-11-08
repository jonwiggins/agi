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

    // Refresh task details every 3 seconds
    setInterval(loadTaskDetails, 3000);
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
        const task = await response.json();

        // Store for later use
        currentTaskData = task;

        // Update task details
        document.getElementById('task-title').textContent = task.context?.title || task.task || 'Untitled Task';
        document.getElementById('task-status').textContent = task.status;
        document.getElementById('task-status').className = `status-badge ${task.status}`;

        document.getElementById('detail-status').textContent = task.status;
        document.getElementById('detail-agents').textContent = task.metrics?.total_agents || '-';
        document.getElementById('detail-depth').textContent = task.metrics?.max_depth || '-';
        document.getElementById('detail-time').textContent =
            task.metrics?.execution_time_seconds ?
            `${task.metrics.execution_time_seconds.toFixed(2)}s` : '-';

        // Update cost metrics
        const totalCost = task.metrics?.cost_usd || 0;
        const totalAgents = task.metrics?.total_agents || 0;
        const avgCost = totalAgents > 0 ? totalCost / totalAgents : 0;

        document.getElementById('detail-cost').textContent = formatCost(totalCost);
        document.getElementById('detail-tokens').textContent = formatNumber(task.metrics?.total_tokens);
        document.getElementById('detail-avg-cost').textContent = formatCost(avgCost);

        // Show error section if task failed
        if (task.status === 'failed' || task.status === 'timeout') {
            const errorSection = document.getElementById('error-section');
            errorSection.style.display = 'block';

            if (task.error) {
                document.getElementById('error-type').textContent = task.error.type || 'Error';
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

        // Update result if completed
        if (task.result) {
            const resultBox = document.getElementById('task-result');
            resultBox.innerHTML = `<pre>${JSON.stringify(task.result, null, 2)}</pre>`;
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
        const agent = await response.json();

        if (agent.error) {
            document.getElementById('agent-details').innerHTML = `
                <p class="empty-state">Unable to load agent details</p>
            `;
            return;
        }

        // Build tool calls section
        let toolCallsHtml = '';
        if (agent.tool_calls && agent.tool_calls.length > 0) {
            toolCallsHtml = `
                <div class="mt-2">
                    <strong>Tool Calls (${agent.tool_calls.length}):</strong>
                    ${agent.tool_calls.map(tc => `
                        <div class="tool-call-item">
                            <div class="tool-call-header">
                                <span class="tool-name">${tc.tool}</span>
                                <span class="tool-time">${new Date(tc.timestamp).toLocaleTimeString()}</span>
                            </div>
                            <details class="tool-call-details">
                                <summary>Parameters & Result</summary>
                                <div class="tool-call-content">
                                    <strong>Input:</strong>
                                    <pre>${JSON.stringify(tc.input, null, 2)}</pre>
                                    <strong>Output:</strong>
                                    <pre>${JSON.stringify(tc.result, null, 2)}</pre>
                                </div>
                            </details>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        const detailsHtml = `
            <div class="details-grid">
                <div class="detail-item">
                    <span class="detail-label">Agent ID:</span>
                    <span title="${agent.agent_id}">${agent.agent_id.substring(0, 8)}...</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Status:</span>
                    <span class="status-badge ${agent.status}">${agent.status}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Depth:</span>
                    <span>${agent.depth}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Tool Calls:</span>
                    <span>${agent.tool_calls ? agent.tool_calls.length : 0}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Cost:</span>
                    <span class="cost-value">${formatCost(agent.metrics?.cost_usd || 0)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Tokens:</span>
                    <span>${formatNumber((agent.metrics?.prompt_tokens || 0) + (agent.metrics?.completion_tokens || 0))}</span>
                </div>
            </div>
            <div class="mt-2">
                <strong>Task:</strong>
                <p>${agent.assigned_task}</p>
            </div>
            ${agent.thoughts ? `
                <div class="mt-2">
                    <strong>Thoughts:</strong>
                    <p>${agent.thoughts}</p>
                </div>
            ` : ''}
            ${agent.result ? `
                <div class="mt-2">
                    <strong>Result:</strong>
                    <pre>${JSON.stringify(agent.result, null, 2)}</pre>
                </div>
            ` : ''}
            ${toolCallsHtml}
        `;

        document.getElementById('agent-details').innerHTML = detailsHtml;
    } catch (error) {
        console.error('Error loading agent details:', error);
        document.getElementById('agent-details').innerHTML = `
            <p class="empty-state">Error loading agent details</p>
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
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (websocket) {
        websocket.close();
    }
});
