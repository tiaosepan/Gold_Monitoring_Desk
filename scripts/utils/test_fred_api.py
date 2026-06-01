"""
测试FRED API连接
"""
import sys
import os
import asyncio
import aiohttp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.utils import FREDAPIClient


async def test_fred_api_direct():
    """直接测试FRED API"""
    api_key = os.environ.get('FRED_API_KEY')
    
    print("=" * 60)
    print("FRED API连接测试")
    print("=" * 60)
    
    if not api_key:
        print("[错误] FRED_API_KEY环境变量未设置")
        return False
    
    print(f"API密钥: {api_key[:8]}...{api_key[-8:]}")
    print()
    
    # 测试10年期美债
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': 'DGS10',
        'api_key': api_key,
        'file_type': 'json',
        'sort_order': 'desc',
        'limit': 1
    }
    
    print("请求URL: " + url)
    print(f"参数: series_id=DGS10, limit=1")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            print("发送请求...")
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"HTTP状态码: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    print("\n原始响应:")
                    import json
                    print(json.dumps(data, indent=2)[:500])
                    
                    if data.get('observations'):
                        obs = data['observations'][0]
                        value = obs.get('value')
                        date = obs.get('date')
                        
                        print(f"\n[成功] 获取到美债数据:")
                        print(f"  日期: {date}")
                        print(f"  收益率: {value}%")
                        
                        if value and value != '.':
                            print(f"\n[OK] FRED API测试通过！")
                            print(f"  10年期美债收益率: {value}%")
                            return True
                        else:
                            print(f"\n[警告] 收益率值无效: {value}")
                            return False
                    else:
                        print("\n[错误] 响应中没有observations字段")
                        return False
                else:
                    text = await response.text()
                    print(f"\n[错误] HTTP {response.status}")
                    print(f"响应内容: {text[:500]}")
                    return False
                    
    except Exception as e:
        print(f"\n[错误] 请求失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_fred_client():
    """测试FRED客户端类"""
    api_key = os.environ.get('FRED_API_KEY')
    
    print("\n" + "=" * 60)
    print("测试FREDAPIClient类")
    print("=" * 60)
    
    if not api_key:
        print("[错误] FRED_API_KEY环境变量未设置")
        return False
    
    try:
        async with FREDAPIClient(api_key=api_key) as client:
            print("客户端已创建")
            
            # 测试10年期
            print("\n测试10年期美债...")
            data_10y = await client.get_latest_yield('10y')
            
            if data_10y:
                print(f"[成功] 10年期数据: {data_10y}")
                
                # 测试简化接口
                yield_value = await client.get_yield('10y')
                print(f"[成功] 收益率: {yield_value}%")
                
                return True
            else:
                print("[失败] 无法获取数据")
                return False
                
    except Exception as e:
        print(f"[错误] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("FRED API完整测试\n")
    
    # 测试1: 直接API调用
    result1 = await test_fred_api_direct()
    
    # 测试2: 客户端类
    result2 = await test_fred_client()
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"直接API调用: {'[OK] 通过' if result1 else '[FAIL] 失败'}")
    print(f"客户端类测试: {'[OK] 通过' if result2 else '[FAIL] 失败'}")
    print("=" * 60)
    
    return result1 and result2


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
