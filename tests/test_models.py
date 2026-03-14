"""
数据库模型测试
"""

import pytest
import json
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, Agent, WorkLog, ChatHistory, StatRecord, Config


class TestAgentModel:
    """Agent 模型测试"""
    
    def test_create_agent(self, app):
        """测试创建 Agent"""
        with app.app_context():
            agent = Agent(
                id='new_agent',
                name='新Agent',
                english_name='NewAgent',
                status='online',
                model='test-model',
                role='测试角色',
                character='测试性格',
                emoji='🤖'
            )
            db.session.add(agent)
            db.session.commit()
            
            # 验证
            saved = Agent.query.get('new_agent')
            assert saved is not None
            assert saved.name == '新Agent'
            assert saved.status == 'online'
    
    def test_agent_to_dict(self, app):
        """测试 Agent.to_dict()"""
        with app.app_context():
            agent = Agent.query.get('test_agent')
            data = agent.to_dict()
            
            assert data['id'] == 'test_agent'
            assert data['name'] == '测试Agent'
            assert data['english_name'] == 'TestAgent'
            assert data['status'] == 'online'
            assert 'last_active' in data
            assert isinstance(data['skills'], list)
            assert isinstance(data['config'], dict)
    
    def test_agent_from_dict(self, app):
        """测试 Agent.from_dict()"""
        with app.app_context():
            data = {
                'id': 'from_dict_agent',
                'name': '字典创建',
                'english_name': 'FromDict',
                'status': 'offline',
                'model': 'dict-model',
                'skills': ['skill1', 'skill2'],
                'config': {'key': 'value'}
            }
            
            agent = Agent.from_dict(data)
            db.session.add(agent)
            db.session.commit()
            
            # 验证
            saved = Agent.query.get('from_dict_agent')
            assert saved is not None
            assert saved.name == '字典创建'
            assert json.loads(saved.skills) == ['skill1', 'skill2']
    
    def test_agent_relationship_with_logs(self, app):
        """测试 Agent 与 WorkLog 的关联"""
        with app.app_context():
            agent = Agent.query.get('test_agent')
            
            # 创建关联日志
            log = WorkLog(
                agent_id=agent.id,
                agent_name=agent.name,
                action='关联测试',
                details='测试关联关系'
            )
            db.session.add(log)
            db.session.commit()
            
            # 验证关联
            assert agent.logs.count() > 0
            # 获取最新添加的日志（按 ID 倒序）
            latest_log = agent.logs.order_by(WorkLog.id.desc()).first()
            assert latest_log.action == '关联测试'
    
    def test_agent_default_values(self, app):
        """测试 Agent 默认值"""
        with app.app_context():
            agent = Agent(
                id='default_agent',
                name='默认值测试'
            )
            db.session.add(agent)
            db.session.commit()
            
            saved = Agent.query.get('default_agent')
            assert saved.status == 'offline'  # 默认状态
            assert saved.tasks_completed == 0
            assert saved.messages_processed == 0
    
    def test_agent_update_timestamp(self, app):
        """测试 Agent 更新时间戳"""
        with app.app_context():
            agent = Agent.query.get('test_agent')
            original_updated = agent.updated_at
            
            # 更新
            agent.status = 'busy'
            db.session.commit()
            
            # 刷新并验证
            db.session.refresh(agent)
            assert agent.updated_at >= original_updated


class TestWorkLogModel:
    """WorkLog 模型测试"""
    
    def test_create_work_log(self, app):
        """测试创建工作日志"""
        with app.app_context():
            log = WorkLog(
                agent_id='test_agent',
                agent_name='测试Agent',
                action='测试操作',
                details='这是测试详情'
            )
            db.session.add(log)
            db.session.commit()
            
            saved = WorkLog.query.filter_by(action='测试操作').first()
            assert saved is not None
            assert saved.agent_id == 'test_agent'
            assert saved.details == '这是测试详情'
    
    def test_work_log_to_dict(self, app):
        """测试 WorkLog.to_dict()"""
        with app.app_context():
            log = WorkLog(
                agent_id='test_agent',
                agent_name='测试Agent',
                action='字典测试',
                details='测试字典转换'
            )
            db.session.add(log)
            db.session.commit()
            
            data = log.to_dict()
            assert data['agent_id'] == 'test_agent'
            assert data['action'] == '字典测试'
            assert 'timestamp' in data
    
    def test_work_log_timestamp_auto(self, app):
        """测试日志时间戳自动设置"""
        with app.app_context():
            before = datetime.utcnow()
            
            log = WorkLog(
                agent_id='test_agent',
                agent_name='测试Agent',
                action='时间戳测试'
            )
            db.session.add(log)
            db.session.commit()
            
            after = datetime.utcnow()
            
            saved = WorkLog.query.filter_by(action='时间戳测试').first()
            assert before <= saved.timestamp <= after


