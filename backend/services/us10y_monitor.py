"""
美债监控服务 - 完全匹配原系统（支持FRED API回退）
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import aiohttp
import asyncio
import csv
import io
import os

from ..database import USTreasury, SystemConfig, UpdateRecord, DataSourceHealth
from ..utils import SinaFinanceAPI, safe_float, EastmoneyAPI, CNBCAPI, us10y_logger


class US10YMonitorService:
    """美债监控服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.api = SinaFinanceAPI()
        self.cnbc_api = CNBCAPI()
        self.fred_api_key = os.environ.get('FRED_API_KEY')  # 从环境变量读取FRED API密钥
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.api.__aenter__()
        await self.cnbc_api.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.api.__aexit__(exc_type, exc_val, exc_tb)
        await self.cnbc_api.__aexit__(exc_type, exc_val, exc_tb)
    
    async def _fetch_from_yahoo(self, tenor: str = '10y') -> Optional[float]:
        """
        从Yahoo Finance获取美债收益率

        Args:
            tenor: 期限（10y/5y/20y/30y）

        Returns:
            收益率值或None
        """
        symbol_map = {
            '10y': '%5ETNX',   # 10年期
            '5y': '%5EFVX',    # 5年期
            '20y': '%5ETYX',   # 30年期（20y用30y代替）
            '30y': '%5ETYX'    # 30年期
        }

        symbol = symbol_map.get(tenor, '%5ETNX')

        try:
            import urllib.request
            import json
            # 使用5分钟间隔获取日内数据，避免返回每日单一数据点
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=1d"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                result = data.get('chart', {}).get('result', [])
                if result:
                    # 从日内数据中获取最新收盘价
                    indicators = result[0].get('indicators', {})
                    quote = indicators.get('quote', [{}])[0]
                    closes = quote.get('close', [])
                    # 找到最后一个有效值
                    for price in reversed(closes):
                        if price is not None and price > 0:
                            return float(price)
        except Exception as e:
            print(f"Yahoo Finance错误: {e}")

        return None

    async def _fetch_from_fred_public(self, tenor: str = '10y') -> Optional[float]:
        """
        从FRED公开CSV获取美债收益率（无需API Key）

        Args:
            tenor: 期限（10y/5y/20y）

        Returns:
            收益率值或None
        """
        series_map = {
            '10y': 'DGS10',
            '5y': 'DGS5',
            '20y': 'DGS20'
        }

        series_id = series_map.get(tenor, 'DGS10')

        try:
            import urllib.request
            # 使用公开的CSV接口
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&vintage_date=latest"
            with urllib.request.urlopen(url, timeout=10) as response:
                text = response.read().decode('utf-8')
                # 解析CSV获取最新有效值
                lines = text.strip().split('\n')
                for line in reversed(lines):
                    if ',' in line:
                        parts = line.split(',')
                        if len(parts) == 2:
                            date_str, value = parts
                            if value and value != '.':
                                try:
                                    return float(value)
                                except:
                                    continue
        except Exception as e:
            print(f"FRED公开API错误: {e}")

        return None

    async def _fetch_from_fred(self, tenor: str = '10y') -> Optional[float]:
        """
        从FRED API获取美债收益率（回退方案，需要API Key）

        Args:
            tenor: 期限（10y/5y/20y）

        Returns:
            收益率值或None
        """
        if not self.fred_api_key:
            return None

        series_map = {
            '10y': 'DGS10',
            '5y': 'DGS5',
            '20y': 'DGS20'
        }

        series_id = series_map.get(tenor, 'DGS10')
        url = f"https://api.stlouisfed.org/fred/series/observations"

        params = {
            'series_id': series_id,
            'api_key': self.fred_api_key,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 1
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('observations'):
                            value = data['observations'][0].get('value')
                            if value and value != '.':
                                return float(value)
        except Exception as e:
            print(f"FRED API错误: {e}")

        return None
    
    async def fetch_and_save_data(self, tenor: str = '10y') -> Dict:
        """
        获取并保存美债数据（快速失败策略，优化超时）

        Args:
            tenor: 期限（5y/10y/20y）

        Returns:
            操作结果
        """
        start_time = datetime.now()
        source = None
        eastmoney_api = EastmoneyAPI()

        try:
            # 快速失败策略：优先使用实时数据源
            yield_value = None
            
            # 1. 优先尝试CNBC（实时，最可靠，2秒超时）
            try:
                cnbc_value = await asyncio.wait_for(self.cnbc_api.get_yield(tenor), timeout=2.0)
                if cnbc_value and cnbc_value > 0:
                    yield_value = cnbc_value
                    source = 'CNBC'
                    us10y_logger.debug(f"CNBC API成功 - {tenor}: {yield_value}%")
            except (asyncio.TimeoutError, Exception) as e:
                us10y_logger.debug(f"CNBC API失败 - {tenor}: {str(e)}")
            
            # 2. 尝试新浪API（实时，已修复403，2秒超时）
            if not yield_value:
                try:
                    sina_data = await asyncio.wait_for(self.api.get_us10y_data(), timeout=2.0)
                    if sina_data and sina_data.get('us10y', 0) > 0:
                        yield_value = sina_data['us10y']
                        source = 'Sina'
                        us10y_logger.debug(f"Sina API成功 - {tenor}: {yield_value}%")
                except (asyncio.TimeoutError, Exception) as e:
                    us10y_logger.debug(f"Sina API失败 - {tenor}: {str(e)}")
            
            # 3. 尝试FRED（官方每日数据，3秒超时）
            if not yield_value and self.fred_api_key:
                try:
                    fred_value = await asyncio.wait_for(self._fetch_from_fred(tenor), timeout=3.0)
                    if fred_value and fred_value > 0:
                        yield_value = fred_value
                        source = 'FRED'
                        us10y_logger.debug(f"FRED API成功 - {tenor}: {yield_value}%")
                except (asyncio.TimeoutError, Exception) as e:
                    us10y_logger.debug(f"FRED API失败 - {tenor}: {str(e)}")
            
            # 4. 最后尝试东方财富（备用，3秒超时）
            if not yield_value:
                try:
                    eastmoney_data = await asyncio.wait_for(eastmoney_api.get_yield(tenor), timeout=3.0)
                    if eastmoney_data and eastmoney_data.get('yield', 0) > 0:
                        yield_value = eastmoney_data['yield']
                        source = 'Eastmoney'
                        us10y_logger.debug(f"Eastmoney API成功 - {tenor}: {yield_value}%")
                except (asyncio.TimeoutError, Exception) as e:
                    us10y_logger.debug(f"Eastmoney API失败 - {tenor}: {str(e)}")
            
            # 5. 所有源都失败
            if not yield_value:
                raise ValueError(f"所有数据源都无法获取有效的{tenor}美债数据")

            # 获取轮询间隔配置
            poll_config = self.db.query(SystemConfig).filter_by(config_key='poll_interval_seconds').first()
            poll_interval = int(poll_config.config_value) if poll_config else 60

            # 检测收益率下跌信号（阈值改为5bp）
            lookback_hours = self._get_config('us10y_drop_lookback_hours', 24.0)
            threshold_bp = self._get_config('us10y_drop_threshold_bp', 5.0)

            cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
            from sqlalchemy import func
            max_yield = self.db.query(func.max(USTreasury.yield_pct)).filter(
                USTreasury.fetched_at >= cutoff_time,
                USTreasury.tenor == tenor
            ).scalar()

            drop_bp = (max_yield - yield_value) * 100 if max_yield else 0
            yield_signal = 1 if drop_bp >= threshold_bp else 0

            # 期限显示名称
            tenor_display = tenor.upper().replace('Y', 'Y ')
            note = f"{tenor_display}: 现值 {yield_value:.3f}% / 高点 {max_yield:.3f}% / {lookback_hours}h回落 {drop_bp:.2f}bp (阈值 {threshold_bp:.2f}bp)" if max_yield else f"{tenor_display}: 现值 {yield_value:.3f}%"
            
            # 保存到数据库
            us10y_record = USTreasury(
                fetched_at=datetime.now(),
                yield_pct=round(yield_value, 3),
                yield_signal=yield_signal,
                source=source,
                tenor=tenor,
                note=note
            )
            
            self.db.add(us10y_record)
            
            # 记录更新日志
            update_record = UpdateRecord(
                data_type='us_treasury',
                status='success',
                record_count=1
            )
            self.db.add(update_record)
            
            # 更新数据源健康状态
            self._update_data_source_health(source, 'healthy', None)
            
            self.db.commit()
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                'success': True,
                'message': '美债数据采集成功',
                'duration_ms': duration_ms,
                'data': {
                    'yield_pct': round(yield_value, 3),
                    'yield_signal': yield_signal,
                    'source': source,
                    'tenor': tenor,
                    'fetched_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            # 记录错误
            error_msg = str(e)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            update_record = UpdateRecord(
                data_type='us_treasury',
                status='failed',
                record_count=0,
                error_message=error_msg
            )
            self.db.add(update_record)
            
            # 更新数据源健康状态
            self._update_data_source_health('Sina/FRED API', 'error', error_msg)
            
            self.db.commit()
            
            return {
                'success': False,
                'message': f'美债数据采集失败: {error_msg}',
                'duration_ms': duration_ms,
                'data': None
            }
    
    def _get_config(self, key: str, default: float) -> float:
        """获取配置值"""
        config = self.db.query(SystemConfig).filter_by(config_key=key).first()
        return safe_float(config.config_value if config else str(default), default)
    
    def _update_data_source_health(self, source_name: str, status: str, error_message: Optional[str]):
        """
        更新数据源健康状态
        
        Args:
            source_name: 数据源名称
            status: 状态
            error_message: 错误消息
        """
        health = self.db.query(DataSourceHealth).filter_by(source_name=source_name).first()
        
        if health:
            health.status = status
            health.updated_at = datetime.now()
            
            if status == 'healthy':
                health.last_success_at = datetime.now()
                health.error_count = 0
            else:
                health.last_error_at = datetime.now()
                health.error_count += 1
        else:
            health = DataSourceHealth(
                source_name=source_name,
                status=status,
                last_success_at=datetime.now() if status == 'healthy' else None,
                last_error_at=datetime.now() if status != 'healthy' else None,
                error_count=0 if status == 'healthy' else 1
            )
            self.db.add(health)
    
    def get_latest_data(self, limit: int = 100) -> List[Dict]:
        """
        获取最新的美债数据
        
        Args:
            limit: 返回记录数
            
        Returns:
            数据列表
        """
        records = self.db.query(USTreasury).order_by(USTreasury.fetched_at.desc()).limit(limit).all()
        
        return [{
            'id': r.id,
            'fetched_at': r.fetched_at.isoformat(),
            'yield_pct': r.yield_pct,
            'yield_signal': r.yield_signal,
            'source': r.source,
            'tenor': r.tenor,
            'note': r.note
        } for r in records]
    
    def detect_yield_drop(self, lookback_hours: float = 24.0, threshold_bp: float = 1.0) -> Optional[Dict]:
        """
        检测收益率下跌
        
        Args:
            lookback_hours: 回看小时数
            threshold_bp: 阈值（基点）
            
        Returns:
            如果检测到下跌，返回详情；否则返回None
        """
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
        
        # 获取最新数据
        latest = self.db.query(USTreasury).order_by(USTreasury.fetched_at.desc()).first()
        
        if not latest:
            return None
        
        # 获取回看期内的最高收益率
        from sqlalchemy import func
        max_yield = self.db.query(func.max(USTreasury.yield_pct)).filter(
            USTreasury.fetched_at >= cutoff_time
        ).scalar()
        
        if not max_yield:
            return None
        
        # 计算下跌幅度（基点）
        drop_bp = (max_yield - latest.yield_pct) * 100
        
        if drop_bp >= threshold_bp:
            return {
                'alert_type': '美债收益率下跌警报',
                'level': 2,
                'content': f"美债收益率下跌\n"
                          f"期限: {latest.tenor}\n"
                          f"当前收益率: {latest.yield_pct:.2f}%\n"
                          f"最高收益率: {max_yield:.2f}%\n"
                          f"下跌幅度: {drop_bp:.2f}bp\n"
                          f"阈值: {threshold_bp:.2f}bp\n"
                          f"数据源: {latest.source}",
                'timestamp': latest.fetched_at
            }
        
        return None
    
    def get_yield_stats(self) -> Dict:
        """
        获取收益率统计信息
        
        Returns:
            统计数据
        """
        # 获取最新记录
        latest = self.db.query(USTreasury).order_by(USTreasury.fetched_at.desc()).first()
        
        if not latest:
            return {
                'current_yield': 0,
                'avg_yield': 0,
                'max_yield': 0,
                'min_yield': 0
            }
        
        # 获取最近24小时的统计
        from sqlalchemy import func
        recent_time = datetime.now() - timedelta(hours=24)
        stats = self.db.query(
            func.avg(USTreasury.yield_pct).label('avg_yield'),
            func.max(USTreasury.yield_pct).label('max_yield'),
            func.min(USTreasury.yield_pct).label('min_yield')
        ).filter(
            USTreasury.fetched_at >= recent_time
        ).first()
        
        return {
            'current_yield': round(latest.yield_pct, 3),
            'avg_yield': round(stats.avg_yield or 0, 3),
            'max_yield': round(stats.max_yield or 0, 3),
            'min_yield': round(stats.min_yield or 0, 3)
        }
