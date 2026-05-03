"""
API路由 - 完全匹配原系统
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime, timedelta

from ..database import get_db, SystemConfig, SGEPrice, USTreasury, RSSEvent, RSSSource, ReversalCondition, UpdateRecord, PushLog, AlertHistory
from ..services import SGEMonitorService, US10YMonitorService, RSSCollectorService, ReversalDetectorService
from ..utils.cache import get_cache

router = APIRouter()
cache = get_cache()


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/ping")
async def ping():
    """极简端点（无数据库查询）"""
    return {"pong": datetime.now().isoformat()}


@router.get("/api/db_test")
async def db_test(db: Session = Depends(get_db)):
    """测试单次数据库查询"""
    latest = db.query(SGEPrice).order_by(SGEPrice.fetched_at.desc()).first()
    return {
        "id": latest.id if latest else None,
        "time": latest.fetched_at.isoformat() if latest else None
    }


@router.get("/api/status")
async def get_system_status(db: Session = Depends(get_db)):
    """
    获取系统状态（完全匹配原系统格式）
    """
    # 尝试从缓存获取静态配置（30秒TTL）
    cache_key = "status:static_config"
    cached_config = cache.get(cache_key)
    
    if cached_config:
        config_dict = cached_config['config_dict']
        rss_feed_sources = cached_config['rss_feed_sources']
    else:
        # 获取所有配置
        configs = db.query(SystemConfig).all()
        config_dict = {c.config_key: c.config_value for c in configs}
        
        # 获取RSS源完整信息
        rss_sources = db.query(RSSSource).all()
        rss_feed_sources = [{
            'id': rs.id,
            'name': rs.name,
            'url': rs.url,
            'category': rs.category,
            'enabled': bool(rs.is_active)
        } for rs in rss_sources]
        
        # 缓存静态配置（不含任何推送凭据）
        cache.set(cache_key, {
            'config_dict': config_dict,
            'rss_feed_sources': rss_feed_sources,
        }, ttl_seconds=30)
    
    # 构建settings（系统不配置外发消息推送）
    settings = {
        'notification_targets': [],
        'premium_threshold': float(config_dict.get('premium_threshold', 20.0)),
        'poll_interval_seconds': int(config_dict.get('poll_interval_seconds', 60)),
        'alert_cooldown_seconds': int(config_dict.get('alert_cooldown_seconds', 900)),
        'request_timeout_seconds': float(config_dict.get('request_timeout_seconds', 10.0)),
        'reversal_cooldown_seconds': int(config_dict.get('reversal_cooldown_seconds', 1800)),
        'reversal_price_lookback_minutes': int(config_dict.get('reversal_price_lookback_minutes', 60)),
        'reversal_price_rebound_pct': float(config_dict.get('reversal_price_rebound_pct', 1.2)),
        'reversal_price_ma_window': int(config_dict.get('reversal_price_ma_window', 15)),
        'reversal_signal_window_minutes': int(config_dict.get('reversal_signal_window_minutes', 180)),
        'us10y_poll_interval_seconds': int(config_dict.get('poll_interval_seconds', 60)),
        'us10y_drop_lookback_hours': float(config_dict.get('us10y_drop_lookback_hours', 24.0)),
        'us10y_drop_threshold_bp': float(config_dict.get('us10y_drop_threshold_bp', 1.0)),
        'us10y_tenors': ['10y'],
        'rss_poll_interval_seconds': int(config_dict.get('rss_poll_interval_seconds', 1800)),
        'rss_feed_sources': rss_feed_sources
    }
    
    # 市场状态
    market_state = {
        'sge': {
            'active': True,
            'label': '运行中',
            'detail': '国内金或国际金有可用价格源'
        },
        'reversal': {
            'active': True,
            'label': '运行中',
            'detail': '黄金盘面监控可用'
        },
        'us10y': {
            'active': True,
            'label': '可用',
            'detail': '十年期美债数据源可用（Sina优先，FRED回退）'
        },
        'rss': {
            'active': True,
            'label': '可用',
            'detail': 'RSS 手动抓取和定时抓取配置可用'
        }
    }
    
    # 获取最新SGE样本
    latest_sample = db.query(SGEPrice).order_by(SGEPrice.fetched_at.desc()).first()
    latest_sample_dict = None
    if latest_sample:
        latest_sample_dict = {
            'id': latest_sample.id,
            'fetched_at': latest_sample.fetched_at.isoformat(),
            'shfe_price_cny_per_g': latest_sample.shfe_price_cny_per_g,
            'london_price_usd_per_oz': latest_sample.london_price_usd_per_oz,
            'usdcny_rate': latest_sample.usdcny_rate,
            'london_price_cny_per_g': latest_sample.london_price_cny_per_g,
            'premium_cny_per_g': latest_sample.premium_cny_per_g,
            'poll_interval_seconds': latest_sample.poll_interval_seconds,
            'both_markets_open': latest_sample.both_markets_open,
            'shfe_market_open': latest_sample.shfe_market_open,
            'london_market_open': latest_sample.london_market_open,
            'alert_triggered': latest_sample.alert_triggered,
            'raw_payload': latest_sample.raw_payload,
            'note': latest_sample.note
        }
    
    # 获取最近警报（暂时为空）
    recent_alerts = []
    
    # 获取最近抓取运行记录
    recent_fetch_runs = db.query(UpdateRecord).filter_by(
        data_type='sge_price'
    ).order_by(UpdateRecord.created_at.desc()).limit(10).all()
    
    recent_fetch_runs_list = [{
        'id': r.id,
        'fetched_at': r.created_at.isoformat(),
        'success': 1 if r.status == 'success' else 0,
        'poll_interval_seconds': int(config_dict.get('poll_interval_seconds', 60)),
        'duration_ms': 2000,  # 估算值
        'error_message': r.error_message
    } for r in recent_fetch_runs]
    
    # 获取最近样本
    recent_samples = db.query(SGEPrice).order_by(SGEPrice.fetched_at.desc()).limit(20).all()
    recent_samples_list = [{
        'id': r.id,
        'fetched_at': r.fetched_at.isoformat(),
        'shfe_price_cny_per_g': r.shfe_price_cny_per_g,
        'london_price_usd_per_oz': r.london_price_usd_per_oz,
        'usdcny_rate': r.usdcny_rate,
        'london_price_cny_per_g': r.london_price_cny_per_g,
        'premium_cny_per_g': r.premium_cny_per_g,
        'poll_interval_seconds': r.poll_interval_seconds,
        'both_markets_open': r.both_markets_open,
        'shfe_market_open': r.shfe_market_open,
        'london_market_open': r.london_market_open,
        'alert_triggered': r.alert_triggered,
        'raw_payload': r.raw_payload,
        'note': r.note
    } for r in recent_samples]
    
    # 获取反转数据
    latest_reversal = db.query(ReversalCondition).order_by(ReversalCondition.fetched_at.desc()).first()
    latest_reversal_dict = None
    if latest_reversal:
        latest_reversal_dict = {
            'id': latest_reversal.id,
            'fetched_at': latest_reversal.fetched_at.isoformat(),
            'gold_price_usd_per_oz': latest_reversal.gold_price_usd_per_oz,
            'usdcny_rate': latest_reversal.usdcny_rate,
            'price_signal': latest_reversal.price_signal,
            'political_signal': latest_reversal.political_signal,
            'war_signal': latest_reversal.war_signal,
            'us10y_signal': latest_reversal.us10y_signal,
            'signal_level': latest_reversal.signal_level,
            'triggered_conditions': latest_reversal.triggered_conditions,
            'note': latest_reversal.note
        }
    
    # 获取反转警报历史
    reversal_alerts = db.query(AlertHistory).filter_by(
        alert_type='reversal'
    ).order_by(AlertHistory.created_at.desc()).limit(10).all()
    
    reversal_alerts_list = [{
        'id': a.id,
        'sample_id': a.related_id,
        'sent_at': a.created_at.isoformat(),
        'signal_level': a.level,
        'triggered_conditions': a.content.split('触发条件: ')[1].split('\n')[0] if '触发条件: ' in a.content else '',
        'success': 1 if a.status == 'success' else 0,
        'response_text': a.response_text or '',
    } for a in reversal_alerts]
    
    # 获取反转运行记录
    reversal_runs = db.query(UpdateRecord).filter_by(
        data_type='reversal'
    ).order_by(UpdateRecord.created_at.desc()).limit(10).all()
    
    reversal_runs_list = [{
        'id': r.id,
        'fetched_at': r.created_at.isoformat(),
        'success': 1 if r.status == 'success' else 0,
        'poll_interval_seconds': int(config_dict.get('poll_interval_seconds', 60)),
        'duration_ms': 1500,
        'rss_error_count': 0,
        'error_message': r.error_message
    } for r in reversal_runs]
    
    # 获取最近RSS事件
    recent_rss_events = db.query(RSSEvent).order_by(RSSEvent.fetched_at.desc()).limit(15).all()
    recent_rss_events_list = [{
        'id': e.id,
        'fetched_at': e.fetched_at.isoformat(),
        'published_at': e.published_at.isoformat() if e.published_at else None,
        'source': e.source.name if e.source else 'Unknown',
        'feed_url': e.feed_url,
        'title': e.title,
        'link': e.link,
        'summary': e.summary,
        'event_type': e.event_type,
        'matched_keywords': e.matched_keywords,
        'content_hash': e.content_hash,
        'impact_score': e.impact_score,
        'impact_level': e.impact_level,
        'impact_note': e.impact_note
    } for e in recent_rss_events]
    
    # 获取RSS抓取记录
    recent_rss_fetch_runs = db.query(UpdateRecord).filter_by(
        data_type='rss_events'
    ).order_by(UpdateRecord.created_at.desc()).limit(10).all()
    
    recent_rss_fetch_runs_list = [{
        'id': r.id,
        'fetched_at': r.created_at.isoformat(),
        'success': 1 if r.status == 'success' else 0,
        'duration_ms': 30000,
        'item_count': r.record_count,
        'error_count': 0,
        'error_message': r.error_message
    } for r in recent_rss_fetch_runs]
    
    # 获取美债数据
    latest_us10y = db.query(USTreasury).order_by(USTreasury.fetched_at.desc()).first()
    latest_us10y_dict = None
    if latest_us10y:
        latest_us10y_dict = {
            'id': latest_us10y.id,
            'fetched_at': latest_us10y.fetched_at.isoformat(),
            'yield_pct': latest_us10y.yield_pct,
            'yield_signal': latest_us10y.yield_signal,
            'source': latest_us10y.source,
            'note': latest_us10y.note,
            'tenor': latest_us10y.tenor
        }
    
    # 获取美债运行记录
    us10y_runs = db.query(UpdateRecord).filter_by(
        data_type='us_treasury'
    ).order_by(UpdateRecord.created_at.desc()).limit(10).all()
    
    us10y_runs_list = [{
        'id': r.id,
        'fetched_at': r.created_at.isoformat(),
        'success': 1 if r.status == 'success' else 0,
        'poll_interval_seconds': int(config_dict.get('poll_interval_seconds', 60)),
        'duration_ms': 5000,
        'error_message': r.error_message,
        'tenor': 'all'
    } for r in us10y_runs]
    
    # 构建响应（完全匹配原系统格式）
    response = {
        'settings': settings,
        'market_state': market_state,
        'latest_sample': latest_sample_dict,
        'recent_alerts': recent_alerts,
        'recent_fetch_runs': recent_fetch_runs_list,
        'recent_samples': recent_samples_list,
        'gold_reversal': {
            'latest_sample': latest_reversal_dict,
            'recent_alerts': reversal_alerts_list,
            'recent_runs': reversal_runs_list,
            'recent_events': recent_rss_events_list,
            'recent_rss_fetch_runs': recent_rss_fetch_runs_list
        },
        'us10y_reversal': {
            'latest_sample': latest_us10y_dict,
            'latest_samples': {
                '10y': latest_us10y_dict
            } if latest_us10y_dict else {},
            'recent_runs': us10y_runs_list
        },
        'scheduler': {
            'running': True,
            'next_run_time': (datetime.now() + timedelta(seconds=int(config_dict.get('poll_interval_seconds', 60)))).isoformat(),
            'rss_next_run_time': (datetime.now() + timedelta(seconds=int(config_dict.get('rss_poll_interval_seconds', 1800)))).isoformat(),
            'us10y_next_run_time': (datetime.now() + timedelta(seconds=int(config_dict.get('poll_interval_seconds', 60)))).isoformat()
        }
    }
    
    return response


@router.post("/api/sge/fetch")
async def fetch_sge_data(db: Session = Depends(get_db)):
    """手动触发SGE数据采集"""
    async with SGEMonitorService(db) as service:
        result = await service.fetch_and_save_data()
        return result


@router.get("/api/sge/latest")
async def get_latest_sge(limit: int = 100, db: Session = Depends(get_db)):
    """获取最新SGE数据"""
    service = SGEMonitorService(db)
    data = service.get_latest_data(limit)
    return {'success': True, 'data': data}


@router.get("/api/sge/stats")
async def get_sge_stats(db: Session = Depends(get_db)):
    """获取SGE统计信息"""
    service = SGEMonitorService(db)
    stats = service.get_premium_stats()
    return {'success': True, 'data': stats}


@router.post("/api/us10y/fetch")
async def fetch_us10y_data(tenor: str = '10y', db: Session = Depends(get_db)):
    """手动触发美债数据采集"""
    async with US10YMonitorService(db) as service:
        result = await service.fetch_and_save_data(tenor)
        return result


@router.get("/api/us10y/latest")
async def get_latest_us10y(limit: int = 100, db: Session = Depends(get_db)):
    """获取最新美债数据"""
    service = US10YMonitorService(db)
    data = service.get_latest_data(limit)
    return {'success': True, 'data': data}


@router.get("/api/us10y/stats")
async def get_us10y_stats(db: Session = Depends(get_db)):
    """获取美债统计信息"""
    service = US10YMonitorService(db)
    stats = service.get_yield_stats()
    return {'success': True, 'data': stats}


@router.post("/api/rss/collect")
async def collect_rss_data(db: Session = Depends(get_db)):
    """手动触发RSS采集"""
    async with RSSCollectorService(db) as service:
        result = await service.collect_all()
        return result


@router.get("/api/rss/events")
async def get_rss_events(
    limit: int = 100,
    event_type: str = None,
    db: Session = Depends(get_db)
):
    """获取RSS事件"""
    service = RSSCollectorService(db)
    data = service.get_recent_events(limit, event_type)
    return {'success': True, 'data': data}


@router.get("/api/rss/high-score")
async def get_high_score_events(
    threshold: int = 7,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取高分RSS事件"""
    service = RSSCollectorService(db)
    data = service.get_high_score_events(threshold, limit)
    return {'success': True, 'data': data}


