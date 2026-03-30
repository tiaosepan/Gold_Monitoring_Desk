"""
FRED API客户端
用于获取美国国债收益率数据（作为Sina API的回退方案）
"""
import aiohttp
from datetime import datetime
from typing import Dict, Optional, List


class FREDAPIClient:
    """FRED API客户端"""
    
    BASE_URL = "https://api.stlouisfed.org/fred"
    
    # 期限映射
    SERIES_MAP = {
        '5y': 'DGS5',
        '10y': 'DGS10',
        '20y': 'DGS20',
        '30y': 'DGS30'
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化FRED API客户端
        
        Args:
            api_key: FRED API密钥（可选，如果为None则无法使用）
        """
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def get_latest_yield(self, tenor: str = '10y') -> Optional[Dict]:
        """
        获取最新的国债收益率
        
        Args:
            tenor: 期限（5y/10y/20y/30y）
            
        Returns:
            收益率数据或None
        """
        if not self.api_key:
            return None
        
        series_id = self.SERIES_MAP.get(tenor, 'DGS10')
        url = f"{self.BASE_URL}/series/observations"
        
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 1
        }
        
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('observations'):
                        obs = data['observations'][0]
                        value = obs.get('value')
                        date = obs.get('date')
                        
                        if value and value != '.':
                            return {
                                'yield': float(value),
                                'date': date,
                                'tenor': tenor,
                                'series_id': series_id,
                                'timestamp': datetime.now()
                            }
        except Exception as e:
            print(f"FRED API错误: {e}")
        
        return None
    
    async def get_historical_yields(self, tenor: str = '10y', limit: int = 100) -> List[Dict]:
        """
        获取历史收益率数据
        
        Args:
            tenor: 期限
            limit: 返回记录数
            
        Returns:
            历史数据列表
        """
        if not self.api_key:
            return []
        
        series_id = self.SERIES_MAP.get(tenor, 'DGS10')
        url = f"{self.BASE_URL}/series/observations"
        
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': limit
        }
        
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    for obs in data.get('observations', []):
                        value = obs.get('value')
                        date = obs.get('date')
                        
                        if value and value != '.':
                            results.append({
                                'yield': float(value),
                                'date': date,
                                'tenor': tenor
                            })
                    
                    return results
        except Exception as e:
            print(f"FRED API错误: {e}")
        
        return []
    
    async def get_yield(self, tenor: str = '10y') -> Optional[float]:
        """
        获取美债收益率（简化接口）
        
        Args:
            tenor: 期限（5y/10y/20y/30y）
            
        Returns:
            收益率百分比，失败返回None
        """
        data = await self.get_latest_yield(tenor)
        return data.get('yield') if data else None
