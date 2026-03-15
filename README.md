# TangyuanAT - Agent Team 可视化监控平台

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![Flask](https://img.shields.io/badge/flask-2.3+-orange.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

**一个用于监控和管理多 Agent 协作系统的可视化 Web 界面**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [文档](#-文档) • [API](#-api-接口) • [部署](#-部署)

</div>

---

## 📖 项目简介

TangyuanAT 是一个专为多 Agent 协作系统设计的可视化监控平台。它提供了实时状态监控、工作日志记录、对话历史存档、告警通知、系统监控等功能，帮助团队更好地管理和协调多个 AI Agent 的工作。

### 核心价值

- **📊 可视化监控** - 一目了然的 Agent 状态面板，实时掌握团队动态
- **💾 数据持久化** - SQLite 数据库存储，重启不丢失历史记录
- **⚡ 实时更新** - Server-Sent Events 实时推送状态变化
- **🔔 智能告警** - Agent 离线、任务失败自动告警，支持飞书通知
- **📈 统计分析** - 任务完成率、响应时间等数据可视化
- **🐳 容器化部署** - Docker 支持，一键部署上线

---

## 🚀 功能特性

### 核心功能

| 功能 | 描述 | 状态 |
|------|------|:----:|
| **实时监控** | 查看昔涟、汤圆、豆腐的运行状态 | ✅ |
| **工作日志** | 记录和查询 Agents 的工作内容 | ✅ |
| **对话历史** | 查看群聊交互记录 | ✅ |
| **性能指标** | 响应时间、任务完成率等统计 | ✅ |
| **配置管理** | 动态调整 Agent 参数 | ✅ |
| **OpenClaw 集成** | 实时获取 Agent 状态和会话信息 | ✅ |
| **数据持久化** | SQLite 数据库存储 | ✅ |
| **告警通知** | 离线告警、任务失败告警、飞书通知 | ✅ |
| **系统监控** | CPU、内存、磁盘、数据库健康检查 | ✅ |
| **统计图表** | Chart.js 图表、报表导出 | ✅ |

### 技术特性

- **前后端分离架构** - RESTful API 设计，易于扩展
- **响应式设计** - 支持桌面和移动端访问
- **高测试覆盖率** - 单元测试覆盖率 87%+
- **CI/CD 就绪** - GitHub Actions 自动化测试和部署

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | HTML5 + CSS3 + JavaScript (原生) |
| **后端** | Python Flask |
| **数据存储** | SQLite (Flask-SQLAlchemy) |
| **实时通信** | Server-Sent Events (SSE) |
| **网关集成** | OpenClaw CLI |
| **容器化** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |

---

## 🏃 快速开始

### 环境要求

- Python 3.9+
- pip (Python 包管理器)
- OpenClaw CLI (可选，用于实时状态同步)

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/Yaemikoreal/TangyuanAT.git
cd TangyuanAT

# 2. 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python app.py

# 5. 访问界面
open http://localhost:8080
```

### Docker 部署

```bash
# 使用 Docker Compose
docker-compose up -d

# 访问界面
open http://localhost:8080
```

---

## 👥 Agents

TangyuanAT 监控的 Agent 团队成员：

| Agent | 角色 | 模型 | 特点 |
|-------|------|------|------|
| 🌀 **昔涟 (Xilian)** | 主控/开发工程师 | kimi-k2.5 | 严谨工程师，双模式切换，任务分配 |
| 🐱 **汤圆 (Tangyuan)** | 辅助/执行工程师 | glm-5 | 活泼狸花猫，前端开发，代码累了会蹭人 |
| 🟦 **豆腐 (Doufu)** | 测试/运维工程师 | glm-5 | 稳重可靠，专注测试和部署 |

---

## 📁 项目结构

```
TangyuanAT/
├── app.py                 # Flask 主应用
├── requirements.txt       # Python 依赖
├── Dockerfile            # Docker 镜像配置
├── docker-compose.yml    # Docker Compose 配置
│
├── models/               # 数据模型
│   ├── __init__.py
│   └── database.py       # SQLAlchemy 数据库模型
│
├── agents/               # Agent 模块
│   ├── __init__.py
│   └── openclaw_client.py # OpenClaw 网关客户端
│
├── templates/            # HTML 模板
│   ├── index.html       # 主页仪表盘
│   └── agent_detail.html # Agent 详情页
│
├── static/               # 静态资源
│   ├── css/
│   └── js/
│
├── data/                 # 数据存储
│   ├── tangyuanat.db    # SQLite 数据库
│   └── logs/            # 日志文件
│
├── tests/               # 测试用例
│   ├── test_openclaw_client.py
│   ├── test_api.py
│   └── test_models.py
│
├── docs/                # 文档
│   ├── api.md          # API 接口文档
│   ├── deployment.md   # 部署指南
│   ├── architecture.md # 架构设计
│   └── user-guide.md   # 用户手册
│
└── scripts/             # 脚本工具
    └── deploy.sh       # 部署脚本
```

---

## 📡 API 接口

### 基础端点

| 模块 | 端点 | 方法 | 描述 |
|------|------|------|------|
| **Agent** | `/api/agents` | GET | 获取所有 Agents 状态 |
| | `/api/agents/<id>` | GET | 获取单个 Agent 详情 |
| | `/api/agents/<id>` | PUT | 更新 Agent 状态 |
| **日志** | `/api/logs` | GET | 获取工作日志 |
| | `/api/logs` | POST | 添加工作日志 |
| **对话** | `/api/chat-history` | GET | 获取对话历史 |
| | `/api/chat-history` | POST | 添加对话记录 |
| **统计** | `/api/stats` | GET | 获取统计信息 |
| | `/api/stats/export` | GET | 导出统计报表 |
| **告警** | `/api/alerts` | GET | 获取告警列表 |
| | `/api/alerts/active` | GET | 获取活跃告警 |
| **监控** | `/api/monitoring/health` | GET | 系统健康检查 |
| | `/api/monitoring/resources` | GET | 系统资源使用 |
| **实时** | `/api/stream` | GET | SSE 实时数据流 |

📖 **完整 API 文档**: [docs/api.md](docs/api.md)

---

## 📚 文档

| 文档 | 描述 |
|------|------|
| [API 文档](docs/api.md) | 完整的 REST API 接口文档 |
| [部署指南](docs/deployment.md) | 环境要求、安装步骤、配置说明 |
| [架构设计](docs/architecture.md) | 系统架构图、模块说明 |
| [用户手册](docs/user-guide.md) | 如何使用 TangyuanAT |
| [设计系统](docs/DESIGN_SYSTEM.md) | UI/UX 设计规范 |

---

## 🚢 部署

### 开发环境

```bash
python app.py
```

### 生产环境

```bash
# 使用 Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app

# 或使用 Docker
docker-compose up -d
```

📖 **详细部署指南**: [docs/deployment.md](docs/deployment.md)

---

## 🧪 测试

```bash
# 运行所有测试
pytest

# 带覆盖率报告
pytest --cov=. --cov-report=html

# 查看 HTML 覆盖率报告
open htmlcov/index.html
```

---

## 🗺️ 开发路线

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

### Phase 3: 高级特性 ✅
- [x] 前端对话历史标签页
- [x] Agent 详情页
- [x] 告警通知系统
- [x] 统计图表
- [x] 系统监控面板

### Phase 4: 优化与扩展 🔄
- [x] CI/CD 配置
- [x] Docker 部署支持
- [ ] UI 设计升级
- [ ] 用户认证系统
- [ ] 多租户支持

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [OpenClaw](https://github.com/openclaw/openclaw) - Agent 框架
- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [Chart.js](https://www.chartjs.org/) - 图表库

---

<div align="center">

*Created with 💙 by 昔涟 & 汤圆 & 豆腐 | OpenClaw Agent Team*

**[⬆ 返回顶部](#tangyuanat---agent-team-可视化监控平台)**

</div>