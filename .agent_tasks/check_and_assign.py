#!/usr/bin/env python3
"""
TangyuanAT 自主任务检查和分配脚本
额度优化版本
"""

import json
import os
from datetime import datetime

TASK_BOARD = "/Users/yaemiko/openclawwork/TangyuanAT/.agent_tasks/task_board.md"
AUTO_ASSIGN_RULES = "/Users/yaemiko/openclawwork/TangyuanAT/.agent_tasks/auto_assign_rules.md"
DAILY_LOG = "/Users/yaemiko/openclawwork/TangyuanAT/.agent_tasks/daily_log.md"

# 每日额度预算
DAILY_QUOTA = {
    "checks": 2,  # 每日检查次数
    "tasks": 3,   # 每日任务分配次数
    "used_checks": 0,
    "used_tasks": 0
}

def load_daily_quota():
    """加载今日额度使用情况"""
    today = datetime.now().strftime("%Y-%m-%d")
    quota_file = f"/Users/yaemiko/openclawwork/TangyuanAT/.agent_tasks/quota_{today}.json"
    
    if os.path.exists(quota_file):
        with open(quota_file, 'r') as f:
            return json.load(f)
    return DAILY_QUOTA.copy()

def save_daily_quota(quota):
    """保存额度使用情况"""
    today = datetime.now().strftime("%Y-%m-%d")
    quota_file = f"/Users/yaemiko/openclawwork/TangyuanAT/.agent_tasks/quota_{today}.json"
    
    with open(quota_file, 'w') as f:
        json.dump(quota, f, indent=2)

def check_github_issues():
    """检查 GitHub Issues 状态"""
    # 使用 gh CLI 检查
    import subprocess
    
    try:
        result = subprocess.run(
            ['gh', 'issue', 'list', '--repo', 'Yaemikoreal/TangyuanAT', '--json', 'number,title,state,labels'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            issues = json.loads(result.stdout)
            open_issues = [i for i in issues if i['state'] == 'OPEN']
            return open_issues
    except Exception as e:
        print(f"检查 Issues 失败: {e}")
    
    return []

def assign_task(issue, quota):
    """根据规则分配任务"""
    if quota['used_tasks'] >= quota['tasks']:
        return None, "额度不足"
    
    # 根据标签判断优先级
    labels = [l['name'] for l in issue.get('labels', [])]
    
    if 'bug' in labels or 'critical' in labels:
        assignee = 'xilian'
        priority = 'P0'
    elif 'feature' in labels:
        # 负载均衡
        if quota['used_tasks'] % 2 == 0:
            assignee = 'tangyuan'
        else:
            assignee = 'doufu'
        priority = 'P1'
    else:
        assignee = 'doufu'
        priority = 'P2'
    
    quota['used_tasks'] += 1
    return assignee, priority

def update_task_board(issue, assignee, priority):
    """更新任务板"""
    # 写入 task_board.md
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    update = f"""
### 🆕 新任务自动分配
**时间:** {timestamp}  
**Issue:** #{issue['number']} - {issue['title']}  
**优先级:** {priority}  
**分配给:** {assignee}  
**状态:** 待开始

---
"""
    
    with open(TASK_BOARD, 'a') as f:
        f.write(update)

def generate_daily_report(quota, issues):
    """生成日报"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    report = f"""## TangyuanAT 日报 - {today}

### 额度使用
- 检查次数: {quota['used_checks']}/{quota['checks']}
- 任务分配: {quota['used_tasks']}/{quota['tasks']}
- 剩余预算: 检查 {quota['checks'] - quota['used_checks']}, 任务 {quota['tasks'] - quota['used_tasks']}

### Issues 状态
- Open Issues: {len(issues)}
- 今日分配: {quota['used_tasks']}

### 待处理任务
"""
    
    for issue in issues[:5]:  # 只显示前5个
        report += f"- #{issue['number']}: {issue['title']}\n"
    
    with open(DAILY_LOG, 'a') as f:
        f.write(report + "\n---\n")
    
    return report

def main():
    """主函数"""
    print("=" * 50)
    print("TangyuanAT 自主任务检查")
    print("=" * 50)
    
    # 加载额度
    quota = load_daily_quota()
    quota['used_checks'] += 1
    
    print(f"\n额度状态: 检查 {quota['used_checks']}/{quota['checks']}, 任务 {quota['used_tasks']}/{quota['tasks']}")
    
    # 检查 Issues
    print("\n检查 GitHub Issues...")
    issues = check_github_issues()
    
    if not issues:
        print("✅ 无待处理 Issues，跳过任务分配")
        save_daily_quota(quota)
        return
    
    print(f"发现 {len(issues)} 个 Open Issues")
    
    # 分配任务
    assigned = 0
    for issue in issues:
        if quota['used_tasks'] >= quota['tasks']:
            print(f"⚠️ 额度不足，跳过剩余 Issues")
            break
        
        assignee, priority = assign_task(issue, quota)
        if assignee:
            print(f"✅ 分配 Issue #{issue['number']} 给 {assignee} ({priority})")
            update_task_board(issue, assignee, priority)
            assigned += 1
    
    # 保存额度
    save_daily_quota(quota)
    
    # 生成报告
    report = generate_daily_report(quota, issues)
    print("\n" + "=" * 50)
    print(report)
    print("=" * 50)

if __name__ == '__main__':
    main()
