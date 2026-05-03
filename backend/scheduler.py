"""
任务调度器
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from sqlalchemy.orm import Session

from .database import SessionLocal, SchedulerStatus, SystemConfig
from .services import (
    SGEMonitorService,
    US10YMonitorService,
    RSSCollectorService,
    ReversalDetectorService
)
from .utils import scheduler_logger, metrics

# 导入V2版本检测器
try:
    from .services.reversal_detector_v2 import ReversalDetectorServiceV2
    V2_AVAILABLE = True
    scheduler_logger.info("反转检测器V2已加载")
except ImportError:
    V2_AVAILABLE = False
    scheduler_logger.warning("反转检测器V2未找到，将使用V1版本")


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        # 配置调度器：允许任务并发，优化执行池
        self.scheduler = AsyncIOScheduler(
            job_defaults={
                'coalesce': True,  # 合并堆积的任务
                'max_instances': 1,  # 同一任务最多1个实例
                'misfire_grace_time': 15  # 任务错过时间容限15秒
            }
        )
        self.db: Session = None
        self.sge_last_fetch_time = None  # 记录上次SGE采集时间
    
    def start(self):
        """启动调度器"""
        scheduler_logger.info("=" * 60)
        scheduler_logger.info("任务调度器启动中...")
        scheduler_logger.info("=" * 60)
        
        # SGE监控任务 - 动态调整频率（开市60秒，休市300秒）
        self.scheduler.add_job(
            self.sge_monitor_task,
            trigger=IntervalTrigger(seconds=60),
            id='sge_monitor',
            name='SGE价格监控',
            replace_existing=True,
            max_instances=1,  # 防止任务并发执行
            coalesce=True     # 合并错过的任务
        )
        scheduler_logger.info("已注册任务: SGE价格监控 (60秒/次)")

        # 美债监控任务 - 每60秒执行一次
        self.scheduler.add_job(
            self.us10y_monitor_task,
            trigger=IntervalTrigger(seconds=60),
            id='us10y_monitor',
            name='美债收益率监控',
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        scheduler_logger.info("已注册任务: 美债收益率监控 (60秒/次)")
        
        # RSS采集任务 - 每15分钟执行一次
        self.scheduler.add_job(
            self.rss_collector_task,
            trigger=IntervalTrigger(minutes=15),
            id='rss_collector',
            name='RSS事件采集',
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        scheduler_logger.info("已注册任务: RSS事件采集 (15分钟/次)")
        
        # 反转检测任务 - 每1分钟执行一次
        self.scheduler.add_job(
            self.reversal_detector_task,
            trigger=IntervalTrigger(minutes=1),
            id='reversal_detector',
            name='反转条件检测',
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        scheduler_logger.info("已注册任务: 反转条件检测 (1分钟/次)")
        
        # 启动调度器
        self.scheduler.start()
        scheduler_logger.info("=" * 60)
        scheduler_logger.info("任务调度器已启动！")
        scheduler_logger.info("=" * 60)
    
    def shutdown(self):
        """关闭调度器"""
        scheduler_logger.info("任务调度器正在关闭...")
        self.scheduler.shutdown()
        scheduler_logger.info("任务调度器已关闭")
    
    async def sge_monitor_task(self):
        """SGE监控任务 - 支持休市时降低采集频率"""
        start_time = datetime.now()
        
        # 计算实际采集间隔
        if self.sge_last_fetch_time:
            actual_interval = (start_time - self.sge_last_fetch_time).total_seconds()
            scheduler_logger.debug(f"SGE监控任务开始 - 距离上次: {actual_interval:.1f}秒")
            metrics.set_sge_frequency(actual_interval)
        else:
            scheduler_logger.debug("SGE监控任务首次执行")
        
        self.sge_last_fetch_time = start_time
        
        db = SessionLocal()
        try:
            # 更新任务状态
            self._update_task_status(db, 'sge_monitor', 'running')
            
            # 执行监控
            async with SGEMonitorService(db) as service:
                result = await service.fetch_and_save_data()
                
                duration_ms = result.get('duration_ms', 0)
                duration_seconds = duration_ms / 1000.0
                
                # 记录Prometheus指标
                status = 'success' if result['success'] else 'failed'
                metrics.record_sge_fetch(status, duration_seconds, result.get('data'))
                
                if result.get('market_status'):
                    metrics.record_market_status(result['market_status'])
                
                scheduler_logger.info(f"SGE数据采集完成 - 耗时: {duration_ms}ms - 状态: {result.get('message')}")
                
                # 检查市场状态，动态调整采集频率
                if result.get('market_status'):
                    both_open = result['market_status'].get('both_markets_open', 0)
                    shfe_open = result['market_status'].get('shfe_market_open', 0)
                    
                    # 动态调整下次执行间隔
                    if both_open == 1:
                        interval_seconds = 60
                        market_desc = "双市场开盘"
                    elif shfe_open == 1:
                        interval_seconds = 120
                        market_desc = "仅沪金开盘"
                    else:
                        interval_seconds = 300
                        market_desc = "休市"
                    
                    # 检查调度器是否正在运行
                    if not self.scheduler or not self.scheduler.running:
                        scheduler_logger.debug(f"调度器未运行，跳过频率调整")
                    else:
                        # 获取当前任务的触发器间隔
                        job = self.scheduler.get_job('sge_monitor')
                        
                        if job and hasattr(job.trigger, 'interval'):
                            current_interval = job.trigger.interval.total_seconds()
                            
                            # 只有间隔改变时才重新调度
                            if abs(current_interval - interval_seconds) > 1:
                                try:
                                    self.scheduler.reschedule_job(
                                        'sge_monitor',
                                        trigger=IntervalTrigger(seconds=interval_seconds)
                                    )
                                    scheduler_logger.info(
                                        f"SGE采集频率已调整: {int(current_interval)}秒 → {interval_seconds}秒 "
                                        f"(市场状态: {market_desc})"
                                    )
                                except Exception as e:
                                    scheduler_logger.warning(f"频率调整失败: {str(e)}")
                            else:
                                scheduler_logger.debug(f"SGE采集频率保持: {interval_seconds}秒 (市场状态: {market_desc})")
                        else:
                            scheduler_logger.warning(f"无法获取SGE任务信息，跳过频率调整")
                
                # 检查是否需要推送警报
                if result['success']:
                    alert = service.check_premium_alert()
                    if alert:
                        scheduler_logger.warning(f"检测到SGE溢价警报: {alert.get('content')}")
                        await self._send_alert(alert)
            
            # 更新任务状态
            self._update_task_status(db, 'sge_monitor', 'success')
            
            total_duration = int((datetime.now() - start_time).total_seconds() * 1000)
            scheduler_logger.debug(f"SGE监控任务完成 - 总耗时: {total_duration}ms")
            
        except Exception as e:
            total_duration = int((datetime.now() - start_time).total_seconds() * 1000)
            scheduler_logger.error(f"SGE监控任务执行失败 - 耗时: {total_duration}ms - 错误: {str(e)}", exc_info=True)
            self._update_task_status(db, 'sge_monitor', 'failed', str(e))
        finally:
            db.close()
    
    async def us10y_monitor_task(self):
        """美债监控任务 - 支持多期限(5Y/10Y/20Y)"""
        start_time = datetime.now()
        scheduler_logger.debug("美债监控任务开始执行")
        
        db = SessionLocal()
        try:
            # 更新任务状态
            self._update_task_status(db, 'us10y_monitor', 'running')

            # 执行监控 - 采集所有期限
            async with US10YMonitorService(db) as service:
                for tenor in ['5y', '10y', '20y']:
                    result = await service.fetch_and_save_data(tenor)
                    
                    duration_seconds = result.get('duration_ms', 0) / 1000.0
                    status = 'success' if result['success'] else 'failed'
                    
                    # 记录Prometheus指标
                    metrics.record_us10y_fetch(
                        tenor, 
                        status, 
                        duration_seconds, 
                        result.get('data', {}).get('yield_pct') if result['success'] else None
                    )
                    
                    if result['success']:
                        scheduler_logger.info(f"美债数据采集成功 - 期限: {tenor} - 耗时: {result.get('duration_ms', 0)}ms")
                        
                        # 检查是否需要推送警报
                        alert = service.detect_yield_drop()
                        if alert:
                            scheduler_logger.warning(f"检测到美债收益率警报: {tenor}")
                            await self._send_alert(alert)
                    else:
                        scheduler_logger.warning(f"美债数据采集失败 - 期限: {tenor} - 错误: {result.get('message')}")

            # 更新任务状态
            self._update_task_status(db, 'us10y_monitor', 'success')
            
            total_duration = int((datetime.now() - start_time).total_seconds() * 1000)
            scheduler_logger.debug(f"美债监控任务完成 - 总耗时: {total_duration}ms")

        except Exception as e:
            total_duration = int((datetime.now() - start_time).total_seconds() * 1000)
            scheduler_logger.error(f"美债监控任务执行失败 - 耗时: {total_duration}ms - 错误: {str(e)}", exc_info=True)
            self._update_task_status(db, 'us10y_monitor', 'failed', str(e))
        finally:
            db.close()
    
    async def rss_collector_task(self):
        """RSS采集任务"""
        start_time = datetime.now()
        scheduler_logger.debug("RSS采集任务开始执行")
        
        db = SessionLocal()
        try:
            # 更新任务状态
            self._update_task_status(db, 'rss_collector', 'running')
            
            # 执行采集
            async with RSSCollectorService(db) as service:
                result = await service.collect_all()
                
                duration_ms = result.get('duration_ms', 0)
                duration_seconds = duration_ms / 1000.0
                new_events = result.get('total_new_events', 0)
                error_count = result.get('error_count', 0)
                
                # 记录Prometheus指标（按源记录）
                for source_result in result.get('results', []):
                    source_name = source_result.get('source', 'unknown')
                    source_status = 'success' if source_result.get('success') else 'failed'
                    metrics.rss_collect_total.labels(source=source_name, status=source_status).inc()
                
                scheduler_logger.info(
                    f"RSS采集完成 - 耗时: {duration_ms}ms - 新增事件: {new_events} - 错误源: {error_count}"
                )
                
                # 高分事件仅记录日志（系统不对外推送）
                if result['success']:
                    high_score_events = service.get_high_score_events(6)
                    if high_score_events:
                        scheduler_logger.info(
                            f"发现 {len(high_score_events)} 个高分RSS事件（仅站内数据，不推送）"
                        )
            
            # 更新任务状态
            self._update_task_status(db, 'rss_collector', 'success')
            
            total_duration = int((datetime.now() - start_time).total_seconds() * 1000)
            scheduler_logger.debug(f"RSS采集任务完成 - 总耗时: {total_duration}ms")
            
        except Exception as e:
            total_duration = int((datetime.now() - start_time).total_seconds() * 1000)
            scheduler_logger.error(f"RSS采集任务执行失败 - 耗时: {total_duration}ms - 错误: {str(e)}", exc_info=True)
            self._update_task_status(db, 'rss_collector', 'failed', str(e))
        finally:
            db.close()
    
    async def reversal_detector_task(self):
        """反转检测任务（支持V1/V2版本切换）"""
        start_time = datetime.now()
        scheduler_logger.debug("反转检测任务开始执行")
        
        db = SessionLocal()
        try:
            # 更新任务状态
            self._update_task_status(db, 'reversal_detector', 'running')
            
            # 读取版本配置
            version_config = db.query(SystemConfig).filter_by(
                config_key='reversal_detector_version'
            ).first()
            version = version_config.config_value if version_config else 'v1'
            
            # 根据配置选择版本
            if V2_AVAILABLE and version in ['v2', 'v2_weighted']:
                scheduler_logger.debug(f"使用反转检测器版本: {version}")
                service = ReversalDetectorServiceV2(db)
                use_weighted = (version == 'v2_weighted')
                result = await service.detect_and_save_v2(use_weighted=use_weighted)
            else:
                if version not in ['v1']:
                    scheduler_logger.warning(f"未知版本'{version}'，使用V1版本")
                scheduler_logger.debug("使用反转检测器版本: v1")
                service = ReversalDetectorService(db)
                result = await service.detect_and_save()
            
            duration_ms = result.get('duration_ms', 0)
            duration_seconds = duration_ms / 1000.0
            status = 'success' if result['success'] else 'failed'
            
            # 记录Prometheus指标
            metrics.record_reversal_detect(status, duration_seconds, result.get('data'))
            
            if result['success'] and result.get('data'):
                data = result['data']
                signal_level = data.get('signal_level', 0)
                triggered = data.get('triggered_conditions', '')
                
                scheduler_logger.info(
                    f"反转检测完成 - 耗时: {duration_ms}ms - 等级: Level {signal_level} - 触发条件: {triggered or '无'}"
                )
                
                # 根据版本选择推送策略
                should_push = False
                if version in ['v2', 'v2_weighted']:
                    # V2推送策略: Level 3/4推送
                    should_push = (signal_level >= 3)
                    if should_push:
                        alert = service.create_alert_v2(data)
                        scheduler_logger.warning(f"检测到Level {signal_level}反转信号 (V2) - {data.get('level_description', '')}")
                else:
                    # V1推送策略: Level 2及以上推送
                    should_push = (signal_level >= 2)
                    if should_push:
                        alert = service.create_alert(data)
                        scheduler_logger.warning(f"检测到Level {signal_level}反转信号 (V1)")
                
                if should_push and alert:
                    await self._send_alert(alert)
            else:
                scheduler_logger.warning(f"反转检测失败: {result.get('message')}")
            
            # 更新任务状态
            self._update_task_status(db, 'reversal_detector', 'success')
            
            total_duration = int((datetime.now() - start_time).total_seconds() * 1000)
            scheduler_logger.debug(f"反转检测任务完成 - 总耗时: {total_duration}ms")
            
        except Exception as e:
            total_duration = int((datetime.now() - start_time).total_seconds() * 1000)
            scheduler_logger.error(f"反转检测任务执行失败 - 耗时: {total_duration}ms - 错误: {str(e)}", exc_info=True)
            self._update_task_status(db, 'reversal_detector', 'failed', str(e))
        finally:
            db.close()
    
    def _update_task_status(self, db: Session, task_name: str, status: str, error_message: str = None):
        """
        更新任务状态
        
        Args:
            db: 数据库会话
            task_name: 任务名称
            status: 状态
            error_message: 错误消息
        """
        task = db.query(SchedulerStatus).filter_by(task_name=task_name).first()
        
        if task:
            if status == 'running':
                task.last_run_at = datetime.now()
            
            task.status = status
            task.error_message = error_message
            task.updated_at = datetime.now()
            
            # 计算下次运行时间（简化版本）
            if status == 'success' or status == 'failed':
                from datetime import timedelta
                intervals = {
                    'sge_monitor': 1,
                    'us10y_monitor': 1,
                    'rss_collector': 15,
                    'reversal_detector': 1
                }
                interval = intervals.get(task_name, 5)
                task.next_run_at = datetime.now() + timedelta(minutes=interval)
            
            db.commit()
    
    async def _send_alert(self, alert: dict):
        """警报仅写日志，不调用任何外部消息推送。"""
        preview = (alert.get('content') or '')[:200]
        scheduler_logger.warning(
            f"[警报·仅日志] {alert.get('alert_type', 'alert')} | "
            f"level={alert.get('level')} | {preview}"
        )


# 全局调度器实例
scheduler = TaskScheduler()
