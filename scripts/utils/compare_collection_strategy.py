"""对比原系统和复刻系统的采集策略"""
import requests
from datetime import datetime, timedelta
from backend.database import SessionLocal, SGEPrice

print("=" * 80)
print("采集策略对比分析")
print("=" * 80)
print()

# 1. 检查本地系统的采集间隔
print("【复刻系统】本地采集分析")
print("-" * 80)

db = SessionLocal()
recent_data = db.query(SGEPrice).order_by(SGEPrice.fetched_at.desc()).limit(20).all()

if len(recent_data) >= 2:
    intervals = []
    for i in range(len(recent_data) - 1):
        time_diff = (recent_data[i].fetched_at - recent_data[i+1].fetched_at).total_seconds()
        intervals.append(time_diff)
    
    print(f"最近采集记录: {len(recent_data)} 条")
    print(f"平均间隔: {sum(intervals)/len(intervals):.1f} 秒")
    print(f"最小间隔: {min(intervals):.1f} 秒")
    print(f"最大间隔: {max(intervals):.1f} 秒")
    print()
    
    # 统计间隔分布
    count_60 = sum(1 for x in intervals if 50 <= x <= 70)
    count_120 = sum(1 for x in intervals if 110 <= x <= 130)
    count_300 = sum(1 for x in intervals if 290 <= x <= 310)
    count_other = len(intervals) - count_60 - count_120 - count_300
    
    print("间隔分布:")
    print(f"  60秒 (50-70s):   {count_60} 次 ({count_60/len(intervals)*100:.1f}%)")
    print(f"  120秒 (110-130s): {count_120} 次 ({count_120/len(intervals)*100:.1f}%)")
    print(f"  300秒 (290-310s): {count_300} 次 ({count_300/len(intervals)*100:.1f}%)")
    print(f"  其他间隔:         {count_other} 次 ({count_other/len(intervals)*100:.1f}%)")
    print()
    
    # 判断策略
    if count_300 > len(intervals) * 0.5:
        print("[检测结果] 智能采集策略:")
        print("   当前以低频采集为主（300秒），说明系统识别为休市状态")
    elif count_60 > len(intervals) * 0.5:
        print("[检测结果] 智能采集策略:")
        print("   当前以高频采集为主（60秒），说明系统识别为开市状态")
    elif count_120 > len(intervals) * 0.3:
        print("[检测结果] 智能采集策略:")
        print("   当前以中频采集为主（120秒），说明单市场开盘状态")
    else:
        print("[检测结果] 采集间隔混合，可能处于市场切换时段")
else:
    print("数据不足，无法分析")

db.close()
print()

# 2. 分析原系统可能的策略
print("【原系统】推测分析")
print("-" * 80)
print()

print("无法直接访问原系统后端代码，但可以通过以下方式推测:")
print()

print("方案1: 观察原系统API响应")
print("  访问: http://rev.sccit.com.cn:8000/api/sge/latest")
print("  多次访问，记录数据更新时间")
print("  分析: 休市时段 vs 开市时段的更新频率")
print()

print("方案2: 查看原系统配置")
print("  页面显示: 主轮询频率 (秒)")
print("  如果是固定值 → 固定频率策略")
print("  如果没有显示 → 可能是动态策略")
print()

print("方案3: 长期观察数据")
print("  记录原系统的数据更新时间戳")
print("  统计休市和开市时段的采集频率")
print("  对比是否有明显差异")
print()

# 3. 常见的金融监控系统策略
print("【行业最佳实践】")
print("-" * 80)
print()

print("常见的采集策略类型:")
print()
print("1. 固定频率策略（传统方式）")
print("   优点: 实现简单，行为可预测")
print("   缺点: 资源浪费，休市时无意义采集")
print("   适用: 早期系统、小规模监控")
print()
print("2. 智能动态策略（现代方式）")
print("   优点: 节省资源，按需采集")
print("   缺点: 实现复杂，需要市场状态判断")
print("   适用: 生产系统、大规模监控")
print()
print("3. 事件驱动策略（高级方式）")
print("   优点: 实时响应，零延迟")
print("   缺点: 依赖WebSocket等实时连接")
print("   适用: 高频交易、实时预警")
print()

# 4. 推测原系统策略
print("【推测结论】")
print("-" * 80)
print()

print("基于以下证据:")
print("  1. 原系统是生产级系统（rev.sccit.com.cn）")
print("  2. 页面有'主轮询频率'配置项")
print("  3. 系统设计较为完善（支持多数据源、RSS等）")
print()

print("推测:")
print("  原系统 **可能** 采用以下策略之一:")
print()
print("  情况A: 固定频率（60秒）")
print("    - 配置项固定为60秒")
print("    - 24小时持续采集")
print("    - 简单可靠")
print()
print("  情况B: 智能动态调整")
print("    - 根据市场状态自动调整")
print("    - 配置项为'开市频率'")
print("    - 休市时降低频率")
print()
print("  情况C: 手动配置 + 固定频率")
print("    - 管理员手动调整配置")
print("    - 系统按配置固定执行")
print("    - 需要人工干预")
print()

print("最可能: 情况A（固定60秒）或 情况C（手动配置）")
print("原因: 智能策略需要额外开发成本，早期系统多采用固定策略")
print()

# 5. 对比优势
print("【复刻系统优势】")
print("-" * 80)
print()

print("如果原系统采用固定频率策略，复刻系统的智能策略优势:")
print()
print("[优势1] 资源节省: 减少约50%的采集次数")
print("[优势2] 数据库优化: 减少约50%的写入")
print("[优势3] 网络优化: 减少约50%的API请求")
print("[优势4] 自动化: 无需人工调整配置")
print("[优势5] 保持质量: 开市时仍高频采集")
print()

print("如果原系统也采用智能策略，则:")
print("[对齐] 功能对齐: 与原系统行为一致")
print("[标准] 最佳实践: 符合行业标准")
print()

print("=" * 80)
print("建议: 观察原系统在休市/开市时段的数据更新频率来验证")
print("=" * 80)
