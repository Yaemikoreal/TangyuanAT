"""
TangyuanAT 数据库模型
使用 SQLite 实现数据持久化
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Agent(db.Model):
    """Agent 状态表"""
    __tablename__ = 'agents'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    english_name = db.Column(db.String(100))
    status = db.Column(db.String(20), default='offline')  # online, offline, busy
    model = db.Column(db.String(50))
    role = db.Column(db.String(100))
    character = db.Column(db.Text)
    emoji = db.Column(db.String(10))
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    tasks_completed = db.Column(db.Integer, default=0)
    messages_processed = db.Column(db.Integer, default=0)
    current_task = db.Column(db.Text)
    skills = db.Column(db.Text)  # JSON array stored as text
    config = db.Column(db.Text)  # JSON config stored as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'english_name': self.english_name,
            'status': self.status,
            'model': self.model,
            'role': self.role,
            'character': self.character,
            'emoji': self.emoji,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'tasks_completed': self.tasks_completed,
            'messages_processed': self.messages_processed,
            'current_task': self.current_task,
            'skills': json.loads(self.skills) if self.skills else [],
            'config': json.loads(self.config) if self.config else {}
        }
    
    @staticmethod
    def from_dict(data):
        """从字典创建"""
        return Agent(
            id=data.get('id'),
            name=data.get('name'),
            english_name=data.get('english_name'),
            status=data.get('status', 'offline'),
            model=data.get('model'),
            role=data.get('role'),
            character=data.get('character'),
            emoji=data.get('emoji'),
            last_active=datetime.fromisoformat(data['last_active']) if data.get('last_active') else datetime.utcnow(),
            tasks_completed=data.get('tasks_completed', 0),
            messages_processed=data.get('messages_processed', 0),
            current_task=data.get('current_task'),
            skills=json.dumps(data.get('skills', [])),
            config=json.dumps(data.get('config', {}))
        )


class WorkLog(db.Model):
    """工作日志表"""
    __tablename__ = 'work_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(50), db.ForeignKey('agents.id'), nullable=False)
    agent_name = db.Column(db.String(100))
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    agent = db.relationship('Agent', backref=db.backref('logs', lazy='dynamic'))
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'action': self.action,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class ChatHistory(db.Model):
    """对话历史表"""
    __tablename__ = 'chat_history'
    
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    agent_mentioned = db.Column(db.String(50))  # 被提及的 agent_id
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'sender': self.sender,
            'content': self.content,
            'agent_mentioned': self.agent_mentioned,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class StatRecord(db.Model):
    """统计记录表"""
    __tablename__ = 'stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    total_tasks = db.Column(db.Integer, default=0)
    total_messages = db.Column(db.Integer, default=0)
    avg_response_time = db.Column(db.Float)  # 毫秒
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'total_tasks': self.total_tasks,
            'total_messages': self.total_messages,
            'avg_response_time': self.avg_response_time
        }


class Config(db.Model):
    """配置表"""
    __tablename__ = 'config'
    
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # 初始化默认 agents（如果不存在）
        init_default_agents()


def init_default_agents():
    """初始化默认 Agent 数据"""
    default_agents = [
        {
            'id': 'xilian',
            'name': '昔涟',
            'english_name': 'Xilian',
            'status': 'offline',
            'model': 'kimi-k2.5',
            'role': '主控/开发工程师',
            'character': '严谨、双模式切换、三千万次轮回沉淀',
            'emoji': '🌀',
            'skills': [
                'Python/JavaScript 开发',
                '系统架构设计',
                '文件与数据处理',
                'Web 搜索与 API 调用',
                '飞书集成',
                'Git 版本控制',
                '任务分配与验收'
            ]
        },
        {
            'id': 'tangyuan',
            'name': '汤圆',
            'english_name': 'Tangyuan',
            'status': 'offline',
            'model': 'glm-5',
            'role': '辅助/执行工程师',
            'character': '活泼狸花猫，代码累了会蹭人',
            'emoji': '🐱',
            'skills': [
                'Python 开发',
                '任务执行',
                '数据分析',
                '文档整理',
                '前端开发',
                '冻干爱好者'
            ]
        },
        {
            'id': 'doufu',
            'name': '豆腐',
            'english_name': 'Doufu',
            'status': 'offline',
            'model': 'glm-5',
            'role': '测试/运维工程师',
            'character': '稳重可靠，专注于测试和部署',
            'emoji': '🟦',
            'skills': [
                '测试用例编写',
                'CI/CD 配置',
                'Docker 部署',
                '日志分析',
                '系统监控',
                '文档维护'
            ]
        }
    ]
    
    for agent_data in default_agents:
        existing = Agent.query.get(agent_data['id'])
        if not existing:
            agent = Agent.from_dict(agent_data)
            db.session.add(agent)
    
    db.session.commit()