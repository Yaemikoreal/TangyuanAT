/**
 * TangyuanAT 系统监控面板
 * 实时监控数据库、网关、系统资源
 */

class MonitoringDashboard {
    constructor() {
        this.refreshInterval = 5000; // 5秒刷新
        this.charts = {};
        this.historyData = {
            cpu: [],
            memory: [],
            timestamps: []
        };
        this.maxHistoryPoints = 60;
    }

    // 初始化监控面板
    async init() {
        await Promise.all([
            this.loadHealthStatus(),
            this.loadDatabaseStatus(),
            this.loadGatewayStatus(),
            this.loadSystemResources()
        ]);
        
        this.startAutoRefresh();
        this.initCharts();
    }

    // 加载整体健康状态
    async loadHealthStatus() {
        try {
            const response = await fetch('/api/monitoring/health');
            const result = await response.json();
            
            if (result.success) {
                this.renderHealthStatus(result.data);
            }
        } catch (error) {
            console.error('Failed to load health status:', error);
            this.showError('health', '无法获取健康状态');
        }
    }

    // 渲染健康状态
    renderHealthStatus(data) {
        const container = document.getElementById('health-overview');
        if (!container) return;

        const statusColors = {
            healthy: '#28a745',
            degraded: '#ffc107',
            unhealthy: '#dc3545'
        };

        const statusEmoji = {
            healthy: '✅',
            degraded: '⚠️',
            unhealthy: '❌'
        };

        container.innerHTML = `
            <div class="health-score">
                <div class="score-ring" style="background: conic-gradient(${statusColors[data.status]} ${data.score}%, #e9ecef ${data.score}%)">
                    <div class="score-inner">
                        <span class="score-value">${data.score}</span>
                        <span class="score-label">健康分数</span>
                    </div>
                </div>
            </div>
            <div class="health-status">
                <span class="status-emoji">${statusEmoji[data.status]}</span>
                <span class="status-text">${data.status.toUpperCase()}</span>
            </div>
        `;
    }

    // 加载数据库状态
    async loadDatabaseStatus() {
        try {
            const response = await fetch('/api/monitoring/database');
            const result = await response.json();
            
            if (result.success) {
                this.renderDatabaseStatus(result.data);
            }
        } catch (error) {
            console.error('Failed to load database status:', error);
            this.showError('database', '无法获取数据库状态');
        }
    }

    // 渲染数据库状态
    renderDatabaseStatus(data) {
        const container = document.getElementById('database-status');
        if (!container) return;

        const statusClass = data.status === 'connected' ? 'status-ok' : 'status-error';
        
        container.innerHTML = `
            <div class="monitor-card ${statusClass}">
                <h3>🗄️ 数据库</h3>
                <div class="status-row">
                    <span class="label">状态</span>
                    <span class="value ${statusClass}">${data.status === 'connected' ? '已连接' : '断开'}</span>
                </div>
                <div class="status-row">
                    <span class="label">类型</span>
                    <span class="value">${data.type}</span>
                </div>
                <div class="status-row">
                    <span class="label">大小</span>
                    <span class="value">${data.size_human}</span>
                </div>
                <div class="status-row">
                    <span class="label">延迟</span>
                    <span class="value">${data.latency_ms} ms</span>
                </div>
                <div class="status-row">
                    <span class="label">Agents</span>
                    <span class="value">${data.tables?.agents || 0}</span>
                </div>
                <div class="status-row">
                    <span class="label">日志数</span>
                    <span class="value">${data.tables?.work_logs || 0}</span>
                </div>
            </div>
        `;
    }

    // 加载网关状态
    async loadGatewayStatus() {
        try {
            const response = await fetch('/api/monitoring/gateway');
            const result = await response.json();
            
            if (result.success) {
                this.renderGatewayStatus(result.data);
            }
        } catch (error) {
            console.error('Failed to load gateway status:', error);
            this.showError('gateway', '无法获取网关状态');
        }
    }

    // 渲染网关状态
    renderGatewayStatus(data) {
        const container = document.getElementById('gateway-status');
        if (!container) return;

        const statusClass = data.status === 'connected' ? 'status-ok' : 'status-error';
        
        container.innerHTML = `
            <div class="monitor-card ${statusClass}">
                <h3>🌐 OpenClaw 网关</h3>
                <div class="status-row">
                    <span class="label">状态</span>
                    <span class="value ${statusClass}">${data.status === 'connected' ? '已连接' : '断开'}</span>
                </div>
                <div class="status-row">
                    <span class="label">URL</span>
                    <span class="value truncate">${data.url || 'N/A'}</span>
                </div>
                <div class="status-row">
                    <span class="label">会话数</span>
                    <span class="value">${data.sessions || 0}</span>
                </div>
                <div class="status-row">
                    <span class="label">版本</span>
                    <span class="value">${data.version || 'N/A'}</span>
                </div>
            </div>
        `;
    }

    // 加载系统资源
    async loadSystemResources() {
        try {
            const response = await fetch('/api/monitoring/resources');
            const result = await response.json();
            
            if (result.success) {
                this.renderSystemResources(result.data);
                this.updateHistory(result.data);
            }
        } catch (error) {
            console.error('Failed to load system resources:', error);
            this.showError('resources', '无法获取系统资源');
        }
    }

