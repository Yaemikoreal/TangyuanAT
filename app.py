"""
TangyuanAT - Agent Team 可视化监控平台
Flask 后端主应用
集成 SQLite 数据持久化 + OpenClaw 网关
"""

from flask import Flask, render_template, jsonify, Response, request
from flask_cors import CORS
from datetime import datetime
import json
import os
import threading
import time

# 导入数据库模型
from models import db, Agent, WorkLog, ChatHistory, StatRecord, Config, init_db

# 导入 OpenClaw 客户端
from agents import get_client

app = Flask(__name__)

# 配置数据库
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'tangyuanat.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 启用 CORS
CORS(app)

# 初始化数据库
init_db(app)

# OpenClaw 客户端
openclaw = get_client()


# ============ 页面路由 ============

@app.route('/')
def index():
    """主页 - 仪表盘"""
    return render_template('index.html')


# ============ Agent API ============

@app.route('/api/agents')
def get_agents():
    """获取所有 Agents 状态"""
    try:
        # 从数据库获取 agents
        agents = Agent.query.all()
        agents_data = {a.id: a.to_dict() for a in agents}
        
        # 尝试从 OpenClaw 获取实时状态
        for agent_id in agents_data:
            status_info = openclaw.get_agent_status_from_sessions(agent_id)
            if status_info.get('status') != 'unknown':
                agents_data[agent_id]['status'] = status_info['status']
                agents_data[agent_id]['last_active'] = status_info.get('last_active', agents_data[agent_id]['last_active'])
        
        return jsonify({
            "success": True,
            "data": agents_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/agents/<agent_id>')
def get_agent(agent_id):
    """获取单个 Agent 详情"""
    try:
        agent = Agent.query.get(agent_id)
        if agent:
            return jsonify({
                "success": True,
                "data": agent.to_dict()
            })
        return jsonify({"success": False, "error": "Agent not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/agents/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """更新 Agent 状态"""
    try:
        agent = Agent.query.get(agent_id)
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        data = request.get_json()
        
        # 更新字段
        if 'status' in data:
            agent.status = data['status']
        if 'current_task' in data:
            agent.current_task = data['current_task']
        if 'model' in data:
            agent.model = data['model']
        if 'config' in data:
            agent.config = json.dumps(data['config'])
        
        agent.last_active = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "data": agent.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ============ 日志 API ============

@app.route('/api/logs')
def get_logs():
    """获取工作日志"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        agent_id = request.args.get('agent_id')
        
        query = WorkLog.query
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        
        logs = query.order_by(WorkLog.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            "success": True,
            "data": [log.to_dict() for log in logs.items],
            "total": logs.total,
            "pages": logs.pages,
            "current_page": page
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/logs', methods=['POST'])
def add_log():
    """添加工作日志"""
    try:
        data = request.get_json()
        
        log = WorkLog(
            agent_id=data.get('agent_id'),
            agent_name=data.get('agent_name'),
            action=data.get('action'),
            details=data.get('details'),
            timestamp=datetime.utcnow()
        )
        
        db.session.add(log)
        
        # 更新 agent 任务计数
        agent = Agent.query.get(data.get('agent_id'))
        if agent:
            agent.tasks_completed += 1
            agent.last_active = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "data": log.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ============ 对话历史 API ============

@app.route('/api/chat-history')
def get_chat_history():
    """获取对话历史"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        history = ChatHistory.query.order_by(
            ChatHistory.timestamp.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "success": True,
            "data": [msg.to_dict() for msg in history.items],
            "total": history.total,
            "pages": history.pages,
            "current_page": page
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/chat-history', methods=['POST'])
def add_chat_message():
    """添加对话记录"""
    try:
        data = request.get_json()
        
        msg = ChatHistory(
            sender=data.get('sender'),
            content=data.get('content'),
            agent_mentioned=data.get('agent_mentioned'),
            timestamp=datetime.utcnow()
        )
        
        db.session.add(msg)
        
        # 更新 agent 消息计数
        if data.get('agent_mentioned'):
            agent = Agent.query.get(data['agent_mentioned'])
            if agent:
                agent.messages_processed += 1
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "data": msg.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ============ 统计 API ============

@app.route('/api/stats')
def get_stats():
    """获取统计信息"""
    try:
        # 计算统计数据
        total_tasks = db.session.query(db.func.sum(Agent.tasks_completed)).scalar() or 0
        total_messages = db.session.query(db.func.sum(Agent.messages_processed)).scalar() or 0
        agents_online = Agent.query.filter_by(status='online').count()
        
        # 获取今日统计
        today = datetime.utcnow().date()
        today_stats = StatRecord.query.filter_by(date=today).first()
        
        stats = {
            "total_tasks": total_tasks,
            "total_messages": total_messages,
            "agents_online": agents_online,
            "agents_total": Agent.query.count(),
            "uptime": "运行中",  # TODO: 计算实际运行时间
            "today_tasks": today_stats.total_tasks if today_stats else 0,
            "today_messages": today_stats.total_messages if today_stats else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============ 配置 API ============

@app.route('/api/config')
def get_config():
    """获取配置"""
    try:
        configs = Config.query.all()
        config_dict = {c.key: json.loads(c.value) if c.value.startswith('{') or c.value.startswith('[') else c.value 
                       for c in configs}
        
        return jsonify({
            "success": True,
            "data": config_dict
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        data = request.get_json()
        
        for key, value in data.items():
            config = Config.query.get(key)
            value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            
            if config:
                config.value = value_str
                config.updated_at = datetime.utcnow()
            else:
                config = Config(key=key, value=value_str)
                db.session.add(config)
        
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ============ SSE 实时流 ============

@app.route('/api/stream')
def stream():
    """SSE 实时数据流"""
    def event_stream():
        while True:
            try:
                # 从数据库获取最新状态
                agents = Agent.query.all()
                agents_data = {a.id: a.to_dict() for a in agents}
                
                # 尝试获取 OpenClaw 实时状态
                status = openclaw.get_status()
                
                data = {
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "agents": agents_data,
                    "openclaw_status": "connected" if status.get('success') else "disconnected"
                }
                yield f"data: {json.dumps(data)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
            time.sleep(5)  # 每5秒发送一次心跳
    
    return Response(event_stream(), mimetype='text/event-stream')


# ============ OpenClaw 状态 API ============

@app.route('/api/openclaw/status')
def get_openclaw_status():
    """获取 OpenClaw 网关状态"""
    try:
        status = openclaw.get_status()
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/openclaw/sessions')
def get_openclaw_sessions():
    """获取 OpenClaw 会话列表"""
    try:
        active_minutes = request.args.get('active_minutes', 60, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        sessions = openclaw.get_sessions(active_minutes=active_minutes, limit=limit)
        return jsonify({
            "success": True,
            "data": sessions
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============ 启动 ============

if __name__ == '__main__':
    print("=" * 50)
    print("TangyuanAT Agent Team Monitor")
    print("=" * 50)
    print(f"Dashboard: http://localhost:5000")
    print(f"Database: {DATABASE_PATH}")
    print("Agents: Xilian (昔涟) & Tangyuan (汤圆)")
    print("=" * 50)
    
    # 记录启动日志
    with app.app_context():
        xilian = Agent.query.get('xilian')
        tangyuan = Agent.query.get('tangyuan')
        
        if xilian:
            log = WorkLog(agent_id='xilian', agent_name='昔涟', 
                         action='系统启动', details='TangyuanAT 监控平台初始化完成')
            db.session.add(log)
        
        if tangyuan:
            log = WorkLog(agent_id='tangyuan', agent_name='汤圆',
                         action='系统启动', details='汤圆已上线，等待指令喵~')
            db.session.add(log)
        
        db.session.commit()
    
    app.run(host='0.0.0.0', port=5000, debug=True)