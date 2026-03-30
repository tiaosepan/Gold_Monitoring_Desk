import sqlite3
from datetime import datetime, timedelta

db_path = 'database/gold_monitor.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 找到价格为1010.2附近的记录
cursor.execute("""
    SELECT fetched_at, shfe_price_cny_per_g, london_price_cny_per_g, premium_cny_per_g, note, raw_payload
    FROM sge_prices
    WHERE shfe_price_cny_per_g BETWEEN 1009 AND 1011
    ORDER BY fetched_at DESC
    LIMIT 5
""")

rows = cursor.fetchall()
print(f"=== 查找价格在1009-1011之间的记录（共{len(rows)}条）===\n")

for row in rows:
    fetched_at, shfe_price, london_price, premium, note, raw_payload = row
    print(f"时间: {fetched_at}")
    print(f"人民币金价: {shfe_price}")
    print(f"国际金折算: {london_price}")
    print(f"溢价: {premium}")
    print(f"备注: {note}")
    print(f"原始数据: {raw_payload[:300] if raw_payload else 'N/A'}...")
    print("-" * 80)

conn.close()