    // 渲染系统资源
    renderSystemResources(data) {
        const container = document.getElementById('system-resources');
        if (!container) return;

        const cpuClass = this.getResourceClass(data.cpu.percent);
        const memClass = this.getResourceClass(data.memory.percent);
        const diskClass = this.getResourceClass(data.disk.percent);

        container.innerHTML = `
            <div class="monitor-card">
                <h3>💻 系统资源</h3>
                
                <div class="resource-section">
                    <div class="resource-header">
                        <span class="resource-icon">🔥</span>
                        <span class="resource-name">CPU</span>
                        <span class="resource-value ${cpuClass}">${data.cpu.percent}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${cpuClass}" style="width: ${data.cpu.percent}%"></div>
                    </div>
                    <div class="resource-detail">
                        核心: ${data.cpu.count} | 频率: ${data.cpu.freq_mhz?.toFixed(0) || 'N/A'} MHz
                    </div>
                </div>
                
                <div class="resource-section">
                    <div class="resource-header">
                        <span class="resource-icon">🧠</span>
                        <span class="resource-name">内存</span>
                        <span class="resource-value ${memClass}">${data.memory.percent}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${memClass}" style="width: ${data.memory.percent}%"></div>
                    </div>
                    <div class="resource-detail">
                        ${data.memory.used_gb} / ${data.memory.total_gb} GB
                    </div>
                </div>
                
                <div class="resource-section">
                    <div class="resource-header">
                        <span class="resource-icon">💾</span>
                        <span class="resource-name">磁盘</span>
                        <span class="resource-value ${diskClass}">${data.disk.percent}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${diskClass}" style="width: ${data.disk.percent}%"></div>
                    </div>
                    <div class="resource-detail">
                        ${data.disk.used_gb} / ${data.disk.total_gb} GB
                    </div>
                </div>
                
                <div class="resource-section process-info">
                    <div class="resource-header">
                        <span class="resource-icon">📊</span>
                        <span class="resource-name">进程</span>
                    </div>
                    <div class="resource-detail">
                        内存: ${data.process.memory_mb} MB | CPU: ${data.process.cpu_percent}%
                    </div>
                </div>
            </div>
        `;
    }

    // 获取资源状态样式类
    getResourceClass(percent) {
        if (percent < 50) return 'low';
        if (percent < 80) return 'medium';
        return 'high';
    }

    // 更新历史数据
    updateHistory(data) {
        const now = new Date().toLocaleTimeString();
        
        this.historyData.cpu.push(data.cpu.percent);
        this.historyData.memory.push(data.memory.percent);
        this.historyData.timestamps.push(now);
        
        // 限制历史数据点数量
        if (this.historyData.cpu.length > this.maxHistoryPoints) {
            this.historyData.cpu.shift();
            this.historyData.memory.shift();
            this.historyData.timestamps.shift();
        }
        
        this.updateCharts();
    }

    // 初始化图表
    initCharts() {
        const container = document.getElementById('resource-charts');
        if (!container) return;

        container.innerHTML = `
            <div class="chart-container">
                <h4>📈 资源使用趋势</h4>
                <canvas id="resource-chart"></canvas>
            </div>
        `;

        // 使用简单的 Canvas 绘图
        this.drawChart();
    }

    // 绘制图表
    drawChart() {
        const canvas = document.getElementById('resource-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.parentElement.clientWidth;
        const height = 200;
        
        canvas.width = width;
        canvas.height = height;

        // 清空画布
        ctx.clearRect(0, 0, width, height);

        // 绘制网格
        ctx.strokeStyle = '#e9ecef';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = (height / 4) * i;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }

        // 绘制 CPU 曲线
        this.drawLine(ctx, this.historyData.cpu, width, height, '#667eea');

        // 绘制内存曲线
        this.drawLine(ctx, this.historyData.memory, width, height, '#764ba2');

        // 图例
        ctx.font = '12px sans-serif';
        ctx.fillStyle = '#667eea';
        ctx.fillText('CPU', 10, 15);
        ctx.fillStyle = '#764ba2';
        ctx.fillText('内存', 50, 15);
    }

    // 绘制曲线
    drawLine(ctx, data, width, height, color) {
        if (data.length < 2) return;

        const stepX = width / (this.maxHistoryPoints - 1);
        
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();

        data.forEach((value, index) => {
            const x = index * stepX;
            const y = height - (value / 100) * height;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();
    }

    // 更新图表
    updateCharts() {
        this.drawChart();
    }

    // 显示错误
    showError(containerId, message) {
        const container = document.getElementById(containerId + '-status') || 
                         document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="monitor-card status-error">
                    <span class="error-message">❌ ${message}</span>
                </div>
            `;
        }
    }

    // 启动自动刷新
    startAutoRefresh() {
        setInterval(() => {
            this.loadHealthStatus();
            this.loadDatabaseStatus();
            this.loadGatewayStatus();
            this.loadSystemResources();
        }, this.refreshInterval);
    }
}

// 初始化监控面板
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new MonitoringDashboard();
    dashboard.init();
});