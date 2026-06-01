"""检查数据采集频率"""
from backend.database import SessionLocal, SGEPrice, ReversalCondition
from datetime import datetime, timedelta

db = SessionLocal()

# 检查最近24小时的数据
now = datetime.now()
day_ago = now - timedelta(days=1)
hour_ago = now - timedelta(hours=1)

# SGE数据
sge_24h = db.query(SGEPrice).filter(SGEPrice.fetched_at >= day_ago).count()
sge_1h = db.query(SGEPrice).filter(SGEPrice.fetched_at >= hour_ago).count()

# 反转数据
reversal_24h = db.query(ReversalCondition).filter(ReversalCondition.fetched_at >= day_ago).count()
reversal_1h = db.query(ReversalCondition).filter(ReversalCondition.fetched_at >= hour_ago).count()

# 获取最近几条SGE记录的时间间隔
recent_sge = db.query(SGEPrice).order_by(SGEPrice.fetched_at.desc()).limit(10).all()
if len(recent_sge) >= 2:
    intervals = []
    for i in range(len(recent_sge) - 1):
        delta = recent_sge[i].fetched_at - recent_sge[i+1].fetched_at
        intervals.append(delta.total_seconds())
    avg_interval = sum(intervals) / len(intervals) if intervals else 0
else:
    avg_interval = 0

print("=" * 60)
print("数据采集频率统计")
print("=" * 60)
print()
print("【最近24小时】")
print(f"  SGE溢价数据:     {sge_24h:4d} 条  (理论值: 1440条 按60秒计)")
print(f"  黄金反转数据:     {reversal_24h:4d} 条  (理论值: 144条 按10分钟计)")
print()
print("【最近1小时】")
print(f"  SGE溢价数据:     {sge_1h:4d} 条  (理论值: 60条 按60秒计)")
print(f"  黄金反转数据:     {reversal_1h:4d} 条  (理论值: 6条 按10分钟计)")
print()
print("【实际采集间隔】")
if avg_interval > 0:
    print(f"  SGE实际间隔:     {avg_interval:.1f} 秒/次")
    print(f"  配置间隔:        60 秒/次")
    print(f"  完成率:          {(60/avg_interval*100 if avg_interval > 0 else 0):.1f}%")
else:
    print(f"  数据不足，无法计算")
print()
print("【反转检测间隔】")
print(f"  配置间隔:        600 秒/次 (10分钟)")
print()
print("=" * 60)
print("为什么两个图表的曲线不一样？")
print("=" * 60)
print()
print("1. 数据来源不同：")
print("   - SGE溢价走势:  sge_prices表 (人民币金价/国际金折算)")
print("   - 黄金反转监控:  reversal_conditions表 (现货金美元价)")
print()
print("2. 采集频率不同：")
print(f"   - SGE溢价:      每60秒采集  → 数据点密集 → 曲线平滑")
print(f"   - 反转检测:      每10分钟    → 数据点稀疏 → 曲线粗糙")
print()
print("3. 单位不同：")
print("   - SGE图左轴:    元/克 (约900-1200)")
print("   - 反转图左轴:    美元/盎司 (约4000-5000)")
print()
print("4. 展示目的不同：")
print("   - SGE图:        监控国内溢价 (沪金-国际金)")
print("   - 反转图:        检测趋势反转信号")
print()
print("=" * 60)
print("结论：曲线形状相似但数值/密度不同是正常现象！")
print("=" * 60)

db.close()
