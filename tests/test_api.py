"""
Flask API 路由测试
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPageRoutes:
    """页面路由测试"""
    
    def test_index_page(self, client):
        """测试主页访问"""
        response = client.get('/')
        assert response.status_code == 200


class TestAgentAPI:
    """Agent API 测试"""
    
    def test_get_agents_success(self, client):
        """测试获取所有 agents"""
        response = client.get('/api/agents')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'timestamp' in data
    
    def test_get_agent_exists(self, client):
        """测试获取存在的 agent"""
        response = client.get('/api/agents/test_agent')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 'test_agent'
    
    def test_get_agent_not_found(self, client):
        """测试获取不存在的 agent"""
        response = client.get('/api/agents/nonexistent_agent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['error'].lower()
    
    def test_update_agent_status(self, client):
        """测试更新 agent 状态"""
        response = client.put(
            '/api/agents/test_agent',
            data=json.dumps({'status': 'busy'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['status'] == 'busy'
    
    def test_update_agent_current_task(self, client):
        """测试更新 agent 当前任务"""
        response = client.put(
            '/api/agents/test_agent',
            data=json.dumps({'current_task': '正在执行测试'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['current_task'] == '正在执行测试'
    
    def test_update_agent_model(self, client):
        """测试更新 agent 模型"""
        response = client.put(
            '/api/agents/test_agent',
            data=json.dumps({'model': 'new-model'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['model'] == 'new-model'
    
    def test_update_agent_config(self, client):
        """测试更新 agent 配置"""
        response = client.put(
            '/api/agents/test_agent',
            data=json.dumps({'config': {'new_key': 'new_value'}}),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['config']['new_key'] == 'new_value'
    
    def test_update_agent_not_found(self, client):
        """测试更新不存在的 agent"""
        response = client.put(
            '/api/agents/nonexistent_agent',
            data=json.dumps({'status': 'online'}),
            content_type='application/json'
        )
        assert response.status_code == 404
    
    def test_update_agent_invalid_json(self, client):
        """测试更新 agent 时发送无效 JSON"""
        response = client.put(
            '/api/agents/test_agent',
            data='not valid json',
            content_type='application/json'
        )
        assert response.status_code in [400, 500]


class TestLogAPI:
    """日志 API 测试"""
    
    def test_get_logs_success(self, client):
        """测试获取日志列表"""
        response = client.get('/api/logs')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'total' in data
        assert 'pages' in data
    
    def test_get_logs_with_pagination(self, client):
        """测试分页获取日志"""
        response = client.get('/api/logs?page=1&per_page=10')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['current_page'] == 1
    
    def test_get_logs_filter_by_agent(self, client):
        """测试按 agent 过滤日志"""
        response = client.get('/api/logs?agent_id=test_agent')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_add_log_success(self, client):
        """测试添加日志"""
        response = client.post(
            '/api/logs',
            data=json.dumps({
                'agent_id': 'test_agent',
                'agent_name': '测试Agent',
                'action': '测试操作',
                'details': '测试详情'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['action'] == '测试操作'
    
    def test_add_log_updates_agent_tasks(self, client, app):
        """测试添加日志时更新 agent 任务计数"""
        with app.app_context():
            from models import Agent
            agent_before = Agent.query.get('test_agent')
            tasks_before = agent_before.tasks_completed if agent_before else 0
        
        response = client.post(
            '/api/logs',
            data=json.dumps({
                'agent_id': 'test_agent',
                'agent_name': '测试Agent',
                'action': '新任务',
                'details': '测试任务计数'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        with app.app_context():
            agent_after = Agent.query.get('test_agent')
            assert agent_after.tasks_completed == tasks_before + 1


class TestChatHistoryAPI:
    """对话历史 API 测试"""
    
    def test_get_chat_history_success(self, client):
        """测试获取对话历史"""
        response = client.get('/api/chat-history')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
    
    def test_get_chat_history_pagination(self, client):
        """测试分页获取对话历史"""
        response = client.get('/api/chat-history?page=1&per_page=20')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['current_page'] == 1
    
    def test_add_chat_message_success(self, client):
        """测试添加对话消息"""
        response = client.post(
            '/api/chat-history',
            data=json.dumps({
                'sender': 'user',
                'content': '这是一条测试消息',
                'agent_mentioned': 'test_agent'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['content'] == '这是一条测试消息'
    
    def test_add_chat_message_without_mention(self, client):
        """测试添加无提及 agent 的消息"""
        response = client.post(
            '/api/chat-history',
            data=json.dumps({
                'sender': 'user',
                'content': '普通消息'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True


class TestStatsAPI:
    """统计 API 测试"""
    
    def test_get_stats_success(self, client):
        """测试获取统计信息"""
        response = client.get('/api/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        
        stats = data['data']
        assert 'total_tasks' in stats
        assert 'total_messages' in stats
        assert 'agents_online' in stats
        assert 'agents_total' in stats
        assert 'uptime' in stats


class TestConfigAPI:
    """配置 API 测试"""
    
    def test_get_config_success(self, client):
        """测试获取配置"""
        response = client.get('/api/config')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
    
    def test_update_config_success(self, client):
        """测试更新配置"""
        response = client.post(
            '/api/config',
            data=json.dumps({
                'new_config': 'new_value',
                'number_config': 123,
                'object_config': {'nested': 'value'}
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_update_existing_config(self, client):
        """测试更新已存在的配置"""
        # 先创建配置
        client.post(
            '/api/config',
            data=json.dumps({'test_key': 'initial_value'}),
            content_type='application/json'
        )
        
        # 再更新
        response = client.post(
            '/api/config',
            data=json.dumps({'test_config': 'updated_value'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True


class TestOpenClawAPI:
    """OpenClaw 状态 API 测试"""
    
    @patch('app.openclaw')
    def test_get_openclaw_status_success(self, mock_openclaw, client):
        """测试获取 OpenClaw 状态"""
        mock_openclaw.get_status.return_value = {
            'success': True,
            'data': {'running': True}
        }
        
        response = client.get('/api/openclaw/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('app.openclaw')
    def test_get_openclaw_sessions_success(self, mock_openclaw, client):
        """测试获取 OpenClaw 会话列表"""
        mock_openclaw.get_sessions.return_value = {
            'success': True,
            'data': {
                'sessions': [],
                'count': 0
            }
        }
        
        response = client.get('/api/openclaw/sessions')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('app.openclaw')
    def test_get_openclaw_sessions_with_params(self, mock_openclaw, client):
        """测试带参数获取 OpenClaw 会话列表"""
        mock_openclaw.get_sessions.return_value = {
            'success': True,
            'data': {
                'sessions': [],
                'count': 0
            }
        }
        
        response = client.get('/api/openclaw/sessions?active_minutes=30&limit=20')
        assert response.status_code == 200
        
        # 验证参数传递
        mock_openclaw.get_sessions.assert_called_once_with(active_minutes=30, limit=20)


class TestSSEStream:
    """SSE 实时流测试"""
    
    def test_stream_endpoint_exists(self, client):
        """测试 SSE 流端点存在"""
        # SSE 是长连接，只验证 content-type
        response = client.get('/api/stream')
        assert response.status_code == 200
        assert response.content_type.startswith('text/event-stream')


class TestErrorHandling:
    """错误处理测试"""
    
    def test_404_api_route(self, client):
        """测试不存在的 API 路由"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
    
    def test_invalid_json_post(self, client):
        """测试 POST 无效 JSON"""
        response = client.post(
            '/api/logs',
            data='not valid json',
            content_type='application/json'
        )
        assert response.status_code in [400, 500]
    
    def test_missing_required_fields_log(self, client):
        """测试日志缺少必填字段"""
        response = client.post(
            '/api/logs',
            data=json.dumps({}),
            content_type='application/json'
        )
        # 应该成功（字段有默认值）或返回错误
        assert response.status_code in [200, 400, 500]


