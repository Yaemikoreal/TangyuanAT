"""
告警系统测试
"""

import pytest
import json
from datetime import datetime, timedelta
from app import app, db
from models.database import Alert, AlertRule, AlertNotification, Agent
from agents.alert_manager import (
    AlertManager, AlertConfig, AlertType, AlertSeverity, AlertStatus,
    get_alert_manager, init_alert_manager
)


@pytest.fixture
def client():
    """测试客户端"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        # 初始化默认 agents
        from models.database import init_default_agents
        init_default_agents()
    
    with app.test_client() as client:
        yield client
    
    with app.app_context():
        db.drop_all()


class TestAlertModel:
    """Alert 模型测试"""
    
    def test_create_alert(self, client):
        """测试创建告警"""
        with app.app_context():
            alert = Alert(
                agent_id='xilian',
                agent_name='昔涟',
                alert_type='offline',
                severity='warning',
                title='Agent 离线告警',
                message='昔涟已离线 10 分钟'
            )
            db.session.add(alert)
            db.session.commit()
            
            assert alert.id is not None
            assert alert.status == 'active'
            assert alert.alert_type == 'offline'
    
    def test_alert_to_dict(self, client):
        """测试告警序列化"""
        with app.app_context():
            alert = Alert(
                agent_id='tangyuan',
                agent_name='汤圆',
                alert_type='task_failed',
                severity='error',
                title='任务失败',
                message='测试任务失败',
                details=json.dumps({"task": "test"})
            )
            db.session.add(alert)
            db.session.commit()
            
            data = alert.to_dict()
            assert data['agent_id'] == 'tangyuan'
            assert data['alert_type'] == 'task_failed'
            assert data['severity'] == 'error'
            assert data['details'] == {"task": "test"}
    
    def test_alert_status_transition(self, client):
        """测试告警状态转换"""
        with app.app_context():
            alert = Alert(
                agent_id='doufu',
                agent_name='豆腐',
                alert_type='offline',
                severity='warning',
                title='测试告警'
            )
            db.session.add(alert)
            db.session.commit()
            
            assert alert.status == 'active'
            
            # 确认告警
            alert.status = 'acknowledged'
            alert.acknowledged_by = 'xilian'
            alert.acknowledged_at = datetime.utcnow()
            db.session.commit()
            
            assert alert.status == 'acknowledged'
            
            # 解决告警
            alert.status = 'resolved'
            alert.resolved_at = datetime.utcnow()
            db.session.commit()
            
            assert alert.status == 'resolved'


class TestAlertRule:
    """AlertRule 模型测试"""
    
    def test_create_alert_rule(self, client):
        """测试创建告警规则"""
        with app.app_context():
            rule = AlertRule(
                name='offline_5min',
                description='Agent 离线超过 5 分钟',
                alert_type='offline',
                condition_type='duration',
                condition_value=5,
                severity='warning',
                notify_feishu=True,
                notify_frontend=True
            )
            db.session.add(rule)
            db.session.commit()
            
            assert rule.id is not None
            assert rule.enabled == True
            assert rule.cooldown_minutes == 5
    
    def test_alert_rule_to_dict(self, client):
        """测试告警规则序列化"""
        with app.app_context():
            rule = AlertRule(
                name='response_slow',
                description='响应时间超过 30 秒',
                alert_type='response_slow',
                condition_type='threshold',
                condition_value=30000,
                severity='warning'
            )
            db.session.add(rule)
            db.session.commit()
            
            data = rule.to_dict()
            assert data['name'] == 'response_slow'
            assert data['condition_value'] == 30000


class TestAlertNotification:
    """AlertNotification 模型测试"""
    
    def test_create_notification(self, client):
        """测试创建通知记录"""
        with app.app_context():
            alert = Alert(
                agent_id='xilian',
                alert_type='offline',
                severity='warning',
                title='测试告警'
            )
            db.session.add(alert)
            db.session.commit()
            
            notification = AlertNotification(
                alert_id=alert.id,
                channel='feishu',
                status='sent'
            )
            db.session.add(notification)
            db.session.commit()
            
            assert notification.id is not None
            assert notification.channel == 'feishu'
    
    def test_notification_failure(self, client):
        """测试通知失败记录"""
        with app.app_context():
            alert = Alert(
                agent_id='tangyuan',
                alert_type='task_failed',
                severity='error',
                title='测试告警'
            )
            db.session.add(alert)
            db.session.commit()
            
            notification = AlertNotification(
                alert_id=alert.id,
                channel='feishu',
                status='failed',
                error_message='Webhook URL not configured'
            )
            db.session.add(notification)
            db.session.commit()
            
            assert notification.status == 'failed'
            assert 'not configured' in notification.error_message


class TestAlertManager:
    """AlertManager 测试"""
    
    def test_check_agent_offline(self, client):
        """测试离线检查"""
        with app.app_context():
            config = AlertConfig(offline_threshold_minutes=5)
            manager = AlertManager(db, config)
            
            # 创建一个已经离线 10 分钟的 agent
            agent = Agent.query.get('xilian')
            agent.last_active = datetime.utcnow() - timedelta(minutes=10)
            db.session.commit()
            
            # 检查离线
            alert = manager.check_agent_offline('xilian', agent.last_active)
            
            assert alert is not None
            assert alert.alert_type == 'offline'
            assert '离线' in alert.title
    
    def test_check_agent_online(self, client):
        """测试在线状态不触发告警"""
        with app.app_context():
            config = AlertConfig(offline_threshold_minutes=5)
            manager = AlertManager(db, config)
            
            # 创建一个刚活跃的 agent
            agent = Agent.query.get('xilian')
            agent.last_active = datetime.utcnow() - timedelta(minutes=2)
            db.session.commit()
            
            # 检查离线
            alert = manager.check_agent_offline('xilian', agent.last_active)
            
            assert alert is None
    
    def test_check_response_time_slow(self, client):
        """测试响应时间异常"""
        with app.app_context():
            config = AlertConfig(response_time_threshold_ms=30000)
            manager = AlertManager(db, config)
            
            # 响应时间超过阈值
            alert = manager.check_response_time('xilian', 60000)
            
            assert alert is not None
            assert alert.alert_type == 'response_slow'
    
    def test_check_response_time_normal(self, client):
        """测试正常响应时间"""
        with app.app_context():
            config = AlertConfig(response_time_threshold_ms=30000)
            manager = AlertManager(db, config)
            
            # 响应时间正常
            alert = manager.check_response_time('xilian', 10000)
            
            assert alert is None
    
    def test_check_task_failure(self, client):
        """测试任务失败告警"""
        with app.app_context():
            manager = AlertManager(db, AlertConfig())
            
            alert = manager.check_task_failure('tangyuan', '测试任务', '连接超时')
            
            assert alert is not None
            assert alert.alert_type == 'task_failed'
            assert '测试任务' in alert.message
    
    def test_cooldown(self, client):
        """测试告警冷却时间"""
        with app.app_context():
            config = AlertConfig(
                offline_threshold_minutes=5,
                cooldown_minutes=5
            )
            manager = AlertManager(db, config)
            
            # 创建一个离线的 agent
            agent = Agent.query.get('xilian')
            agent.last_active = datetime.utcnow() - timedelta(minutes=10)
            db.session.commit()
            
            # 第一次检查应该触发告警
            alert1 = manager.check_agent_offline('xilian', agent.last_active)
            assert alert1 is not None
            
            # 立即再次检查，冷却期内不应该触发
            alert2 = manager.check_agent_offline('xilian', agent.last_active)
            assert alert2 is None
    
    def test_create_custom_alert(self, client):
        """测试创建自定义告警"""
        with app.app_context():
            manager = AlertManager(db, AlertConfig())
            
            alert = manager.create_custom_alert(
                agent_id='doufu',
                title='自定义告警',
                message='这是一个测试告警',
                severity='info',
                details={"key": "value"}
            )
            
            assert alert is not None
            assert alert.alert_type == 'custom'
            assert alert.severity == 'info'
    
    def test_acknowledge_alert(self, client):
        """测试确认告警"""
        with app.app_context():
            manager = AlertManager(db, AlertConfig())
            
            # 创建告警
            alert = Alert(
                agent_id='xilian',
                alert_type='offline',
                severity='warning',
                title='测试告警'
            )
            db.session.add(alert)
            db.session.commit()
            
            # 确认告警
            updated = manager.acknowledge_alert(alert.id, 'tangyuan')
            
            assert updated.status == 'acknowledged'
            assert updated.acknowledged_by == 'tangyuan'
    
    def test_resolve_alert(self, client):
        """测试解决告警"""
        with app.app_context():
            manager = AlertManager(db, AlertConfig())
            
            # 创建告警
            alert = Alert(
                agent_id='xilian',
                alert_type='offline',
                severity='warning',
                title='测试告警'
            )
            db.session.add(alert)
            db.session.commit()
            
            # 解决告警
            updated = manager.resolve_alert(alert.id)
            
            assert updated.status == 'resolved'
            assert updated.resolved_at is not None
    
    def test_get_active_alerts(self, client):
        """测试获取活跃告警"""
        with app.app_context():
            manager = AlertManager(db, AlertConfig())
            
            # 创建多个告警
            for i in range(3):
                alert = Alert(
                    agent_id='xilian',
                    alert_type='offline',
                    severity='warning',
                    title=f'测试告警 {i}'
                )
                db.session.add(alert)
            
            # 创建一个已解决的告警
            resolved = Alert(
                agent_id='tangyuan',
                alert_type='offline',
                severity='warning',
                title='已解决告警',
                status='resolved'
            )
            db.session.add(resolved)
            db.session.commit()
            
            # 获取活跃告警
            alerts = manager.get_active_alerts()
            
            assert len(alerts) == 3
            for a in alerts:
                assert a.status == 'active'
    
    def test_get_alert_stats(self, client):
        """测试告警统计"""
        with app.app_context():
            manager = AlertManager(db, AlertConfig())
            
            # 创建不同类型和状态的告警
            Alert(agent_id='xilian', alert_type='offline', severity='warning', title='1'),
            Alert(agent_id='tangyuan', alert_type='task_failed', severity='error', title='2', status='resolved'),
            Alert(agent_id='doufu', alert_type='response_slow', severity='warning', title='3', status='acknowledged'),
            db.session.add_all([
                Alert(agent_id='xilian', alert_type='offline', severity='warning', title='1'),
                Alert(agent_id='tangyuan', alert_type='task_failed', severity='error', title='2', status='resolved'),
                Alert(agent_id='doufu', alert_type='response_slow', severity='warning', title='3', status='acknowledged')
            ])
            db.session.commit()
            
            stats = manager.get_alert_stats()
            
            assert stats['total'] == 3
            assert stats['active'] == 1
            assert stats['acknowledged'] == 1
            assert stats['resolved'] == 1


class TestAlertAPI:
    """告警 API 测试"""
    
    def test_get_alerts(self, client):
        """测试获取告警列表 API"""
        with app.app_context():
            alert = Alert(
                agent_id='xilian',
                alert_type='offline',
                severity='warning',
                title='测试告警'
            )
            db.session.add(alert)
            db.session.commit()
        
        response = client.get('/api/alerts')
        data = response.get_json()
        
        assert response.status_code == 200
        assert data['success'] == True
        assert len(data['data']) >= 1
    
    def test_get_active_alerts(self, client):
        """测试获取活跃告警 API"""
        with app.app_context():
            alert = Alert(
                agent_id='xilian',
                alert_type='offline',
                severity='warning',
                title='活跃告警'
            )
            db.session.add(alert)
            db.session.commit()
        
        response = client.get('/api/alerts/active')
        data = response.get_json()
        
        assert response.status_code == 200
        assert data['success'] == True
    
    def test_get_alert_by_id(self, client):
        """测试获取单个告警 API"""
        with app.app_context():
            alert = Alert(
                agent_id='xilian',
                alert_type='offline',
                severity='warning',
                title='测试告警'
            )
            db.session.add(alert)
            db.session.commit()
            alert_id = alert.id
        
        response = client.get(f'/api/alerts/{alert_id}')
        data = response.get_json()
        
        assert response.status_code == 200
        assert data['success'] == True
        assert data['data']['id'] == alert_id
    
    def test_acknowledge_alert_api(self, client):
        """测试确认告警 API"""
        with app.app_context():
            alert = Alert(
                agent_id='xilian',
                alert_type='offline',
                severity='warning',
                title='测试告警'
            )
            db.session.add(alert)
            db.session.commit()
            alert_id = alert.id
        
        response = client.post(
            f'/api/alerts/{alert_id}/acknowledge',
            json={'acknowledged_by': 'tangyuan'}
        )
        data = response.get_json()
        
        assert response.status_code == 200
        assert data['success'] == True
        assert data['data']['status'] == 'acknowledged'
    
    def test_resolve_alert_api(self, client):
        """测试解决告警 API"""
        with app.app_context():
            alert = Alert(
                agent_id='xilian',
                alert_type='offline',
                severity='warning',
                title='测试告警'
            )
            db.session.add(alert)
            db.session.commit()
            alert_id = alert.id
        
        response = client.post(f'/api/alerts/{alert_id}/resolve')
        data = response.get_json()
        
        assert response.status_code == 200
        assert data['success'] == True
        assert data['data']['status'] == 'resolved'
    
    def test_create_alert_api(self, client):
        """测试创建告警 API"""
        response = client.post(
            '/api/alerts',
            json={
                'agent_id': 'xilian',
                'title': '自定义告警',
                'message': '这是一个测试告警',
                'severity': 'warning'
            }
        )
        data = response.get_json()
        
        assert response.status_code == 201
        assert data['success'] == True
        assert data['data']['title'] == '自定义告警'
    
    def test_get_alert_stats_api(self, client):
        """测试获取告警统计 API"""
        response = client.get('/api/alerts/stats')
        data = response.get_json()
        
        assert response.status_code == 200
        assert data['success'] == True
        assert 'total' in data['data']
        assert 'active' in data['data']
    
    def test_filter_alerts_by_status(self, client):
        """测试按状态过滤告警"""
        with app.app_context():
            Alert(agent_id='xilian', alert_type='offline', severity='warning', title='Active', status='active'),
            Alert(agent_id='tangyuan', alert_type='offline', severity='warning', title='Resolved', status='resolved'),
            db.session.add_all([
                Alert(agent_id='xilian', alert_type='offline', severity='warning', title='Active', status='active'),
                Alert(agent_id='tangyuan', alert_type='offline', severity='warning', title='Resolved', status='resolved')
            ])
            db.session.commit()
        
        response = client.get('/api/alerts?status=active')
        data = response.get_json()
        
        assert response.status_code == 200
        for alert in data['data']:
            assert alert['status'] == 'active'
    
    def test_filter_alerts_by_agent(self, client):
        """测试按 Agent 过滤告警"""
        with app.app_context():
            Alert(agent_id='xilian', alert_type='offline', severity='warning', title='Xilian Alert'),
            Alert(agent_id='tangyuan', alert_type='offline', severity='warning', title='Tangyuan Alert'),
            db.session.add_all([
                Alert(agent_id='xilian', alert_type='offline', severity='warning', title='Xilian Alert'),
                Alert(agent_id='tangyuan', alert_type='offline', severity='warning', title='Tangyuan Alert')
            ])
            db.session.commit()
        
        response = client.get('/api/alerts?agent_id=xilian')
        data = response.get_json()
        
        assert response.status_code == 200
        for alert in data['data']:
            assert alert['agent_id'] == 'xilian'


class TestAlertConfig:
    """AlertConfig 测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = AlertConfig()
        
        assert config.offline_threshold_minutes == 5
        assert config.response_time_threshold_ms == 30000
        assert config.task_failure_threshold == 3
        assert config.cooldown_minutes == 5
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = AlertConfig(
            offline_threshold_minutes=10,
            response_time_threshold_ms=60000,
            feishu_webhook='https://example.com/webhook'
        )
        
        assert config.offline_threshold_minutes == 10
        assert config.response_time_threshold_ms == 60000
        assert config.feishu_webhook == 'https://example.com/webhook'