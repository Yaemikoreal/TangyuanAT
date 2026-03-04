"""
OpenClaw 网关客户端
用于获取真实的 Agent 状态和会话信息
"""

import subprocess
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class OpenClawClient:
    """OpenClaw 命令行客户端"""
    
    def __init__(self, openclaw_path: str = 'openclaw'):
        """
        初始化客户端
        
        Args:
            openclaw_path: openclaw 命令路径，默认从 PATH 查找
        """
        self.openclaw_path = openclaw_path
    
    def _run_command(self, *args) -> Dict:
        """
        执行 openclaw 命令并返回结果
        
        Args:
            *args: 命令参数
            
        Returns:
            dict: 解析后的 JSON 结果或错误信息
        """
        try:
            cmd = [self.openclaw_path] + list(args)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': result.stderr or 'Unknown error',
                    'returncode': result.returncode
                }
            
            # 尝试解析 JSON
            output = result.stdout.strip()
            if output:
                try:
                    return {
                        'success': True,
                        'data': json.loads(output)
                    }
                except json.JSONDecodeError:
                    # 非 JSON 输出，返回原始文本
                    return {
                        'success': True,
                        'raw': output
                    }
            
            return {'success': True, 'data': None}
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timeout'}
        except FileNotFoundError:
            return {'success': False, 'error': f'OpenClaw not found: {self.openclaw_path}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict:
        """
        获取 OpenClaw 状态
        
        Returns:
            dict: 状态信息
        """
        result = self._run_command('status')
        return result
    
    def get_sessions(self, active_minutes: Optional[int] = None, 
                     limit: Optional[int] = None) -> Dict:
        """
        获取会话列表
        
        Args:
            active_minutes: 只返回最近活跃的会话
            limit: 返回数量限制
            
        Returns:
            dict: 会话列表
        """
        args = ['sessions', 'list']
        if active_minutes:
            args.extend(['--active-minutes', str(active_minutes)])
        if limit:
            args.extend(['--limit', str(limit)])
        
        return self._run_command(*args)
    
    def get_session_history(self, session_key: str, limit: int = 10) -> Dict:
        """
        获取会话历史
        
        Args:
            session_key: 会话标识
            limit: 消息数量限制
            
        Returns:
            dict: 会话历史
        """
        return self._run_command('sessions', 'history', session_key, '--limit', str(limit))
    
    def parse_status_to_agent(self, status_data: Dict, agent_id: str) -> Optional[Dict]:
        """
        将 OpenClaw 状态数据转换为 Agent 格式
        
        Args:
            status_data: OpenClaw 状态数据
            agent_id: 要查找的 agent ID
            
        Returns:
            dict: Agent 数据或 None
        """
        if not status_data or not status_data.get('success'):
            return None
        
        # 解析状态数据
        # 格式可能因 openclaw status 输出而异
        data = status_data.get('data', status_data.get('raw', {}))
        
        # 如果是文本输出，需要解析
        if isinstance(data, str):
            # 尝试从文本中提取状态
            return self._parse_status_text(data, agent_id)
        
        # 如果是结构化数据
        if isinstance(data, dict):
            # 检查是否是运行中的 agent
            runtime = data.get('runtime', {})
            agent = runtime.get('agent', '')
            
            if agent:
                # 当前运行的 agent
                return {
                    'id': agent.lower() if isinstance(agent, str) else agent_id,
                    'status': 'online' if data.get('running', True) else 'offline',
                    'model': runtime.get('model', 'unknown'),
                    'last_active': datetime.utcnow().isoformat()
                }
        
        return None
    
    def _parse_status_text(self, text: str, agent_id: str) -> Optional[Dict]:
        """
        解析文本格式的状态输出
        
        Args:
            text: 状态文本
            agent_id: agent ID
            
        Returns:
            dict: 解析后的状态
        """
        # 简单的状态检测
        lines = text.lower().split('\n')
        status = 'offline'
        
        for line in lines:
            if agent_id.lower() in line:
                if 'online' in line or 'running' in line or 'active' in line:
                    status = 'online'
                elif 'busy' in line:
                    status = 'busy'
                break
        
        return {
            'id': agent_id,
            'status': status,
            'last_active': datetime.utcnow().isoformat()
        }
    
    def get_agent_status_from_sessions(self, agent_name: str) -> Dict:
        """
        从会话列表推断 Agent 状态
        
        Args:
            agent_name: agent 名称
            
        Returns:
            dict: 状态信息
        """
        result = self.get_sessions(active_minutes=60)
        
        if not result.get('success'):
            return {'status': 'unknown', 'error': result.get('error')}
        
        sessions = result.get('data', [])
        if isinstance(sessions, dict):
            sessions = sessions.get('sessions', [])
        
        # 检查是否有活跃会话
        agent_name_lower = agent_name.lower()
        for session in sessions:
            label = session.get('label', '').lower()
            agent = session.get('agent', '').lower()
            
            if agent_name_lower in label or agent_name_lower in agent:
                return {
                    'status': 'online',
                    'session_key': session.get('sessionKey'),
                    'last_active': session.get('lastMessageAt')
                }
        
        return {'status': 'offline'}


# 单例客户端实例
_client = None

def get_client() -> OpenClawClient:
    """获取 OpenClaw 客户端单例"""
    global _client
    if _client is None:
        _client = OpenClawClient()
    return _client