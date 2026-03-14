"""
Pytest 配置和共享 fixtures
"""

import pytest
import os
import sys
import tempfile

# 设置测试环境变量（在导入 app 之前）
os.environ['TESTING'] = 'true'

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 创建临时数据库路径
_db_fd, _db_path = tempfile.mkstemp(suffix='.db')
os.environ['DATABASE_URL'] = f'sqlite:///{_db_path}'

# 现在导入 app（会在测试配置下初始化）
from app import app as flask_app
from models import db, Agent, WorkLog, ChatHistory, StatRecord, Config


@pytest.fixture
def app():
    """创建测试用的 Flask 应用"""
    # 使用临时数据库
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # 配置测试数据库
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with flask_app.app_context():
        # 删除所有表并重新创建（确保干净状态）
        db.drop_all()
        db.create_all()
        # 初始化测试数据
        init_test_data()
    
    yield flask_app
    
    # 清理
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建 CLI 测试运行器"""
    return app.test_cli_runner()


@pytest.fixture
def sample_agent_data():
    """示例 agent 数据"""
    return {
        'id': 'test_agent',
        'name': '测试Agent',
        'english_name': 'TestAgent',
        'status': 'online',
        'model': 'test-model',
        'role': '测试角色',
        'character': '测试性格',
        'emoji': '🧪',
        'skills': ['测试', '示例'],
        'config': {'key': 'value'}
    }


@pytest.fixture
def sample_log_data():
    """示例日志数据"""
    return {
        'agent_id': 'test_agent',
        'agent_name': '测试Agent',
        'action': '执行测试',
        'details': '这是一个测试日志'
    }


@pytest.fixture
def sample_chat_data():
    """示例对话数据"""
    return {
        'sender': 'user',
        'content': '你好，测试消息',
        'agent_mentioned': 'test_agent'
    }


def init_test_data():
    """初始化测试数据"""
    # 创建测试 agent
    agent = Agent(
        id='test_agent',
        name='测试Agent',
        english_name='TestAgent',
        status='online',
        model='test-model',
        role='测试角色',
        character='测试性格',
        emoji='🧪',
        skills='["测试", "示例"]',
        config='{"key": "value"}'
    )
    db.session.add(agent)
    
    # 创建测试日志
    log = WorkLog(
        agent_id='test_agent',
        agent_name='测试Agent',
        action='初始化',
        details='系统初始化测试数据'
    )
    db.session.add(log)
    
    # 创建测试配置
    config = Config(
        key='test_config',
        value='test_value',
        description='测试配置项'
    )
    db.session.add(config)
    
    db.session.commit()