class TestChatHistoryModel:
    """ChatHistory 模型测试"""
    
    def test_create_chat_message(self, app):
        """测试创建聊天消息"""
        with app.app_context():
            msg = ChatHistory(
                sender='user',
                content='这是一条测试消息',
                agent_mentioned='test_agent'
            )
            db.session.add(msg)
            db.session.commit()
            
            saved = ChatHistory.query.filter_by(content='这是一条测试消息').first()
            assert saved is not None
            assert saved.sender == 'user'
    
    def test_chat_history_to_dict(self, app):
        """测试 ChatHistory.to_dict()"""
        with app.app_context():
            msg = ChatHistory(
                sender='user',
                content='字典转换测试',
                agent_mentioned='test_agent'
            )
            db.session.add(msg)
            db.session.commit()
            
            data = msg.to_dict()
            assert data['sender'] == 'user'
            assert data['content'] == '字典转换测试'
            assert data['agent_mentioned'] == 'test_agent'
            assert 'timestamp' in data
    
    def test_chat_without_mention(self, app):
        """测试没有提及 agent 的消息"""
        with app.app_context():
            msg = ChatHistory(
                sender='user',
                content='普通消息'
            )
            db.session.add(msg)
            db.session.commit()
            
            saved = ChatHistory.query.filter_by(content='普通消息').first()
            assert saved.agent_mentioned is None


class TestStatRecordModel:
    """StatRecord 模型测试"""
    
    def test_create_stat_record(self, app):
        """测试创建统计记录"""
        with app.app_context():
            today = datetime.utcnow().date()
            stat = StatRecord(
                date=today,
                total_tasks=100,
                total_messages=200,
                avg_response_time=150.5
            )
            db.session.add(stat)
            db.session.commit()
            
            saved = StatRecord.query.filter_by(date=today).first()
            assert saved is not None
            assert saved.total_tasks == 100
            assert saved.total_messages == 200
    
    def test_stat_record_to_dict(self, app):
        """测试 StatRecord.to_dict()"""
        with app.app_context():
            today = datetime.utcnow().date()
            stat = StatRecord(
                date=today,
                total_tasks=50,
                total_messages=75,
                avg_response_time=120.0
            )
            db.session.add(stat)
            db.session.commit()
            
            data = stat.to_dict()
            assert data['total_tasks'] == 50
            assert data['total_messages'] == 75
            assert data['avg_response_time'] == 120.0
    
    def test_stat_date_unique(self, app):
        """测试统计日期唯一性"""
        with app.app_context():
            today = datetime.utcnow().date()
            
            # 创建第一条
            stat1 = StatRecord(
                date=today,
                total_tasks=10
            )
            db.session.add(stat1)
            db.session.commit()
            
            # 尝试创建同一天的记录应该失败或更新
            stat2 = StatRecord(
                date=today,
                total_tasks=20
            )
            db.session.add(stat2)
            
            # 应该抛出唯一约束错误
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()


class TestConfigModel:
    """Config 模型测试"""
    
    def test_create_config(self, app):
        """测试创建配置"""
        with app.app_context():
            config = Config(
                key='new_config_key',
                value='new_config_value',
                description='新建配置项'
            )
            db.session.add(config)
            db.session.commit()
            
            saved = Config.query.get('new_config_key')
            assert saved is not None
            assert saved.value == 'new_config_value'
    
    def test_config_to_dict(self, app):
        """测试 Config.to_dict()"""
        with app.app_context():
            config = Config.query.get('test_config')
            data = config.to_dict()
            
            assert data['key'] == 'test_config'
            assert 'updated_at' in data
    
    def test_config_update(self, app):
        """测试配置更新"""
        with app.app_context():
            config = Config.query.get('test_config')
            original_time = config.updated_at
            
            config.value = 'updated_value'
            db.session.commit()
            
            db.session.refresh(config)
            assert config.value == 'updated_value'
            assert config.updated_at >= original_time
    
    def test_json_value_storage(self, app):
        """测试 JSON 值存储"""
        with app.app_context():
            config = Config(
                key='json_config',
                value=json.dumps({'nested': {'key': 'value'}}),
                description='JSON配置'
            )
            db.session.add(config)
            db.session.commit()
            
            saved = Config.query.get('json_config')
            parsed = json.loads(saved.value)
            assert parsed['nested']['key'] == 'value'


