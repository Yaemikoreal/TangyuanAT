# Issue #001: 修复 uptime 显示为固定值的问题

## 问题描述
当前 `/api/stats` 接口返回的 `uptime` 字段是固定字符串 `"运行中"`，而非实际的运行时长。

## 代码位置
`app.py` 第244行：
```python
"uptime": "运行中",  # TODO: 计算实际运行时间
```

## 期望行为
返回格式化的运行时长，例如：
- `"2h 30m"` - 运行2小时30分钟
- `"1d 5h"` - 运行1天5小时
- `"45m"` - 运行45分钟

## 实现建议

### 方案1：使用启动时间戳（推荐）
```python
import time

# 在应用启动时记录
START_TIME = time.time()

def get_uptime():
    elapsed = int(time.time() - START_TIME)
    days = elapsed // 86400
    hours = (elapsed % 86400) // 3600
    minutes = (elapsed % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or not parts:
        parts.append(f"{minutes}m")
    
    return " ".join(parts)
```

### 方案2：使用 datetime
```python
from datetime import datetime, timedelta

START_TIME = datetime.utcnow()

def get_uptime():
    delta = datetime.utcnow() - START_TIME
    total_seconds = int(delta.total_seconds())
    # ... 同上格式化
```

## 修改范围
- [ ] `app.py`: 添加启动时间记录
- [ ] `app.py`: 修改 `/api/stats` 接口
- [ ] 可选：`templates/index.html`: 优化前端显示样式

## 优先级
**P1 - 高**（影响用户体验）

## 验收标准
- [ ] API返回真实的运行时长
- [ ] 格式清晰易读
- [ ] 重启后重新计时
- [ ] 不影响现有功能

---
*Created by PhiLia093 via automated code review | 2026-03-05*
