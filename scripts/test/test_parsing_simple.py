import asyncio
import aiohttp
import re

async def test_parsing():
    url = "http://hq.sinajs.cn/list=gds_AU9999"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://finance.sina.com.cn'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            text = await response.text()
            match = re.search(r'"([^"]*)"', text)
            if match:
                data_str = match.group(1)
                fields = data_str.split(',')
                
                print("Field 0:", fields[0] if len(fields) > 0 else 'N/A')
                print("Field 2:", fields[2] if len(fields) > 2 else 'N/A')
                print("Field 3:", fields[3] if len(fields) > 3 else 'N/A')
                print("Field 4:", fields[4] if len(fields) > 4 else 'N/A')
                print("Field 5:", fields[5] if len(fields) > 5 else 'N/A')
                print("Field 6:", fields[6] if len(fields) > 6 else 'N/A')
                print("Field 7:", fields[7] if len(fields) > 7 else 'N/A')
                print("Field 8:", fields[8] if len(fields) > 8 else 'N/A')
                
                # Test current logic
                price = 0.0
                try:
                    if len(fields) > 2 and fields[2]:
                        price = float(fields[2])
                        print(f"\nCurrent logic uses Field 2: {price}")
                except:
                    pass
                
                if price == 0.0:
                    try:
                        if len(fields) > 3 and fields[3]:
                            price = float(fields[3])
                            print(f"\nCurrent logic uses Field 3: {price}")
                    except:
                        pass
                
                if price == 0.0:
                    try:
                        if len(fields) > 6 and fields[6]:
                            price = float(fields[6])
                            print(f"\nWARNING: Using Field 6 (TIME!): {price}")
                    except Exception as e:
                        print(f"\nField 6 conversion failed (expected - it's time): {e}")
                
                if price == 0.0:
                    print("\nERROR: No price found!")
                else:
                    print(f"\nFinal price: {price}")

if __name__ == '__main__':
    asyncio.run(test_parsing())
