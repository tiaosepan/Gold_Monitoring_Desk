"""
东方财富API数据采集工具 - 用于获取美债收益率
"""
import aiohttp
import re
from datetime import datetime
from typing import Dict, Optional


class EastmoneyAPI:
    """东方财富API客户端"""

    # 东方财富美债收益率API
    US10Y_URL = "https://quote.eastmoney.com/bond/USTREASURY-10Y.html"

    # secid映射：东方财富使用124.前缀
    SECID_MAP = {
        '5y': '124.US5Y',
        '10y': '124.US10Y',
        '20y': '124.US20Y'
    }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        pass

    async def get_yield(self, tenor: str = '10y') -> Optional[Dict]:
        """
        获取美国国债收益率（从东方财富）

        Args:
            tenor: 期限（5y/10y/20y）

        Returns:
            包含收益率、时间戳的字典，获取失败返回None
        """
        secid = self.SECID_MAP.get(tenor, '124.US10Y')

        try:
            async with aiohttp.ClientSession() as session:
                # 东方财富实时行情API - 使用push2delay避免302重定向问题
                url = "https://push2delay.eastmoney.com/api/qt/stock/get"
                params = {
                    "secid": secid,
                    "fields": "f43,f57,f58,f107,f50",
                    "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                    "cb": ""
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://quote.eastmoney.com/"
                }

                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if data and data.get('data') and isinstance(data['data'], dict):
                                # f43 是最新价（收益率）
                                yield_value = data['data'].get('f43', 0)
                                if yield_value:
                                    # 东方财富收益率需要除以100
                                    return {
                                        'yield': yield_value / 100,
                                        'tenor': tenor,
                                        'timestamp': datetime.now(),
                                        'source': 'Eastmoney'
                                    }
                            # 如果data为null或无效，返回None
                            return None
                        except Exception as e:
                            # 如果不是JSON，尝试文本解析
                            text = await response.text()
                            print(f"东方财富返回非JSON: {text[:100]}")
                            return None
        except Exception as e:
            print(f"东方财富API错误: {e}")

        return None

    # 兼容旧接口
    async def get_us10y_yield(self) -> Optional[Dict]:
        """获取美国10年期国债收益率（从东方财富）- 兼容旧接口"""
        return await self.get_yield('10y')

    async def get_us10y_yield_backup(self) -> Optional[Dict]:
        """
        备用方法：从新浪获取美债数据
        """
        tenor = '10y'
        sina_symbol_map = {
            '5y': 'GB5YR',
            '10y': 'GB10YR',
            '20y': 'GB20YR'
        }
        symbol = sina_symbol_map.get(tenor, 'GB10YR')

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://hq.sinajs.cn/list={symbol}"
                headers = {
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://finance.sina.com.cn/"
                }

                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        text = await response.text(encoding='gbk')
                        # 格式: var hq_str_GB10YR="数值";
                        match = re.search(r'"([^"]*)"', text)
                        if match and match.group(1):
                            value = float(match.group(1))
                            if value > 0:
                                return {
                                    'yield': value,
                                    'tenor': tenor,
                                    'timestamp': datetime.now(),
                                    'source': f'Sina-{symbol}'
                                }
        except Exception as e:
            print(f"新浪美债API错误: {e}")

        return None


# 测试代码
if __name__ == "__main__":
    import asyncio

    async def test():
        api = EastmoneyAPI()
        result = await api.get_us10y_yield()
        print("东方财富结果:", result)

        if not result:
            result = await api.get_us10y_yield_backup()
            print("备用结果:", result)

    asyncio.run(test())
