"""
新浪财经API数据采集工具
"""
import aiohttp
import re
from datetime import datetime
from typing import Dict, Optional


class SinaFinanceAPI:
    """新浪财经API客户端"""
    
    BASE_URL = "https://hq.sinajs.cn/list="
    
    # 数据代码映射
    SYMBOLS = {
        'sge_au9999': 'gds_AU9999',      # AU9999上海金现货（替代nf_AU0期货以获取现货数据）
        'xauusd': 'hf_XAU',              # 国际金价(伦敦金现货，美元/盎司)
        'usdcny': 'USDCNY',              # 美元兑人民币
        'us10y': 'GB10YR'                # 美国10年期国债收益率
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 添加请求头规避403拒绝
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://finance.sina.com.cn/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def fetch_data(self, symbols: list) -> Dict:
        """
        获取多个品种的数据
        
        Args:
            symbols: 品种代码列表
            
        Returns:
            数据字典
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # 构建请求URL
        symbol_codes = [self.SYMBOLS.get(s, s) for s in symbols]
        url = f"{self.BASE_URL}{','.join(symbol_codes)}"
        
        # 添加请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://finance.sina.com.cn/'
        }
        
        try:
            async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    text = await response.text(encoding='gbk')
                    parsed_data = self._parse_response(text, symbols)
                    # 添加原始响应
                    parsed_data['raw_response'] = text
                    return parsed_data
                else:
                    raise Exception(f"API请求失败: HTTP {response.status}")
        except Exception as e:
            raise Exception(f"获取数据失败: {str(e)}")
    
    def _parse_response(self, text: str, symbols: list) -> Dict:
        """
        解析API响应
        
        Args:
            text: 响应文本
            symbols: 品种代码列表
            
        Returns:
            解析后的数据字典
        """
        result = {}
        lines = text.strip().split('\n')
        
        for i, line in enumerate(lines):
            if i >= len(symbols):
                break
            
            symbol = symbols[i]
            
            # 提取数据部分
            match = re.search(r'"([^"]*)"', line)
            if not match:
                continue
            
            data_str = match.group(1)
            fields = data_str.split(',')
            
            # 根据不同品种解析数据
            if symbol == 'sge_au9999':
                # gds_AU9999格式(上海金现货): 日期,时间,现价,开盘,最高,最低,昨收,涨跌,涨跌幅,...
                # 字段0=日期, 字段1=时间, 字段2=现价(最重要)
                # 字段3=开盘, 字段4=最高, 字段5=最低, 字段6=昨收
                # 优先顺序: 字段2(现价) -> 字段3(开盘) -> 字段6(昨收)
                price = 0.0
                try:
                    if len(fields) > 2 and fields[2]:
                        price = float(fields[2])  # 现价
                    if price == 0.0 and len(fields) > 3 and fields[3]:
                        price = float(fields[3])  # 开盘价
                    if price == 0.0 and len(fields) > 6 and fields[6]:
                        price = float(fields[6])  # 昨收价
                except:
                    price = 0.0
                result[symbol] = {
                    'price': price,
                    'timestamp': datetime.now()
                }
            
            elif symbol == 'xauusd':
                # 伦敦金现货格式: 最新价,...
                result[symbol] = {
                    'price': float(fields[0]) if len(fields) > 0 and fields[0] else 0.0,  # 最新价
                    'timestamp': datetime.now()
                }
            
            elif symbol == 'usdcny':
                # 汇率格式: 时间,买价,卖价,最新价,...
                result[symbol] = {
                    'rate': float(fields[1]) if len(fields) > 1 and fields[1] else 0.0,  # 买价
                    'timestamp': datetime.now()
                }
            
            elif symbol == 'us10y':
                # 美债收益率格式: 收益率,...
                result[symbol] = {
                    'yield': float(fields[0]) if len(fields) > 0 and fields[0] else 0.0,
                    'timestamp': datetime.now()
                }
        
        return result
    
    async def get_gold_data(self) -> Dict:
        """
        获取黄金相关数据（SGE、国际金价、汇率）
        
        Returns:
            包含SGE价格、国际金价、汇率的字典
        """
        symbols = ['sge_au9999', 'xauusd', 'usdcny']
        data = await self.fetch_data(symbols)
        
        return {
            'sge_price': data.get('sge_au9999', {}).get('price', 0.0),
            'international_price': data.get('xauusd', {}).get('price', 0.0),
            'usdcny_rate': data.get('usdcny', {}).get('rate', 0.0),
            'timestamp': datetime.now()
        }
    
    async def get_us10y_data(self) -> Dict:
        """
        获取美国10年期国债收益率
        
        Returns:
            包含收益率和时间戳的字典
        """
        symbols = ['us10y']
        data = await self.fetch_data(symbols)
        
        return {
            'us10y': data.get('us10y', {}).get('yield', 0.0),
            'timestamp': datetime.now()
        }
    
    async def get_us10y_yield(self) -> Dict:
        """
        获取美国10年期国债收益率（别名）
        
        Returns:
            包含收益率和时间戳的字典
        """
        return await self.get_us10y_data()
    
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()


# 测试代码
if __name__ == "__main__":
    import asyncio
    
    async def test():
        async with SinaFinanceAPI() as api:
            # 测试获取黄金数据
            gold_data = await api.get_gold_data()
            print("黄金数据:", gold_data)
            
            # 测试获取美债数据
            us10y_data = await api.get_us10y_yield()
            print("美债数据:", us10y_data)
    
    asyncio.run(test())
