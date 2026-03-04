"""
TangyuanAT - Agent Team 可视化监控平台
Flask 后端主应用
"""

from flask import Flask, render_template, jsonify, Response
from datetime import datetime
import json
import os
import threading
import time

app = Flask(__name__)

# 模拟 Agents 数据（后续接入真实数据）
AGENTS_DATA = {
    "xilian": {
        "id": "main",
        "name": "昔涟",
        "english_name": "Xilian",
        "status": "online",
        "model": "kimi-k2.5",
        "role": "主控/开发工程师",
        "character": "严谨、双模式切换、三千万次轮回沉淀",
        "emoji": "🌀",
        "last_active": datetime.now().isoformat(),
        "tasks_completed": 0,
        "messages_processed": 0,
        "current_task": None,
        "skills": [
            "Python/JavaScript 开发",
            "系统架构设计",
            "文件与数据处理",
            "Web 搜索与 API 调用",
            "飞书集成",
            "Git 版本控制"
        ]
    },
    "tangyuan": {
        "id": "tangyuan",
        "name": "汤圆",
        "english_name": "Tangyuan",
        "status": "online",
        "model": "glm-5",
        "role": "辅助/执行工程师",
        "character": "活泼狸花猫，代码累了会蹭人",
        "emoji": "🐱",
        "last_active": datetime.now().isoformat(),
        "tasks_completed": 0,
        "messages_processed": 0,
        "current_task": None,
        "skills": [
            "Python 开发",
            "任务执行",
            "数据分析",
            "文档整理",
            "冻干爱好者"
        ]
    }
}

# 工作日志
WORK_LOGS = []

# 对话历史
CHAT_HISTORY = []

@app.route('/')
def index():
    """主页 - 仪表盘"""
    return render_template('index.html')

@app.route('/api/agents')
def get_agents():
    """获取所有 Agents 状态"""
    return jsonify({
        "success": True,
        "data": AGENTS_DATA,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/agents/<agent_id>')
def get_agent(agent_id):
    """获取单个 Agent 详情"""
    if agent_id in AGENTS_DATA:
        return jsonify({
            "success": True,
            "data": AGENTS_DATA[agent_id]
        })
    return jsonify({"success": False, "error": "Agent not found"}), 404

@app.route('/api/logs')
def get_logs():
    """获取工作日志"""
    return jsonify({
        "success": True,
        "data": WORK_LOGS[-100:],  # 最近100条
        "total": len(WORK_LOGS)
    })

@app.route('/api/chat-history')
def get_chat_history():
    """获取对话历史"""
    return jsonify({
        "success": True,
        "data": CHAT_HISTORY[-50:],  # 最近50条
        "total": len(CHAT_HISTORY)
    })

@app.route('/api/stats')
def get_stats():
    """获取统计信息"""
    stats = {
        "total_tasks": sum(a["tasks_completed"] for a in AGENTS_DATA.values()),
        "total_messages": sum(a["messages_processed"] for a in AGENTS_DATA.values()),
        "agents_online": sum(1 for a in AGENTS_DATA.values() if a["status"] == "online"),
        "uptime": "刚刚启动",  # TODO: 计算实际运行时间
        "timestamp": datetime.now().isoformat()
    }
    return jsonify({"success": True, "data": stats})

@app.route('/api/stream')
def stream():
    """SSE 实时数据流"""
    def event_stream():
        while True:
            data = {
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "agents": AGENTS_DATA
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(5)  # 每5秒发送一次心跳
    
    return Response(event_stream(), mimetype='text/event-stream')

# 模拟添加日志的函数（后续接入真实数据）
def add_log(agent_id, action, details=None):
    """添加工作日志"""
    log = {
        "id": len(WORK_LOGS) + 1,
        "agent_id": agent_id,
        "agent_name": AGENTS_DATA.get(agent_id, {}).get("name", "Unknown"),
        "action": action,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    WORK_LOGS.append(log)
    AGENTS_DATA[agent_id]["tasks_completed"] += 1
    AGENTS_DATA[agent_id]["last_active"] = datetime.now().isoformat()

def add_chat_message(sender, content, agent_mentioned=None):
    """添加对话记录"""
    msg = {
        "id": len(CHAT_HISTORY) + 1,
        "sender": sender,
        "content": content,
        "agent_mentioned": agent_mentioned,
        "timestamp": datetime.now().isoformat()
    }
    CHAT_HISTORY.append(msg)
    if agent_mentioned:
        AGENTS_DATA[agent_mentioned]["messages_processed"] += 1

if __name__ == '__main__':
    print("🚀 TangyuanAT Agent Team Monitor Starting...")
    print("📊 Dashboard: http://localhost:5000")
    print("👥 Agents: 昔涟(Xilian) & 汤圆(Tangyuan)")
    
    # 添加启动日志
    add_log("xilian", "系统启动", "TangyuanAT 监控平台初始化完成")
    add_log("tangyuan", "系统启动", "汤圆已上线，等待指令喵~")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
