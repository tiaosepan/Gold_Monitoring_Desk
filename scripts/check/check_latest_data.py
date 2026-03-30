import sqlite3

db_path = 'database/gold_monitor.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取最新10条记录
cursor.execute("""
    SELECT fetched_at, shfe_price_cny_per_g, note
    FROM sge_prices
    ORDER BY fetched_at DESC
    LIMIT 15
""")

rows = cursor.fetchall()
print("=== Latest 15 Records ===\n")
print(f"{'Time':<22} {'Price':<12} {'Note'}")
print("-" * 100)

for row in rows:
    fetched_at, shfe_price, note = row
    # 检查是nf_AU0还是AU9999
    source = "nf_AU0" if "nf_AU0" in (note or "") else "AU9999" if "AU9999" in (note or "") else "Unknown"
    print(f"{fetched_at:<22} {shfe_price:<12.4f} [{source}] {note[:60] if note else 'N/A'}...")

conn.close()
