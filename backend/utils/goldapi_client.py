"""
Gold-API.com 数据采集客户端
官方文档: https://www.gold-api.com/
"""
import aiohttp
from datetime import datetime
from typing import Dict, Optional


class GoldAPIClient:
    """Gold-API.com API客户端"""
    
    BASE_URL = "https://api.gold-api.com"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_key: API密钥（可选，免费版无需密钥）
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        headers = {
            'User-Agent': 'Gold-Monitor/1.0',
            'Accept': 'application/json'
        }
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def get_xau_price(self) -> Dict:
        """
        获取XAU金价（美元/盎司）
        
        Returns:
            包含金价和时间戳的字典
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.BASE_URL}/price/XAU"
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        'price': float(data.get('price', 0)),
                        'currency': data.get('currency', 'USD'),
                        'symbol': data.get('symbol', 'XAU'),
                        'updated_at': data.get('updatedAt'),
                        'timestamp': datetime.now(),
                        'raw_data': data
                    }
                else:
                    raise Exception(f"API请求失败: HTTP {response.status}")
        except Exception as e:
            raise Exception(f"获取Gold-API数据失败: {str(e)}")
    
    async def get_currency_rate(self, from_currency: str = 'USD', to_currency: str = 'CNY') -> Dict:
        """
        获取汇率（需要付费API Key）
        
        Args:
            from_currency: 源货币
            to_currency: 目标货币
            
        Returns:
            汇率数据
        """
        if not self.api_key:
            raise Exception("获取汇率需要API Key，请使用其他数据源")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.BASE_URL}/currency/{from_currency}/{to_currency}"
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'rate': float(data.get('rate', 0)),
                        'from': from_currency,
                        'to': to_currency,
                        'timestamp': datetime.now()
                    }
                else:
                    raise Exception(f"API请求失败: HTTP {response.status}")
        except Exception as e:
            raise Exception(f"获取汇率失败: {str(e)}")
    
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()


# 测试代码
if __name__ == "__main__":
    import asyncio
    
    async def test():
        async with GoldAPIClient() as client:
            # 测试获取金价
            xau_data = await client.get_xau_price()
            print("XAU金价:", xau_data)
    
    asyncio.run(test())
