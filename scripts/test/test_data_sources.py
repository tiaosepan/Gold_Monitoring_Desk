"""
测试数据源切换功能
"""
import asyncio
import sys
import os

# 设置控制台编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.utils import GoldAPIClient, SinaFinanceAPI


async def test_goldapi():
    """测试 Gold-API 数据源"""
    print("\n" + "="*60)
    print("测试主数据源: Gold-API.com")
    print("="*60)
    
    try:
        async with GoldAPIClient() as client:
            data = await client.get_xau_price()
            print(f"[OK] 获取成功")
            print(f"  金价: ${data['price']:.2f}/盎司")
            print(f"  更新时间: {data['updated_at']}")
            print(f"  响应数据: {data['raw_data']}")
            return True
    except Exception as e:
        print(f"[FAIL] 获取失败: {str(e)}")
        return False


async def test_sina():
    """测试新浪财经数据源"""
    print("\n" + "="*60)
    print("测试备用数据源: 新浪财经")
    print("="*60)
    
    try:
        async with SinaFinanceAPI() as api:
            # 测试国际金价
            data = await api.fetch_data(['xauusd'])
            price = data.get('xauusd', {}).get('price', 0)
            print(f"[OK] 国际金价获取成功")
            print(f"  金价: ${price:.2f}/盎司")
            
            # 测试沪金和汇率
            data = await api.fetch_data(['sge_au9999', 'usdcny'])
            sge_price = data.get('sge_au9999', {}).get('price', 0)
            usdcny = data.get('usdcny', {}).get('rate', 0)
            print(f"[OK] 沪金和汇率获取成功")
            print(f"  沪金: {sge_price:.2f}元/克")
            print(f"  汇率: {usdcny:.4f}")
            return True
    except Exception as e:
        print(f"[FAIL] 获取失败: {str(e)}")
        return False


async def test_failover():
    """测试主备切换逻辑"""
    print("\n" + "="*60)
    print("测试主备切换逻辑")
    print("="*60)
    
    # 模拟主数据源失败的场景
    print("\n场景1: 主数据源正常 -> 使用主数据源")
    try:
        async with GoldAPIClient() as primary:
            data = await primary.get_xau_price()
            print(f"[OK] 使用主数据源 Gold-API: ${data['price']:.2f}/盎司")
    except Exception as e:
        print(f"主数据源失败，切换到备用数据源...")
        async with SinaFinanceAPI() as backup:
            data = await backup.fetch_data(['xauusd'])
            price = data.get('xauusd', {}).get('price', 0)
            print(f"[OK] 使用备用数据源 新浪财经: ${price:.2f}/盎司")


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("黄金监控系统 - 数据源测试")
    print("="*60)
    
    # 测试主数据源
    goldapi_ok = await test_goldapi()
    
    # 测试备用数据源
    sina_ok = await test_sina()
    
    # 测试切换逻辑
    await test_failover()
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"主数据源 (Gold-API): {'[OK] 正常' if goldapi_ok else '[FAIL] 异常'}")
    print(f"备用数据源 (新浪财经): {'[OK] 正常' if sina_ok else '[FAIL] 异常'}")
    
    if goldapi_ok and sina_ok:
        print("\n[OK] 所有数据源工作正常！")
    elif goldapi_ok or sina_ok:
        print("\n[WARN] 至少一个数据源可用，系统可以继续运行")
    else:
        print("\n[FAIL] 所有数据源均不可用，请检查网络连接")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