@router.post("/api/reversal/detect")
async def detect_reversal(db: Session = Depends(get_db)):
    """手动触发反转检测"""
    service = ReversalDetectorService(db)
    result = await service.detect_and_save()
    return result


@router.get("/api/reversal/latest")
async def get_latest_reversal(db: Session = Depends(get_db)):
    """获取最新反转检测结果"""
    service = ReversalDetectorService(db)
    data = service.get_latest_reversal()
    return {'success': True, 'data': data}


@router.get("/api/reversal/history")
async def get_reversal_history(range: str = "1H", db: Session = Depends(get_db)):
    """获取反转历史记录（支持时间范围参数）"""
    service = ReversalDetectorService(db)
    return service.get_reversal_history(range_str=range)


@router.get("/api/config")
async def get_config(db: Session = Depends(get_db)):
    """获取系统配置"""
    configs = db.query(SystemConfig).all()
    return {
        'success': True,
        'data': {c.config_key: c.config_value for c in configs}
    }


@router.post("/api/config")
async def update_config(config_data: Dict, db: Session = Depends(get_db)):
    """更新系统配置"""
    try:
        for key, value in config_data.items():
            config = db.query(SystemConfig).filter_by(config_key=key).first()
            if config:
                config.config_value = str(value)
            else:
                config = SystemConfig(
                    config_key=key,
                    config_value=str(value),
                    description=key
                )
                db.add(config)
        
        db.commit()
        return {'success': True, 'message': '配置更新成功'}
    except Exception as e:
        return {'success': False, 'message': f'配置更新失败: {str(e)}'}


