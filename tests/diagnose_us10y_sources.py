"""
美债数据源诊断工具
测试所有3个数据源的可用性
"""
import asyncio
import aiohttp
import os
from datetime import datetime


async def test_sina_api():
    """测试新浪财经API"""
    print("\n" + "="*60)
    print("测试数据源 1/3: 新浪财经 (Sina Finance)")
    print("="*60)
    
    url = "http://hq.sinajs.cn/list=GB10YR"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"HTTP状态码: {response.status}")
                
                if response.status == 200:
                    text = await response.text()
                    print(f"原始响应: {text[:200]}")
                    
                    if "GB10YR=" in text:
                        parts = text.split('="')[1].split('",')[0].split(',')
                        if len(parts) >= 2:
                            yield_value = float(parts[1])
                            print(f"[OK] 成功 - 10年期美债收益率: {yield_value}%")
                            return True, yield_value
                    
                    print("[FAIL] 失败 - 数据格式异常")
                    return False, None
                else:
                    print(f"[FAIL] 失败 - HTTP {response.status}")
                    return False, None
    except Exception as e:
        print(f"[ERROR] 错误: {str(e)}")
        return False, None


async def test_fred_api():
    """测试FRED API"""
    print("\n" + "="*60)
    print("测试数据源 2/3: FRED (Federal Reserve Economic Data)")
    print("="*60)
    
    api_key = os.environ.get('FRED_API_KEY')
    print(f"API密钥配置: {'已配置' if api_key else '[WARN] 未配置'}")
    
    if not api_key:
        print("[WARN] 跳过测试 - 需要设置环境变量 $env:FRED_API_KEY")
        print("获取密钥: https://fred.stlouisfed.org/docs/api/api_key.html")
        return False, None
    
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': 'DGS10',
        'api_key': api_key,
        'file_type': 'json',
        'sort_order': 'desc',
        'limit': 1
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"HTTP状态码: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"响应结构: {list(data.keys())}")
                    
                    if data.get('observations'):
                        obs = data['observations'][0]
                        value = obs.get('value')
                        date = obs.get('date')
                        
                        print(f"最新数据日期: {date}")
                        print(f"原始值: {value}")
                        
                        if value and value != '.':
                            yield_value = float(value)
                            print(f"[OK] 成功 - 10年期美债收益率: {yield_value}%")
                            return True, yield_value
                        else:
                            print("[FAIL] 失败 - 值为空或无效")
                            return False, None
                    else:
                        print(f"[FAIL] 失败 - 无观测数据: {data}")
                        return False, None
                else:
                    text = await response.text()
                    print(f"[FAIL] 失败 - HTTP {response.status}: {text[:200]}")
                    return False, None
    except Exception as e:
        print(f"[ERROR] 错误: {str(e)}")
        return False, None


async def test_eastmoney_api():
    """测试东方财富API"""
    print("\n" + "="*60)
    print("测试数据源 3/3: 东方财富 (Eastmoney)")
    print("="*60)
    
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        'reportName': 'RPT_IMP_INTERESTRATEN',
        'columns': 'EMI_COUNTRY_NAME,LATEST_VALUE,INDICATOR_NAME',
        'filter': '(EMI_COUNTRY_NAME="美国")(INDICATOR_NAME="国债收益率10年")',
        'pageSize': 1,
        'sortColumns': 'REPORT_DATE',
        'sortTypes': -1,
        'source': 'WEB',
        'client': 'WEB'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"HTTP状态码: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"响应结构: {list(data.keys())}")
                    print(f"返回码: {data.get('code')}")
                    
                    result = data.get('result')
                    if result and result.get('data'):
                        items = result['data']
                        print(f"数据项数: {len(items)}")
                        
                        if items:
                            item = items[0]
                            yield_value = item.get('LATEST_VALUE')
                            country = item.get('EMI_COUNTRY_NAME')
                            
                            print(f"国家: {country}")
                            print(f"原始值: {yield_value}")
                            
                            if yield_value:
                                print(f"[OK] 成功 - 10年期美债收益率: {yield_value}%")
                                return True, float(yield_value)
                    
                    print(f"[FAIL] 失败 - 无有效数据: {data}")
                    return False, None
                else:
                    text = await response.text()
                    print(f"[FAIL] 失败 - HTTP {response.status}: {text[:200]}")
                    return False, None
    except Exception as e:
        print(f"[ERROR] 错误: {str(e)}")
        return False, None


async def test_manual_fred():
    """手动测试FRED API（使用测试密钥）"""
    print("\n" + "="*60)
    print("手动测试: 使用公开测试密钥访问FRED")
    print("="*60)
    
    # 尝试使用演示密钥（可能会失败）
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': 'DGS10',
        'api_key': 'abcdefghijklmnopqrstuvwxyz123456',  # 示例密钥
        'file_type': 'json',
        'limit': 1
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"HTTP状态码: {response.status}")
                text = await response.text()
                print(f"响应内容: {text[:300]}")
                
                if "api_key" in text.lower() and "invalid" in text.lower():
                    print("\n[WARN] FRED API需要有效的API密钥")
                    print("获取免费密钥: https://fred.stlouisfed.org/docs/api/api_key.html")
    except Exception as e:
        print(f"请求错误: {str(e)}")


async def main():
    """主测试函数"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "美债数据源诊断工具" + " "*26 + "║")
    print("║" + " "*10 + "US Treasury Yield Data Sources Diagnostics" + " "*3 + "║")
    print("╚" + "="*58 + "╝")
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 测试3个主要数据源
    results['sina'] = await test_sina_api()
    results['fred'] = await test_fred_api()
    results['eastmoney'] = await test_eastmoney_api()
    
    # 手动FRED测试
    await test_manual_fred()
    
    # 汇总报告
    print("\n" + "="*60)
    print("诊断结果汇总")
    print("="*60)
    
    print(f"\n数据源可用性:")
    for source, (success, value) in results.items():
        status = "[OK] 可用" if success else "[FAIL] 不可用"
        value_str = f"({value}%)" if value else ""
        print(f"  {source.upper():12} {status} {value_str}")
    
    available_sources = sum(1 for success, _ in results.values() if success)
    print(f"\n可用数据源: {available_sources}/3")
    
    if available_sources == 0:
        print("\n[WARN] 警告: 所有数据源都不可用！")
        print("\n可能原因:")
        print("  1. 网络连接问题（防火墙/代理）")
        print("  2. API端点已变更")
        print("  3. FRED API密钥未配置")
        print("  4. 数据格式发生变化")
    elif available_sources < 3:
        print(f"\n[WARN] 注意: {3-available_sources}个数据源不可用")
        print("建议检查不可用的数据源配置")
    else:
        print("\n[OK] 所有数据源正常工作")
    
    print("\n" + "="*60)
    print("诊断完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
