import asyncio
import aiohttp
import re

async def test_au9999_detailed():
    url = "http://hq.sinajs.cn/list=gds_AU9999"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://finance.sina.com.cn'
    }
    
    async with aiohttp.ClientSession() as session:
        # 获取3次数据，观察变化
        for i in range(3):
            async with session.get(url, headers=headers) as response:
                text = await response.text()
                print(f"\n=== 第{i+1}次采集 ===")
                match = re.search(r'"([^"]*)"', text)
                if match:
                    data = match.group(1)
                    fields = data.split(',')
                    
                    # 显示关键字段
                    print(f"字段0(昨收?): {fields[0] if len(fields) > 0 else 'N/A'}")
                    print(f"字段1: {fields[1] if len(fields) > 1 else 'N/A'}")
                    print(f"字段2(现价/买价): {fields[2] if len(fields) > 2 else 'N/A'}")
                    print(f"字段3(卖价?): {fields[3] if len(fields) > 3 else 'N/A'}")
                    print(f"字段4(最高): {fields[4] if len(fields) > 4 else 'N/A'}")
                    print(f"字段5(最低): {fields[5] if len(fields) > 5 else 'N/A'}")
                    print(f"字段6(时间): {fields[6] if len(fields) > 6 else 'N/A'}")
                    print(f"字段7: {fields[7] if len(fields) > 7 else 'N/A'}")
                    print(f"字段8: {fields[8] if len(fields) > 8 else 'N/A'}")
                    
                    # 测试当前逻辑
                    price = 0.0
                    if len(fields) > 2 and fields[2]:
                        try:
                            price = float(fields[2])
                            print(f"✓ 使用字段2: {price}")
                        except:
                            pass
                    if price == 0.0 and len(fields) > 3 and fields[3]:
                        try:
                            price = float(fields[3])
                            print(f"✓ 使用字段3: {price}")
                        except:
                            pass
                    if price == 0.0 and len(fields) > 6 and fields[6]:
                        try:
                            price = float(fields[6])
                            print(f"⚠️ 使用字段6(时间!): {price}")
                        except Exception as e:
                            print(f"✗ 字段6转换失败: {e}")
            
            if i < 2:
                await asyncio.sleep(2)

if __name__ == '__main__':
    asyncio.run(test_au9999_detailed())
