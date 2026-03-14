"""
告警管理器
负责告警规则检查、通知发送、历史记录
"""

import json
import time
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """告警类型"""
    OFFLINE = "offline"              # Agent 离线
    TASK_FAILED = "task_failed"      # 任务失败
    RESPONSE_SLOW = "response_slow"  # 响应时间异常
    CUSTOM = "custom"                # 自定义告警


class AlertSeverity(Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class AlertConfig:
    """告警配置"""
    # 离线告警配置
    offline_threshold_minutes: int = 5  # 离线超过多少分钟触发告警
    
    # 响应时间告警配置
    response_time_threshold_ms: int = 30000  # 响应时间超过多少毫秒触发告警
    
    # 任务失败告警配置
    task_failure_threshold: int = 3  # 连续失败多少次触发告警
    
    # 通知配置
    feishu_webhook: Optional[str] = None
    enable_feishu: bool = True
    enable_frontend: bool = True
    
    # 冷却时间
    cooldown_minutes: int = 5  # 同一告警冷却时间


class AlertManager:
    """告警管理器"""
    
    def __init__(self, db, config: Optional[AlertConfig] = None):
        """
        初始化告警管理器
        
        Args:
            db: Flask-SQLAlchemy 数据库实例
            config: 告警配置
        """
        self.db = db
        self.config = config or AlertConfig()
        
        # 导入模型（延迟导入避免循环依赖）
        from models.database import Alert, AlertRule, AlertNotification, Agent
        self.Alert = Alert
        self.AlertRule = AlertRule
        self.AlertNotification = AlertNotification
        self.Agent = Agent
        
        # 告警回调
        self._callbacks: List[Callable] = []
        
        # 检查线程
        self._check_thread: Optional[threading.Thread] = None
        self._running = False
        
        # 上次告警时间（用于冷却）
        self._last_alert_times: Dict[str, datetime] = {}
    
    def register_callback(self, callback: Callable):
        """注册告警回调函数"""
        self._callbacks.append(callback)
    
    def _trigger_callbacks(self, alert: Any):
        """触发所有回调"""
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调执行失败: {e}")
    
    def check_agent_offline(self, agent_id: str, last_active: Optional[datetime] = None) -> Optional[Any]:
        """
        检查 Agent 是否离线
        
        Args:
            agent_id: Agent ID
            last_active: 最后活跃时间
            
        Returns:
            Alert 对象如果触发告警，否则 None
        """
        if last_active is None:
            return None
        
        now = datetime.utcnow()
        offline_duration = now - last_active
        threshold = timedelta(minutes=self.config.offline_threshold_minutes)
        
        if offline_duration > threshold:
            # 检查冷却时间
            alert_key = f"offline:{agent_id}"
            if self._is_in_cooldown(alert_key):
                return None
            
            # 创建告警
            agent = self.Agent.query.get(agent_id)
            agent_name = agent.name if agent else agent_id
            
            alert = self.Alert(
                agent_id=agent_id,
                agent_name=agent_name,
                alert_type=AlertType.OFFLINE.value,
                severity=AlertSeverity.WARNING.value,
                title=f"Agent {agent_name} 离线告警",
                message=f"Agent {agent_name} 已离线 {int(offline_duration.total_seconds() / 60)} 分钟",
                details=json.dumps({
                    "offline_minutes": int(offline_duration.total_seconds() / 60),
                    "last_active": last_active.isoformat() if last_active else None
                })
            )
            
            self.db.session.add(alert)
            self.db.session.commit()
            
            # 更新冷却时间
            self._last_alert_times[alert_key] = now
            
            # 触发回调
            self._trigger_callbacks(alert)
            
            return alert
        
        return None
    
    def check_response_time(self, agent_id: str, response_time_ms: float) -> Optional[Any]:
        """
        检查响应时间是否异常
        
        Args:
            agent_id: Agent ID
            response_time_ms: 响应时间（毫秒）
            
        Returns:
            Alert 对象如果触发告警，否则 None
        """
        if response_time_ms <= self.config.response_time_threshold_ms:
            return None
        
        # 检查冷却时间
        alert_key = f"response_slow:{agent_id}"
        if self._is_in_cooldown(alert_key):
            return None
        
        # 创建告警
        agent = self.Agent.query.get(agent_id)
        agent_name = agent.name if agent else agent_id
        
        alert = self.Alert(
            agent_id=agent_id,
            agent_name=agent_name,
            alert_type=AlertType.RESPONSE_SLOW.value,
            severity=AlertSeverity.WARNING.value,
            title=f"Agent {agent_name} 响应时间异常",
            message=f"Agent {agent_name} 响应时间 {int(response_time_ms)}ms 超过阈值 {self.config.response_time_threshold_ms}ms",
            details=json.dumps({
                "response_time_ms": response_time_ms,
                "threshold_ms": self.config.response_time_threshold_ms
            })
        )
        
        self.db.session.add(alert)
        self.db.session.commit()
        
        # 更新冷却时间
        self._last_alert_times[alert_key] = datetime.utcnow()
        
        # 触发回调
        self._trigger_callbacks(alert)
        
        return alert
    
    def check_task_failure(self, agent_id: str, task_name: str, error: str) -> Optional[Any]:
        """
        检查任务失败
        
        Args:
            agent_id: Agent ID
            task_name: 任务名称
            error: 错误信息
            
        Returns:
            Alert 对象如果触发告警，否则 None
        """
        # 检查冷却时间
        alert_key = f"task_failed:{agent_id}"
        if self._is_in_cooldown(alert_key):
            return None
        
        # 创建告警
        agent = self.Agent.query.get(agent_id)
        agent_name = agent.name if agent else agent_id
        
        alert = self.Alert(
            agent_id=agent_id,
            agent_name=agent_name,
            alert_type=AlertType.TASK_FAILED.value,
            severity=AlertSeverity.ERROR.value,
            title=f"Agent {agent_name} 任务失败",
            message=f"任务 '{task_name}' 执行失败: {error}",
            details=json.dumps({
                "task_name": task_name,
                "error": error
            })
        )
        
        self.db.session.add(alert)
        self.db.session.commit()
        
        # 更新冷却时间
        self._last_alert_times[alert_key] = datetime.utcnow()
        
        # 触发回调
        self._trigger_callbacks(alert)
        
        return alert
    
    def create_custom_alert(
        self,
        agent_id: str,
        title: str,
        message: str,
        severity: str = "warning",
        details: Optional[Dict] = None
    ) -> Any:
        """
        创建自定义告警
        
        Args:
            agent_id: Agent ID
            title: 告警标题
            message: 告警消息
            severity: 严重程度
            details: 额外详情
            
        Returns:
            Alert 对象
        """
        agent = self.Agent.query.get(agent_id)
        agent_name = agent.name if agent else agent_id
        
        alert = self.Alert(
            agent_id=agent_id,
            agent_name=agent_name,
            alert_type=AlertType.CUSTOM.value,
            severity=severity,
            title=title,
            message=message,
            details=json.dumps(details or {})
        )
        
        self.db.session.add(alert)
        self.db.session.commit()
        
        # 触发回调
        self._trigger_callbacks(alert)
        
        return alert
    
    def _is_in_cooldown(self, alert_key: str) -> bool:
        """检查是否在冷却期内"""
        if alert_key not in self._last_alert_times:
            return False
        
        last_time = self._last_alert_times[alert_key]
        cooldown = timedelta(minutes=self.config.cooldown_minutes)
        
        return datetime.utcnow() - last_time < cooldown
    
    def send_feishu_notification(self, alert: Any, webhook_url: Optional[str] = None) -> bool:
        """
        发送飞书通知
        
        Args:
            alert: Alert 对象
            webhook_url: 飞书 webhook URL（可选，默认使用配置）
            
        Returns:
            bool: 是否发送成功
        """
        url = webhook_url or self.config.feishu_webhook
        if not url:
            logger.warning("飞书 webhook 未配置，跳过通知")
            return False
        
        # 构建飞书消息卡片
        severity_colors = {
            "info": "blue",
            "warning": "yellow",
            "error": "red",
            "critical": "red"
        }
        
        severity_emojis = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        color = severity_colors.get(alert.severity, "grey")
        emoji = severity_emojis.get(alert.severity, "📢")
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{emoji} {alert.title}"
                    },
                    "template": color
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "plain_text",
                            "content": alert.message or ""
                        }
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**Agent:** {alert.agent_name or alert.agent_id}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**类型:** {alert.alert_type}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**严重程度:** {alert.severity}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**时间:** {alert.created_at.strftime('%Y-%m-%d %H:%M:%S') if alert.created_at else 'N/A'}"
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            success = response.status_code == 200
            
            # 记录通知
            notification = self.AlertNotification(
                alert_id=alert.id,
                channel="feishu",
                status="sent" if success else "failed",
                error_message=None if success else response.text,
                sent_at=datetime.utcnow() if success else None
            )
            self.db.session.add(notification)
            self.db.session.commit()
            
            if success:
                logger.info(f"飞书通知发送成功: {alert.title}")
            else:
                logger.error(f"飞书通知发送失败: {response.text}")
            
            return success
            
        except Exception as e:
            logger.error(f"飞书通知发送异常: {e}")
            
            # 记录失败
            notification = self.AlertNotification(
                alert_id=alert.id,
                channel="feishu",
                status="failed",
                error_message=str(e)
            )
            self.db.session.add(notification)
            self.db.session.commit()
            
            return False
    
    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> Optional[Any]:
        """
        确认告警
        
        Args:
            alert_id: 告警 ID
            acknowledged_by: 确认人
            
        Returns:
            更新后的 Alert 对象
        """
        alert = self.Alert.query.get(alert_id)
        if not alert:
            return None
        
        alert.status = AlertStatus.ACKNOWLEDGED.value
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        
        self.db.session.commit()
        
        return alert
    
    def resolve_alert(self, alert_id: int) -> Optional[Any]:
        """
        解决告警
        
        Args:
            alert_id: 告警 ID
            
        Returns:
            更新后的 Alert 对象
        """
        alert = self.Alert.query.get(alert_id)
        if not alert:
            return None
        
        alert.status = AlertStatus.RESOLVED.value
        alert.resolved_at = datetime.utcnow()
        
        self.db.session.commit()
        
        return alert
    
    def get_active_alerts(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Any]:
        """
        获取活跃告警
        
        Args:
            agent_id: Agent ID（可选）
            limit: 返回数量限制
            
        Returns:
            Alert 列表
        """
        query = self.Alert.query.filter_by(status=AlertStatus.ACTIVE.value)
        
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        
        return query.order_by(self.Alert.created_at.desc()).limit(limit).all()
    
    def get_alert_history(
        self,
        agent_id: Optional[str] = None,
        alert_type: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        获取告警历史
        
        Args:
            agent_id: Agent ID（可选）
            alert_type: 告警类型（可选）
            status: 告警状态（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            limit: 返回数量限制
            
        Returns:
            Alert 列表
        """
        query = self.Alert.query
        
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        if alert_type:
            query = query.filter_by(alert_type=alert_type)
        if status:
            query = query.filter_by(status=status)
        if start_time:
            query = query.filter(self.Alert.created_at >= start_time)
        if end_time:
            query = query.filter(self.Alert.created_at <= end_time)
        
        return query.order_by(self.Alert.created_at.desc()).limit(limit).all()
    
    def get_alert_stats(self) -> Dict:
        """
        获取告警统计
        
        Returns:
            统计数据字典
        """
        total = self.Alert.query.count()
        active = self.Alert.query.filter_by(status=AlertStatus.ACTIVE.value).count()
        acknowledged = self.Alert.query.filter_by(status=AlertStatus.ACKNOWLEDGED.value).count()
        resolved = self.Alert.query.filter_by(status=AlertStatus.RESOLVED.value).count()
        
        # 按类型统计
        by_type = {}
        for alert_type in [t.value for t in AlertType]:
            by_type[alert_type] = self.Alert.query.filter_by(alert_type=alert_type).count()
        
        # 按严重程度统计
        by_severity = {}
        for severity in [s.value for s in AlertSeverity]:
            by_severity[severity] = self.Alert.query.filter_by(severity=severity).count()
        
        # 今日告警
        today = datetime.utcnow().date()
        today_alerts = self.Alert.query.filter(
            self.Alert.created_at >= datetime.combine(today, datetime.min.time())
        ).count()
        
        return {
            "total": total,
            "active": active,
            "acknowledged": acknowledged,
            "resolved": resolved,
            "by_type": by_type,
            "by_severity": by_severity,
            "today": today_alerts
        }
    
    def start_background_check(self, interval_seconds: int = 60):
        """
        启动后台检查线程
        
        Args:
            interval_seconds: 检查间隔（秒）
        """
        if self._running:
            return
        
        self._running = True
        
        def check_loop():
            while self._running:
                try:
                    self._check_all_agents()
                except Exception as e:
                    logger.error(f"告警检查失败: {e}")
                
                time.sleep(interval_seconds)
        
        self._check_thread = threading.Thread(target=check_loop, daemon=True)
        self._check_thread.start()
        
        logger.info(f"告警检查线程已启动，间隔 {interval_seconds} 秒")
    
    def stop_background_check(self):
        """停止后台检查线程"""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=5)
            self._check_thread = None
        
        logger.info("告警检查线程已停止")
    
    def _check_all_agents(self):
        """检查所有 Agent 状态"""
        agents = self.Agent.query.all()
        
        for agent in agents:
            try:
                # 检查离线状态
                if agent.last_active:
                    self.check_agent_offline(agent.id, agent.last_active)
            except Exception as e:
                logger.error(f"检查 Agent {agent.id} 失败: {e}")


# 单例实例
_alert_manager: Optional[AlertManager] = None


def get_alert_manager(db=None) -> AlertManager:
    """
    获取告警管理器单例
    
    Args:
        db: Flask-SQLAlchemy 数据库实例（首次调用时需要）
        
    Returns:
        AlertManager 实例
    """
    global _alert_manager
    
    if _alert_manager is None and db is not None:
        _alert_manager = AlertManager(db)
    
    return _alert_manager


def init_alert_manager(app, db):
    """
    初始化告警管理器
    
    Args:
        app: Flask 应用实例
        db: Flask-SQLAlchemy 数据库实例
    """
    global _alert_manager
    
    # 从配置读取
    config = AlertConfig(
        offline_threshold_minutes=app.config.get('ALERT_OFFLINE_THRESHOLD', 5),
        response_time_threshold_ms=app.config.get('ALERT_RESPONSE_TIME_THRESHOLD', 30000),
        task_failure_threshold=app.config.get('ALERT_TASK_FAILURE_THRESHOLD', 3),
        feishu_webhook=app.config.get('FEISHU_WEBHOOK_URL'),
        enable_feishu=app.config.get('ALERT_ENABLE_FEISHU', True),
        enable_frontend=app.config.get('ALERT_ENABLE_FRONTEND', True),
        cooldown_minutes=app.config.get('ALERT_COOLDOWN_MINUTES', 5)
    )
    
    _alert_manager = AlertManager(db, config)
    
    # 如果配置了自动检查，启动后台线程
    if app.config.get('ALERT_AUTO_CHECK', False):
        interval = app.config.get('ALERT_CHECK_INTERVAL', 60)
        _alert_manager.start_background_check(interval)
    
    return _alert_manager