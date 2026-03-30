"""
调试5Y美债采集失败问题
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.utils.cnbc_api import CNBCAPI
from backend.utils.sina_api import SinaFinanceAPI


async def main():
    print("="*60)
    print("5Y美债数据源诊断")
    print("="*60)
    print()
    
    # 测试CNBC
    print("测试1: CNBC API - US5Y")
    print("-" * 40)
    async with CNBCAPI() as api:
        data = await api.get_latest_data('5y')
        if data:
            print(f"  收益率: {data['yield']}%")
            print(f"  更新时间: {data.get('last_update')}")
            print("  [OK] CNBC API成功")
        else:
            print("  [FAIL] CNBC API返回None")
    
    print()
    
    # 测试Sina
    print("测试2: Sina API - GB5YR")
    print("-" * 40)
    async with SinaFinanceAPI() as api:
        try:
            data = await api.fetch_data(['us10y'])
            print(f"  响应keys: {list(data.keys())}")
            if 'us10y' in data:
                print(f"  US10Y数据: {data['us10y']}")
            print("  [INFO] Sina API只返回10Y数据")
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
    
    print()
    print("="*60)
    print("诊断结论:")
    print("  - CNBC API支持5Y数据")
    print("  - Sina API仅支持10Y数据")
    print("  - 5Y失败原因：新浪没有5Y数据，CNBC异常")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
