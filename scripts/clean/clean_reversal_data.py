"""清理反转检测数据库中的高频旧数据，保留最近60分钟的数据"""
import sqlite3
from datetime import datetime, timedelta

db_path = r"d:\www\prototype\Gold_Monitoring_Desk\database\gold_monitor.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取当前时间和60分钟前的时间
now = datetime.now()
cutoff_time = now - timedelta(hours=1)
cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')

print(f"当前时间: {now}")
print(f"删除 {cutoff_str} 之前的所有反转检测记录...")

# 删除60分钟前的所有数据
cursor.execute("DELETE FROM reversal_conditions WHERE fetched_at < ?", (cutoff_str,))
deleted_count = cursor.rowcount

conn.commit()

# 查看剩余记录数量
cursor.execute("SELECT COUNT(*) FROM reversal_conditions")
remaining_count = cursor.fetchone()[0]

print(f"已删除 {deleted_count} 条旧记录")
print(f"剩余 {remaining_count} 条记录")

# 显示最早和最晚的记录时间
cursor.execute("SELECT MIN(fetched_at), MAX(fetched_at) FROM reversal_conditions")
min_time, max_time = cursor.fetchone()

if min_time and max_time:
    print(f"数据时间范围: {min_time} 至 {max_time}")
else:
    print("数据库中没有反转记录")

conn.close()
print("清理完成！")
