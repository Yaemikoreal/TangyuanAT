# TangyuanAT 项目需求文档

## 当前状态分析

### 已完成
- [x] Flask 后端基础框架
- [x] 前端 HTML/CSS/JS 完整界面
- [x] SSE 实时数据流 (/api/stream)
- [x] Agents 状态展示 API
- [x] 工作日志 API
- [x] 统计面板 API

### 待实现功能（按优先级排序）

#### P0 - 关键需求

1. **数据持久化**
   - 现状：所有数据存储在内存，重启后丢失
   - 需求：接入 SQLite 数据库
   - 涉及表：agents, logs, chat_history, stats

2. **OpenClaw 网关集成**
   - 现状：使用 mock 数据
   - 需求：真实获取 Agent 状态
   - 接口：调用 openclaw status/sessions_list 等命令
   - 文件：新增 `agents/openclaw_client.py`

#### P1 - 重要需求

3. **对话历史展示**
   - 现状：API 已定义 (/api/chat-history)，前端未实现
   - 需求：前端添加对话历史标签页

4. **配置管理**
   - 现状：无动态配置接口
   - 需求：
     - GET /api/config - 获取配置
     - POST /api/config - 更新配置
     - 支持修改 Agent 参数（模型、角色等）

5. **Agent 详情页**
   - 现状：只有列表展示
   - 需求：点击 Agent 卡片进入详情页
   - 内容：技能详情、历史任务、性能图表

#### P2 - 优化需求

6. **告警通知**
   - Agent 离线提醒
   - 任务失败通知
   - 异常响应时间警告

7. **详细统计**
   - 响应时间趋势图
   - 任务完成率统计
   - 每日/每周报表

8. **安全增强**
   - API 鉴权
   - 访问日志
   - 配置加密存储

---

## 技术方案建议

### Phase 1: 数据层 (P0)
```python
# models/database.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Agent(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100))
    status = db.Column(db.String(20))
    model = db.Column(db.String(50))
    tasks_completed = db.Column(db.Integer, default=0)
    messages_processed = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime)
    config = db.Column(db.JSON)

class WorkLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(50), db.ForeignKey('agent.id'))
    action = db.Column(db.String(200))
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

### Phase 2: OpenClaw 集成 (P0)
```python
# agents/openclaw_client.py
import subprocess
import json

class OpenClawClient:
    def get_agent_status(self):
        result = subprocess.run(
            ['openclaw', 'status'],
            capture_output=True, text=True
        )
        return self._parse_status(result.stdout)
    
    def get_sessions(self):
        result = subprocess.run(
            ['openclaw', 'sessions', 'list'],
            capture_output=True, text=True
        )
        return json.loads(result.stdout)
```

---

## 验收标准

每个需求完成后需满足：
- [ ] 功能正常实现
- [ ] 代码通过审查
- [ ] 单元测试覆盖
- [ ] 文档已更新

---

*Created by PhiLia093 | 2026-03-04*
