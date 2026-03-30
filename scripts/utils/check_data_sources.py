"""
检查数据源健康状态
"""
import sys
import os
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database import SessionLocal, RSSSource, DataSourceHealth
from backend.utils import SinaFinanceAPI, FREDAPIClient, EastmoneyAPI
import aiohttp


async def check_sina_api():
    """检查新浪财经API"""
    print("\n" + "=" * 60)
    print("检查新浪财经API...")
    print("=" * 60)
    
    try:
        async with SinaFinanceAPI() as api:
            # 测试黄金数据
            start_time = datetime.now()
            gold_data = await api.get_gold_data()
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            print(f"[OK] 黄金数据采集成功 - 耗时: {duration_ms}ms")
            print(f"     沪金价格: {gold_data.get('sge_price', 0)} 元/克")
            print(f"     伦敦金价: {gold_data.get('international_price', 0)} 美元/盎司")
            print(f"     汇率: {gold_data.get('usdcny_rate', 0)}")
            
            # 数据有效性检查
            if gold_data.get('international_price', 0) == 0:
                print("[警告] 伦敦金价格为0，数据可能异常")
                return False
            
            if gold_data.get('usdcny_rate', 0) == 0:
                print("[警告] 汇率为0，数据可能异常")
                return False
            
            # 测试美债数据
            start_time = datetime.now()
            us10y_data = await api.get_us10y_yield()
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            print(f"[OK] 美债数据采集成功 - 耗时: {duration_ms}ms")
            print(f"     美债收益率: {us10y_data.get('us10y', 0)}%")
            
            if us10y_data.get('us10y', 0) == 0:
                print("[警告] 美债收益率为0，可能需要配置FRED API作为备源")
            
            return True
            
    except Exception as e:
        print(f"[错误] 新浪财经API检查失败: {str(e)}")
        return False


async def check_fred_api():
    """检查FRED API（可选备源）"""
    print("\n" + "=" * 60)
    print("检查FRED API（美债备源）...")
    print("=" * 60)
    
    # 检查环境变量
    fred_key = os.environ.get('FRED_API_KEY')
    if not fred_key:
        print("[提示] 未配置FRED_API_KEY环境变量")
        print("     如需使用FRED API作为美债数据备源，请设置:")
        print("     $env:FRED_API_KEY=\"your_api_key\"")
        return None
    
    try:
        async with FREDAPIClient(api_key=fred_key) as api:
            start_time = datetime.now()
            yield_value = await api.get_yield('10y')
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if yield_value and yield_value > 0:
                print(f"[OK] FRED API可用 - 耗时: {duration_ms}ms")
                print(f"     10年期美债: {yield_value}%")
                return True
            else:
                print(f"[警告] FRED API返回无效数据")
                return False
            
    except Exception as e:
        print(f"[警告] FRED API检查失败: {str(e)}")
        print("     建议配置有效的FRED_API_KEY")
        return False


async def check_eastmoney_api():
    """检查东方财富API（美债备源）"""
    print("\n" + "=" * 60)
    print("检查东方财富API（美债备源）...")
    print("=" * 60)
    
    try:
        async with EastmoneyAPI() as api:
            start_time = datetime.now()
            data = await api.get_us10y_yield()
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            print(f"[OK] 东方财富API可用 - 耗时: {duration_ms}ms")
            print(f"     10年期美债: {data.get('yield_pct', 0)}%")
            return True
            
    except Exception as e:
        print(f"[警告] 东方财富API检查失败: {str(e)}")
        return False


async def check_rss_sources():
    """检查RSS源稳定性"""
    print("\n" + "=" * 60)
    print("检查RSS源稳定性...")
    print("=" * 60)
    
    db = SessionLocal()
    sources = db.query(RSSSource).filter_by(is_active=1).all()
    
    if not sources:
        print("[警告] 没有配置活跃的RSS源")
        db.close()
        return False
    
    print(f"找到 {len(sources)} 个活跃RSS源\n")
    
    success_count = 0
    failed_sources = []
    
    async with aiohttp.ClientSession() as session:
        for source in sources:
            try:
                start_time = datetime.now()
                async with session.get(source.url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        # 简单验证RSS格式
                        if 'xml' in content[:200].lower() or 'rss' in content[:200].lower() or 'feed' in content[:200].lower():
                            print(f"[OK] {source.name} - 耗时: {duration_ms}ms - 状态: {response.status}")
                            success_count += 1
                        else:
                            print(f"[警告] {source.name} - 返回内容不是有效的RSS格式")
                            failed_sources.append({
                                'name': source.name,
                                'url': source.url,
                                'reason': '非RSS格式'
                            })
                    else:
                        print(f"[错误] {source.name} - HTTP {response.status} - {source.url}")
                        failed_sources.append({
                            'name': source.name,
                            'url': source.url,
                            'reason': f'HTTP {response.status}'
                        })
                        
            except asyncio.TimeoutError:
                print(f"[错误] {source.name} - 超时 - {source.url}")
                failed_sources.append({
                    'name': source.name,
                    'url': source.url,
                    'reason': '请求超时'
                })
            except Exception as e:
                print(f"[错误] {source.name} - {str(e)[:60]}")
                failed_sources.append({
                    'name': source.name,
                    'url': source.url,
                    'reason': str(e)[:60]
                })
    
    db.close()
    
    print("\n" + "-" * 60)
    print(f"检查结果: {success_count}/{len(sources)} 个源正常")
    
    if failed_sources:
        print("\n异常RSS源列表:")
        for i, source in enumerate(failed_sources, 1):
            print(f"\n{i}. {source['name']}")
            print(f"   URL: {source['url']}")
            print(f"   原因: {source['reason']}")
        print("\n建议: 在数据库中将这些源的is_active设置为0，或修复URL")
    
    return success_count == len(sources)


async def check_all_sources():
    """检查所有数据源"""
    print("=" * 60)
    print("黄金监控中台 - 数据源健康检查")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {
        'sina': await check_sina_api(),
        'fred': await check_fred_api(),
        'eastmoney': await check_eastmoney_api(),
        'rss': await check_rss_sources()
    }
    
    print("\n" + "=" * 60)
    print("检查结果汇总:")
    print("=" * 60)
    print(f"新浪财经API: {'正常' if results['sina'] else '异常'}")
    print(f"FRED API: {'正常' if results['fred'] else '未配置' if results['fred'] is None else '异常'}")
    print(f"东方财富API: {'正常' if results['eastmoney'] else '异常'}")
    print(f"RSS源: {'全部正常' if results['rss'] else '部分异常'}")
    
    print("\n建议:")
    if not results['sina']:
        print("- [关键] 新浪财经API异常，这是主要数据源，请立即检查网络连接")
    
    if results['fred'] is None:
        print("- [建议] 配置FRED API作为美债数据备源")
    elif not results['fred']:
        print("- [提示] FRED API配置异常，请检查API密钥")
    
    if not results['eastmoney']:
        print("- [提示] 东方财富API异常，但有其他备源可用")
    
    if not results['rss']:
        print("- [建议] 部分RSS源异常，建议禁用异常源或修复URL")
    
    print("=" * 60)
    
    return all(v for k, v in results.items() if v is not None)


if __name__ == "__main__":
    result = asyncio.run(check_all_sources())
    sys.exit(0 if result else 1)
