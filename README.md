# TangyuanAT - Agent Team 可视化监控平台

一个用于监控和管理多 Agent 协作系统的可视化 Web 界面。

## 功能特性

- 📊 **实时监控**: 查看昔涟和汤圆的运行状态
- 📝 **工作日志**: 记录和查询 Agents 的工作内容
- 💬 **对话历史**: 查看群聊交互记录
- ⚡ **性能指标**: 响应时间、任务完成率等统计
- 🔧 **配置管理**: 动态调整 Agent 参数

## 技术栈

- **前端**: HTML5 + CSS3 + JavaScript (原生)
- **后端**: Python Flask
- **数据存储**: JSON 文件 / SQLite
- **实时通信**: Server-Sent Events (SSE)

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
| 昔涟 (Xilian) | 主控/开发 | kimi-k2.5 | 严谨工程师，双模式切换 |
| 汤圆 (Tangyuan) | 辅助/执行 | glm-5 | 活泼狸花猫，代码累了会蹭人 |

## 项目结构

```
TangyuanAT/
├── app.py                 # Flask 主应用
├── config.py              # 配置文件
├── agents/                # Agent 模块
│   ├── __init__.py
│   ├── xilian.py         # 昔涟接口
│   └── tangyuan.py       # 汤圆接口
├── static/               # 静态资源
│   ├── css/
│   ├── js/
│   └── images/
├── templates/            # HTML 模板
│   └── index.html
├── data/                 # 数据存储
│   ├── logs/
│   └── stats/
└── README.md
```

## 开发计划

### Phase 1: 基础框架
- [x] 项目初始化
- [ ] Flask 后端搭建
- [ ] 前端基础界面
- [ ] Agent 状态 mock 数据

### Phase 2: 核心功能
- [ ] 实时状态监控
- [ ] 工作日志记录
- [ ] 对话历史展示
- [ ] 性能指标统计

### Phase 3: 高级特性
- [ ] 与 OpenClaw 网关集成
- [ ] 真实 Agent 数据接入
- [ ] 远程命令执行
- [ ] 告警通知

---
*Created by 昔涟 & 汤圆 | OpenClaw Agent Team*
