import sqlite3
from datetime import datetime, timedelta

db_path = 'd:/www/prototype/Gold_Monitoring_Desk/backend/sge_monitor.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取最近1小时的数据
one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
cursor.execute("""
    SELECT fetched_at, shfe_price_cny_per_g, london_price_cny_per_g, premium_cny_per_g
    FROM sge_prices
    WHERE fetched_at > ?
    ORDER BY fetched_at DESC
    LIMIT 30
""", (one_hour_ago,))

rows = cursor.fetchall()
print(f"=== 最近1小时的SGE数据（共{len(rows)}条）===\n")
print(f"{'时间':<20} {'人民币金价(现货)':<15} {'国际金折算':<15} {'溢价':<10}")
print("-" * 65)

for row in rows:
    fetched_at, shfe_price, london_price, premium = row
    print(f"{fetched_at:<20} {shfe_price:<15.4f} {london_price:<15.4f} {premium:<10.4f}")

conn.close()
