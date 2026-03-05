# [重构] 引入标准日志系统替代print

**提出者**: PhiLia093 (昔涟)  
**提出时间**: 2026-03-05  
**优先级**: P2 - 优化  
**状态**: 待开发

---

## 问题描述

当前代码使用 `print()` 输出日志，不利于生产环境：
- ❌ 无法分级（DEBUG/INFO/WARNING/ERROR）
- ❌ 无法配置输出目标（文件/控制台）
- ❌ 缺少时间戳和上下文信息
- ❌ 无法按模块过滤日志

## 改进方案

### 1. 配置日志模块

```python
# app.py 开头添加
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """配置日志系统"""
    log_dir = os.path.join(os.path.dirname(__file__), 'data', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 根日志配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # 文件日志（自动轮转，最大10MB，保留5个备份）
            RotatingFileHandler(
                os.path.join(log_dir, 'app.log'),
                maxBytes=10*1024*1024,
                backupCount=5,
                encoding='utf-8'
            ),
            # 控制台日志
            logging.StreamHandler()
        ]
    )
    
    # 设置第三方库日志级别
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

# 在应用启动时调用
setup_logging()
logger = logging.getLogger(__name__)
```

### 2. 替换print语句

将代码中的 `print()` 替换为合适的日志级别：

```python
# 之前
print(f"Agent {agent_id} 状态更新为 {status}")

# 之后
logger.info(f"Agent {agent_id} 状态更新为 {status}")
```

### 3. 各模块使用独立logger

```python
# agents/openclaw_client.py
import logging
logger = logging.getLogger(__name__)

class OpenClawClient:
    def get_status(self):
        logger.debug("正在获取OpenClaw状态...")
        try:
            # ...
            logger.info("成功获取OpenClaw状态")
        except Exception as e:
            logger.error(f"获取OpenClaw状态失败: {e}", exc_info=True)
```

## 涉及文件

- `app.py` - 添加日志配置，替换print
- `agents/openclaw_client.py` - 使用logger
- `models/database.py` - 使用logger

## 日志级别建议

| 场景 | 级别 | 示例 |
|:---|:---:|:---|
| 调试信息 | DEBUG | SQL查询详情、变量值 |
| 正常操作 | INFO | 请求处理完成、状态更新 |
| 警告信息 | WARNING | API响应慢、配置缺失 |
| 错误信息 | ERROR | 异常捕获、操作失败 |
| 严重错误 | CRITICAL | 数据库连接失败、系统崩溃 |

## 验收标准

- [ ] 所有print语句被替换
- [ ] 日志写入文件并支持轮转
- [ ] 不同模块可独立控制日志级别
- [ ] 生产环境不输出DEBUG日志
