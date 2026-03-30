import sqlite3

db_path = 'database/gold_monitor.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查是否还有nf_AU0数据
cursor.execute("SELECT COUNT(*) FROM sge_prices WHERE note LIKE '%nf_AU0%'")
nf_count = cursor.fetchone()[0]
print(f"nf_AU0 records: {nf_count}")

# 检查所有数据的价格范围
cursor.execute("SELECT MIN(shfe_price_cny_per_g), MAX(shfe_price_cny_per_g), COUNT(*) FROM sge_prices")
min_p, max_p, total = cursor.fetchone()
print(f"Total records: {total}")
print(f"Price range: {min_p:.4f} - {max_p:.4f}")

# 查找异常低价数据（<960）
cursor.execute("SELECT COUNT(*), MIN(shfe_price_cny_per_g) FROM sge_prices WHERE shfe_price_cny_per_g < 960")
low_count, min_low = cursor.fetchone()
print(f"\nRecords < 960: {low_count}")
if min_low:
    print(f"Minimum price: {min_low:.4f}")

# 查找这些低价数据的详情
if low_count > 0:
    cursor.execute("""
        SELECT fetched_at, shfe_price_cny_per_g, note
        FROM sge_prices
        WHERE shfe_price_cny_per_g < 960
        ORDER BY fetched_at DESC
        LIMIT 10
    """)
    print("\n=== Low Price Records (<960) ===")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]:.4f} - {row[2][:50] if row[2] else 'N/A'}...")

conn.close()
