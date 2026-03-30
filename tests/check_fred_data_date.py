"""
检查FRED API返回数据的日期
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.utils.fred_api import FREDAPIClient


async def main():
    api_key = os.environ.get('FRED_API_KEY', '38b7f7dc5b334dfea2c32abdac59232f')
    
    print("="*60)
    print("FRED API数据时效性检查")
    print("="*60)
    print(f"\n当前时间: 2026-03-30 (周日)")
    print(f"API密钥: {'已配置' if api_key else '未配置'}")
    print()
    
    async with FREDAPIClient(api_key) as client:
        for tenor in ['5y', '10y', '20y']:
            print(f"\n{tenor.upper()} 美债:")
            print("-" * 40)
            
            data = await client.get_latest_yield(tenor)
            
            if data:
                print(f"  收益率: {data['yield']}%")
                print(f"  数据日期: {data['date']}")
                print(f"  获取时间: {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  系列ID: {data['series_id']}")
                
                # 计算数据延迟
                from datetime import datetime
                data_date = datetime.strptime(data['date'], '%Y-%m-%d')
                now = datetime.now()
                delay_days = (now - data_date).days
                
                if delay_days == 0:
                    print(f"  时效性: [实时] 今日数据")
                elif delay_days == 1:
                    print(f"  时效性: [次日] 延迟1天")
                elif delay_days <= 3:
                    print(f"  时效性: [近期] 延迟{delay_days}天")
                else:
                    print(f"  时效性: [滞后] 延迟{delay_days}天")
            else:
                print("  [失败] 无法获取数据")
    
    print("\n" + "="*60)
    print("FRED API特性说明")
    print("="*60)
    print("""
FRED (Federal Reserve Economic Data) 特点:
1. 官方数据源: 美联储经济数据库
2. 更新频率: 每个交易日更新一次（收盘后）
3. 数据类型: 每日收盘价，非实时tick数据
4. 周末/节假日: 不更新，使用最近交易日数据
5. 数据延迟: 通常T+0（当日交易日收盘后可用）

当前情况（2026-03-30周日）:
- 美国市场周末休市
- FRED返回的是最近交易日（周五2026-03-26）的数据
- 这是正常行为，非实时数据

如需实时数据（分钟级更新），建议使用:
1. Bloomberg API (商业)
2. Trading Economics API (商业)
3. 新浪财经API (免费，但已被403拒绝)
    """)
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
