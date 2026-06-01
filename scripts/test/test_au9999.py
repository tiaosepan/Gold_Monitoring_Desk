import asyncio
import aiohttp

async def test_au9999():
    url = "http://hq.sinajs.cn/list=gds_AU9999"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://finance.sina.com.cn'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            text = await response.text()
            print("=== AU9999 原始数据 ===")
            print(text)
            print("\n=== 字段解析 ===")
            # 提取引号内的数据
            import re
            match = re.search(r'"([^"]*)"', text)
            if match:
                data = match.group(1)
                fields = data.split(',')
                for i, field in enumerate(fields[:20]):  # 只显示前20个字段
                    print(f"字段{i}: {field}")

if __name__ == '__main__':
    asyncio.run(test_au9999())
