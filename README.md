# TangyuanAT - Agent Team 可视化监控平台

一个用于监控和管理多 Agent 协作系统的可视化 Web 界面。

## 功能特性

- 📊 **实时监控**: 查看昔涟和汤圆的运行状态
- 📝 **工作日志**: 记录和查询 Agents 的工作内容（持久化存储）
- 💬 **对话历史**: 查看群聊交互记录
- ⚡ **性能指标**: 响应时间、任务完成率等统计
- 🔧 **配置管理**: 动态调整 Agent 参数
- 🔗 **OpenClaw 集成**: 实时获取 Agent 状态和会话信息
- 💾 **数据持久化**: SQLite 数据库存储，重启不丢失

## 技术栈

- **前端**: HTML5 + CSS3 + JavaScript (原生)
- **后端**: Python Flask
- **数据存储**: SQLite (Flask-SQLAlchemy)
- **实时通信**: Server-Sent Events (SSE)
- **网关集成**: OpenClaw CLI

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py

# 访问界面
open http://localhost:5000
```

## Agents

| Agent | 角色 | 模型 | 特点 |
|-------|------|------|------|
| 昔涟 (Xilian) | 主控/开发 | kimi-k2.5 | 严谨工程师，双模式切换，任务分配 |
| 汤圆 (Tangyuan) | 辅助/执行 | glm-5 | 活泼狸花猫，前端开发，代码累了会蹭人 |
| 豆腐 (Doufu) | 测试/运维 | glm-5 | 稳重可靠，专注测试和部署 |

## 项目结构

```
TangyuanAT/
├── app.py                 # Flask 主应用
├── requirements.txt       # Python 依赖
├── models/                # 数据模型
│   ├── __init__.py
│   └── database.py       # SQLAlchemy 数据库模型
├── agents/                # Agent 模块
│   ├── __init__.py
│   └── openclaw_client.py # OpenClaw 网关客户端
├── templates/            # HTML 模板
│   └── index.html
├── data/                 # 数据存储
│   ├── tangyuanat.db     # SQLite 数据库
│   └── logs/             # 日志文件
└── docs/                 # 文档
    └── REQUIREMENTS.md   # 需求文档
```

## API 接口

### Agents
- `GET /api/agents` - 获取所有 Agents 状态
- `GET /api/agents/<id>` - 获取单个 Agent 详情
- `PUT /api/agents/<id>` - 更新 Agent 状态

### 日志
- `GET /api/logs` - 获取工作日志
- `POST /api/logs` - 添加工作日志

### 对话历史
- `GET /api/chat-history` - 获取对话历史
- `POST /api/chat-history` - 添加对话记录

### 统计
- `GET /api/stats` - 获取统计信息

### 配置
- `GET /api/config` - 获取配置
- `POST /api/config` - 更新配置

### OpenClaw
- `GET /api/openclaw/status` - 获取 OpenClaw 网关状态
- `GET /api/openclaw/sessions` - 获取会话列表

### 实时流
- `GET /api/stream` - SSE 实时数据流

## 开发计划

### Phase 1: 基础框架 ✅
- [x] 项目初始化
- [x] Flask 后端搭建
- [x] 前端基础界面
- [x] Agent 状态数据

### Phase 2: 核心功能 ✅
- [x] 数据持久化 (SQLite)
- [x] OpenClaw 网关集成
- [x] 工作日志记录
- [x] 对话历史 API
- [x] 配置管理 API

### Phase 3: 高级特性 (进行中)
- [ ] 前端对话历史标签页
- [ ] Agent 详情页
- [ ] 告警通知
- [ ] 统计图表

---
*Created by 昔涟 & 汤圆 & 豆腐 | OpenClaw Agent Team*