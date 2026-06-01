"""
CNBC API客户端 - 实时美债收益率数据源
"""
import aiohttp
from datetime import datetime
from typing import Dict, Optional
import re


class CNBCAPI:
    """CNBC Quote API客户端（实时数据）"""
    
    BASE_URL = "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol"
    
    # 美债代码映射
    SYMBOL_MAP = {
        '5y': 'US5Y',   # 5年期美债收益率
        '10y': 'US10Y', # 10年期美债收益率
        '20y': 'US30Y', # 30年期美债收益率（代替20Y）
        '30y': 'US30Y'  # 30年期美债收益率
    }
    
    def __init__(self):
        """初始化CNBC API客户端"""
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.cnbc.com/'
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
        symbol = self.SYMBOL_MAP.get(tenor, 'US10Y')
        
        params = {
            'symbols': symbol,
            'requestMethod': 'quick',
            'noform': 1,
            'partnerId': 2,
            'fund': 1,
            'exthrs': 1,
            'output': 'json'
        }
        
        try:
            async with self.session.get(self.BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 解析响应结构
                    formatted = data.get('FormattedQuoteResult', {})
                    quotes = formatted.get('FormattedQuote', [])
                    
                    if quotes and len(quotes) > 0:
                        quote = quotes[0]
                        last_price = quote.get('last', '')
                        
                        # 解析百分比字符串（例如："4.398%"）
                        if last_price:
                            # 移除百分号并转换为浮点数
                            yield_str = last_price.replace('%', '').strip()
                            try:
                                yield_value = float(yield_str)
                                return yield_value
                            except ValueError:
                                pass
                
                return None
                
        except Exception as e:
            # 静默失败，让调用者处理
            return None
    
    async def get_latest_data(self, tenor: str = '10y') -> Optional[Dict]:
        """
        获取详细的最新数据
        
        Args:
            tenor: 期限
            
        Returns:
            包含收益率、时间戳等的字典
        """
        symbol = self.SYMBOL_MAP.get(tenor, 'US10Y')
        
        params = {
            'symbols': symbol,
            'requestMethod': 'quick',
            'noform': 1,
            'partnerId': 2,
            'fund': 1,
            'exthrs': 1,
            'output': 'json'
        }
        
        try:
            async with self.session.get(self.BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    formatted = data.get('FormattedQuoteResult', {})
                    quotes = formatted.get('FormattedQuote', [])
                    
                    if quotes and len(quotes) > 0:
                        quote = quotes[0]
                        last_price = quote.get('last', '')
                        last_time = quote.get('last_time', '')
                        
                        if last_price:
                            yield_str = last_price.replace('%', '').strip()
                            try:
                                yield_value = float(yield_str)
                                
                                return {
                                    'yield': yield_value,
                                    'tenor': tenor,
                                    'source': 'CNBC',
                                    'timestamp': datetime.now(),
                                    'last_update': last_time,
                                    'symbol': symbol
                                }
                            except ValueError:
                                pass
                
                return None
                
        except Exception as e:
            return None
