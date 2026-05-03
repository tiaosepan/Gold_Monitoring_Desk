"""
数据库连接和模型定义
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

# 数据库文件路径
DB_FILE = 'gold_monitor.db'
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', DB_FILE)
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 创建引擎
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


# 模型定义
class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String, unique=True, nullable=False)
    config_value = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SGEPrice(Base):
    __tablename__ = "sge_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fetched_at = Column(DateTime, nullable=False)
    shfe_price_cny_per_g = Column(Float, nullable=False)
    london_price_usd_per_oz = Column(Float, nullable=False)
    usdcny_rate = Column(Float, nullable=False)
    london_price_cny_per_g = Column(Float, nullable=False)
    premium_cny_per_g = Column(Float, nullable=False)
    poll_interval_seconds = Column(Integer, default=60)
    both_markets_open = Column(Integer, default=0)
    shfe_market_open = Column(Integer, default=0)
    london_market_open = Column(Integer, default=0)
    alert_triggered = Column(Integer, default=0)
    raw_payload = Column(Text)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class USTreasury(Base):
    __tablename__ = "us_treasury"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fetched_at = Column(DateTime, nullable=False)
    yield_pct = Column(Float, nullable=False)
    yield_signal = Column(Integer, default=0)
    source = Column(String, default='Sina')
    tenor = Column(String, default='10y')
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class RSSSource(Base):
    __tablename__ = "rss_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    category = Column(String, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    events = relationship("RSSEvent", back_populates="source")


class RSSEvent(Base):
    __tablename__ = "rss_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fetched_at = Column(DateTime, default=datetime.now)
    source_id = Column(Integer, ForeignKey('rss_sources.id'), nullable=False)
    feed_url = Column(String)
    title = Column(String, nullable=False)
    link = Column(String)
    summary = Column(Text)
    published_at = Column(DateTime)
    event_type = Column(String, nullable=False)
    matched_keywords = Column(String)
    content_hash = Column(String)
    impact_score = Column(Integer, nullable=False)
    impact_level = Column(String)
    impact_note = Column(Text)
    is_pushed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    
    source = relationship("RSSSource", back_populates="events")


class ReversalCondition(Base):
    __tablename__ = "reversal_conditions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fetched_at = Column(DateTime, nullable=False)
    gold_price_usd_per_oz = Column(Float, nullable=False)
    usdcny_rate = Column(Float, nullable=False)
    price_signal = Column(Integer, default=0)
    political_signal = Column(Integer, default=0)
    war_signal = Column(Integer, default=0)
    us10y_signal = Column(Integer, default=0)
    signal_level = Column(Integer, nullable=False)
    triggered_conditions = Column(String)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class PushTarget(Base):
    __tablename__ = "push_targets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    webhook_url = Column(String, nullable=False)
    secret = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    logs = relationship("PushLog", back_populates="target")


class PushLog(Base):
    __tablename__ = "push_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey('push_targets.id'), nullable=False)
    message_type = Column(String, nullable=False)
    message_content = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    target = relationship("PushTarget", back_populates="logs")


class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String, nullable=False)
    module = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class UpdateRecord(Base):
    __tablename__ = "update_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    data_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    record_count = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class MarketStatus(Base):
    __tablename__ = "market_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    is_open = Column(Integer, nullable=False)
    market_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class AlertHistory(Base):
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String, nullable=False)
    alert_level = Column(Integer, nullable=False)
    alert_content = Column(Text, nullable=False)
    is_pushed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class DataSourceHealth(Base):
    __tablename__ = "data_source_health"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    last_success_at = Column(DateTime)
    last_error_at = Column(DateTime)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SchedulerStatus(Base):
    __tablename__ = "scheduler_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String, unique=True, nullable=False)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    status = Column(String, nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 使用ORM插入初始数据
    db = SessionLocal()
    try:
        # 检查是否已经初始化
        if db.query(SystemConfig).count() == 0:
            # 插入系统配置（与原系统一致）
            configs = [
                SystemConfig(config_key='premium_threshold', config_value='20.0', description='SGE溢价阈值（元/克）'),
                SystemConfig(config_key='poll_interval_seconds', config_value='60', description='轮询间隔（秒）'),
                SystemConfig(config_key='alert_cooldown_seconds', config_value='900', description='警报冷却时间（秒）'),
                SystemConfig(config_key='reversal_cooldown_seconds', config_value='1800', description='反转冷却时间（秒）'),
                SystemConfig(config_key='reversal_price_lookback_minutes', config_value='60', description='价格回看分钟数'),
                SystemConfig(config_key='reversal_price_rebound_pct', config_value='1.2', description='价格反弹百分比'),
                SystemConfig(config_key='reversal_price_ma_window', config_value='15', description='价格MA窗口'),
                SystemConfig(config_key='reversal_signal_window_minutes', config_value='180', description='信号窗口分钟数'),
                SystemConfig(config_key='us10y_drop_threshold_bp', config_value='1.0', description='美债下跌阈值(bp)'),
                SystemConfig(config_key='us10y_drop_lookback_hours', config_value='24.0', description='美债回看小时数'),
                SystemConfig(config_key='us10y_cooldown_seconds', config_value='900', description='美债预警冷却时间（秒）'),
                SystemConfig(config_key='rss_poll_interval_seconds', config_value='1800', description='RSS轮询间隔（秒）'),
                SystemConfig(config_key='request_timeout_seconds', config_value='10.0', description='请求超时时间（秒）'),
                SystemConfig(config_key='market_open_time', config_value='09:00', description='市场开盘时间'),
                SystemConfig(config_key='market_close_time', config_value='15:30', description='市场收盘时间'),
                SystemConfig(config_key='system_name', config_value='黄金监控中台', description='系统名称'),
                SystemConfig(config_key='system_version', config_value='1.0.0', description='系统版本'),
            ]
            db.add_all(configs)
            
            # 插入RSS源（与原系统一致）
            rss_sources = [
                RSSSource(name='虎嗅网', url='https://rss.huxiu.com/', category='political', is_active=1),
                RSSSource(name='彭博经济', url='https://quanwenrss.com/bloomberg/economics', category='political', is_active=1),
                RSSSource(name='金十数据1', url='http://rss.jintiankansha.me/rss/GM3DSNZUGJ6DOYTEG5RWENZRGUZDENLDGAYGMMDGMRSTONBRMUYWMM3FMQ2DGYZXMZSTGNDGG4YQ====', category='political', is_active=1),
                RSSSource(name='Beehiiv订阅', url='https://rss.beehiiv.com/feeds/4aF2pGVAEN.xml', category='war', is_active=1),
                RSSSource(name='金十数据2', url='http://rss.jintiankansha.me/rss/GM4DKMRUG56DIYZTHE2TAY3EGNTDAMLGMQZWKMRRGNRWCZBQMY2TSZLEGEYTQN3DMQYDSNZUGQYA====', category='war', is_active=1),
            ]
            db.add_all(rss_sources)
            
            # 插入数据源健康记录
            health_records = [
                DataSourceHealth(source_name='Gold-API', status='unknown'),
                DataSourceHealth(source_name='Sina Finance API', status='unknown'),
                DataSourceHealth(source_name='Sina Finance API - 沪金汇率', status='unknown'),
                DataSourceHealth(source_name='RSS Sources', status='unknown'),
            ]
            db.add_all(health_records)
            
            # 插入任务调度状态
            scheduler_statuses = [
                SchedulerStatus(task_name='sge_monitor', status='pending'),
                SchedulerStatus(task_name='us10y_monitor', status='pending'),
                SchedulerStatus(task_name='rss_collector', status='pending'),
                SchedulerStatus(task_name='reversal_detector', status='pending'),
            ]
            db.add_all(scheduler_statuses)
            
            db.commit()
            print("初始数据插入成功")
    except Exception as e:
        print(f"初始化数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
    print("数据库初始化完成！")