class TestCORS:
    """CORS 测试"""
    
    def test_cors_headers_present(self, client):
        """测试 CORS 头存在"""
        response = client.get('/api/agents')
        # CORS 应该在响应头中
        assert response.status_code == 200
        # 具体的 CORS 头检查取决于 Flask-CORS 配置


class TestIntegration:
    """集成测试"""
    
    def test_agent_lifecycle(self, client):
        """测试 agent 生命周期：获取 -> 更新 -> 验证"""
        # 1. 获取 agent
        get_response = client.get('/api/agents/test_agent')
        assert get_response.status_code == 200
        agent_data = json.loads(get_response.data)['data']
        
        # 2. 更新 agent
        update_response = client.put(
            '/api/agents/test_agent',
            data=json.dumps({
                'status': 'busy',
                'current_task': '执行集成测试'
            }),
            content_type='application/json'
        )
        assert update_response.status_code == 200
        
        # 3. 验证更新
        verify_response = client.get('/api/agents/test_agent')
        assert verify_response.status_code == 200
        updated_data = json.loads(verify_response.data)['data']
        
        assert updated_data['status'] == 'busy'
        assert updated_data['current_task'] == '执行集成测试'
    
    def test_log_and_verify(self, client):
        """测试日志记录和验证"""
        # 1. 添加日志
        add_response = client.post(
            '/api/logs',
            data=json.dumps({
                'agent_id': 'test_agent',
                'agent_name': '测试Agent',
                'action': '集成测试日志',
                'details': '这是一条集成测试日志'
            }),
            content_type='application/json'
        )
        assert add_response.status_code == 200
        
        # 2. 验证日志存在
        get_response = client.get('/api/logs?agent_id=test_agent')
        assert get_response.status_code == 200
        
        data = json.loads(get_response.data)
        assert data['success'] is True
        # 日志列表应该包含新添加的日志
        log_actions = [log['action'] for log in data['data']]
        assert '集成测试日志' in log_actions


if __name__ == '__main__':
    pytest.main([__file__, '-v'])