/**
 * 对话历史模块
 * 支持消息展示、Agent 筛选、分页加载、SSE 实时更新
 */

// 状态
let currentPage = 1;
let currentAgentFilter = 'all';
let isLoading = false;
let hasMore = true;
const perPage = 50;

// Agent 配置
const agentConfig = {
    xilian: { name: '昔涟', emoji: '🌀', color: '#667eea' },
    tangyuan: { name: '汤圆', emoji: '🐱', color: '#764ba2' },
    doufu: { name: '豆腐', emoji: '🐩', color: '#28a745' }
};

// 加载对话历史
async function loadChatHistory(page = 1, append = false) {
    if (isLoading) return;
    isLoading = true;
    
    showLoading(true);
    
    try {
        let url = `/api/chat-history?page=${page}&per_page=${perPage}`;
        if (currentAgentFilter !== 'all') {
            url += `&agent_id=${currentAgentFilter}`;
        }
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success) {
            renderChatMessages(result.data, append);
            hasMore = result.pages > result.current_page;
            updatePagination(result);
        }
    } catch (error) {
        console.error('Failed to load chat history:', error);
        showError('加载失败，请重试');
    } finally {
        isLoading = false;
        showLoading(false);
    }
}

// 渲染消息列表
function renderChatMessages(messages, append = false) {
    const container = document.getElementById('chat-messages');
    if (!append) {
        container.innerHTML = '';
    }
    
    messages.forEach(msg => {
        const item = createMessageElement(msg);
        container.appendChild(item);
    });
    
    if (!append && messages.length > 0) {
        container.scrollTop = 0;
    }
}

// 创建消息元素
function createMessageElement(msg) {
    const agent = agentConfig[msg.agent_mentioned] || { name: '系统', emoji: '⚙️', color: '#666' };
    const time = formatDateTime(msg.timestamp);
    
    const div = document.createElement('div');
    div.className = 'chat-message';
    div.innerHTML = `
        <div class="message-avatar" style="background: ${agent.color}20; color: ${agent.color}">
            ${agent.emoji}
        </div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender" style="color: ${agent.color}">${agent.name}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-text">${escapeHtml(msg.content)}</div>
        </div>
    `;
    return div;
}

// 更新分页
function updatePagination(result) {
    const pagination = document.getElementById('pagination-info');
    if (pagination) {
        pagination.textContent = `第 ${result.current_page} / ${result.pages} 页，共 ${result.total} 条`;
    }
    
    const loadMoreBtn = document.getElementById('load-more-btn');
    if (loadMoreBtn) {
        loadMoreBtn.disabled = !hasMore;
        loadMoreBtn.textContent = hasMore ? '加载更多' : '没有更多了';
    }
}

// 切换 Agent 筛选
function setAgentFilter(agentId) {
    currentAgentFilter = agentId;
    currentPage = 1;
    
    // 更新按钮状态
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.agent === agentId);
    });
    
    loadChatHistory(1);
}

// 加载更多
function loadMore() {
    if (!hasMore || isLoading) return;
    currentPage++;
    loadChatHistory(currentPage, true);
}

// SSE 实时更新
function connectChatSSE() {
    const eventSource = new EventSource('/api/stream');
    
    eventSource.addEventListener('chat', (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'new_message') {
                prependMessage(data.message);
            }
        } catch (e) {
            console.error('SSE parse error:', e);
        }
    });
    
    eventSource.onerror = () => {
        console.log('Chat SSE disconnected, reconnecting...');
        setTimeout(connectChatSSE, 5000);
    };
}

// 添加新消息到顶部
function prependMessage(msg) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    
    // 检查筛选条件
    if (currentAgentFilter !== 'all' && msg.agent_mentioned !== currentAgentFilter) {
        return;
    }
    
    const item = createMessageElement(msg);
    container.insertBefore(item, container.firstChild);
    
    // 显示新消息提示
    showNewMessageIndicator();
}

// 显示新消息提示
function showNewMessageIndicator() {
    let indicator = document.getElementById('new-message-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'new-message-indicator';
        indicator.className = 'new-message-indicator';
        indicator.textContent = '有新消息';
        indicator.onclick = () => {
            indicator.remove();
        };
        const container = document.getElementById('chat-messages');
        if (container) {
            container.parentElement.insertBefore(indicator, container);
        }
    }
}

// 辅助函数
function formatDateTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins} 分钟前`;
    if (diffHours < 24) return `${diffHours} 小时前`;
    if (diffDays < 7) return `${diffDays} 天前`;
    
    return date.toLocaleDateString('zh-CN', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(show) {
    const loader = document.getElementById('chat-loading');
    if (loader) {
        loader.style.display = show ? 'flex' : 'none';
    }
}

function showError(message) {
    const container = document.getElementById('chat-messages');
    if (container) {
        container.innerHTML = `<div class="error-state">${message}</div>`;
    }
}

// 导出
window.ChatHistory = {
    load: loadChatHistory,
    setFilter: setAgentFilter,
    loadMore: loadMore,
    connectSSE: connectChatSSE
};