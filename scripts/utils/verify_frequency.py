"""验证采集频率优化"""
import time
from datetime import datetime, timedelta
from backend.database import SessionLocal, ReversalCondition

print("=" * 70)
print("采集频率优化验证")
print("=" * 70)
print()
print("正在监控反转检测任务的执行情况...")
print("预期：每1分钟新增一条记录")
print()

db = SessionLocal()

# 获取当前最新记录
latest_before = db.query(ReversalCondition).order_by(
    ReversalCondition.fetched_at.desc()
).first()

if latest_before:
    print(f"当前最新记录时间: {latest_before.fetched_at}")
    print(f"信号等级: Level {latest_before.signal_level}")
    print()
else:
    print("数据库中暂无反转记录")
    print()

print("等待新数据采集... (最长等待90秒)")
print("-" * 70)

# 等待最多90秒，检查是否有新记录
max_wait = 90
check_interval = 10
elapsed = 0

new_record = None
while elapsed < max_wait:
    time.sleep(check_interval)
    elapsed += check_interval
    
    # 刷新数据库会话
    db.expire_all()
    
    # 检查是否有新记录
    latest_now = db.query(ReversalCondition).order_by(
        ReversalCondition.fetched_at.desc()
    ).first()
    
    if latest_now and (not latest_before or latest_now.id != latest_before.id):
        new_record = latest_now
        break
    
    print(f"已等待 {elapsed} 秒... (无新数据)")

print("-" * 70)
print()

if new_record:
    time_diff = (new_record.fetched_at - latest_before.fetched_at).total_seconds()
    print("[OK] 检测到新记录！")
    print(f"   新记录时间: {new_record.fetched_at}")
    print(f"   信号等级: Level {new_record.signal_level}")
    print(f"   时间间隔: {time_diff:.0f} 秒")
    print()
    
    if 50 <= time_diff <= 70:
        print("[SUCCESS] 采集频率正常！约每1分钟采集一次。")
    elif 550 <= time_diff <= 650:
        print("[WARNING] 频率仍为10分钟，可能需要重启服务器。")
    else:
        print(f"[WARNING] 间隔为 {time_diff:.0f} 秒，请检查调度器配置。")
else:
    print("[ERROR] 等待超时，未检测到新数据。")
    print("   可能原因：")
    print("   1. 调度器未启动")
    print("   2. 任务执行失败")
    print("   3. 需要重启服务器")

print()

# 统计最近1小时数据
hour_ago = datetime.now() - timedelta(hours=1)
count_1h = db.query(ReversalCondition).filter(
    ReversalCondition.fetched_at >= hour_ago
).count()

print("最近1小时统计：")
print(f"  反转数据: {count_1h} 条")
print(f"  期望值: 60 条 (按1分钟频率)")
print(f"  完成率: {(count_1h/60*100):.1f}%")
print()

if count_1h >= 50:
    print("[SUCCESS] 采集频率已优化到位！")
elif count_1h >= 5:
    print("[WARNING] 频率仍较低，建议检查调度器配置。")
else:
    print("[ERROR] 数据采集异常，请检查服务器日志。")

print()
print("=" * 70)
print("验证完成")
print("=" * 70)

db.close()
