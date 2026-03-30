"""清理异常高频数据并保留正常采样数据"""
import sqlite3
from datetime import datetime
from collections import defaultdict

db_path = r"d:\www\prototype\Gold_Monitoring_Desk\database\gold_monitor.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("清理异常高频采集数据")
print("=" * 80)

def clean_table_by_sampling(table_name, min_interval_seconds, time_column='fetched_at'):
    """
    清理表中的高频数据，保留符合最小间隔的采样点
    """
    print(f"\n处理表: {table_name}")
    print(f"  最小间隔要求: {min_interval_seconds}秒")
    
    # 获取所有记录，按时间排序
    cursor.execute(f"""
        SELECT id, {time_column} 
        FROM {table_name} 
        ORDER BY {time_column} ASC
    """)
    records = cursor.fetchall()
    
    if len(records) == 0:
        print("  无数据")
        return
    
    print(f"  原始记录数: {len(records)}")
    
    # 采样逻辑：保留符合最小间隔的记录
    keep_ids = []
    last_kept_time = None
    
    for record_id, time_str in records:
        current_time = datetime.fromisoformat(time_str)
        
        if last_kept_time is None:
            # 保留第一条记录
            keep_ids.append(record_id)
            last_kept_time = current_time
        else:
            interval = (current_time - last_kept_time).total_seconds()
            if interval >= min_interval_seconds:
                # 间隔足够，保留
                keep_ids.append(record_id)
                last_kept_time = current_time
    
    # 删除不保留的记录
    delete_count = len(records) - len(keep_ids)
    
    if delete_count > 0:
        # 批量删除
        keep_ids_str = ','.join(map(str, keep_ids))
        cursor.execute(f"DELETE FROM {table_name} WHERE id NOT IN ({keep_ids_str})")
        conn.commit()
        print(f"  删除记录数: {delete_count}")
        print(f"  保留记录数: {len(keep_ids)}")
        print(f"  清理率: {delete_count/len(records)*100:.1f}%")
    else:
        print("  无需清理")

# 清理各表数据
# 1. 反转数据：应该每分钟一次（60秒）
clean_table_by_sampling('reversal_conditions', min_interval_seconds=55)

# 2. SGE数据：根据配置应该每60秒一次
clean_table_by_sampling('sge_prices', min_interval_seconds=55)

# 3. 美债数据：根据配置应该每60秒一次
clean_table_by_sampling('us_treasury', min_interval_seconds=55)

# 4. RSS事件：根据配置应该每15分钟一次（900秒）
clean_table_by_sampling('rss_events', min_interval_seconds=850)

# 统计清理后的结果
print("\n" + "=" * 80)
print("清理后统计")
print("=" * 80)

tables = [
    ('reversal_conditions', 60),
    ('sge_prices', 60),
    ('us_treasury', 60),
    ('rss_events', 900)
]

for table_name, expected_interval in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    
    cursor.execute(f"""
        SELECT fetched_at 
        FROM {table_name} 
        ORDER BY fetched_at DESC 
        LIMIT 10
    """)
    recent_times = [row[0] for row in cursor.fetchall()]
    
    print(f"\n{table_name}:")
    print(f"  总记录数: {count}")
    print(f"  预期间隔: {expected_interval}秒")
    
    if len(recent_times) >= 2:
        # 检查最近的间隔
        intervals = []
        for i in range(1, len(recent_times)):
            t1 = datetime.fromisoformat(recent_times[i])
            t2 = datetime.fromisoformat(recent_times[i-1])
            interval = (t2 - t1).total_seconds()
            intervals.append(interval)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            print(f"  最近平均间隔: {avg_interval:.1f}秒")
            print(f"  最近10条时间范围: {recent_times[-1]} 至 {recent_times[0]}")

conn.close()

print("\n" + "=" * 80)
print("清理完成！")
print("=" * 80)
