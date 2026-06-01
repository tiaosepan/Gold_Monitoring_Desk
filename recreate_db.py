"""
重新创建数据库（使用新的数据库文件名）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# 修改数据库文件名
os.environ['DB_FILE'] = 'gold_monitor_v2.db'

from backend.database import Base, engine, SessionLocal, SystemConfig, RSSSource, DataSourceHealth, SchedulerStatus

# 创建所有表
print("创建数据库表...")
Base.metadata.create_all(bind=engine)
print("表创建完成")

# 插入初始数据
db = SessionLocal()
try:
    # 插入系统配置（与原系统一致）- 如果不存在
    config_data = [
        ('premium_threshold', '20.0', 'SGE溢价阈值（元/克）'),
        ('poll_interval_seconds', '60', '轮询间隔（秒）'),
        ('alert_cooldown_seconds', '900', '警报冷却时间（秒）'),
        ('reversal_cooldown_seconds', '1800', '反转冷却时间（秒）'),
        ('reversal_price_lookback_minutes', '60', '价格回看分钟数'),
        ('reversal_price_rebound_pct', '1.2', '价格反弹百分比'),
        ('reversal_price_ma_window', '15', '价格MA窗口'),
        ('reversal_signal_window_minutes', '180', '信号窗口分钟数'),
        ('us10y_drop_threshold_bp', '1.0', '美债下跌阈值(bp)'),
        ('us10y_drop_lookback_hours', '24.0', '美债回看小时数'),
        ('rss_poll_interval_seconds', '1800', 'RSS轮询间隔（秒）'),
        ('request_timeout_seconds', '10.0', '请求超时时间（秒）'),
        ('market_open_time', '09:00', '市场开盘时间'),
        ('market_close_time', '15:30', '市场收盘时间'),
        ('system_name', '黄金监控中台', '系统名称'),
        ('system_version', '1.0.0', '系统版本'),
    ]
    for key, value, desc in config_data:
        existing = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
        if not existing:
            db.add(SystemConfig(config_key=key, config_value=value, description=desc))
    
    # 插入RSS源（与原系统一致）- 如果不存在
    rss_data = [
        ('虎嗅网', 'https://rss.huxiu.com/', 'political'),
        ('彭博经济', 'https://quanwenrss.com/bloomberg/economics', 'political'),
        ('金十数据1', 'http://rss.jintiankansha.me/rss/GM3DSNZUGJ6DOYTEG5RWENZRGUZDENLDGAYGMMDGMRSTONBRMUYWMM3FMQ2DGYZXMZSTGNDGG4YQ====', 'political'),
        ('Beehiiv订阅', 'https://rss.beehiiv.com/feeds/4aF2pGVAEN.xml', 'war'),
        ('金十数据2', 'http://rss.jintiankansha.me/rss/GM4DKMRUG56DIYZTHE2TAY3EGNTDAMLGMQZWKMRRGNRWZCYBGEYTSZLEGEYTQN3DMQYDSNZUGQYA====', 'war'),
    ]
    for name, url, category in rss_data:
        existing = db.query(RSSSource).filter(RSSSource.url == url).first()
        if not existing:
            db.add(RSSSource(name=name, url=url, category=category, is_active=1))
    
    # 插入数据源健康记录 - 如果不存在
    health_data = ['Sina Finance API', 'FRED API', 'RSS Sources']
    for source_name in health_data:
        existing = db.query(DataSourceHealth).filter(DataSourceHealth.source_name == source_name).first()
        if not existing:
            db.add(DataSourceHealth(source_name=source_name, status='unknown'))
    
    # 插入任务调度状态（如果不存在）
    task_names = ['sge_monitor', 'us10y_monitor', 'rss_collector', 'reversal_detector']
    for task_name in task_names:
        existing = db.query(SchedulerStatus).filter(SchedulerStatus.task_name == task_name).first()
        if not existing:
            db.add(SchedulerStatus(task_name=task_name, status='pending'))
    
    db.commit()
    print("初始数据插入成功！")
    print(f"  - 配置项: {db.query(SystemConfig).count()}")
    print(f"  - RSS源: {db.query(RSSSource).count()}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
