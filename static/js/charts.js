/**
 * 统计图表模块
 * 使用 Chart.js 实现响应时间趋势图和任务完成率饼图
 */

// 图表实例
let responseTimeChart = null;
let taskCompletionChart = null;

// 颜色配置
const chartColors = {
    xilian: { bg: 'rgba(102, 126, 234, 0.2)', border: '#667eea' },
    tangyuan: { bg: 'rgba(118, 75, 162, 0.2)', border: '#764ba2' },
    doufu: { bg: 'rgba(40, 167, 69, 0.2)', border: '#28a745' }
};

// 加载 Chart.js 库
async function loadChartJS() {
    if (window.Chart) return;
    
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js';
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// 初始化响应时间趋势图
async function initResponseTimeChart() {
    await loadChartJS();
    
    const ctx = document.getElementById('response-time-chart');
    if (!ctx) return;
    
    // 获取数据
    const data = await fetchResponseTimeData();
    
    if (responseTimeChart) {
        responseTimeChart.destroy();
    }
    
    responseTimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: '昔涟',
                    data: data.xilian,
                    borderColor: chartColors.xilian.border,
                    backgroundColor: chartColors.xilian.bg,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '汤圆',
                    data: data.tangyuan,
                    borderColor: chartColors.tangyuan.border,
                    backgroundColor: chartColors.tangyuan.bg,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '豆腐',
                    data: data.doufu,
                    borderColor: chartColors.doufu.border,
                    backgroundColor: chartColors.doufu.bg,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: '响应时间趋势 (最近 24 小时)'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '响应时间 (ms)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '时间'
                    }
                }
            }
        }
    });
}

// 初始化任务完成率饼图
async function initTaskCompletionChart() {
    await loadChartJS();
    
    const ctx = document.getElementById('task-completion-chart');
    if (!ctx) return;
    
    // 获取数据
    const data = await fetchTaskCompletionData();
    
    if (taskCompletionChart) {
        taskCompletionChart.destroy();
    }
    
    taskCompletionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    chartColors.xilian.border,
                    chartColors.tangyuan.border,
                    chartColors.doufu.border
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                title: {
                    display: true,
                    text: '任务完成率对比'
                }
            }
        }
    });
}

// 获取响应时间数据
async function fetchResponseTimeData() {
    try {
        const response = await fetch('/api/stats/response-time');
        const result = await response.json();
        
        if (result.success) {
            return result.data;
        }
    } catch (error) {
        console.error('Failed to fetch response time data:', error);
    }
    
    // 返回模拟数据
    const labels = [];
    const now = new Date();
    for (let i = 23; i >= 0; i--) {
        const time = new Date(now - i * 3600000);
        labels.push(time.getHours() + ':00');
    }
    
    return {
        labels,
        xilian: generateRandomData(24, 100, 500),
        tangyuan: generateRandomData(24, 150, 600),
        doufu: generateRandomData(24, 80, 400)
    };
}

// 获取任务完成数据
async function fetchTaskCompletionData() {
    try {
        const response = await fetch('/api/agents');
        const result = await response.json();
        
        if (result.success) {
            const agents = result.data;
            return {
                labels: ['昔涟', '汤圆', '豆腐'],
                values: [
                    agents.xilian?.tasks_completed || 0,
                    agents.tangyuan?.tasks_completed || 0,
                    agents.doufu?.tasks_completed || 0
                ]
            };
        }
    } catch (error) {
        console.error('Failed to fetch task completion data:', error);
    }
    
    return {
        labels: ['昔涟', '汤圆', '豆腐'],
        values: [15, 28, 42]
    };
}

// 生成随机数据 (用于演示)
function generateRandomData(count, min, max) {
    return Array.from({ length: count }, () => 
        Math.floor(Math.random() * (max - min + 1)) + min
    );
}

// 切换时间范围
function setTimeRange(range) {
    // 更新按钮状态
    document.querySelectorAll('.time-range-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.range === range);
    });
    
    // 重新加载图表
    initResponseTimeChart();
}

// 导出报表
async function exportReport(format = 'csv') {
    try {
        const response = await fetch(`/api/stats/export?format=${format}`);
        
        if (format === 'csv') {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `tangyuanat_report_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
        } else if (format === 'json') {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `tangyuanat_report_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            window.URL.revokeObjectURL(url);
        }
    } catch (error) {
        console.error('Export failed:', error);
        alert('导出失败，请重试');
    }
}

// 刷新所有图表
async function refreshCharts() {
    await Promise.all([
        initResponseTimeChart(),
        initTaskCompletionChart()
    ]);
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    refreshCharts();
    
    // 每5分钟自动刷新
    setInterval(refreshCharts, 300000);
});

// 导出
window.Charts = {
    initResponseTime: initResponseTimeChart,
    initTaskCompletion: initTaskCompletionChart,
    setTimeRange,
    exportReport,
    refresh: refreshCharts
};