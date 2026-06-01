"""
黄金反转检测服务 V2 - 优化版等级判断逻辑

改进点:
1. 等级定义更直观: Level 0-4 按信号数量递增
2. 推送策略清晰: Level 3/4 推送，Level 1/2 观察，Level 0 无信号
3. 引入信号强度权重: 不同信号重要性不同
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import ReversalCondition, SGEPrice, RSSEvent, USTreasury, SystemConfig, AlertHistory
from ..utils import safe_float, reversal_logger


class ReversalDetectorServiceV2:
    """黄金反转检测服务 V2（优化版）"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_config(self, key: str, default: float) -> float:
        """获取配置值"""
        config = self.db.query(SystemConfig).filter_by(config_key=key).first()
        return safe_float(config.config_value if config else str(default), default)
    
    def detect_price_condition(self) -> tuple[int, str, float]:
        """
        检测价格条件
        
        Returns:
            (信号值, 说明文本, 信号强度)
        """
        lookback_minutes = int(self._get_config('reversal_price_lookback_minutes', 60))
        rebound_pct = self._get_config('reversal_price_rebound_pct', 1.2)
        ma_window = int(self._get_config('reversal_price_ma_window', 15))
        
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)
        recent_prices = self.db.query(SGEPrice).filter(
            SGEPrice.fetched_at >= cutoff_time
        ).order_by(SGEPrice.fetched_at.asc()).all()
        
        if len(recent_prices) < ma_window:
            return 0, f"数据不足(需要{ma_window}条)", 0.0
        
        latest_price = recent_prices[-1].london_price_usd_per_oz
        ma15_prices = [p.london_price_usd_per_oz for p in recent_prices[-ma_window:]]
        ma15 = sum(ma15_prices) / len(ma15_prices)
        min_price = min(p.london_price_usd_per_oz for p in recent_prices)
        
        if min_price > 0:
            rebound = ((latest_price - min_price) / min_price) * 100
        else:
            rebound = 0
        
        # 信号强度: 反弹幅度越大，信号越强
        signal_strength = min(rebound / rebound_pct, 2.0)  # 最大2.0
        
        signal = 1 if rebound >= rebound_pct else 0
        note = f"现价 {latest_price:.2f} / 低点 {min_price:.2f} / MA15 {ma15:.2f} / 反弹 {rebound:.2f}%"
        
        return signal, note, signal_strength
    
    def detect_political_condition(self) -> tuple[int, str, float]:
        """
        检测政治条件
        
        Returns:
            (信号值, 说明文本, 信号强度)
        """
        signal_window = int(self._get_config('reversal_signal_window_minutes', 180))
        cutoff_time = datetime.now() - timedelta(minutes=signal_window)
        
        high_score_events = self.db.query(RSSEvent).filter(
            RSSEvent.event_type == 'political',
            RSSEvent.impact_score >= 6,
            RSSEvent.fetched_at >= cutoff_time
        ).order_by(RSSEvent.impact_score.desc()).limit(3).all()
        
        if high_score_events:
            # 信号强度: 基于事件评分计算（6-10分 → 0.6-1.0强度）
            avg_score = sum(e.impact_score for e in high_score_events) / len(high_score_events)
            signal_strength = (avg_score - 5) / 5.0  # 归一化到0-1范围
            
            titles = ' | '.join([e.title[:50] + '...' if len(e.title) > 50 else e.title 
                                for e in high_score_events])
            return 1, f"政治事件(评分{avg_score:.1f}): {titles}", signal_strength
        
        return 0, "无高分政治事件", 0.0
    
    def detect_war_condition(self) -> tuple[int, str, float]:
        """
        检测战争条件
        
        Returns:
            (信号值, 说明文本, 信号强度)
        """
        signal_window = int(self._get_config('reversal_signal_window_minutes', 180))
        cutoff_time = datetime.now() - timedelta(minutes=signal_window)
        
        high_score_events = self.db.query(RSSEvent).filter(
            RSSEvent.event_type == 'war',
            RSSEvent.impact_score >= 6,
            RSSEvent.fetched_at >= cutoff_time
        ).order_by(RSSEvent.impact_score.desc()).limit(3).all()
        
        if high_score_events:
            # 信号强度: 基于事件评分计算
            avg_score = sum(e.impact_score for e in high_score_events) / len(high_score_events)
            signal_strength = (avg_score - 5) / 5.0
            
            titles = ' | '.join([e.title[:50] + '...' if len(e.title) > 50 else e.title 
                                for e in high_score_events])
            return 1, f"战争进度(评分{avg_score:.1f}): {titles}", signal_strength
        
        return 0, "无高分战争事件", 0.0
    
    def detect_us10y_condition(self) -> tuple[int, str, float]:
        """
        检测美债条件
        
        Returns:
            (信号值, 说明文本, 信号强度)
        """
        lookback_hours = self._get_config('us10y_drop_lookback_hours', 24.0)
        threshold_bp = self._get_config('us10y_drop_threshold_bp', 1.0)

        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)

        latest = self.db.query(USTreasury).filter(
            USTreasury.tenor == '10y'
        ).order_by(USTreasury.fetched_at.desc()).first()

        if not latest:
            return 0, "无美债数据", 0.0

        max_yield = self.db.query(func.max(USTreasury.yield_pct)).filter(
            USTreasury.fetched_at >= cutoff_time,
            USTreasury.tenor == '10y'
        ).scalar()
        
        if not max_yield:
            return 0, "历史数据不足", 0.0
        
        drop_bp = (max_yield - latest.yield_pct) * 100
        
        # 信号强度: 下跌幅度越大，信号越强
        signal_strength = min(drop_bp / threshold_bp, 2.0)  # 最大2.0
        
        signal = 1 if drop_bp >= threshold_bp else 0
        note = f"10Y: 现值 {latest.yield_pct:.3f}% / 高点 {max_yield:.3f}% / {lookback_hours}h回落 {drop_bp:.2f}bp (阈值 {threshold_bp:.2f}bp)"
        
        return signal, note, signal_strength
    
    def determine_reversal_level_v2(self, 
                                    price_signal: int, 
                                    political_signal: int, 
                                    war_signal: int, 
                                    us10y_signal: int,
                                    price_strength: float = 1.0,
                                    political_strength: float = 1.0,
                                    war_strength: float = 1.0,
                                    us10y_strength: float = 1.0) -> tuple[int, str]:
        """
        确定反转等级（V2版本 - 更直观的等级定义）
        
        新逻辑:
        - Level 0: 无信号 - 无反转迹象
        - Level 1: 1个信号 - 弱信号，观察阶段
        - Level 2: 2个信号 - 中等信号，关注阶段
        - Level 3: 3个信号 - 强信号，准备行动 [开始推送]
        - Level 4: 4个信号 - 极强信号，立即行动 [优先推送]
        
        推送策略:
        - Level 3/4: 推送告警
        - Level 1/2: 仅记录，不推送
        - Level 0: 无信号，不记录
        
        Args:
            *_signal: 各类信号值 (0/1)
            *_strength: 各类信号强度 (0.0-2.0)
            
        Returns:
            (反转等级, 等级说明)
        """
        # 统计触发的信号数量
        signal_count = price_signal + political_signal + war_signal + us10y_signal
        
        # 基础等级 = 信号数量
        level = signal_count
        
        # 构建触发信号列表
        triggered = []
        if price_signal: triggered.append(f'价格(强度{price_strength:.1f})')
        if political_signal: triggered.append(f'政治(强度{political_strength:.1f})')
        if war_signal: triggered.append(f'战争(强度{war_strength:.1f})')
        if us10y_signal: triggered.append(f'美债(强度{us10y_strength:.1f})')
        
        # 等级说明
        level_descriptions = {
            0: "无信号 - 无反转迹象",
            1: "弱信号 - 观察阶段 (1个信号触发)",
            2: "中等信号 - 关注阶段 (2个信号触发)",
            3: "强信号 - 准备行动 (3个信号触发) [推送]",
            4: "极强信号 - 立即行动 (4个信号触发) [推送]"
        }
        
        description = level_descriptions.get(level, "未知等级")
        
        reversal_logger.info(f"反转等级判定: Level {level} - {description}")
        if triggered:
            reversal_logger.info(f"触发信号: {', '.join(triggered)}")
        
        return level, description
    
    def determine_reversal_level_weighted(self, 
                                          signals: Dict[str, int],
                                          strengths: Dict[str, float]) -> tuple[int, str, float]:
        """
        确定反转等级（加权版本 - 考虑信号强度）
        
        改进点:
        - 使用加权评分系统，而非简单计数
        - 不同信号有不同权重（价格25%、政治25%、战争25%、美债25%）
        - 信号强度也参与计算
        
        评分规则:
        - 0-20分: Level 0 (无信号)
        - 21-40分: Level 1 (弱信号)
        - 41-60分: Level 2 (中等信号)
        - 61-80分: Level 3 (强信号) [推送]
        - 81-100分: Level 4 (极强信号) [推送]
        
        Args:
            signals: 各类信号值字典
            strengths: 各类信号强度字典
            
        Returns:
            (反转等级, 等级说明, 综合评分)
        """
        # 信号权重配置（可调整）
        weights = {
            'price': 25.0,      # 价格信号权重25%
            'political': 25.0,  # 政治信号权重25%
            'war': 25.0,        # 战争信号权重25%
            'us10y': 25.0       # 美债信号权重25%
        }
        
        # 计算加权评分
        weighted_score = 0.0
        for signal_type, weight in weights.items():
            signal = signals.get(signal_type, 0)
            strength = strengths.get(signal_type, 0.0)
            
            # 信号触发时，权重 × 信号强度
            if signal == 1:
                contribution = weight * min(strength, 1.0)  # 强度限制在0-1
                weighted_score += contribution
                reversal_logger.debug(f"{signal_type}信号贡献: {contribution:.2f}分 (权重{weight}, 强度{strength:.2f})")
        
        # 根据综合评分确定等级
        if weighted_score >= 81:
            level = 4
            description = f"极强信号 (评分{weighted_score:.0f}/100) [立即推送]"
        elif weighted_score >= 61:
            level = 3
            description = f"强信号 (评分{weighted_score:.0f}/100) [推送]"
        elif weighted_score >= 41:
            level = 2
            description = f"中等信号 (评分{weighted_score:.0f}/100) [关注]"
        elif weighted_score >= 21:
            level = 1
            description = f"弱信号 (评分{weighted_score:.0f}/100) [观察]"
        else:
            level = 0
            description = f"无信号 (评分{weighted_score:.0f}/100)"
        
        reversal_logger.info(f"加权评分判定: Level {level} - {description}")
        
        return level, description, weighted_score
    
    async def detect_and_save_v2(self, use_weighted: bool = False) -> Dict:
        """
        执行反转检测并保存结果（V2版本）
        
        Args:
            use_weighted: 是否使用加权评分系统（默认False，使用简单计数）
        
        Returns:
            检测结果
        """
        start_time = datetime.now()
        reversal_logger.debug("开始反转检测 (V2版本)")
        
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
            
            # 执行四类条件检测（获取信号、说明、强度）
            price_signal, price_note, price_strength = self.detect_price_condition()
            political_signal, political_note, political_strength = self.detect_political_condition()
            war_signal, war_note, war_strength = self.detect_war_condition()
            us10y_signal, us10y_note, us10y_strength = self.detect_us10y_condition()
            
            reversal_logger.debug(
                f"信号检测结果 - Price: {price_signal}(强度{price_strength:.2f}) - "
                f"Political: {political_signal}(强度{political_strength:.2f}) - "
                f"War: {war_signal}(强度{war_strength:.2f}) - "
                f"US10Y: {us10y_signal}(强度{us10y_strength:.2f})"
            )
            
            # 确定反转等级（选择判定方法）
            if use_weighted:
                # 使用加权评分系统
                signals = {
                    'price': price_signal,
                    'political': political_signal,
                    'war': war_signal,
                    'us10y': us10y_signal
                }
                strengths = {
                    'price': price_strength,
                    'political': political_strength,
                    'war': war_strength,
                    'us10y': us10y_strength
                }
                signal_level, level_description, weighted_score = self.determine_reversal_level_weighted(
                    signals, strengths
                )
            else:
                # 使用简单计数系统
                signal_level, level_description = self.determine_reversal_level_v2(
                    price_signal, political_signal, war_signal, us10y_signal,
                    price_strength, political_strength, war_strength, us10y_strength
                )
            
            # 构建触发条件列表
            triggered = []
            if price_signal: triggered.append('price')
            if political_signal: triggered.append('political')
            if war_signal: triggered.append('war')
            if us10y_signal: triggered.append('us10y')
            
            triggered_conditions = ','.join(triggered) if triggered else ''
            
            # 构建note
            note_parts = [f"[V2] {level_description}"]
            note_parts.append(f"盘面: {price_note}")
            note_parts.append(f"{us10y_note}")
            if political_note != "无高分政治事件":
                note_parts.append(political_note)
            if war_note != "无高分战争事件":
                note_parts.append(war_note)
            
            note = ' | '.join(note_parts)
            
            # 保存检测结果（复用原表结构）
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
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            reversal_logger.info(
                f"反转检测完成 (V2) - 耗时: {duration_ms}ms - {level_description} - "
                f"触发条件: {triggered_conditions or '无'}"
            )
            
            return {
                'success': True,
                'message': '反转检测完成 (V2版本)',
                'duration_ms': duration_ms,
                'data': {
                    'signal_level': signal_level,
                    'level_description': level_description,
                    'price_signal': price_signal,
                    'political_signal': political_signal,
                    'war_signal': war_signal,
                    'us10y_signal': us10y_signal,
                    'triggered_conditions': triggered_conditions,
                    'note': note,
                    'signal_strengths': {
                        'price': price_strength,
                        'political': political_strength,
                        'war': war_strength,
                        'us10y': us10y_strength
                    }
                }
            }
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            reversal_logger.error(f"反转检测失败 (V2) - 耗时: {duration_ms}ms - 错误: {str(e)}", exc_info=True)
            
            return {
                'success': False,
                'message': f'反转检测失败: {str(e)}',
                'duration_ms': duration_ms,
                'data': None
            }
    
    def should_push_alert(self, signal_level: int) -> bool:
        """
        判断是否应该推送警报（V2版本 - 更清晰的推送策略）
        
        推送规则:
        - Level 3/4: 推送（强信号和极强信号）
        - Level 0/1/2: 不推送（无信号、弱信号、中等信号）
        
        Args:
            signal_level: 信号等级
            
        Returns:
            是否应该推送
        """
        # Level 3/4才推送
        if signal_level < 3:
            return False
        
        # 检查冷却期
        cooldown_seconds = int(self._get_config('reversal_cooldown_seconds', 1800))
        cooldown_time = datetime.now() - timedelta(seconds=cooldown_seconds)
        recent_alert = self.db.query(AlertHistory).filter(
            AlertHistory.alert_type == 'reversal',
            AlertHistory.created_at >= cooldown_time
        ).first()
        
        return recent_alert is None
    
    def create_alert_v2(self, reversal_data: Dict) -> Dict:
        """
        创建反转警报（V2版本）
        
        Args:
            reversal_data: 反转数据
            
        Returns:
            警报内容
        """
        level = reversal_data['signal_level']
        conditions = reversal_data['triggered_conditions']
        level_desc = reversal_data.get('level_description', '')
        
        # 等级名称映射
        level_names = {
            4: '🔴 极强信号 - 立即行动',
            3: '🟠 强信号 - 准备行动',
            2: '🟡 中等信号 - 持续关注',
            1: '🟢 弱信号 - 观察阶段',
            0: '⚪ 无信号'
        }
        
        level_name = level_names.get(level, '未知等级')
        
        # 构建警报内容
        content_parts = [
            f"反转等级: Level {level}",
            f"等级描述: {level_name}",
            f"等级说明: {level_desc}",
            f"触发信号: {conditions}",
            f"金价: {reversal_data.get('gold_price_usd_per_oz', 0):.2f} 美元/盎司",
            ""
        ]
        
        # 添加信号强度信息
        if 'signal_strengths' in reversal_data:
            strengths = reversal_data['signal_strengths']
            content_parts.append("各信号强度:")
            if strengths.get('price', 0) > 0:
                content_parts.append(f"  - 价格信号: {strengths['price']:.2f}")
            if strengths.get('political', 0) > 0:
                content_parts.append(f"  - 政治信号: {strengths['political']:.2f}")
            if strengths.get('war', 0) > 0:
                content_parts.append(f"  - 战争信号: {strengths['war']:.2f}")
            if strengths.get('us10y', 0) > 0:
                content_parts.append(f"  - 美债信号: {strengths['us10y']:.2f}")
        
        return {
            'alert_type': '黄金反转预警 V2',
            'level': level,
            'level_name': level_name,
            'content': '\n'.join(content_parts),
            'timestamp': datetime.now()
        }
