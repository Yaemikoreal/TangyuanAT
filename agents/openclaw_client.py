"""
OpenClaw 网关客户端
用于获取真实的 Agent 状态和会话信息
"""

import subprocess
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from functools import lru_cache


class OpenClawClient:
    """OpenClaw 命令行客户端"""
    
    # 缓存配置
    CACHE_TTL_SECONDS = 30  # 缓存有效期（秒）
    
    def __init__(self, openclaw_path: str = 'openclaw'):
        """
        初始化客户端
        
        Args:
            openclaw_path: openclaw 命令路径，默认从 PATH 查找
        """
        self.openclaw_path = openclaw_path
        self._cli_available: Optional[bool] = None
        self._last_check_time: float = 0
        
        # 缓存
        self._sessions_cache: Optional[Dict] = None
        self._sessions_cache_time: float = 0
        self._status_cache: Optional[Dict] = None
        self._status_cache_time: float = 0
    
    def _is_cli_available(self, force_check: bool = False) -> bool:
        """
        检查 OpenClaw CLI 是否可用
        
        Args:
            force_check: 是否强制重新检查
            
        Returns:
            bool: CLI 是否可用
        """
        now = time.time()
        
        # 5分钟内不重复检查
        if not force_check and self._cli_available is not None:
            if now - self._last_check_time < 300:
                return self._cli_available
        
        try:
            result = subprocess.run(
                [self.openclaw_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='replace'
            )
            self._cli_available = result.returncode == 0
            self._last_check_time = now
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            self._cli_available = False
            self._last_check_time = now
        
        return self._cli_available
    
    def _run_command(self, *args, use_json: bool = True, timeout: int = 30) -> Dict:
        """
        执行 openclaw 命令并返回结果
        
        Args:
            *args: 命令参数
            use_json: 是否使用 JSON 输出格式
            timeout: 超时时间（秒）
            
        Returns:
            dict: 解析后的 JSON 结果或错误信息
        """
        # 先检查 CLI 是否可用
        if not self._is_cli_available():
            return {
                'success': False,
                'error': 'OpenClaw CLI 不可用',
                'error_code': 'CLI_NOT_FOUND'
            }
        
        try:
            cmd = [self.openclaw_path] + list(args)
            if use_json:
                cmd.append('--json')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                # 解析错误信息
                error_msg = result.stderr.strip() if result.stderr else 'Unknown error'
                
                # 检查是否是 CLI 不可用的错误
                if 'not found' in error_msg.lower() or 'command not found' in error_msg.lower():
                    self._cli_available = False
                    return {
                        'success': False,
                        'error': 'OpenClaw CLI 不可用',
                        'error_code': 'CLI_NOT_FOUND'
                    }
                
                return {
                    'success': False,
                    'error': error_msg,
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
                except json.JSONDecodeError as e:
                    # 非 JSON 输出，返回原始文本
                    return {
                        'success': True,
                        'raw': output,
                        'json_error': str(e)
                    }
            
            return {'success': True, 'data': None}
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': '命令执行超时',
                'error_code': 'TIMEOUT'
            }
        except FileNotFoundError:
            self._cli_available = False
            return {
                'success': False,
                'error': f'OpenClaw 命令未找到: {self.openclaw_path}',
                'error_code': 'CLI_NOT_FOUND'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': 'UNKNOWN_ERROR'
            }
    
    def get_status(self, use_cache: bool = True) -> Dict:
        """
        获取 OpenClaw 状态
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            dict: 状态信息
        """
        now = time.time()
        
        # 检查缓存
        if use_cache and self._status_cache is not None:
            if now - self._status_cache_time < self.CACHE_TTL_SECONDS:
                return self._status_cache
        
        result = self._run_command('status')
        
        # 更新缓存
        if use_cache:
            self._status_cache = result
            self._status_cache_time = now
        
        return result
    
    def get_sessions(self, active_minutes: Optional[int] = None,
                     all_agents: bool = False,
                     use_cache: bool = True) -> Dict:
        """
        获取会话列表
        
        Args:
            active_minutes: 只返回最近活跃的会话（分钟）
            all_agents: 是否获取所有 agents 的会话
            use_cache: 是否使用缓存
            
        Returns:
            dict: 会话列表
        """
        now = time.time()
        
        # 检查缓存
        if use_cache and self._sessions_cache is not None:
            if now - self._sessions_cache_time < self.CACHE_TTL_SECONDS:
                # 如果需要过滤，从缓存中过滤
                cached = self._sessions_cache.copy()
                if cached.get('success') and cached.get('data'):
                    sessions = cached['data'].get('sessions', [])
                    if active_minutes is not None:
                        cutoff = now - active_minutes * 60
                        sessions = [
                            s for s in sessions
                            if s.get('updatedAt', 0) / 1000 > cutoff
                        ]
                        cached['data'] = {**cached['data'], 'sessions': sessions, 'count': len(sessions)}
                    return cached
        
        args = ['sessions']
        if all_agents:
            args.append('--all-agents')
        if active_minutes is not None:
            args.extend(['--active', str(active_minutes)])
        
        result = self._run_command(*args)
        
        # 更新缓存（只在请求全部数据时缓存）
        if use_cache and all_agents and active_minutes is None:
            self._sessions_cache = result
            self._sessions_cache_time = now
        
        return result
    
    def get_session_history(self, session_key: str, limit: int = 10) -> Dict:
        """
        获取会话历史
        
        Args:
            session_key: 会话标识
            limit: 消息数量限制
            
        Returns:
            dict: 会话历史
        """
        # 注意：openclaw 没有直接的 sessions history 命令
        # 这里需要检查实际的命令格式
        result = self._run_command('sessions', '--agent', session_key.split(':')[1] if ':' in session_key else session_key)
        return result
    
    def get_agent_status_from_sessions(self, agent_id: str, use_cache: bool = True) -> Dict:
        """
        从会话列表推断 Agent 状态
        
        Args:
            agent_id: agent ID（如 'main', 'tangyuan', 'doufu'）
            use_cache: 是否使用缓存
            
        Returns:
            dict: 状态信息，包含:
                - status: 'online' | 'offline' | 'unknown'
                - model: 当前使用的模型
                - last_active: 最后活跃时间
                - session_key: 当前会话标识
        """
        # 获取所有 agents 的 sessions
        result = self.get_sessions(all_agents=True, use_cache=use_cache)
        
        if not result.get('success'):
            return {
                'status': 'unknown',
                'error': result.get('error'),
                'error_code': result.get('error_code')
            }
        
        data = result.get('data', {})
        sessions = data.get('sessions', [])
        
        if not sessions:
            return {'status': 'offline'}
        
        # 查找匹配的 agent
        # agent_id 可能是 'xilian'，但 sessions 中是 'main'
        agent_mapping = {
            'xilian': 'main',
            'main': 'main',
            'tangyuan': 'tangyuan',
            'doufu': 'doufu'
        }
        
        target_agent = agent_mapping.get(agent_id.lower(), agent_id.lower())
        
        # 找到该 agent 的最新会话
        agent_sessions = [
            s for s in sessions
            if s.get('agentId', '').lower() == target_agent
        ]
        
        if not agent_sessions:
            return {'status': 'offline'}
        
        # 找到最新的会话（按 updatedAt 排序）
        latest_session = max(agent_sessions, key=lambda s: s.get('updatedAt', 0))
        
        # 计算最后活跃时间
        updated_at = latest_session.get('updatedAt', 0)
        age_ms = latest_session.get('ageMs', 0)
        
        # 判断在线状态：5分钟内有活动视为在线
        status = 'online' if age_ms < 5 * 60 * 1000 else 'offline'
        
        # 转换时间戳
        last_active = None
        if updated_at:
            last_active = datetime.fromtimestamp(updated_at / 1000).isoformat()
        
        return {
            'status': status,
            'model': latest_session.get('model'),
            'model_provider': latest_session.get('modelProvider'),
            'last_active': last_active,
            'session_key': latest_session.get('key'),
            'age_minutes': age_ms / (60 * 1000) if age_ms else None
        }
    
    def get_all_agents_status(self, use_cache: bool = True) -> Dict[str, Dict]:
        """
        获取所有 agents 的状态
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            dict: agent_id -> status_info 的映射
        """
        result = self.get_sessions(all_agents=True, use_cache=use_cache)
        
        if not result.get('success'):
            return {}
        
        data = result.get('data', {})
        sessions = data.get('sessions', [])
        
        # 按 agent 分组
        agent_sessions: Dict[str, List] = {}
        for session in sessions:
            agent_id = session.get('agentId', 'unknown')
            if agent_id not in agent_sessions:
                agent_sessions[agent_id] = []
            agent_sessions[agent_id].append(session)
        
        # 计算每个 agent 的状态
        status_map = {}
        
        # agent ID 映射（用于显示）
        display_names = {
            'main': 'xilian',
            'tangyuan': 'tangyuan',
            'doufu': 'doufu'
        }
        
        for agent_id, sessions_list in agent_sessions.items():
            if not sessions_list:
                continue
            
            # 找到最新的会话
            latest = max(sessions_list, key=lambda s: s.get('updatedAt', 0))
            age_ms = latest.get('ageMs', 0)
            
            # 判断状态
            status = 'online' if age_ms < 5 * 60 * 1000 else 'offline'
            
            updated_at = latest.get('updatedAt', 0)
            last_active = datetime.fromtimestamp(updated_at / 1000).isoformat() if updated_at else None
            
            # 使用显示名称
            display_id = display_names.get(agent_id, agent_id)
            
            status_map[display_id] = {
                'status': status,
                'model': latest.get('model'),
                'model_provider': latest.get('modelProvider'),
                'last_active': last_active,
                'session_key': latest.get('key'),
                'age_minutes': age_ms / (60 * 1000) if age_ms else None
            }
        
        return status_map
    
    def get_agent_history(self, agent_id: str, limit: int = 10) -> Dict:
        """
        获取指定 agent 的历史消息
        
        Args:
            agent_id: agent ID
            limit: 消息数量限制
            
        Returns:
            dict: 历史消息
        """
        # agent ID 映射
        agent_mapping = {
            'xilian': 'main',
            'main': 'main',
            'tangyuan': 'tangyuan',
            'doufu': 'doufu'
        }
        
        target_agent = agent_mapping.get(agent_id.lower(), agent_id.lower())
        
        # 使用 --agent 参数获取特定 agent 的 sessions
        result = self._run_command('sessions', '--agent', target_agent, '--json')
        
        if not result.get('success'):
            return {
                'success': False,
                'error': result.get('error'),
                'messages': []
            }
        
        data = result.get('data', {})
        sessions = data.get('sessions', [])
        
        # 获取每个 session 的最后消息时间
        history = []
        for session in sessions[:limit]:
            updated_at = session.get('updatedAt', 0)
            if updated_at:
                history.append({
                    'session_key': session.get('key'),
                    'timestamp': datetime.fromtimestamp(updated_at / 1000).isoformat(),
                    'model': session.get('model'),
                    'kind': session.get('kind')
                })
        
        return {
            'success': True,
            'agent_id': agent_id,
            'messages': history,
            'total_sessions': len(sessions)
        }
    
    def clear_cache(self):
        """清除所有缓存"""
        self._sessions_cache = None
        self._sessions_cache_time = 0
        self._status_cache = None
        self._status_cache_time = 0
    
    def is_gateway_running(self) -> bool:
        """
        检查 OpenClaw Gateway 是否运行
        
        Returns:
            bool: Gateway 是否运行
        """
        status = self.get_status(use_cache=False)
        if status.get('success'):
            data = status.get('data', {})
            # 检查 gateway 状态
            if isinstance(data, dict):
                return data.get('running', False)
        return False


# 单例客户端实例
_client: Optional[OpenClawClient] = None


def get_client() -> OpenClawClient:
    """获取 OpenClaw 客户端单例"""
    global _client
    if _client is None:
        _client = OpenClawClient()
    return _client


def get_agent_status(agent_id: str) -> Dict:
    """
    快捷方法：获取指定 agent 的状态
    
    Args:
        agent_id: agent ID
        
    Returns:
        dict: 状态信息
    """
    return get_client().get_agent_status_from_sessions(agent_id)


def get_all_agents_status() -> Dict[str, Dict]:
    """
    快捷方法：获取所有 agents 的状态
    
    Returns:
        dict: agent_id -> status 的映射
    """
    return get_client().get_all_agents_status()