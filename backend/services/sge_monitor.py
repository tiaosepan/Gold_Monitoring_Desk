"""
SGE监控服务 - 完全匹配原系统
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session

from ..database import SGEPrice, SystemConfig, UpdateRecord, DataSourceHealth
from ..utils import SinaFinanceAPI, GoldAPIClient, oz_to_gram, safe_float, sge_logger


class SGEMonitorService:
    """SGE价格监控服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.primary_api = SinaFinanceAPI()  # 主数据源：新浪财经
        self.backup_api = GoldAPIClient()  # 备用数据源：Gold-API
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.primary_api.__aenter__()
        await self.backup_api.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.primary_api.__aexit__(exc_type, exc_val, exc_tb)
        await self.backup_api.__aexit__(exc_type, exc_val, exc_tb)
    
    def _check_market_open(self) -> Dict[str, int]:
        """
        检查市场开盘状态
        
        Returns:
            市场开盘状态字典
        """
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()  # 0=周一, 6=周日
        
        # 沪金市场：周一至周五 9:00-15:30 和 21:00-02:30（夜盘）
        shfe_open = 0
        if weekday < 5:  # 周一到周五
            # 日盘：9:00-15:30
            if (hour == 9 and minute >= 0) or (9 < hour < 15) or (hour == 15 and minute <= 30):
                shfe_open = 1
            # 夜盘：21:00-02:30
            elif hour >= 21 or hour < 2 or (hour == 2 and minute <= 30):
                shfe_open = 1
        
        # 伦敦金市场：24小时交易（周一凌晨到周六凌晨）
        # 简化处理：周一到周五全天开盘，周六周日休市
        london_open = 1 if weekday < 5 else 0
        
        # 双市场都开盘
        both_open = 1 if shfe_open == 1 and london_open == 1 else 0
        
        return {
            'shfe_market_open': shfe_open,
            'london_market_open': london_open,
            'both_markets_open': both_open
        }
    
    async def _fetch_international_gold_price(self) -> tuple[float, str, str]:
        """
        获取国际金价（主备切换）
        
        Returns:
            (金价, 数据源名称, 原始响应)
        """
        # 尝试主数据源: 新浪财经 hf_XAU
        try:
            sge_logger.debug("尝试从主数据源 新浪财经 hf_XAU 获取国际金价")
            sina_data = await self.primary_api.fetch_data(['xauusd'])
            price = safe_float(sina_data.get('xauusd', {}).get('price', 0))
            
            if price > 0:
                sge_logger.info(f"✓ 主数据源 新浪财经 成功: ${price}/盎司 (准实时)")
                self._update_data_source_health('Sina Finance API', 'healthy', None)
                return price, '新浪财经', sina_data.get('raw_response', '')
        except Exception as e:
            sge_logger.warning(f"主数据源 新浪财经 失败: {str(e)}")
            self._update_data_source_health('Sina Finance API', 'error', str(e))
        
        # 切换到备用数据源: Gold-API
        try:
            sge_logger.debug("切换到备用数据源 Gold-API")
            gold_data = await self.backup_api.get_xau_price()
            price = safe_float(gold_data.get('price', 0))
            
            if price > 0:
                sge_logger.info(f"✓ 备用数据源 Gold-API 成功: ${price}/盎司")
                self._update_data_source_health('Gold-API', 'healthy', None)
                return price, 'Gold-API(备)', str(gold_data.get('raw_data', ''))
        except Exception as e:
            sge_logger.error(f"备用数据源 Gold-API 也失败: {str(e)}")
            self._update_data_source_health('Gold-API', 'error', str(e))
        
        raise Exception("所有国际金价数据源均失败")
    
    async def fetch_and_save_data(self) -> Dict:
        """
        获取并保存SGE数据
        
        Returns:
            操作结果
        """
        start_time = datetime.now()
        sge_logger.debug("开始采集SGE数据")
        
        try:
            # 获取国际金价（主备切换）
            api_start = datetime.now()
            international_price, gold_source, gold_raw = await self._fetch_international_gold_price()
            
            # 获取汇率和沪金（使用新浪财经，这是国内独有数据）
            sina_data = await self.primary_api.fetch_data(['sge_au9999', 'usdcny'])
            sge_price = safe_float(sina_data.get('sge_au9999', {}).get('price', 0))
            usdcny_rate = safe_float(sina_data.get('usdcny', {}).get('rate', 0))
            sina_raw = sina_data.get('raw_response', '')
            
            api_duration = int((datetime.now() - api_start).total_seconds() * 1000)
            
            sge_logger.info(
                f"[数据采集] API响应耗时: {api_duration}ms | "
                f"AU9999: {sge_price}元/克 | 伦敦金: ${international_price}/盎司 | 汇率: {usdcny_rate}"
            )
            
            # 验证国际金价和汇率有效性（这两项不应为0）
            if international_price == 0 or usdcny_rate == 0:
                sge_logger.error(f"数据验证失败: 国际金价={international_price}, 汇率={usdcny_rate}")
                raise ValueError("获取的数据无效：国际金价或汇率为0")

            # 计算国际金价（人民币/克）
            london_price_cny_per_g = oz_to_gram(international_price) * usdcny_rate

            # 检查市场开盘状态
            market_status = self._check_market_open()

            # 当 AU9999 返回 0 时（常见于周末/节假日 SHFE 休市），用历史均值代理
            if sge_price == 0:
                if market_status['shfe_market_open'] == 0:
                    sge_logger.info("SHFE休市，AU9999返回0，查询历史溢价进行代理")
                    recent_records = self.db.query(SGEPrice).filter(
                        SGEPrice.both_markets_open == 1,
                        SGEPrice.premium_cny_per_g > 0
                    ).order_by(SGEPrice.fetched_at.desc()).limit(10).all()

                    if recent_records:
                        avg_premium = sum(r.premium_cny_per_g for r in recent_records) / len(recent_records)
                        sge_price = london_price_cny_per_g + avg_premium
                        sge_logger.info(f"使用历史平均溢价代理: {avg_premium:.4f}元/克")
                    else:
                        sge_logger.error("AU9999返回0且无历史代理数据")
                        raise ValueError("AU9999 返回0且无历史代理数据")
                else:
                    sge_logger.error("SHFE开市但沪金价格为0，数据异常")
                    raise ValueError("获取的数据无效：SHFE开市但沪金价格为0")

            # 计算溢价（元/克）
            # 注意：nf_AU0 在非交易时段仍有有效报价（可能是期货收盘价或做市商报价）
            # 因此始终使用 API 返回的 sge_price 来计算溢价，而不是用代理价格
            premium_cny_per_g = sge_price - london_price_cny_per_g

            # 仅当溢价明显异常（负值或过大）且市场关闭时，才使用历史平均溢价
            if premium_cny_per_g < 0 or premium_cny_per_g > 20:
                if market_status['shfe_market_open'] == 0:
                    sge_logger.warning(f"溢价异常: {premium_cny_per_g:.4f}元/克，使用历史平均溢价")
                    recent_records = self.db.query(SGEPrice).filter(
                        SGEPrice.both_markets_open == 1,
                        SGEPrice.premium_cny_per_g > 0
                    ).order_by(SGEPrice.fetched_at.desc()).limit(10).all()

                    if recent_records:
                        avg_premium = sum(r.premium_cny_per_g for r in recent_records) / len(recent_records)
                        sge_price = london_price_cny_per_g + avg_premium
                        premium_cny_per_g = avg_premium
                        sge_logger.info(f"溢价已修正为: {premium_cny_per_g:.4f}元/克")
            
            # 获取轮询间隔配置
            poll_config = self.db.query(SystemConfig).filter_by(config_key='poll_interval_seconds').first()
            poll_interval = int(poll_config.config_value) if poll_config else 60

            # 构建note - 根据实际数据源动态描述
            original_sge_price = safe_float(sina_data.get('sge_au9999', {}).get('price', 0))
            if market_status['shfe_market_open'] == 1:
                note = f"国内源: 新浪 AU9999 上海金现货；国际源: {gold_source} XAU 现货"
            elif original_sge_price == 0:
                note = f"国内源: AU9999 休市返回0，使用历史均值代理；国际源: {gold_source} XAU 现货"
            else:
                note = f"国内源: AU9999 盘后价(参考)；国际源: {gold_source} XAU 现货"
            
            # 构建原始响应（合并多个数据源）
            raw_payload = f"国际金[{gold_source}]: {gold_raw[:200]}... | 新浪[沪金+汇率]: {sina_raw[:200]}..."
            
            # 记录最终保存的价格（用于追踪数据跳跃问题）
            sge_logger.info(
                f"[即将保存] AU9999={sge_price:.4f} | 国际金折算={london_price_cny_per_g:.4f} | 溢价={premium_cny_per_g:.4f}"
            )
            
            # 保存到数据库（使用原系统字段名）
            sge_record = SGEPrice(
                fetched_at=datetime.now(),
                shfe_price_cny_per_g=round(sge_price, 4),
                london_price_usd_per_oz=round(international_price, 2),
                usdcny_rate=round(usdcny_rate, 4),
                london_price_cny_per_g=round(london_price_cny_per_g, 4),
                premium_cny_per_g=round(premium_cny_per_g, 4),
                poll_interval_seconds=poll_interval,
                both_markets_open=market_status['both_markets_open'],
                shfe_market_open=market_status['shfe_market_open'],
                london_market_open=market_status['london_market_open'],
                alert_triggered=0,
                raw_payload=raw_payload,
                note=note
            )
            
            self.db.add(sge_record)
            
            # 记录更新日志
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            update_record = UpdateRecord(
                data_type='sge_price',
                status='success',
                record_count=1
            )
            self.db.add(update_record)
            
            # 更新新浪财经数据源健康状态（沪金和汇率）
            self._update_data_source_health('Sina Finance API - 沪金汇率', 'healthy', None)
            
            self.db.commit()
            
            sge_logger.info(
                f"SGE数据保存成功 - 耗时: {duration_ms}ms - "
                f"溢价: {premium_cny_per_g:.4f}元/克 - "
                f"市场状态: {'双开' if market_status['both_markets_open'] else '单开' if market_status['shfe_market_open'] else '休市'}"
            )
            
            return {
                'success': True,
                'message': 'SGE数据采集成功',
                'duration_ms': duration_ms,
                'market_status': market_status,
                'data': {
                    'shfe_price_cny_per_g': round(sge_price, 4),
                    'london_price_usd_per_oz': round(international_price, 2),
                    'usdcny_rate': round(usdcny_rate, 4),
                    'london_price_cny_per_g': round(london_price_cny_per_g, 4),
                    'premium_cny_per_g': round(premium_cny_per_g, 4),
                    'fetched_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            # 记录错误
            error_msg = str(e)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            sge_logger.error(f"SGE数据采集失败 - 耗时: {duration_ms}ms - 错误: {error_msg}", exc_info=True)
            
            update_record = UpdateRecord(
                data_type='sge_price',
                status='failed',
                record_count=0,
                error_message=error_msg
            )
            self.db.add(update_record)
            
            # 更新数据源健康状态（记录最终失败）
            self._update_data_source_health('SGE Monitor System', 'error', error_msg)
            
            self.db.commit()
            
            return {
                'success': False,
                'message': f'SGE数据采集失败: {error_msg}',
                'duration_ms': duration_ms,
                'data': None,
                'market_status': None
            }
    
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
    
    def get_latest_data(self, limit: int = 100) -> list:
        """
        获取最新的SGE数据
        
        Args:
            limit: 返回记录数
            
        Returns:
            数据列表
        """
        records = self.db.query(SGEPrice).order_by(SGEPrice.fetched_at.desc()).limit(limit).all()
        
        return [{
            'id': r.id,
            'fetched_at': r.fetched_at.isoformat(),
            'shfe_price_cny_per_g': r.shfe_price_cny_per_g,
            'london_price_usd_per_oz': r.london_price_usd_per_oz,
            'usdcny_rate': r.usdcny_rate,
            'london_price_cny_per_g': r.london_price_cny_per_g,
            'premium_cny_per_g': r.premium_cny_per_g,
            'both_markets_open': r.both_markets_open,
            'shfe_market_open': r.shfe_market_open,
            'london_market_open': r.london_market_open,
            'note': r.note
        } for r in records]
    
    def get_premium_stats(self) -> Dict:
        """
        获取溢价统计信息
        
        Returns:
            统计数据
        """
        # 获取最新记录
        latest = self.db.query(SGEPrice).order_by(SGEPrice.fetched_at.desc()).first()
        
        if not latest:
            return {
                'current_premium': 0,
                'avg_premium': 0,
                'max_premium': 0,
                'min_premium': 0
            }
        
        # 获取最近100条记录的统计
        from sqlalchemy import func
        recent_time = datetime.now() - timedelta(hours=24)
        stats = self.db.query(
            func.avg(SGEPrice.premium_cny_per_g).label('avg_premium'),
            func.max(SGEPrice.premium_cny_per_g).label('max_premium'),
            func.min(SGEPrice.premium_cny_per_g).label('min_premium')
        ).filter(
            SGEPrice.fetched_at >= recent_time
        ).first()
        
        return {
            'current_premium': round(latest.premium_cny_per_g, 4),
            'avg_premium': round(stats.avg_premium or 0, 4),
            'max_premium': round(stats.max_premium or 0, 4),
            'min_premium': round(stats.min_premium or 0, 4)
        }
    
    def check_premium_alert(self) -> Optional[Dict]:
        """
        检查溢价是否超过阈值（带冷却机制）
        
        Returns:
            如果超过阈值且不在冷却期，返回警报信息；否则返回None
        """
        # 获取阈值配置
        threshold_config = self.db.query(SystemConfig).filter_by(
            config_key='premium_threshold'
        ).first()
        
        cooldown_config = self.db.query(SystemConfig).filter_by(
            config_key='alert_cooldown_seconds'
        ).first()
        
        threshold = safe_float(threshold_config.config_value if threshold_config else '20', 20)
        cooldown_seconds = int(cooldown_config.config_value) if cooldown_config else 900
        
        # 获取最新数据
        latest = self.db.query(SGEPrice).order_by(SGEPrice.fetched_at.desc()).first()
        
        if not latest:
            return None
        
        # 检查是否超过阈值
        if latest.premium_cny_per_g >= threshold:
            # 检查冷却期
            cooldown_time = datetime.now() - timedelta(seconds=cooldown_seconds)
            recent_alert = self.db.query(SGEPrice).filter(
                SGEPrice.alert_triggered == 1,
                SGEPrice.fetched_at >= cooldown_time
            ).first()
            
            if not recent_alert:
                # 标记为已触发警报
                latest.alert_triggered = 1
                self.db.commit()
                
                return {
                    'alert_type': 'SGE溢价警报',
                    'level': 3,
                    'content': f"SGE溢价: {latest.premium_cny_per_g}元/克\n"
                              f"阈值: {threshold}元/克\n"
                              f"沪金价格: {latest.shfe_price_cny_per_g}元/克\n"
                              f"国际金价: {latest.london_price_usd_per_oz}美元/盎司\n"
                              f"汇率: {latest.usdcny_rate}",
                    'timestamp': latest.fetched_at
                }
        
        return None
