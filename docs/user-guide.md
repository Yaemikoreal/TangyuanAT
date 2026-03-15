# TangyuanAT 用户操作手册

> 本手册帮助用户快速上手 TangyuanAT 监控平台

---

## 目录

- [快速入门](#快速入门)
- [界面介绍](#界面介绍)
- [功能操作](#功能操作)
- [常见场景](#常见场景)
- [常见问题](#常见问题)

---

## 快速入门

### 访问系统

1. 打开浏览器
2. 输入地址：`http://localhost:8080`（或您部署的地址）
3. 进入 TangyuanAT 主界面

### 界面预览

```
┌────────────────────────────────────────────────────────────┐
│  🐱 TangyuanAT - Agent Team Monitor                    ⚙️  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ 🌀 昔涟     │  │ 🐱 汤圆     │  │ 🟦 豆腐     │       │
│  │ ● 在线      │  │ ● 任务中    │  │ ○ 离线      │       │
│  │ kimi-k2.5   │  │ glm-5       │  │ glm-5       │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                            │
│  📊 统计概览                                               │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 今日任务: 15  今日消息: 42  在线Agent: 2         │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 界面介绍

### 导航栏

| 元素 | 说明 |
|------|------|
| **Logo** | TangyuanAT 品牌标识 |
| **状态指示器** | 网关连接状态 |
| **设置按钮** | 系统配置入口 |

### Agent 卡片

每个 Agent 显示以下信息：

```
┌─────────────────────┐
│ 🌀 昔涟             │  ← Agent 名称 + Emoji
│ ● 在线              │  ← 状态指示
│                     │
│ 模型: kimi-k2.5     │  ← 使用的模型
│ 角色: 主控/开发     │  ← Agent 角色
│ 任务: 编写API文档   │  ← 当前任务
│                     │
│ 已完成: 15 个任务   │  ← 统计信息
│ 最后活跃: 2分钟前   │  ← 活跃时间
└─────────────────────┘
```

### 状态说明

| 状态 | 图标 | 含义 |
|------|:----:|------|
| **在线** | 🟢 | Agent 正常运行，可接收任务 |
| **任务中** | 🟡 | Agent 正在执行任务 |
| **闲置** | ⚪ | Agent 在线但无任务 |
| **离线** | 🔴 | Agent 已断开连接 |

---

## 功能操作

### 1. 查看 Agent 状态

**位置**: 主页仪表盘

**操作步骤**:

1. 打开主页
2. 查看 Agent 卡片区域
3. 点击 Agent 卡片查看详情

**状态刷新**:
- 自动刷新：每 5 秒通过 SSE 更新
- 手动刷新：刷新浏览器页面

### 2. 查看工作日志

**位置**: 日志标签页

**操作步骤**:

1. 点击「日志」标签
2. 查看所有 Agent 的工作记录
3. 使用筛选器按 Agent 过滤

**日志信息包含**:

| 字段 | 说明 |
|------|------|
| 时间 | 日志记录时间 |
| Agent | 执行者 |
| 动作 | 执行的操作 |
| 详情 | 操作详情 |

**API 调用**:

```bash
# 获取所有日志
curl http://localhost:8080/api/logs

# 筛选特定 Agent 的日志
curl "http://localhost:8080/api/logs?agent_id=xilian"
```

### 3. 查看对话历史

**位置**: 对话历史标签页

**操作步骤**:

1. 点击「对话历史」标签
2. 浏览历史消息
3. 使用分页查看更多

**API 调用**:

```bash
# 获取对话历史
curl http://localhost:8080/api/chat-history

# 分页获取
curl "http://localhost:8080/api/chat-history?page=1&per_page=20"
```

### 4. 查看统计数据

**位置**: 统计标签页

**可用数据**:

- 今日任务数
- 今日消息数
- 在线 Agent 数
- 响应时间趋势图
- 任务完成率饼图

**导出报表**:

```bash
# 导出 CSV 格式
curl "http://localhost:8080/api/stats/export?format=csv" -o report.csv

# 导出 JSON 格式
curl "http://localhost:8080/api/stats/export?format=json" -o report.json
```

### 5. 管理告警

**位置**: 告警标签页

#### 查看告警列表

```bash
# 获取所有告警
curl http://localhost:8080/api/alerts

# 获取活跃告警
curl http://localhost:8080/api/alerts/active

# 按状态筛选
curl "http://localhost:8080/api/alerts?status=active"
```

#### 确认告警

```bash
curl -X POST http://localhost:8080/api/alerts/1/acknowledge \
  -H "Content-Type: application/json" \
  -d '{"acknowledged_by": "admin"}'
```

#### 解决告警

```bash
curl -X POST http://localhost:8080/api/alerts/1/resolve
```

#### 发送飞书通知

```bash
curl -X POST http://localhost:8080/api/alerts/1/notify \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "feishu",
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
  }'
```

### 6. 系统监控

**位置**: 监控标签页

#### 健康检查

```bash
curl http://localhost:8080/api/monitoring/health
```

响应示例：

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "score": 95,
    "components": {
      "database": {"status": "healthy"},
      "gateway": {"status": "healthy"}
    }
  }
}
```

#### 资源监控

```bash
curl http://localhost:8080/api/monitoring/resources
```

响应示例：

```json
{
  "success": true,
  "data": {
    "cpu": {"percent": 25.5},
    "memory": {"percent": 46.8, "total_gb": 16.0},
    "disk": {"percent": 50.2, "total_gb": 256.0}
  }
}
```

### 7. 配置管理

**获取配置**:

```bash
curl http://localhost:8080/api/config
```

**更新配置**:

```bash
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "alert_threshold_minutes": 10,
    "max_concurrent_tasks": 15,
    "notification_enabled": true
  }'
```

**可配置项**:

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `alert_threshold_minutes` | Agent 离线告警阈值（分钟） | 5 |
| `max_concurrent_tasks` | 最大并发任务数 | 10 |
| `notification_enabled` | 是否启用通知 | true |

---

## 常见场景

### 场景 1：检查 Agent 是否在线

1. 打开主页
2. 查看 Agent 卡片状态指示
3. 绿色圆点 = 在线，红色圆点 = 离线

**API 方式**:

```bash
curl http://localhost:8080/api/agents/xilian
```

### 场景 2：查看某个 Agent 的工作记录

1. 点击「日志」标签
2. 在筛选器中选择 Agent
3. 浏览该 Agent 的所有工作记录

**API 方式**:

```bash
curl "http://localhost:8080/api/logs?agent_id=tangyuan"
```

### 场景 3：处理 Agent 离线告警

1. 查看告警列表
2. 点击告警查看详情
3. 检查 Agent 状态
4. 确认告警（表示已知晓）
5. 解决问题后，标记告警为已解决

**API 方式**:

```bash
# 获取活跃告警
curl http://localhost:8080/api/alerts/active

# 确认告警
curl -X POST http://localhost:8080/api/alerts/1/acknowledge

# 解决告警
curl -X POST http://localhost:8080/api/alerts/1/resolve
```

### 场景 4：导出统计报表

1. 点击「统计」标签
2. 点击「导出」按钮
3. 选择格式（CSV/JSON）
4. 下载报表文件

**API 方式**:

```bash
# 导出 CSV
curl "http://localhost:8080/api/stats/export?format=csv" -o report.csv

# 导出 JSON
curl "http://localhost:8080/api/stats/export?format=json" -o report.json
```

### 场景 5：检查系统健康状态

1. 点击「监控」标签
2. 查看健康分数和组件状态
3. 查看资源使用情况

**API 方式**:

```bash
# 健康检查
curl http://localhost:8080/api/monitoring/health

# 资源状态
curl http://localhost:8080/api/monitoring/resources

# 数据库状态
curl http://localhost:8080/api/monitoring/database
```

---

## 常见问题

### Q: 页面显示不正常？

**检查清单**:

1. 清除浏览器缓存
2. 检查网络连接
3. 确认服务是否运行

```bash
# 检查服务状态
curl http://localhost:8080/api/monitoring/health
```

### Q: Agent 状态不更新？

**可能原因**:

1. OpenClaw Gateway 未运行
2. 网络连接问题
3. Agent 确实离线

**解决方案**:

```bash
# 检查 OpenClaw 网关
openclaw gateway status

# 启动网关（如果未运行）
openclaw gateway start
```

### Q: 告警通知没收到？

**检查清单**:

1. 飞书 Webhook 配置是否正确
2. 告警规则是否启用
3. 查看告警通知记录

```bash
# 测试飞书通知
curl -X POST http://localhost:8080/api/alerts/1/notify \
  -H "Content-Type: application/json" \
  -d '{"channel": "feishu", "webhook_url": "YOUR_WEBHOOK_URL"}'
```

### Q: 数据库文件在哪里？

默认位置：`data/tangyuanat.db`

```bash
# 查看数据库大小
ls -lh data/tangyuanat.db

# 备份数据库
sqlite3 data/tangyuanat.db ".backup data/backup.db"
```

### Q: 如何重置数据？

```bash
# 停止服务
# 删除数据库
rm data/tangyuanat.db

# 重启服务会自动创建新数据库
python app.py
```

### Q: API 返回 500 错误？

**排查步骤**:

1. 查看服务日志
2. 检查数据库连接
3. 确认请求参数正确

```bash
# 检查服务日志
docker logs tangyuanat  # Docker 部署
# 或
tail -f logs/gunicorn-error.log  # Gunicorn 部署
```

---

## 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| `R` | 刷新页面 |
| `1` | 切换到仪表盘 |
| `2` | 切换到日志 |
| `3` | 切换到统计 |
| `?` | 显示帮助 |

---

## 联系支持

如遇到问题，可以通过以下方式获取帮助：

1. 查看 [API 文档](api.md)
2. 查看 [部署指南](deployment.md)
3. 提交 GitHub Issue

---

*最后更新: 2026-03-15*