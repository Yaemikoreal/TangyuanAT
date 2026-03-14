"""
OpenClaw 客户端单元测试
"""

import pytest
import json
import subprocess
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.openclaw_client import OpenClawClient, get_client, get_agent_status, get_all_agents_status


class TestOpenClawClient:
    """OpenClawClient 测试类"""
    
    def test_init(self):
        """测试初始化"""
        client = OpenClawClient()
        assert client.openclaw_path == 'openclaw'
        
        client = OpenClawClient('/custom/path/openclaw')
        assert client.openclaw_path == '/custom/path/openclaw'
    
    @patch('subprocess.run')
    def test_cli_available_true(self, mock_run):
        """测试 CLI 可用的情况"""
        mock_run.return_value = MagicMock(returncode=0, stdout='openclaw 2026.3.12')
        
        client = OpenClawClient()
        assert client._is_cli_available(force_check=True) is True
    
    @patch('subprocess.run')
    def test_cli_available_false(self, mock_run):
        """测试 CLI 不可用的情况"""
        mock_run.side_effect = FileNotFoundError()
        
        client = OpenClawClient()
        assert client._is_cli_available(force_check=True) is False
    
    @patch('subprocess.run')
    def test_get_sessions_success(self, mock_run):
        """测试获取会话列表成功"""
        mock_data = {
            "path": "/Users/test/.openclaw/sessions.json",
            "count": 2,
            "sessions": [
                {
                    "key": "agent:main:main",
                    "agentId": "main",
                    "model": "kimi-k2.5",
                    "updatedAt": 1773469215842,
                    "ageMs": 100000
                },
                {
                    "key": "agent:tangyuan:tangyuan",
                    "agentId": "tangyuan",
                    "model": "glm-5",
                    "updatedAt": 1773469304142,
                    "ageMs": 20000
                }
            ]
        }
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_data),
            stderr=''
        )
        
        client = OpenClawClient()
        client._cli_available = True  # 跳过 CLI 检查
        
        result = client.get_sessions(all_agents=True, use_cache=False)
        
        assert result['success'] is True
        assert 'data' in result
        assert result['data']['count'] == 2
    
    @patch('subprocess.run')
    def test_get_sessions_cli_not_available(self, mock_run):
        """测试 CLI 不可用时获取会话列表"""
        client = OpenClawClient()
        client._cli_available = False
        
        result = client.get_sessions(use_cache=False)
        
        assert result['success'] is False
        assert result['error_code'] == 'CLI_NOT_FOUND'
    
    @patch('subprocess.run')
    def test_get_agent_status_online(self, mock_run):
        """测试获取在线 agent 状态"""
        mock_data = {
            "count": 1,
            "sessions": [
                {
                    "key": "agent:tangyuan:tangyuan",
                    "agentId": "tangyuan",
                    "model": "glm-5",
                    "modelProvider": "bailian-tangyuan",
                    "updatedAt": int(datetime.now().timestamp() * 1000) - 60000,  # 1分钟前
                    "ageMs": 60000
                }
            ]
        }
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_data),
            stderr=''
        )
        
        client = OpenClawClient()
        client._cli_available = True
        
        result = client.get_agent_status_from_sessions('tangyuan', use_cache=False)
        
        assert result['status'] == 'online'
        assert result['model'] == 'glm-5'
    
    @patch('subprocess.run')
    def test_get_agent_status_offline(self, mock_run):
        """测试获取离线 agent 状态"""
        mock_data = {
            "count": 1,
            "sessions": [
                {
                    "key": "agent:tangyuan:tangyuan",
                    "agentId": "tangyuan",
                    "model": "glm-5",
                    "updatedAt": int(datetime.now().timestamp() * 1000) - 600000,  # 10分钟前
                    "ageMs": 600000
                }
            ]
        }
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_data),
            stderr=''
        )
        
        client = OpenClawClient()
        client._cli_available = True
        
        result = client.get_agent_status_from_sessions('tangyuan', use_cache=False)
        
        assert result['status'] == 'offline'
    
    @patch('subprocess.run')
    def test_get_agent_status_xilian_mapping(self, mock_run):
        """测试 xilian -> main 的映射"""
        mock_data = {
            "count": 1,
            "sessions": [
                {
                    "key": "agent:main:main",
                    "agentId": "main",
                    "model": "kimi-k2.5",
                    "updatedAt": int(datetime.now().timestamp() * 1000) - 400000,  # 约7分钟前
                    "ageMs": 400000
                }
            ]
        }
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_data),
            stderr=''
        )
        
        client = OpenClawClient()
        client._cli_available = True
        
        # 测试 xilian 映射到 main
        result = client.get_agent_status_from_sessions('xilian', use_cache=False)
        
        assert result['status'] == 'offline'  # 7分钟前，超过5分钟
        assert result['model'] == 'kimi-k2.5'
    
    @patch('subprocess.run')
    def test_get_agent_status_no_sessions(self, mock_run):
        """测试没有会话时的状态"""
        mock_data = {
            "count": 0,
            "sessions": []
        }
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_data),
            stderr=''
        )
        
        client = OpenClawClient()
        client._cli_available = True
        
        result = client.get_agent_status_from_sessions('unknown_agent', use_cache=False)
        
        assert result['status'] == 'offline'
    
    @patch('subprocess.run')
    def test_get_agent_status_error(self, mock_run):
        """测试获取状态出错"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='Some error'
        )
        
        client = OpenClawClient()
        client._cli_available = True
        
        result = client.get_agent_status_from_sessions('tangyuan', use_cache=False)
        
        assert result['status'] == 'unknown'
        assert 'error' in result
    
    @patch('subprocess.run')
    def test_get_all_agents_status(self, mock_run):
        """测试获取所有 agents 状态"""
        now = int(datetime.now().timestamp() * 1000)
        mock_data = {
            "count": 3,
            "sessions": [
                {
                    "key": "agent:tangyuan:tangyuan",
                    "agentId": "tangyuan",
                    "model": "glm-5",
                    "modelProvider": "bailian-tangyuan",
                    "updatedAt": now - 60000,  # 1分钟前
                    "ageMs": 60000
                },
                {
                    "key": "agent:main:main",
                    "agentId": "main",
                    "model": "kimi-k2.5",
                    "updatedAt": now - 400000,  # 约7分钟前
                    "ageMs": 400000
                },
                {
                    "key": "agent:doufu:doufu",
                    "agentId": "doufu",
                    "model": "glm-5",
                    "updatedAt": now - 300000,  # 5分钟前
                    "ageMs": 300000
                }
            ]
        }
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_data),
            stderr=''
        )
        
        client = OpenClawClient()
        client._cli_available = True
        
        result = client.get_all_agents_status(use_cache=False)
        
        assert 'tangyuan' in result
        assert result['tangyuan']['status'] == 'online'
        assert 'xilian' in result  # main -> xilian
        assert result['xilian']['status'] == 'offline'  # 7分钟前
        assert 'doufu' in result
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        client = OpenClawClient()
        
        # 设置缓存
        client._sessions_cache = {'success': True, 'data': {'sessions': []}}
        client._sessions_cache_time = 9999999999  # 未来的时间
        
        # 应该返回缓存
        result = client.get_sessions(use_cache=True)
        assert result == client._sessions_cache
        
        # 清除缓存
        client.clear_cache()
        assert client._sessions_cache is None
    
    @patch('subprocess.run')
    def test_graceful_degradation(self, mock_run):
        """测试优雅降级"""
        # 模拟 CLI 完全不可用
        client = OpenClawClient()
        client._cli_available = False
        
        # 获取状态应该返回错误而不是抛出异常
        result = client.get_agent_status_from_sessions('tangyuan')
        
        assert result['status'] in ['unknown', 'offline']
        assert 'error' in result or result['status'] == 'offline'
    
    def test_singleton(self):
        """测试单例模式"""
        client1 = get_client()
        client2 = get_client()
        
        assert client1 is client2
    
    @patch('subprocess.run')
    def test_convenience_functions(self, mock_run):
        """测试便捷函数"""
        mock_data = {
            "count": 1,
            "sessions": [
                {
                    "key": "agent:tangyuan:tangyuan",
                    "agentId": "tangyuan",
                    "model": "glm-5",
                    "updatedAt": int(datetime.now().timestamp() * 1000) - 60000,
                    "ageMs": 60000
                }
            ]
        }
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_data),
            stderr=''
        )
        
        # 重置单例
        import agents.openclaw_client as module
        module._client = None
        
        status = get_agent_status('tangyuan')
        assert status['status'] == 'online'
        
        all_status = get_all_agents_status()
        assert 'tangyuan' in all_status


class TestAgentMapping:
    """测试 agent ID 映射"""
    
    def test_agent_id_mapping(self):
        """测试 agent ID 正确映射"""
        client = OpenClawClient()
        
        # 映射表
        mapping = {
            'xilian': 'main',
            'main': 'main', 
            'tangyuan': 'tangyuan',
            'doufu': 'doufu'
        }
        
        # 验证映射逻辑
        for display_id, internal_id in mapping.items():
            assert mapping.get(display_id.lower(), display_id.lower()) == internal_id


class TestEdgeCases:
    """边缘情况测试"""
    
    @patch('subprocess.run')
    def test_timeout(self, mock_run):
        """测试命令超时"""
        # 需要让 CLI 检查通过（第一次调用 subprocess.run），然后在真正执行命令时超时
        # 第一次调用是 _is_cli_available 中的 openclaw --version
        # 第二次调用是实际的命令执行
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout='openclaw 2026.3.12'),  # CLI 检查通过
            subprocess.TimeoutExpired(cmd='openclaw', timeout=30)  # 命令执行超时
        ]
        
        client = OpenClawClient()
        # 强制重新检查 CLI
        result = client.get_sessions(use_cache=False)
        
        assert result['success'] is False
        assert result['error_code'] == 'TIMEOUT'
    
    @patch('subprocess.run')
    def test_malformed_json(self, mock_run):
        """测试 malformed JSON 响应"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='not valid json {{{',
            stderr=''
        )
        
        client = OpenClawClient()
        client._cli_available = True
        
        result = client.get_sessions(use_cache=False)
        
        # 应该返回 raw 输出而不是崩溃
        assert result['success'] is True
        assert 'raw' in result
    
    @patch('subprocess.run')
    def test_empty_response(self, mock_run):
        """测试空响应"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='',
            stderr=''
        )
        
        client = OpenClawClient()
        client._cli_available = True
        
        result = client.get_sessions(use_cache=False)
        
        assert result['success'] is True
        assert result['data'] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])