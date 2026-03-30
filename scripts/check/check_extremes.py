import sqlite3

db_path = 'database/gold_monitor.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查找最低价记录
cursor.execute("""
    SELECT fetched_at, shfe_price_cny_per_g, london_price_cny_per_g, premium_cny_per_g, note
    FROM sge_prices
    WHERE shfe_price_cny_per_g < 985
    ORDER BY shfe_price_cny_per_g ASC
    LIMIT 10
""")

print("=== Lowest Prices (<985) ===")
for row in cursor.fetchall():
    fetched_at, shfe_price, london_price, premium, note = row
    print(f"{fetched_at}: {shfe_price:.4f} (London: {london_price:.4f}, Premium: {premium:.4f})")
    print(f"  Note: {note[:80] if note else 'N/A'}...")

# 查找最高价记录
cursor.execute("""
    SELECT fetched_at, shfe_price_cny_per_g, london_price_cny_per_g, premium_cny_per_g, note
    FROM sge_prices
    WHERE shfe_price_cny_per_g > 1015
    ORDER BY shfe_price_cny_per_g DESC
    LIMIT 10
""")

print("\n=== Highest Prices (>1015) ===")
for row in cursor.fetchall():
    fetched_at, shfe_price, london_price, premium, note = row
    print(f"{fetched_at}: {shfe_price:.4f} (London: {london_price:.4f}, Premium: {premium:.4f})")
    print(f"  Note: {note[:80] if note else 'N/A'}...")

conn.close()