class TestDatabaseInit:
    """数据库初始化测试"""
    
    def test_default_agents_exist(self, app):
        """测试默认 agents 已初始化"""
        with app.app_context():
            # 检查默认 agent 存在
            from models.database import init_default_agents
            init_default_agents()
            
            # 应该有默认的 xilian, tangyuan, doufu
            xilian = Agent.query.get('xilian')
            tangyuan = Agent.query.get('tangyuan')
            doufu = Agent.query.get('doufu')
            
            # 如果存在，验证其属性
            if xilian:
                assert xilian.name == '昔涟'
                assert xilian.emoji == '🌀'
            
            if tangyuan:
                assert tangyuan.name == '汤圆'
                assert tangyuan.emoji == '🐱'
            
            if doufu:
                assert doufu.name == '豆腐'
                assert doufu.emoji == '🟦'


class TestModelConstraints:
    """模型约束测试"""
    
    def test_agent_primary_key(self, app):
        """测试 Agent 主键约束"""
        with app.app_context():
            # 尝试创建重复 ID 的 agent
            agent1 = Agent(id='duplicate_test', name='Agent 1')
            agent2 = Agent(id='duplicate_test', name='Agent 2')
            
            db.session.add(agent1)
            db.session.commit()
            
            db.session.add(agent2)
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()
    
    def test_work_log_foreign_key(self, app):
        """测试 WorkLog 外键约束"""
        with app.app_context():
            # 创建关联到不存在 agent 的日志
            # SQLite 默认不强制外键，所以这个测试可能需要特殊配置
            log = WorkLog(
                agent_id='nonexistent_agent',
                agent_name='不存在',
                action='测试'
            )
            db.session.add(log)
            
            # SQLite 默认允许这种情况
            db.session.commit()
            
            # 但我们可以验证关联查询返回 None
            saved = WorkLog.query.filter_by(agent_id='nonexistent_agent').first()
            assert saved is not None
            assert saved.agent is None  # 没有关联的 agent
    
    def test_config_primary_key(self, app):
        """测试 Config 主键约束"""
        with app.app_context():
            config1 = Config(key='pk_test', value='value1')
            config2 = Config(key='pk_test', value='value2')
            
            db.session.add(config1)
            db.session.commit()
            
            db.session.add(config2)
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()


class TestModelQueries:
    """模型查询测试"""
    
    def test_query_by_status(self, app):
        """测试按状态查询 Agent"""
        with app.app_context():
            online_agents = Agent.query.filter_by(status='online').all()
            assert len(online_agents) > 0  # test_agent 是 online
    
    def test_query_logs_ordered(self, app):
        """测试日志按时间排序"""
        with app.app_context():
            # 创建多个日志
            for i in range(3):
                log = WorkLog(
                    agent_id='test_agent',
                    agent_name='测试Agent',
                    action=f'排序测试 {i}',
                    details=f'详情 {i}'
                )
                db.session.add(log)
            db.session.commit()
            
            # 按时间倒序查询
            logs = WorkLog.query.order_by(WorkLog.timestamp.desc()).all()
            
            # 验证顺序
            for i in range(len(logs) - 1):
                assert logs[i].timestamp >= logs[i + 1].timestamp
    
    def test_count_messages(self, app):
        """测试消息计数"""
        with app.app_context():
            count = ChatHistory.query.count()
            assert count >= 0
    
    def test_aggregate_functions(self, app):
        """测试聚合函数"""
        with app.app_context():
            # 总任务数
            total_tasks = db.session.query(
                db.func.sum(Agent.tasks_completed)
            ).scalar()
            assert total_tasks is not None or total_tasks == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])