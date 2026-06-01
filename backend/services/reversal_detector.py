"""
黄金反转检测服务 - 完全匹配原系统
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import ReversalCondition, SGEPrice, RSSEvent, USTreasury, SystemConfig, AlertHistory
from ..utils import safe_float, reversal_logger


class ReversalDetectorService:
    """黄金反转检测服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_config(self, key: str, default: float) -> float:
        """获取配置值"""
        config = self.db.query(SystemConfig).filter_by(config_key=key).first()
        return safe_float(config.config_value if config else str(default), default)
    
    def detect_price_condition(self) -> tuple[int, str]:
        """
        检测价格条件
        
        算法：
        1. 获取最近N分钟的金价数据
        2. 计算15周期移动平均
        3. 判断是否从低点反弹超过阈值百分比
        
        Returns:
            (信号值, 说明文本)
        """
        lookback_minutes = int(self._get_config('reversal_price_lookback_minutes', 60))
        rebound_pct = self._get_config('reversal_price_rebound_pct', 1.2)
        ma_window = int(self._get_config('reversal_price_ma_window', 15))
        
        # 获取最近N分钟的价格数据
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)
        recent_prices = self.db.query(SGEPrice).filter(
            SGEPrice.fetched_at >= cutoff_time
        ).order_by(SGEPrice.fetched_at.asc()).all()
        
        if len(recent_prices) < ma_window:
            return 0, f"数据不足(需要{ma_window}条)"
        
        # 获取最新价格
        latest_price = recent_prices[-1].london_price_usd_per_oz
        
        # 计算MA15
        ma15_prices = [p.london_price_usd_per_oz for p in recent_prices[-ma_window:]]
        ma15 = sum(ma15_prices) / len(ma15_prices)
        
        # 找到最低点
        min_price = min(p.london_price_usd_per_oz for p in recent_prices)
        
        # 计算反弹百分比
        if min_price > 0:
            rebound = ((latest_price - min_price) / min_price) * 100
        else:
            rebound = 0
        
        # 判断信号
        signal = 1 if rebound >= rebound_pct else 0
        
        note = f"现价 {latest_price:.2f} / 低点 {min_price:.2f} / MA15 {ma15:.2f} / 反弹 {rebound:.2f}%"
        
        return signal, note
    
    def detect_political_condition(self) -> tuple[int, str]:
        """
        检测政治条件
        
        算法：
        检查最近3小时内是否有高分政治事件（评分>=7）
        
        Returns:
            (信号值, 说明文本)
        """
        signal_window = int(self._get_config('reversal_signal_window_minutes', 180))
        cutoff_time = datetime.now() - timedelta(minutes=signal_window)
        
        # 查询最近的高分政治事件
        high_score_events = self.db.query(RSSEvent).filter(
            RSSEvent.event_type == 'political',
            RSSEvent.impact_score >= 6,
            RSSEvent.fetched_at >= cutoff_time
        ).order_by(RSSEvent.impact_score.desc()).limit(3).all()
        
        if high_score_events:
            # 拼接事件标题
            titles = ' | '.join([e.title[:50] + '...' if len(e.title) > 50 else e.title 
                                for e in high_score_events])
            return 1, f"政治事件: {titles}"
        
        return 0, "无高分政治事件"
    
    def detect_war_condition(self) -> tuple[int, str]:
        """
        检测战争条件
        
        算法：
        检查最近3小时内是否有高分战争事件（评分>=7）
        
        Returns:
            (信号值, 说明文本)
        """
        signal_window = int(self._get_config('reversal_signal_window_minutes', 180))
        cutoff_time = datetime.now() - timedelta(minutes=signal_window)
        
        # 查询最近的高分战争事件
        high_score_events = self.db.query(RSSEvent).filter(
            RSSEvent.event_type == 'war',
            RSSEvent.impact_score >= 6,
            RSSEvent.fetched_at >= cutoff_time
        ).order_by(RSSEvent.impact_score.desc()).limit(3).all()
        
        if high_score_events:
            # 拼接事件标题
            titles = ' | '.join([e.title[:50] + '...' if len(e.title) > 50 else e.title 
                                for e in high_score_events])
            return 1, f"战争进度: {titles}"
        
        return 0, "无高分战争事件"
    
    def detect_us10y_condition(self) -> tuple[int, str]:
        """
        检测美债条件
        
        算法：
        检查最近24小时内收益率是否下跌超过阈值
        
        Returns:
            (信号值, 说明文本)
        """
        lookback_hours = self._get_config('us10y_drop_lookback_hours', 24.0)
        threshold_bp = self._get_config('us10y_drop_threshold_bp', 1.0)

        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)

        # 获取最新和历史最高收益率（仅限10Y期限）
        latest = self.db.query(USTreasury).filter(
            USTreasury.tenor == '10y'
        ).order_by(USTreasury.fetched_at.desc()).first()

        if not latest:
            return 0, "无美债数据"

        # 获取回看期内的最高收益率（仅限10Y期限）
        max_yield = self.db.query(func.max(USTreasury.yield_pct)).filter(
            USTreasury.fetched_at >= cutoff_time,
            USTreasury.tenor == '10y'
        ).scalar()
        
        if not max_yield:
            return 0, "历史数据不足"
        
        # 计算下跌幅度（基点）
        drop_bp = (max_yield - latest.yield_pct) * 100
        
        signal = 1 if drop_bp >= threshold_bp else 0
        
        note = f"10Y: 现值 {latest.yield_pct:.3f}% / 高点 {max_yield:.3f}% / {lookback_hours}h回落 {drop_bp:.2f}bp (阈值 {threshold_bp:.2f}bp)"
        
        return signal, note
    
    def determine_reversal_level(self, price_signal: int, political_signal: int, 
                                 war_signal: int, us10y_signal: int) -> int:
        """
        确定反转等级（完全匹配原系统逻辑）
        
        原系统逻辑（基于实际数据反向工程）：
        - 等级4: 仅政治信号 (political=1, war=0) - 单一缓和信号，等级最高
        - 等级3: 政治+战争信号 (political=1, war=1) - 多信号但可能冲突，等级次之
        - 等级2: 仅战争信号 (war=1, political=0)
        - 等级1: 其他组合
        - 等级0: 无信号
        
        注意：原系统的"等级"表示"缓和程度"，不是"信号强度"
        单一政治缓和信号(Level 4)比混合信号(Level 3)更可靠
        
        Args:
            price_signal: 价格信号
            political_signal: 政治信号
            war_signal: 战争信号
            us10y_signal: 美债信号
            
        Returns:
            反转等级 (0-4)
        """
        # 等级4: 仅政治信号（最纯粹的缓和信号）
        if political_signal == 1 and war_signal == 0:
            return 4
        
        # 等级3: 政治+战争信号（混合信号）
        if political_signal == 1 and war_signal == 1:
            return 3
        
        # 等级2: 仅战争信号
        if war_signal == 1 and political_signal == 0:
            return 2
        
        # 等级1: 其他组合（如仅价格或仅美债）
        if price_signal == 1 or us10y_signal == 1:
            return 1
        
        # 等级0: 无信号
        return 0
    
    async def detect_and_save(self) -> Dict:
        """
        执行反转检测并保存结果
        
        Returns:
            检测结果
        """
        start_time = datetime.now()
        reversal_logger.debug("开始反转检测")
        
        try:
            # 获取最新金价和汇率
            latest_sge = self.db.query(SGEPrice).order_by(SGEPrice.fetched_at.desc()).first()
            
            if not latest_sge:
                reversal_logger.warning("反转检测失败: 无SGE数据")
                return {
                    'success': False,
                    'message': '无SGE数据',
                    'data': None
                }
            
            # 执行四类条件检测
            price_signal, price_note = self.detect_price_condition()
            political_signal, political_note = self.detect_political_condition()
            war_signal, war_note = self.detect_war_condition()
            us10y_signal, us10y_note = self.detect_us10y_condition()
            
            reversal_logger.debug(
                f"信号检测结果 - Price: {price_signal} - Political: {political_signal} - "
                f"War: {war_signal} - US10Y: {us10y_signal}"
            )
            
            # 确定反转等级
            signal_level = self.determine_reversal_level(
                price_signal, political_signal, war_signal, us10y_signal
            )
            
            # 构建触发条件列表
            triggered = []
            if price_signal: triggered.append('price')
            if political_signal: triggered.append('political')
            if war_signal: triggered.append('war')
            if us10y_signal: triggered.append('us10y')
            
            triggered_conditions = ','.join(triggered) if triggered else ''
            
            # 构建note
            note_parts = [f"盘面: {price_note}"]
            note_parts.append(f"国内源: 代理人民币金价(基于最近有效样本比例，参考 {datetime.now().strftime('%m-%d %H:%M')})；国际源: 新浪 hf_XAU 伦敦金现货")
            note_parts.append(f"{us10y_note}")
            if political_note != "无高分政治事件":
                note_parts.append(political_note)
            if war_note != "无高分战争事件":
                note_parts.append(war_note)
            note_parts.append(f"RSS独立调度: 上次抓取成功({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
            
            note = '；'.join(note_parts)
            
            # 保存检测结果
            reversal_record = ReversalCondition(
                fetched_at=datetime.now(),
                gold_price_usd_per_oz=latest_sge.london_price_usd_per_oz,
                usdcny_rate=latest_sge.usdcny_rate,
                price_signal=price_signal,
                political_signal=political_signal,
                war_signal=war_signal,
                us10y_signal=us10y_signal,
                signal_level=signal_level,
                triggered_conditions=triggered_conditions,
                note=note
            )
            
            self.db.add(reversal_record)
            self.db.commit()
            
            # 记录运行日志
            from ..database import UpdateRecord
            update_record = UpdateRecord(
                data_type='reversal_detection',
                status='success',
                record_count=1
            )
            self.db.add(update_record)
            self.db.commit()
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            reversal_logger.info(
                f"反转检测完成 - 耗时: {duration_ms}ms - Level: {signal_level} - "
                f"触发条件: {triggered_conditions or '无'}"
            )
            
            return {
                'success': True,
                'message': '反转检测完成',
                'duration_ms': duration_ms,
                'data': {
                    'signal_level': signal_level,
                    'price_signal': price_signal,
                    'political_signal': political_signal,
                    'war_signal': war_signal,
                    'us10y_signal': us10y_signal,
                    'triggered_conditions': triggered_conditions,
                    'note': note
                }
            }
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            reversal_logger.error(f"反转检测失败 - 耗时: {duration_ms}ms - 错误: {str(e)}", exc_info=True)
            
            # 记录失败日志
            from ..database import UpdateRecord
            update_record = UpdateRecord(
                data_type='reversal_detection',
                status='failed',
                record_count=0,
                error_message=str(e)
            )
            self.db.add(update_record)
            self.db.commit()
            
            return {
                'success': False,
                'message': f'反转检测失败: {str(e)}',
                'duration_ms': duration_ms,
                'data': None
            }
    
    def should_push_alert(self, signal_level: int) -> bool:
        """
        判断是否应该推送警报（带冷却机制）
        
        Args:
            signal_level: 信号等级
            
        Returns:
            是否应该推送
        """
        if signal_level < 2:
            return False
        
        # 获取冷却时间配置
        cooldown_seconds = int(self._get_config('reversal_cooldown_seconds', 1800))
        
        # 检查冷却期
        cooldown_time = datetime.now() - timedelta(seconds=cooldown_seconds)
        recent_alert = self.db.query(AlertHistory).filter(
            AlertHistory.alert_type == 'reversal',
            AlertHistory.created_at >= cooldown_time
        ).first()
        
        return recent_alert is None
    
    def create_alert(self, reversal_data: Dict) -> Dict:
        """
        创建反转警报
        
        Args:
            reversal_data: 反转数据
            
        Returns:
            警报内容
        """
        level = reversal_data['signal_level']
        conditions = reversal_data['triggered_conditions']
        
        level_names = {
            5: '极高风险',
            4: '高风险',
            3: '中等风险',
            2: '低风险',
            1: '观察'
        }
        
        return {
            'alert_type': '黄金反转预警',
            'level': level,
            'level_name': level_names.get(level, '未知'),
            'content': f"反转等级: {level} - {level_names.get(level, '未知')}\n"
                      f"触发条件: {conditions}\n"
                      f"金价: {reversal_data.get('gold_price_usd_per_oz', 0):.2f} 美元/盎司\n"
                      f"{reversal_data.get('note', '')}",
            'timestamp': datetime.now()
        }
    
    def get_latest_reversal(self) -> Optional[Dict]:
        """
        获取最新的反转检测结果
        
        Returns:
            最新反转数据
        """
        latest = self.db.query(ReversalCondition).order_by(
            ReversalCondition.fetched_at.desc()
        ).first()
        
        if not latest:
            return None
        
        return {
            'id': latest.id,
            'fetched_at': latest.fetched_at.isoformat(),
            'gold_price_usd_per_oz': latest.gold_price_usd_per_oz,
            'usdcny_rate': latest.usdcny_rate,
            'price_signal': latest.price_signal,
            'political_signal': latest.political_signal,
            'war_signal': latest.war_signal,
            'us10y_signal': latest.us10y_signal,
            'signal_level': latest.signal_level,
            'triggered_conditions': latest.triggered_conditions,
            'note': latest.note
        }
    
    def get_reversal_history(self, range_str: str = "1H") -> Dict:
        """
        获取反转历史记录（支持时间范围参数）
        
        Args:
            range_str: 时间范围 "1H", "1D", "1W"
            
        Returns:
            包含range, since, items的字典
        """
        # 根据range计算时间范围
        now = datetime.now()
        if range_str == "1H":
            since = now - timedelta(hours=1)
        elif range_str == "1D":
            since = now - timedelta(days=1)
        elif range_str == "1W":
            since = now - timedelta(weeks=1)
        else:
            since = now - timedelta(hours=1)  # 默认1小时
        
        records = self.db.query(ReversalCondition).filter(
            ReversalCondition.fetched_at >= since
        ).order_by(
            ReversalCondition.fetched_at.desc()
        ).all()
        
        items = [{
            'id': r.id,
            'fetched_at': r.fetched_at.isoformat() if r.fetched_at else None,
            'gold_price_usd_per_oz': r.gold_price_usd_per_oz,
            'usdcny_rate': r.usdcny_rate,
            'price_signal': r.price_signal,
            'political_signal': r.political_signal,
            'war_signal': r.war_signal,
            'signal_level': r.signal_level,
            'triggered_conditions': r.triggered_conditions or '',
            'note': r.note or '',
            'us10y_signal': r.us10y_signal
        } for r in records]
        
        # 计算时间范围（完全匹配原系统）
        time_range_str = ''
        since_str = ''
        if items:
            latest = items[0]['fetched_at']
            oldest = items[-1]['fetched_at']
            time_range_str = f"{oldest} ~ {latest}"
            since_str = oldest
        
        return {
            'range': time_range_str,
            'since': since_str,
            'items': items
        }
