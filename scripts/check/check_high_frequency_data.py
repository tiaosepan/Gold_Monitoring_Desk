"""检查数据库中的高频采集异常数据"""
import sqlite3
from datetime import datetime, timedelta
from collections import Counter

db_path = r"d:\www\prototype\Gold_Monitoring_Desk\database\gold_monitor.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("检查数据库中的高频采集异常")
print("=" * 80)

# 1. 检查反转数据的采集频率
print("\n【1. 反转数据频率分析】")
cursor.execute("""
    SELECT fetched_at 
    FROM reversal_conditions 
    WHERE fetched_at >= datetime('now', '-2 hours')
    ORDER BY fetched_at ASC
""")
reversal_times = [row[0] for row in cursor.fetchall()]

if len(reversal_times) > 1:
    intervals = []
    for i in range(1, len(reversal_times)):
        t1 = datetime.fromisoformat(reversal_times[i-1])
        t2 = datetime.fromisoformat(reversal_times[i])
        interval_seconds = (t2 - t1).total_seconds()
        intervals.append(interval_seconds)
    
    interval_counter = Counter([int(i) for i in intervals if i < 120])
    print(f"最近2小时采集了 {len(reversal_times)} 条记录")
    print(f"平均间隔: {sum(intervals)/len(intervals):.1f} 秒")
    print(f"最小间隔: {min(intervals):.1f} 秒")
    print(f"最大间隔: {max(intervals):.1f} 秒")
    print("\n间隔分布（前10个最常见）:")
    for interval, count in interval_counter.most_common(10):
        print(f"  {interval}秒: {count}次")
    
    # 统计异常高频数据（间隔<30秒）
    high_freq_count = sum(1 for i in intervals if i < 30)
    print(f"\n[警告] 异常高频采集（<30秒间隔）: {high_freq_count} 条 ({high_freq_count/len(intervals)*100:.1f}%)")

# 2. 检查SGE数据的采集频率
print("\n【2. SGE数据频率分析】")
cursor.execute("""
    SELECT fetched_at 
    FROM sge_prices 
    WHERE fetched_at >= datetime('now', '-2 hours')
    ORDER BY fetched_at ASC
""")
sge_times = [row[0] for row in cursor.fetchall()]

if len(sge_times) > 1:
    intervals = []
    for i in range(1, len(sge_times)):
        t1 = datetime.fromisoformat(sge_times[i-1])
        t2 = datetime.fromisoformat(sge_times[i])
        interval_seconds = (t2 - t1).total_seconds()
        intervals.append(interval_seconds)
    
    print(f"最近2小时采集了 {len(sge_times)} 条记录")
    print(f"平均间隔: {sum(intervals)/len(intervals):.1f} 秒")
    print(f"最小间隔: {min(intervals):.1f} 秒")
    
    # 统计异常高频数据（间隔<30秒）
    high_freq_count = sum(1 for i in intervals if i < 30)
    if high_freq_count > 0:
        print(f"[警告] 异常高频采集（<30秒间隔）: {high_freq_count} 条 ({high_freq_count/len(intervals)*100:.1f}%)")

# 3. 检查美债数据的采集频率
print("\n【3. 美债数据频率分析】")
cursor.execute("""
    SELECT fetched_at 
    FROM us_treasury 
    WHERE fetched_at >= datetime('now', '-2 hours')
    ORDER BY fetched_at ASC
""")
us10y_times = [row[0] for row in cursor.fetchall()]

if len(us10y_times) > 1:
    intervals = []
    for i in range(1, len(us10y_times)):
        t1 = datetime.fromisoformat(us10y_times[i-1])
        t2 = datetime.fromisoformat(us10y_times[i])
        interval_seconds = (t2 - t1).total_seconds()
        intervals.append(interval_seconds)
    
    print(f"最近2小时采集了 {len(us10y_times)} 条记录")
    print(f"平均间隔: {sum(intervals)/len(intervals):.1f} 秒")
    print(f"最小间隔: {min(intervals):.1f} 秒")
    
    # 统计异常高频数据（间隔<30秒）
    high_freq_count = sum(1 for i in intervals if i < 30)
    if high_freq_count > 0:
        print(f"[警告] 异常高频采集（<30秒间隔）: {high_freq_count} 条 ({high_freq_count/len(intervals)*100:.1f}%)")

# 4. 统计各表总记录数
print("\n【4. 数据库总量统计】")
tables = ['reversal_conditions', 'sge_prices', 'us_treasury', 'rss_events']
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    cursor.execute(f"SELECT MIN(fetched_at), MAX(fetched_at) FROM {table}")
    min_time, max_time = cursor.fetchone()
    print(f"{table}: {count} 条记录")
    if min_time and max_time:
        print(f"  时间范围: {min_time} 至 {max_time}")

conn.close()
print("\n" + "=" * 80)
