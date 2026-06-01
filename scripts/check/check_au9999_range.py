import sqlite3

db_path = 'database/gold_monitor.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查AU9999数据的时间范围
cursor.execute("""
    SELECT MIN(fetched_at), MAX(fetched_at), COUNT(*)
    FROM sge_prices
    WHERE note LIKE '%AU9999%'
""")

min_time, max_time, count = cursor.fetchone()
print(f"AU9999 Data: {count} records")
print(f"Time range: {min_time} to {max_time}")

# 检查最近20条数据
cursor.execute("""
    SELECT fetched_at, shfe_price_cny_per_g
    FROM sge_prices
    ORDER BY fetched_at DESC
    LIMIT 20
""")

print("\n=== Latest 20 Records ===")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]:.4f}")

conn.close()
