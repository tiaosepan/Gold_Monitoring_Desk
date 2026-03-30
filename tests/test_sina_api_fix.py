"""
测试修复新浪API的403问题
"""
import asyncio
import aiohttp


async def test_sina_with_headers():
    """测试添加请求头后的新浪API"""
    url = "http://hq.sinajs.cn/list=GB10YR"
    
    print("="*60)
    print("测试新浪API - 添加请求头规避403")
    print("="*60)
    print()
    
    # 测试1: 无请求头
    print("测试1: 无请求头（原始请求）")
    print("-" * 40)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"HTTP状态: {response.status}")
                if response.status == 200:
                    text = await response.text()
                    print(f"响应内容: {text[:100]}")
                else:
                    print(f"失败原因: {response.reason}")
    except Exception as e:
        print(f"错误: {e}")
    
    print()
    
    # 测试2: 添加User-Agent
    print("测试2: 添加User-Agent")
    print("-" * 40)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"HTTP状态: {response.status}")
                if response.status == 200:
                    text = await response.text()
                    print(f"响应内容: {text[:100]}")
                    
                    # 解析数据
                    if "GB10YR=" in text:
                        parts = text.split('="')[1].split('",')[0].split(',')
                        if len(parts) >= 2:
                            yield_value = float(parts[1])
                            print(f"[OK] 成功解析 - 10年期美债: {yield_value}%")
                            return True, yield_value
                else:
                    print(f"失败原因: {response.reason}")
    except Exception as e:
        print(f"错误: {e}")
    
    print()
    
    # 测试3: 添加完整浏览器头
    print("测试3: 添加完整浏览器请求头")
    print("-" * 40)
    full_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://finance.sina.com.cn/',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=full_headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"HTTP状态: {response.status}")
                if response.status == 200:
                    text = await response.text()
                    print(f"响应内容: {text[:100]}")
                    
                    # 解析数据
                    if "GB10YR=" in text:
                        parts = text.split('="')[1].split('",')[0].split(',')
                        if len(parts) >= 2:
                            yield_value = float(parts[1])
                            print(f"[OK] 成功解析 - 10年期美债: {yield_value}%")
                            return True, yield_value
                else:
                    print(f"失败原因: {response.reason}")
    except Exception as e:
        print(f"错误: {e}")
    
    print()
    print("="*60)
    print("测试结论")
    print("="*60)
    print("新浪API仍然返回403，可能原因:")
    print("1. IP被封禁或限流")
    print("2. 需要Cookie认证")
    print("3. API已关闭对外访问")
    print("建议使用其他实时数据源（Yahoo Finance等）")
    print("="*60)
    
    return False, None


if __name__ == "__main__":
    asyncio.run(test_sina_with_headers())
