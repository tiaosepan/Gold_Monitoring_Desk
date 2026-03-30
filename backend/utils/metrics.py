"""
Prometheus指标导出
"""
from prometheus_client import Counter, Gauge, Histogram, Info
from datetime import datetime
from typing import Optional


# 系统信息
system_info = Info('gold_monitor_system', '系统信息')
system_info.info({
    'version': '1.0.0',
    'name': '黄金监控中台'
})

# ==================== SGE监控指标 ====================
# SGE数据采集计数器
sge_fetch_total = Counter(
    'sge_fetch_total',
    'SGE数据采集总次数',
    ['status']  # success/failed
)

# SGE数据采集耗时
sge_fetch_duration = Histogram(
    'sge_fetch_duration_seconds',
    'SGE数据采集耗时（秒）',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

# SGE当前溢价
sge_premium = Gauge(
    'sge_premium_cny_per_g',
    '当前SGE溢价（元/克）'
)

# SGE沪金价格
sge_shfe_price = Gauge(
    'sge_shfe_price_cny_per_g',
    '沪金价格（元/克）'
)

# 伦敦金价格
sge_london_price = Gauge(
    'sge_london_price_usd_per_oz',
    '伦敦金价格（美元/盎司）'
)

# 汇率
sge_usdcny_rate = Gauge(
    'sge_usdcny_rate',
    '美元人民币汇率'
)

# 市场状态
sge_market_open = Gauge(
    'sge_market_open',
    'SGE市场开盘状态',
    ['market']  # shfe/london/both
)

# SGE采集频率（实际）
sge_actual_frequency = Gauge(
    'sge_actual_frequency_seconds',
    'SGE实际采集间隔（秒）'
)

# ==================== 反转检测指标 ====================
# 反转检测计数器
reversal_detect_total = Counter(
    'reversal_detect_total',
    '反转检测总次数',
    ['status']  # success/failed
)

# 反转检测耗时
reversal_detect_duration = Histogram(
    'reversal_detect_duration_seconds',
    '反转检测耗时（秒）',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

# 当前反转等级
reversal_signal_level = Gauge(
    'reversal_signal_level',
    '当前反转等级（0-4）'
)

# 各类信号状态
reversal_signals = Gauge(
    'reversal_signal_active',
    '反转信号状态',
    ['signal_type']  # price/political/war/us10y
)

# ==================== RSS采集指标 ====================
# RSS采集计数器
rss_collect_total = Counter(
    'rss_collect_total',
    'RSS采集总次数',
    ['source', 'status']  # source_name, success/failed
)

# RSS采集耗时
rss_collect_duration = Histogram(
    'rss_collect_duration_seconds',
    'RSS采集耗时（秒）',
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0)
)

# RSS新增事件数
rss_new_events = Counter(
    'rss_new_events_total',
    'RSS新增事件总数',
    ['event_type']  # political/war
)

# RSS高分事件数
rss_high_score_events = Counter(
    'rss_high_score_events_total',
    'RSS高分事件总数（>=6分）',
    ['event_type']
)

# RSS当前事件总数
rss_events_count = Gauge(
    'rss_events_count',
    '当前RSS事件总数',
    ['event_type']
)

# ==================== 美债监控指标 ====================
# 美债数据采集计数器
us10y_fetch_total = Counter(
    'us10y_fetch_total',
    '美债数据采集总次数',
    ['tenor', 'status']  # 5y/10y/20y, success/failed
)

# 美债数据采集耗时
us10y_fetch_duration = Histogram(
    'us10y_fetch_duration_seconds',
    '美债数据采集耗时（秒）',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

# 美债收益率
us10y_yield = Gauge(
    'us10y_yield_pct',
    '美债收益率（%）',
    ['tenor']  # 5y/10y/20y
)

# ==================== 推送指标 ====================
# 推送计数器
push_total = Counter(
    'push_total',
    '推送总次数',
    ['target_name', 'status']  # target_name, success/failed
)

# 推送耗时
push_duration = Histogram(
    'push_duration_seconds',
    '推送耗时（秒）',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

# ==================== API指标 ====================
# API请求计数器
api_requests_total = Counter(
    'api_requests_total',
    'API请求总数',
    ['method', 'endpoint', 'status']  # GET/POST, /api/status, 200/500
)

# API响应时间
api_response_duration = Histogram(
    'api_response_duration_seconds',
    'API响应时间（秒）',
    ['endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
)

# ==================== 数据库指标 ====================
# 数据库连接池
db_connections = Gauge(
    'db_connections',
    '数据库连接数',
    ['state']  # active/idle
)

# 数据库查询耗时
db_query_duration = Histogram(
    'db_query_duration_seconds',
    '数据库查询耗时（秒）',
    ['query_type'],  # select/insert/update
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0)
)

# ==================== 数据源健康指标 ====================
# 数据源健康状态
data_source_health = Gauge(
    'data_source_health',
    '数据源健康状态（1=健康，0=异常）',
    ['source_name']
)

# 数据源错误计数
data_source_errors = Counter(
    'data_source_errors_total',
    '数据源错误总数',
    ['source_name']
)


class MetricsCollector:
    """指标收集器"""
    
    @staticmethod
    def record_sge_fetch(status: str, duration_seconds: float, data: Optional[dict] = None):
        """记录SGE采集指标"""
        sge_fetch_total.labels(status=status).inc()
        sge_fetch_duration.observe(duration_seconds)
        
        if data and status == 'success':
            sge_premium.set(data.get('premium_cny_per_g', 0))
            sge_shfe_price.set(data.get('shfe_price_cny_per_g', 0))
            sge_london_price.set(data.get('london_price_usd_per_oz', 0))
            sge_usdcny_rate.set(data.get('usdcny_rate', 0))
    
    @staticmethod
    def record_market_status(market_status: dict):
        """记录市场状态"""
        sge_market_open.labels(market='shfe').set(market_status.get('shfe_market_open', 0))
        sge_market_open.labels(market='london').set(market_status.get('london_market_open', 0))
        sge_market_open.labels(market='both').set(market_status.get('both_markets_open', 0))
    
    @staticmethod
    def set_sge_frequency(interval_seconds: float):
        """设置SGE实际采集频率"""
        sge_actual_frequency.set(interval_seconds)
    
    @staticmethod
    def record_reversal_detect(status: str, duration_seconds: float, data: Optional[dict] = None):
        """记录反转检测指标"""
        reversal_detect_total.labels(status=status).inc()
        reversal_detect_duration.observe(duration_seconds)
        
        if data and status == 'success':
            reversal_signal_level.set(data.get('signal_level', 0))
            reversal_signals.labels(signal_type='price').set(data.get('price_signal', 0))
            reversal_signals.labels(signal_type='political').set(data.get('political_signal', 0))
            reversal_signals.labels(signal_type='war').set(data.get('war_signal', 0))
            reversal_signals.labels(signal_type='us10y').set(data.get('us10y_signal', 0))
    
    @staticmethod
    def record_rss_collect(source: str, status: str, duration_seconds: float, 
                          new_events: int = 0, event_type: Optional[str] = None):
        """记录RSS采集指标"""
        rss_collect_total.labels(source=source, status=status).inc()
        rss_collect_duration.observe(duration_seconds)
        
        if new_events > 0 and event_type:
            rss_new_events.labels(event_type=event_type).inc(new_events)
    
    @staticmethod
    def record_high_score_event(event_type: str):
        """记录高分RSS事件"""
        rss_high_score_events.labels(event_type=event_type).inc()
    
    @staticmethod
    def record_us10y_fetch(tenor: str, status: str, duration_seconds: float, yield_pct: Optional[float] = None):
        """记录美债采集指标"""
        us10y_fetch_total.labels(tenor=tenor, status=status).inc()
        us10y_fetch_duration.observe(duration_seconds)
        
        if yield_pct is not None and status == 'success':
            us10y_yield.labels(tenor=tenor).set(yield_pct)
    
    @staticmethod
    def record_push(target_name: str, status: str, duration_seconds: float):
        """记录推送指标"""
        push_total.labels(target_name=target_name, status=status).inc()
        push_duration.observe(duration_seconds)
    
    @staticmethod
    def record_api_request(method: str, endpoint: str, status: int, duration_seconds: float):
        """记录API请求指标"""
        api_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        api_response_duration.labels(endpoint=endpoint).observe(duration_seconds)
    
    @staticmethod
    def update_data_source_health(source_name: str, is_healthy: bool):
        """更新数据源健康状态"""
        data_source_health.labels(source_name=source_name).set(1 if is_healthy else 0)
        if not is_healthy:
            data_source_errors.labels(source_name=source_name).inc()


# 导出收集器实例
metrics = MetricsCollector()
