"""
验证CNBC API客户端
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.utils.cnbc_api import CNBCAPI


async def main():
    print("="*60)
    print("CNBC API客户端验证")
    print("="*60)
    print()
    
    async with CNBCAPI() as api:
        for tenor in ['5y', '10y', '20y']:
            print(f"{tenor.upper()} 美债收益率:")
            print("-" * 40)
            
            data = await api.get_latest_data(tenor)
            
            if data:
                print(f"  收益率: {data['yield']:.3f}%")
                print(f"  数据源: {data['source']}")
                print(f"  代码: {data['symbol']}")
                print(f"  更新时间: {data.get('last_update', 'N/A')}")
                print(f"  获取时间: {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  [OK] 实时数据获取成功")
            else:
                print(f"  [FAIL] 获取失败")
            
            print()
    
    print("="*60)
    print("CNBC API特点:")
    print("  - 实时更新（分钟级）")
    print("  - 免费，无需API密钥")
    print("  - 交易时段实时tick数据")
    print("  - 适合高频监控")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
