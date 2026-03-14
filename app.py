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
import psutil  # 系统资源监控

# 导入数据库模型
from models import db, Agent, WorkLog, ChatHistory, StatRecord, Config, Alert, AlertRule, AlertNotification, init_db

# 导入 OpenClaw 客户端
from agents import get_client, get_alert_manager, init_alert_manager

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
                
                # 检查告警
                alerts_data = []
                try:
                    alert_manager = get_alert_manager(db)
                    for agent in agents:
                        if agent.last_active:
                            alert = alert_manager.check_agent_offline(agent.id, agent.last_active)
                            if alert:
                                alerts_data.append(alert.to_dict())
                except Exception as e:
                    pass  # 告警检查失败不影响主流程
                
                data = {
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "agents": agents_data,
                    "openclaw_status": "connected" if status.get('success') else "disconnected",
                    "alerts": alerts_data
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


# ============ 告警 API ============

@app.route('/api/alerts')
def get_alerts():
    """获取告警列表"""
    try:
        status = request.args.get('status')
        agent_id = request.args.get('agent_id')
        alert_type = request.args.get('alert_type')
        limit = request.args.get('limit', 100, type=int)
        
        query = Alert.query
        
        if status:
            query = query.filter_by(status=status)
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        if alert_type:
            query = query.filter_by(alert_type=alert_type)
        
        alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
        
        return jsonify({
            "success": True,
            "data": [a.to_dict() for a in alerts],
            "count": len(alerts)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/alerts/active')
def get_active_alerts():
    """获取活跃告警"""
    try:
        agent_id = request.args.get('agent_id')
        limit = request.args.get('limit', 100, type=int)
        
        alert_manager = get_alert_manager(db)
        alerts = alert_manager.get_active_alerts(agent_id=agent_id, limit=limit)
        
        return jsonify({
            "success": True,
            "data": [a.to_dict() for a in alerts],
            "count": len(alerts)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/alerts/<int:alert_id>')
def get_alert(alert_id):
    """获取单个告警详情"""
    try:
        alert = Alert.query.get(alert_id)
        if alert:
            return jsonify({
                "success": True,
                "data": alert.to_dict()
            })
        return jsonify({"success": False, "error": "Alert not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """确认告警"""
    try:
        data = request.get_json() or {}
        acknowledged_by = data.get('acknowledged_by', 'system')
        
        alert_manager = get_alert_manager(db)
        alert = alert_manager.acknowledge_alert(alert_id, acknowledged_by)
        
        if alert:
            return jsonify({
                "success": True,
                "data": alert.to_dict()
            })
        return jsonify({"success": False, "error": "Alert not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """解决告警"""
    try:
        alert_manager = get_alert_manager(db)
        alert = alert_manager.resolve_alert(alert_id)
        
        if alert:
            return jsonify({
                "success": True,
                "data": alert.to_dict()
            })
        return jsonify({"success": False, "error": "Alert not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """创建自定义告警"""
    try:
        data = request.get_json()
        
        alert_manager = get_alert_manager(db)
        alert = alert_manager.create_custom_alert(
            agent_id=data.get('agent_id'),
            title=data.get('title'),
            message=data.get('message'),
            severity=data.get('severity', 'warning'),
            details=data.get('details')
        )
        
        return jsonify({
            "success": True,
            "data": alert.to_dict()
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/alerts/stats')
def get_alert_stats():
    """获取告警统计"""
    try:
        alert_manager = get_alert_manager(db)
        stats = alert_manager.get_alert_stats()
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/alerts/<int:alert_id>/notify', methods=['POST'])
def send_alert_notification(alert_id):
    """发送告警通知"""
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({"success": False, "error": "Alert not found"}), 404
        
        data = request.get_json() or {}
        channel = data.get('channel', 'feishu')
        
        alert_manager = get_alert_manager(db)
        
        if channel == 'feishu':
            webhook_url = data.get('webhook_url')
            success = alert_manager.send_feishu_notification(alert, webhook_url)
            
            return jsonify({
                "success": success,
                "message": "飞书通知发送成功" if success else "飞书通知发送失败"
            })
        
        return jsonify({"success": False, "error": f"不支持的通知渠道: {channel}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/alerts/history')
def get_alert_history():
    """获取告警历史"""
    try:
        agent_id = request.args.get('agent_id')
        alert_type = request.args.get('alert_type')
        status = request.args.get('status')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        limit = request.args.get('limit', 100, type=int)
        
        # 解析时间
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None
        
        alert_manager = get_alert_manager(db)
        alerts = alert_manager.get_alert_history(
            agent_id=agent_id,
            alert_type=alert_type,
            status=status,
            start_time=start_dt,
            end_time=end_dt,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": [a.to_dict() for a in alerts],
            "count": len(alerts)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============ 系统监控 API ============

@app.route('/api/monitoring/health')
def get_system_health():
    """获取系统整体健康状态"""
    try:
        # 数据库连接检查
        db_status = "healthy"
        db_message = "Connected"
        try:
            # 执行简单查询测试连接
            db.session.execute(db.text('SELECT 1'))
        except Exception as e:
            db_status = "unhealthy"
            db_message = str(e)
        
        # OpenClaw 网关检查
        openclaw_status = openclaw.get_status()
        gateway_status = "healthy" if openclaw_status.get('success') else "unhealthy"
        
        # 系统资源
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 计算整体健康分数
        health_score = 100
        if db_status == "unhealthy":
            health_score -= 30
        if gateway_status == "unhealthy":
            health_score -= 20
        if cpu_percent > 80:
            health_score -= 15
        if memory.percent > 80:
            health_score -= 15
        if disk.percent > 90:
            health_score -= 10
        
        health_score = max(0, health_score)
        
        return jsonify({
            "success": True,
            "data": {
                "status": "healthy" if health_score >= 70 else "degraded" if health_score >= 40 else "unhealthy",
                "score": health_score,
                "components": {
                    "database": {
                        "status": db_status,
                        "message": db_message,
                        "type": "sqlite"
                    },
                    "gateway": {
                        "status": gateway_status,
                        "message": "OpenClaw gateway " + ("connected" if gateway_status == "healthy" else "disconnected"),
                        "url": openclaw_status.get('url', 'N/A')
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/monitoring/database')
def get_database_status():
    """获取数据库连接状态"""
    try:
        # 测试连接
        start_time = time.time()
        db.session.execute(db.text('SELECT 1'))
        latency = (time.time() - start_time) * 1000  # ms
        
        # 获取数据库信息
        db_size = os.path.getsize(DATABASE_PATH) if os.path.exists(DATABASE_PATH) else 0
        
        # 获取表统计
        agent_count = Agent.query.count()
        log_count = WorkLog.query.count()
        chat_count = ChatHistory.query.count()
        
        return jsonify({
            "success": True,
            "data": {
                "status": "connected",
                "type": "SQLite",
                "path": DATABASE_PATH,
                "size_bytes": db_size,
                "size_human": f"{db_size / 1024:.1f} KB",
                "latency_ms": round(latency, 2),
                "tables": {
                    "agents": agent_count,
                    "work_logs": log_count,
                    "chat_history": chat_count
                },
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "data": {
                "status": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        })


@app.route('/api/monitoring/gateway')
def get_gateway_status():
    """获取 OpenClaw 网关状态"""
    try:
        status = openclaw.get_status()
        
        return jsonify({
            "success": True,
            "data": {
                "status": "connected" if status.get('success') else "disconnected",
                "url": status.get('url', 'N/A'),
                "version": status.get('version', 'N/A'),
                "uptime": status.get('uptime', 'N/A'),
                "sessions": status.get('sessions', 0),
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "data": {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        })


@app.route('/api/monitoring/resources')
def get_system_resources():
    """获取系统资源使用情况"""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # 内存
        memory = psutil.virtual_memory()
        
        # 磁盘
        disk = psutil.disk_usage('/')
        
        # 网络 (可选)
        try:
            net_io = psutil.net_io_counters()
            network = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        except:
            network = None
        
        # 进程信息
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return jsonify({
            "success": True,
            "data": {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "freq_mhz": cpu_freq.current if cpu_freq else None
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": disk.percent
                },
                "network": network,
                "process": {
                    "memory_mb": round(process_memory.rss / (1024**2), 2),
                    "cpu_percent": process.cpu_percent()
                },
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/monitoring/resources/history')
def get_resource_history():
    """获取资源使用历史 (最近 N 个数据点)"""
    try:
        limit = request.args.get('limit', 60, type=int)  # 默认最近60个点
        
        # 从 StatRecord 获取历史数据
        today = datetime.utcnow().date()
        records = StatRecord.query.order_by(StatRecord.date.desc()).limit(limit).all()
        
        history = [{
            "date": r.date.isoformat(),
            "tasks": r.total_tasks,
            "messages": r.total_messages
        } for r in records]
        
        return jsonify({
            "success": True,
            "data": history[::-1]  # 按时间正序
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/monitoring/logs/errors')
def get_error_logs():
    """获取错误日志"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # 查找包含错误关键词的日志
        error_keywords = ['error', 'fail', 'exception', '错误', '失败']
        logs = WorkLog.query.filter(
            db.or_(*[WorkLog.details.ilike(f'%{kw}%') for kw in error_keywords])
        ).order_by(WorkLog.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            "success": True,
            "data": [log.to_dict() for log in logs],
            "count": len(logs)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/monitoring/logs/aggregate')
def get_log_aggregation():
    """获取日志聚合统计"""
    try:
        from sqlalchemy import func
        
        # 按动作类型聚合
        action_stats = db.session.query(
            WorkLog.action,
            func.count(WorkLog.id).label('count')
        ).group_by(WorkLog.action).all()
        
        # 按 Agent 聚合
        agent_stats = db.session.query(
            WorkLog.agent_name,
            func.count(WorkLog.id).label('count')
        ).group_by(WorkLog.agent_name).all()
        
        # 按日期聚合 (最近7天)
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_stats = db.session.query(
            func.date(WorkLog.timestamp).label('date'),
            func.count(WorkLog.id).label('count')
        ).filter(
            WorkLog.timestamp >= seven_days_ago
        ).group_by(
            func.date(WorkLog.timestamp)
        ).all()
        
        return jsonify({
            "success": True,
            "data": {
                "by_action": [{"action": a, "count": c} for a, c in action_stats],
                "by_agent": [{"agent": a, "count": c} for a, c in agent_stats],
                "by_day": [{"date": str(d), "count": c} for d, c in daily_stats]
            }
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
    
    # 初始化告警管理器
    init_alert_manager(app, db)
    print("Alert Manager initialized")
    
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