# ==================== 原系统兼容API端点 ====================

@router.get("/api/history")
async def get_history(range: str = "1D", db: Session = Depends(get_db)):
    """获取SGE历史数据（原系统格式）"""
    try:
        # 根据时间范围获取数据
        if range == "1H":
            since = datetime.now() - timedelta(hours=1)
        elif range == "1W":
            since = datetime.now() - timedelta(weeks=1)
        else:  # 1D
            since = datetime.now() - timedelta(days=1)
        
        samples = db.query(SGEPrice).filter(
            SGEPrice.fetched_at >= since
        ).order_by(SGEPrice.fetched_at.asc()).all()
        
        items = [{
            'id': s.id,
            'fetched_at': s.fetched_at.isoformat() if s.fetched_at else None,
            'shfe_price_cny_per_g': s.shfe_price_cny_per_g,
            'london_price_usd_per_oz': s.london_price_usd_per_oz,
            'london_price_cny_per_g': s.london_price_cny_per_g,
            'usdcny_rate': s.usdcny_rate,
            'premium_cny_per_g': s.premium_cny_per_g,
            'alert_triggered': s.alert_triggered,
            'note': s.note
        } for s in samples]
        
        return {'items': items, 'count': len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/alerts")
async def get_alerts(limit: int = 20, db: Session = Depends(get_db)):
    """获取SGE预警记录（原系统格式）"""
    try:
        alerts = db.query(AlertHistory).filter(
            AlertHistory.alert_type == 'sge'
        ).order_by(AlertHistory.created_at.desc()).limit(limit).all()
        
        items = [{
            'id': a.id,
            'sent_at': a.created_at.isoformat() if a.created_at else None,
            'alert_type': a.alert_type,
            'alert_level': a.alert_level,
            'alert_content': a.alert_content,
            'is_pushed': a.is_pushed
        } for a in alerts]
        
        return {'items': items, 'count': len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/notification/logs")
async def get_notification_logs(limit: int = 50, db: Session = Depends(get_db)):
    """获取推送记录（原系统格式）"""
    try:
        logs = db.query(PushLog).order_by(
            PushLog.created_at.desc()
        ).limit(limit).all()
        
        items = [{
            'id': l.id,
            'sent_at': l.created_at.isoformat() if l.created_at else None,
            'event_type': l.message_type,
            'channel': 'none',
            'target_name': l.target.name if l.target else '默认',
            'content': l.message_content,
            'success': l.status == 'success',
            'response_text': l.error_message or 'Success'
        } for l in logs]
        
        return {'items': items, 'count': len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/reversal/status")
async def get_reversal_status(db: Session = Depends(get_db)):
    """获取反转状态（原系统格式）- 优化版"""
    try:
        # 获取最新反转样本（只查询需要的字段）
        latest = db.query(
            ReversalCondition.id,
            ReversalCondition.fetched_at,
            ReversalCondition.gold_price_usd_per_oz,
            ReversalCondition.usdcny_rate,
            ReversalCondition.signal_level,
            ReversalCondition.price_signal,
            ReversalCondition.political_signal,
            ReversalCondition.war_signal,
            ReversalCondition.us10y_signal,
            ReversalCondition.triggered_conditions,
            ReversalCondition.note
        ).order_by(
            ReversalCondition.fetched_at.desc()
        ).first()
        
        # 获取最近的反转预警（只查询需要的字段）
        recent_alerts = db.query(
            AlertHistory.id,
            AlertHistory.created_at,
            AlertHistory.alert_level,
            AlertHistory.alert_content,
            AlertHistory.is_pushed
        ).filter(
            AlertHistory.alert_type == 'reversal'
        ).order_by(AlertHistory.created_at.desc()).limit(20).all()
        
        # 获取最近的RSS事件（只查询需要的字段，优化为20条）
        recent_events = db.query(
            RSSEvent.id,
            RSSEvent.title,
            RSSEvent.summary,
            RSSEvent.link,
            RSSEvent.published_at,
            RSSEvent.fetched_at,
            RSSEvent.event_type,
            RSSEvent.matched_keywords,
            RSSEvent.impact_score,
            RSSEvent.impact_level,
            RSSEvent.impact_note,
            RSSEvent.source_id
        ).order_by(
            RSSEvent.fetched_at.desc(),
            RSSEvent.published_at.desc()
        ).limit(20).all()
        
        # 获取RSS抓取运行记录
        rss_runs = db.query(UpdateRecord).filter_by(
            data_type='rss_events'
        ).order_by(UpdateRecord.created_at.desc()).limit(10).all()
        
        recent_rss_fetch_runs = [{
            'id': r.id,
            'fetched_at': r.created_at.isoformat(),
            'success': 1 if r.status == 'success' else 0,
            'duration_ms': 30000,
            'item_count': r.record_count,
            'error_count': 0,
            'error_message': r.error_message
        } for r in rss_runs]
        
        # 获取反转运行记录
        reversal_runs = db.query(UpdateRecord).filter_by(
            data_type='reversal_detection'
        ).order_by(UpdateRecord.created_at.desc()).limit(10).all()
        
        recent_runs = [{
            'id': r.id,
            'fetched_at': r.created_at.isoformat(),
            'success': 1 if r.status == 'success' else 0,
            'duration_ms': 30000,
            'signal_level': 0,
            'error_message': r.error_message
        } for r in reversal_runs]
        
        latest_sample = None
        if latest:
            latest_sample = {
                'id': latest[0],
                'fetched_at': latest[1].isoformat() if latest[1] else None,
                'gold_price_usd_per_oz': latest[2],
                'usdcny_rate': latest[3],
                'signal_level': latest[4],
                'price_signal': latest[5],
                'political_signal': latest[6],
                'war_signal': latest[7],
                'us10y_signal': latest[8],
                'triggered_conditions': latest[9],
                'note': latest[10]
            }
        
        # 批量查询RSS源名称（避免N+1查询）
        source_ids = [e[11] for e in recent_events]
        source_map = {}
        if source_ids:
            sources = db.query(RSSSource.id, RSSSource.name).filter(
                RSSSource.id.in_(source_ids)
            ).all()
            source_map = {s[0]: s[1] for s in sources}
        
        return {
            'latest_sample': latest_sample,
            'recent_alerts': [{
                'id': a[0],
                'sent_at': a[1].isoformat() if a[1] else None,
                'alert_level': a[2],
                'alert_content': a[3],
                'is_pushed': a[4]
            } for a in recent_alerts],
            'recent_events': [{
                'id': e[0],
                'title': e[1],
                'summary': e[2],
                'link': e[3],
                'source': source_map.get(e[11], 'Unknown'),
                'published_at': e[4].isoformat() if e[4] else None,
                'fetched_at': e[5].isoformat() if e[5] else None,
                'event_type': e[6],
                'matched_keywords': e[7],
                'impact_score': e[8],
                'impact_level': e[9],
                'impact_note': e[10]
            } for e in recent_events],
            'recent_rss_fetch_runs': recent_rss_fetch_runs,
            'recent_runs': recent_runs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/us10y/status")
async def get_us10y_status(db: Session = Depends(get_db)):
    """获取美债状态（原系统格式）"""
    try:
        # 获取最新美债样本（所有期限）
        latest_samples = {}
        for tenor in ['5y', '10y', '20y']:
            sample = db.query(USTreasury).filter_by(tenor=tenor).order_by(
                USTreasury.fetched_at.desc()
            ).first()
            if sample:
                latest_samples[tenor] = {
                    'id': sample.id,
                    'fetched_at': sample.fetched_at.isoformat() if sample.fetched_at else None,
                    'tenor': sample.tenor,
                    'yield_pct': sample.yield_pct,
                    'source': sample.source,
                    'yield_signal': sample.yield_signal,
                    'note': sample.note
                }
        
        # 默认使用10y作为latest_sample
        latest_sample = latest_samples.get('10y')
        
        # 获取运行记录
        recent_runs = []
        
        return {
            'latest_sample': latest_sample,
            'latest_samples': latest_samples,
            'recent_runs': recent_runs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/us10y/history")
async def get_us10y_history(range: str = "1D", db: Session = Depends(get_db)):
    """获取美债历史数据（原系统格式）"""
    try:
        # 根据时间范围获取数据
        if range == "1H":
            since = datetime.now() - timedelta(hours=1)
        elif range == "1W":
            since = datetime.now() - timedelta(weeks=1)
        else:  # 1D
            since = datetime.now() - timedelta(days=1)
        
        samples = db.query(USTreasury).filter(
            USTreasury.fetched_at >= since
        ).order_by(USTreasury.fetched_at.asc()).all()
        
        items = [{
            'id': s.id,
            'fetched_at': s.fetched_at.isoformat() if s.fetched_at else None,
            'tenor': s.tenor,
            'yield_pct': s.yield_pct,
            'source': s.source,
            'yield_signal': s.yield_signal,
            'note': s.note
        } for s in samples]
        
        return {'items': items, 'count': len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/reversal/events")
async def get_reversal_events(
    limit: int = 20,
    event_type: str = None,
    db: Session = Depends(get_db)
):
    """获取RSS事件（原系统格式）"""
    try:
        query = db.query(RSSEvent)
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        events = query.order_by(
            RSSEvent.fetched_at.desc(),
            RSSEvent.published_at.desc()
        ).limit(limit).all()
        
        items = [{
            'id': e.id,
            'fetched_at': e.fetched_at.isoformat() if e.fetched_at else None,
            'published_at': e.published_at.isoformat() if e.published_at else None,
            'source': e.source.name if e.source else 'Unknown',
            'feed_url': e.feed_url,
            'title': e.title,
            'link': e.link,
            'summary': e.summary,
            'event_type': e.event_type,
            'matched_keywords': e.matched_keywords,
            'content_hash': e.content_hash,
            'impact_score': e.impact_score,
            'impact_level': e.impact_level,
            'impact_note': e.impact_note
        } for e in events]
        
        return {'items': items, 'count': len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/settings")
async def get_settings(db: Session = Depends(get_db)):
    """获取系统配置（原系统格式）"""
    try:
        configs = db.query(SystemConfig).all()
        config_dict = {c.config_key: c.config_value for c in configs}
        
        # 获取RSS源完整信息
        rss_sources = db.query(RSSSource).all()
        rss_feed_sources = [{
            'id': rs.id,
            'name': rs.name,
            'url': rs.url,
            'category': rs.category,
            'enabled': bool(rs.is_active)
        } for rs in rss_sources]
        
        # 构建settings对象（无外发推送配置）
        settings = {
            'notification_targets': [],
            'premium_threshold': float(config_dict.get('premium_threshold', 20.0)),
            'poll_interval_seconds': int(config_dict.get('poll_interval_seconds', 60)),
            'alert_cooldown_seconds': int(config_dict.get('alert_cooldown_seconds', 900)),
            'request_timeout_seconds': float(config_dict.get('request_timeout_seconds', 10.0)),
            'reversal_cooldown_seconds': int(config_dict.get('reversal_cooldown_seconds', 1800)),
            'reversal_price_lookback_minutes': int(config_dict.get('reversal_price_lookback_minutes', 360)),
            'reversal_price_rebound_pct': float(config_dict.get('reversal_price_rebound_pct', 1.2)),
            'reversal_price_ma_window': int(config_dict.get('reversal_price_ma_window', 15)),
            'reversal_signal_window_minutes': int(config_dict.get('reversal_signal_window_minutes', 180)),
            'us10y_poll_interval_seconds': int(config_dict.get('us10y_poll_interval_seconds', 60)),
            'us10y_drop_lookback_hours': float(config_dict.get('us10y_drop_lookback_hours', 24.0)),
            'us10y_drop_threshold_bp': float(config_dict.get('us10y_drop_threshold_bp', 1.0)),
            'us10y_cooldown_seconds': int(config_dict.get('us10y_cooldown_seconds', 900)),
            'us10y_tenors': config_dict.get('us10y_tenors', '10y').split(','),
            'rss_poll_interval_seconds': int(config_dict.get('rss_poll_interval_seconds', 3600)),
            'rss_feed_sources': rss_feed_sources
        }
        
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/settings")
async def update_settings(settings: Dict, db: Session = Depends(get_db)):
    """更新系统配置（原系统格式）"""
    try:
        # 更新配置项
        config_mapping = {
            'premium_threshold': 'premium_threshold',
            'poll_interval_seconds': 'poll_interval_seconds',
            'alert_cooldown_seconds': 'alert_cooldown_seconds',
            'request_timeout_seconds': 'request_timeout_seconds',
        }
        
        for api_key, db_key in config_mapping.items():
            if api_key in settings:
                config = db.query(SystemConfig).filter_by(config_key=db_key).first()
                if config:
                    config.config_value = str(settings[api_key])
                else:
                    db.add(SystemConfig(
                        config_key=db_key,
                        config_value=str(settings[api_key]),
                        description=api_key
                    ))
        
        db.commit()
        return {'success': True, 'message': '配置更新成功'}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/reversal/settings")
async def update_reversal_settings(settings: Dict, db: Session = Depends(get_db)):
    """更新反转配置（原系统格式）"""
    try:
        config_mapping = {
            'reversal_cooldown_seconds': 'reversal_cooldown_seconds',
            'reversal_price_lookback_minutes': 'reversal_price_lookback_minutes',
            'reversal_price_rebound_pct': 'reversal_price_rebound_pct',
            'reversal_price_ma_window': 'reversal_price_ma_window',
            'reversal_signal_window_minutes': 'reversal_signal_window_minutes',
            'us10y_poll_interval_seconds': 'us10y_poll_interval_seconds',
            'us10y_drop_lookback_hours': 'us10y_drop_lookback_hours',
            'us10y_drop_threshold_bp': 'us10y_drop_threshold_bp',
            'us10y_cooldown_seconds': 'us10y_cooldown_seconds',
            'rss_poll_interval_seconds': 'rss_poll_interval_seconds',
        }
        
        for api_key, db_key in config_mapping.items():
            if api_key in settings:
                config = db.query(SystemConfig).filter_by(config_key=db_key).first()
                if config:
                    config.config_value = str(settings[api_key])
                else:
                    db.add(SystemConfig(
                        config_key=db_key,
                        config_value=str(settings[api_key]),
                        description=api_key
                    ))
        
        # 更新美债期限
        if 'us10y_tenors' in settings:
            tenors = settings['us10y_tenors']
            config = db.query(SystemConfig).filter_by(config_key='us10y_tenors').first()
            if config:
                config.config_value = ','.join(tenors)
            else:
                db.add(SystemConfig(
                    config_key='us10y_tenors',
                    config_value=','.join(tenors),
                    description='US Treasury tenors'
                ))
        
        # 更新RSS源
        if 'rss_feed_sources' in settings:
            # 删除现有RSS源
            db.query(RSSSource).delete()
            
            # 添加新的RSS源
            for feed in settings['rss_feed_sources']:
                # 自动判断分类
                category = 'political'
                url_lower = feed['url'].lower()
                title_lower = feed.get('name', '').lower()
                if any(kw in url_lower or kw in title_lower for kw in ['war', 'conflict', 'military', '战争', '冲突', '军事']):
                    category = 'war'
                
                db.add(RSSSource(
                    name=feed.get('name', '未命名RSS源'),
                    url=feed['url'],
                    category=category,
                    is_active=1 if feed.get('enabled', True) else 0
                ))
        
        db.commit()
        return {'success': True, 'message': '配置更新成功'}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/run-once")
async def run_once(db: Session = Depends(get_db)):
    """立即执行所有监控任务（原系统格式）"""
    try:
        # 执行SGE监控
        async with SGEMonitorService(db) as sge_service:
            await sge_service.fetch_and_save_data()
        
        # 执行RSS采集
        async with RSSCollectorService(db) as rss_service:
            await rss_service.collect_all()
        
        # 执行反转检测
        reversal_service = ReversalDetectorService(db)
        await reversal_service.detect_and_save()
        
        return {'success': True, 'message': '已执行 SGE + RSS + 反转检测'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/reversal/run-once")
async def run_reversal_once(db: Session = Depends(get_db)):
    """立即执行反转检测（原系统格式）"""
    try:
        reversal_service = ReversalDetectorService(db)
        await reversal_service.detect_and_save()
        
        return {'success': True, 'message': '已执行反转检测'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/us10y/run-once")
async def run_us10y_once(db: Session = Depends(get_db)):
    """立即执行美债采样（原系统格式）"""
    try:
        us10y_service = US10YMonitorService(db)
        
        # 获取配置的期限
        config = db.query(SystemConfig).filter_by(config_key='us10y_tenors').first()
        tenors = config.config_value.split(',') if config else ['10y']
        
        # 采样所有期限
        for tenor in tenors:
            await us10y_service.fetch_and_save(tenor)
        
        return {'success': True, 'message': f'已采样美债: {", ".join(tenors)}'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/reversal/rss-run-once")
async def run_reversal_rss_once(db: Session = Depends(get_db)):
    """立即执行RSS采集（原系统格式）"""
    try:
        async with RSSCollectorService(db) as rss_service:
            await rss_service.collect_all()
        
        return {'success': True, 'message': '已执行RSS采集'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/rss/sources")
async def get_rss_sources(db: Session = Depends(get_db)):
    """获取所有RSS源"""
    try:
        sources = db.query(RSSSource).order_by(RSSSource.created_at.desc()).all()
        items = [{
            'id': s.id,
            'name': s.name,
            'url': s.url,
            'category': s.category,
            'enabled': bool(s.is_active),
            'created_at': s.created_at.isoformat() if s.created_at else None,
            'updated_at': s.updated_at.isoformat() if s.updated_at else None
        } for s in sources]
        
        return {'success': True, 'items': items, 'count': len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/rss/sources")
async def create_rss_source(source_data: Dict, db: Session = Depends(get_db)):
    """创建RSS源"""
    try:
        # 检查URL是否已存在
        existing = db.query(RSSSource).filter_by(url=source_data['url']).first()
        if existing:
            return {'success': False, 'message': '该RSS源已存在'}
        
        # 自动判断分类
        category = source_data.get('category', 'political')
        if not category or category not in ['political', 'war']:
            url_lower = source_data['url'].lower()
            title_lower = source_data.get('name', '').lower()
            if any(kw in url_lower or kw in title_lower for kw in ['war', 'conflict', 'military', '战争', '冲突', '军事']):
                category = 'war'
            else:
                category = 'political'
        
        # 创建新源
        source = RSSSource(
            name=source_data.get('name', '未命名RSS源'),
            url=source_data['url'],
            category=category,
            is_active=1 if source_data.get('enabled', True) else 0
        )
        db.add(source)
        db.commit()
        
        return {
            'success': True,
            'message': 'RSS源创建成功',
            'data': {
                'id': source.id,
                'name': source.name,
                'url': source.url,
                'category': source.category,
                'enabled': bool(source.is_active)
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/rss/sources/{source_id}")
async def update_rss_source(source_id: int, source_data: Dict, db: Session = Depends(get_db)):
    """更新RSS源"""
    try:
        source = db.query(RSSSource).filter_by(id=source_id).first()
        if not source:
            return {'success': False, 'message': 'RSS源不存在'}
        
        # 更新字段
        if 'name' in source_data:
            source.name = source_data['name']
        if 'url' in source_data:
            source.url = source_data['url']
        if 'category' in source_data:
            source.category = source_data['category']
        if 'enabled' in source_data:
            source.is_active = 1 if source_data['enabled'] else 0
        
        source.updated_at = datetime.now()
        db.commit()
        
        return {'success': True, 'message': 'RSS源更新成功'}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/rss/sources/{source_id}")
async def delete_rss_source(source_id: int, db: Session = Depends(get_db)):
    """删除RSS源"""
    try:
        source = db.query(RSSSource).filter_by(id=source_id).first()
        if not source:
            return {'success': False, 'message': 'RSS源不存在'}
        
        db.delete(source)
        db.commit()
        
        return {'success': True, 'message': 'RSS源删除成功'}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
