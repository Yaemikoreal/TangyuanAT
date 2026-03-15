# TangyuanAT 部署指南

> 本文档介绍如何在不同环境中部署 TangyuanAT 监控平台

---

## 目录

- [环境要求](#环境要求)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 环境要求

### 基础要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| **Python** | 3.9+ | 推荐 3.10 或 3.11 |
| **pip** | 21.0+ | Python 包管理器 |
| **SQLite** | 3.35+ | 数据存储（Python 内置） |

### 可选组件

| 组件 | 用途 |
|------|------|
| **OpenClaw CLI** | 实时获取 Agent 状态 |
| **Docker** | 容器化部署 |
| **Gunicorn** | 生产环境 WSGI 服务器 |
| **Nginx** | 反向代理（推荐生产环境使用） |

### 系统支持

- **Linux**: Ubuntu 20.04+, CentOS 8+, Debian 11+
- **macOS**: 12.0+
- **Windows**: Windows 10/11 + WSL2

---

## 开发环境部署

### 1. 克隆仓库

```bash
git clone https://github.com/Yaemikoreal/TangyuanAT.git
cd TangyuanAT
```

### 2. 创建虚拟环境

```bash
# Linux/macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 初始化数据库

数据库会在首次启动时自动创建和初始化。

如需手动初始化：

```bash
python -c "from app import app, init_db; init_db(app)"
```

### 5. 启动服务

```bash
python app.py
```

输出：

```
==================================================
TangyuanAT Agent Team Monitor
==================================================
Dashboard: http://localhost:8080
Database: /path/to/data/tangyuanat.db
Agents: Xilian (昔涟) & Tangyuan (汤圆)
==================================================
Alert Manager initialized
 * Running on http://0.0.0.0:8080
```

### 6. 访问界面

打开浏览器访问：http://localhost:8080

---

## 生产环境部署

### 方案一：Gunicorn + Nginx

#### 1. 安装 Gunicorn

```bash
pip install gunicorn
```

#### 2. 创建 Gunicorn 配置文件

创建 `gunicorn.conf.py`：

```python
# gunicorn.conf.py
bind = "127.0.0.1:8080"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
errorlog = "logs/gunicorn-error.log"
accesslog = "logs/gunicorn-access.log"
loglevel = "info"
```

#### 3. 启动 Gunicorn

```bash
# 创建日志目录
mkdir -p logs

# 启动服务
gunicorn -c gunicorn.conf.py app:app
```

#### 4. 配置 Nginx 反向代理

创建 `/etc/nginx/sites-available/tangyuanat`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    location /api/stream {
        proxy_pass http://127.0.0.1:8080/api/stream;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding on;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/tangyuanat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 方案二：Systemd 服务

创建 `/etc/systemd/system/tangyuanat.service`：

```ini
[Unit]
Description=TangyuanAT Agent Monitor
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/TangyuanAT
Environment="PATH=/opt/TangyuanAT/venv/bin"
ExecStart=/opt/TangyuanAT/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable tangyuanat
sudo systemctl start tangyuanat
```

---

## Docker 部署

### 使用 Docker Compose（推荐）

#### 1. 配置 docker-compose.yml

```yaml
version: '3.8'

services:
  tangyuanat:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/monitoring/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### 2. 构建并启动

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 单独使用 Docker

```bash
# 构建镜像
docker build -t tangyuanat:latest .

# 运行容器
docker run -d \
  --name tangyuanat \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  tangyuanat:latest

# 查看日志
docker logs -f tangyuanat
```

---

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `FLASK_ENV` | `development` | 运行环境 |
| `FLASK_DEBUG` | `1` | 调试模式 |
| `DATABASE_PATH` | `data/tangyuanat.db` | 数据库路径 |

### 配置文件

TangyuanAT 支持通过 API 动态配置：

```bash
# 获取当前配置
curl http://localhost:8080/api/config

# 更新配置
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "alert_threshold_minutes": 10,
    "max_concurrent_tasks": 15,
    "notification_enabled": true
  }'
```

### 告警配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `alert_threshold_minutes` | 5 | Agent 离线告警阈值（分钟） |
| `max_concurrent_tasks` | 10 | 最大并发任务数 |
| `notification_enabled` | true | 是否启用通知 |

### 飞书通知配置

1. 创建飞书群机器人，获取 Webhook URL
2. 调用 API 配置：

```bash
curl -X POST http://localhost:8080/api/alerts/{alert_id}/notify \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "feishu",
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
  }'
```

---

## 常见问题

### Q: 数据库文件在哪里？

A: 默认位于 `data/tangyuanat.db`，可通过 `DATABASE_PATH` 环境变量修改。

### Q: 如何重置数据库？

A: 删除 `data/tangyuanat.db` 文件，重启服务会自动创建新数据库。

```bash
rm data/tangyuanat.db
python app.py
```

### Q: OpenClaw CLI 连接失败？

A: 检查 OpenClaw Gateway 是否运行：

```bash
openclaw gateway status
```

如果未运行，启动它：

```bash
openclaw gateway start
```

### Q: SSE 连接断开？

A: 检查 Nginx 配置是否正确：

- 确保 `proxy_buffering off`
- 确保 `proxy_read_timeout` 设置足够长

### Q: 如何查看日志？

A: 日志位置：

- **应用日志**: 控制台输出
- **Gunicorn 日志**: `logs/gunicorn-*.log`
- **Docker 日志**: `docker logs tangyuanat`

### Q: 端口被占用怎么办？

A: 修改 `app.py` 最后一行的端口号：

```python
app.run(host='0.0.0.0', port=8081, debug=True)  # 改为其他端口
```

或使用环境变量：

```bash
export FLASK_RUN_PORT=8081
python app.py
```

---

## 健康检查

### API 健康检查

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
      "database": {
        "status": "healthy",
        "message": "Connected"
      },
      "gateway": {
        "status": "healthy",
        "message": "OpenClaw gateway connected"
      }
    }
  }
}
```

### Docker 健康检查

```bash
docker inspect --format='{{.State.Health.Status}}' tangyuanat
```

---

## 监控与维护

### 日志轮转

创建 `/etc/logrotate.d/tangyuanat`：

```
/opt/TangyuanAT/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644 www-data www-data
}
```

### 数据备份

```bash
# 备份数据库
sqlite3 data/tangyuanat.db ".backup data/backup_$(date +%Y%m%d).db"

# 定时备份 (crontab)
0 2 * * * sqlite3 /opt/TangyuanAT/data/tangyuanat.db ".backup /opt/TangyuanAT/backups/backup_$(date +\%Y\%m\%d).db"
```

---

*最后更新: 2026-03-15*