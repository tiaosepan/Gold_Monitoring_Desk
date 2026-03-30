import sqlite3
from datetime import datetime, timedelta

db_path = 'database/gold_monitor.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取最近1小时的所有数据
one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
cursor.execute("""
    SELECT fetched_at, shfe_price_cny_per_g, london_price_cny_per_g, premium_cny_per_g, note
    FROM sge_prices
    WHERE fetched_at > ?
    ORDER BY fetched_at ASC
""", (one_hour_ago,))

rows = cursor.fetchall()
print(f"=== 最近1小时数据（共{len(rows)}条）===\n")
print(f"{'时间':<22} {'AU9999':<12} {'国际金折算':<12} {'溢价':<8} 数据源")
print("-" * 100)

for row in rows:
    fetched_at, shfe_price, london_price, premium, note = row
    # 检查数据源
    if "nf_AU0" in (note or ""):
        source_tag = "[旧:nf_AU0]"
    elif "AU9999" in (note or ""):
        source_tag = "[新:AU9999]"
    else:
        source_tag = "[Unknown]"
    
    print(f"{fetched_at:<22} {shfe_price:<12.4f} {london_price:<12.4f} {premium:<8.4f} {source_tag}")

# 统计数据范围
cursor.execute("""
    SELECT MIN(shfe_price_cny_per_g), MAX(shfe_price_cny_per_g), AVG(shfe_price_cny_per_g)
    FROM sge_prices
    WHERE fetched_at > ?
""", (one_hour_ago,))

min_price, max_price, avg_price = cursor.fetchone()
print(f"\n价格统计: 最小={min_price:.4f}, 最大={max_price:.4f}, 平均={avg_price:.4f}, 波动={max_price - min_price:.4f}")

conn.close()
