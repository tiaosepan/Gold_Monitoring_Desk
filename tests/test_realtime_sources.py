"""
测试多个实时数据源
"""
import asyncio
import aiohttp
from datetime import datetime


async def test_yahoo_debug():
    """调试Yahoo Finance API响应"""
    print("="*60)
    print("测试1: Yahoo Finance API (调试模式)")
    print("="*60)
    
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX"
    params = {'interval': '1d', 'range': '5d'}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as response:
                print(f"HTTP状态: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"响应结构: {list(data.keys())}")
                    
                    chart = data.get('chart', {})
                    result = chart.get('result', [])
                    
                    if result:
                        chart_data = result[0]
                        print(f"图表数据keys: {list(chart_data.keys())}")
                        
                        meta = chart_data.get('meta', {})
                        print(f"Meta信息: regularMarketPrice={meta.get('regularMarketPrice')}")
                        
                        # 尝试获取最新价格
                        indicators = chart_data.get('indicators', {})
                        quote = indicators.get('quote', [{}])[0]
                        close_prices = quote.get('close', [])
                        
                        if close_prices:
                            latest = None
                            for price in reversed(close_prices):
                                if price is not None:
                                    latest = price
                                    break
                            
                            if latest:
                                yield_pct = latest / 10.0
                                print(f"  [OK] 10年期美债: {yield_pct:.2f}%")
                                return True, yield_pct
                        
                        # 尝试从meta获取
                        if meta.get('regularMarketPrice'):
                            yield_pct = meta['regularMarketPrice'] / 10.0
                            print(f"  [OK] 10年期美债 (from meta): {yield_pct:.2f}%")
                            return True, yield_pct
                    
                    print(f"  [FAIL] 无法解析数据结构")
                    print(f"  原始数据: {str(data)[:200]}")
                else:
                    text = await response.text()
                    print(f"  [FAIL] HTTP {response.status}")
                    print(f"  响应: {text[:200]}")
                
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
    
    return False, None


async def test_investing_com():
    """测试Investing.com实时数据"""
    print("\n" + "="*60)
    print("测试2: Investing.com API")
    print("="*60)
    
    # Investing.com的API端点（需要分析网络请求）
    url = "https://api.investing.com/api/financialdata/8907/historical/chart/"
    params = {
        'period': 'P1D',
        'interval': 'PT5M'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Origin': 'https://www.investing.com',
        'Referer': 'https://www.investing.com/'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"HTTP状态: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"响应类型: {type(data)}")
                    print(f"响应预览: {str(data)[:200]}")
                    return True, None
                else:
                    print(f"  [FAIL] HTTP {response.status}")
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
    
    return False, None


async def test_marketwatch():
    """测试MarketWatch实时数据"""
    print("\n" + "="*60)
    print("测试3: MarketWatch API")
    print("="*60)
    
    # MarketWatch的10年期美债页面
    url = "https://www.marketwatch.com/investing/bond/tmubmusd10y"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"HTTP状态: {response.status}")
                
                if response.status == 200:
                    html = await response.text()
                    
                    # 简单搜索价格数据
                    if 'bg-quote' in html:
                        print("  [INFO] 页面包含价格数据（需HTML解析）")
                        print(f"  HTML长度: {len(html)} 字符")
                        return True, None
                    else:
                        print("  [FAIL] 未找到价格数据")
                else:
                    print(f"  [FAIL] HTTP {response.status}")
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
    
    return False, None


async def test_cnbc():
    """测试CNBC实时数据"""
    print("\n" + "="*60)
    print("测试4: CNBC Quote API")
    print("="*60)
    
    # CNBC的quote API
    url = "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol"
    params = {
        'symbols': 'US10Y',
        'requestMethod': 'quick',
        'noform': 1,
        'partnerId': 2,
        'fund': 1,
        'exthrs': 1,
        'output': 'json'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"HTTP状态: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"响应类型: {type(data)}")
                    print(f"响应预览: {str(data)[:300]}")
                    
                    if 'QuickQuoteResult' in data:
                        quote = data['QuickQuoteResult']['QuickQuote']
                        if isinstance(quote, list) and quote:
                            last_price = quote[0].get('last')
                            print(f"  [OK] 10年期美债: {last_price}%")
                            return True, last_price
                else:
                    print(f"  [FAIL] HTTP {response.status}")
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
    
    return False, None


async def main():
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "实时美债数据源测试" + " "*23 + "║")
    print("╚" + "="*58 + "╝")
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # 测试所有实时源
    results['yahoo'] = await test_yahoo_debug()
    results['investing'] = await test_investing_com()
    results['marketwatch'] = await test_marketwatch()
    results['cnbc'] = await test_cnbc()
    
    # 汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    available = sum(1 for success, _ in results.values() if success)
    print(f"\n可用实时数据源: {available}/4")
    
    for source, (success, value) in results.items():
        status = "[OK]" if success else "[FAIL]"
        value_str = f"({value}%)" if value else ""
        print(f"  {source.upper():12} {status} {value_str}")
    
    print("\n推荐数据源:")
    if results['yahoo'][0]:
        print("  1. Yahoo Finance (免费，实时)")
    if results['cnbc'][0]:
        print("  2. CNBC (免费，实时)")
    if available == 0:
        print("  [WARN] 所有实时源都不可用（可能因为周末休市）")
        print("  建议保持使用FRED API（每日数据已足够）")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
