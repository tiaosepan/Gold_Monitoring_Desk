import sqlite3

db_path = 'database/gold_monitor.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 先检查有多少条旧数据
cursor.execute("""
    SELECT COUNT(*) FROM sge_prices WHERE note LIKE '%nf_AU0%'
""")
old_count = cursor.fetchone()[0]
print(f"Found {old_count} old records with nf_AU0")

# 删除所有包含nf_AU0的旧记录
cursor.execute("""
    DELETE FROM sge_prices WHERE note LIKE '%nf_AU0%'
""")

deleted = cursor.rowcount
conn.commit()

# 检查剩余数据
cursor.execute("SELECT COUNT(*) FROM sge_prices")
remaining_count = cursor.fetchone()[0]

print(f"\nDeleted: {deleted} old nf_AU0 records")
print(f"Remaining: {remaining_count} AU9999 records")

conn.close()
