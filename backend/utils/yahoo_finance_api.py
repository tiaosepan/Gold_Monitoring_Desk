"""
Yahoo Finance API客户端 - 实时美债收益率数据源
"""
import aiohttp
from datetime import datetime
from typing import Dict, Optional
import json


class YahooFinanceAPI:
    """Yahoo Finance API客户端（实时数据）"""
    
    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
    
    # 美债代码映射
    SYMBOL_MAP = {
        '5y': '^FVX',   # 5年期美债收益率
        '10y': '^TNX',  # 10年期美债收益率
        '20y': '^TYX',  # 30年期美债收益率（代替20Y）
        '30y': '^TYX'   # 30年期美债收益率
    }
    
    def __init__(self):
        """初始化Yahoo Finance API客户端"""
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def get_yield(self, tenor: str = '10y') -> Optional[float]:
        """
        获取实时美债收益率
        
        Args:
            tenor: 期限（5y/10y/20y/30y）
            
        Returns:
            收益率百分比，失败返回None
        """
        symbol = self.SYMBOL_MAP.get(tenor, '^TNX')
        
        # 使用5分钟K线获取最新价格
        url = f"{self.BASE_URL}/{symbol}"
        params = {
            'interval': '5m',
            'range': '1d'
        }
        
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 解析数据结构
                    result = data.get('chart', {}).get('result', [])
                    if result:
                        chart_data = result[0]
                        
                        # 获取最新收盘价
                        indicators = chart_data.get('indicators', {})
                        quote = indicators.get('quote', [{}])[0]
                        close_prices = quote.get('close', [])
                        
                        # 找到最新的非空价格
                        if close_prices:
                            for price in reversed(close_prices):
                                if price is not None:
                                    # Yahoo返回的是指数值，需要除以10得到百分比
                                    # 例如: ^TNX显示44.2 表示 4.42%
                                    yield_pct = price / 10.0
                                    return yield_pct
                
                return None
                
        except Exception as e:
            print(f"Yahoo Finance API错误 ({tenor}): {e}")
            return None
    
    async def get_all_yields(self) -> Dict[str, Optional[float]]:
        """
        获取所有期限的美债收益率
        
        Returns:
            {tenor: yield_pct} 字典
        """
        results = {}
        for tenor in ['5y', '10y', '20y']:
            results[tenor] = await self.get_yield(tenor)
        return results
    
    async def get_latest_data(self, tenor: str = '10y') -> Optional[Dict]:
        """
        获取详细的最新数据
        
        Args:
            tenor: 期限
            
        Returns:
            包含收益率、时间戳等的字典
        """
        yield_value = await self.get_yield(tenor)
        
        if yield_value:
            return {
                'yield': yield_value,
                'tenor': tenor,
                'source': 'Yahoo',
                'timestamp': datetime.now(),
                'symbol': self.SYMBOL_MAP[tenor]
            }
        
        return None
