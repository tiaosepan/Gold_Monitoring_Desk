-- 黄金监控中台数据库初始化脚本

-- 1. 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. SGE价格数据表
CREATE TABLE IF NOT EXISTS sge_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    sge_price REAL NOT NULL,
    international_price REAL NOT NULL,
    usdcny_rate REAL NOT NULL,
    premium REAL NOT NULL,
    premium_percent REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. 美债数据表
CREATE TABLE IF NOT EXISTS us_treasury (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    yield_value REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. RSS源配置表
CREATE TABLE IF NOT EXISTS rss_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    category TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. RSS事件表
CREATE TABLE IF NOT EXISTS rss_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    link TEXT,
    published_at DATETIME,
    category TEXT NOT NULL,
    score INTEGER NOT NULL,
    is_pushed INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES rss_sources(id)
);

-- 6. 反转条件表
CREATE TABLE IF NOT EXISTS reversal_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    price_condition INTEGER DEFAULT 0,
    political_condition INTEGER DEFAULT 0,
    war_condition INTEGER DEFAULT 0,
    us10y_condition INTEGER DEFAULT 0,
    reversal_level INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. 推送目标配置表
CREATE TABLE IF NOT EXISTS push_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    webhook_url TEXT NOT NULL,
    secret TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 8. 推送记录表
CREATE TABLE IF NOT EXISTS push_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id INTEGER NOT NULL,
    message_type TEXT NOT NULL,
    message_content TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (target_id) REFERENCES push_targets(id)
);

-- 9. 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    module TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 10. 数据更新记录表
CREATE TABLE IF NOT EXISTS update_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_type TEXT NOT NULL,
    status TEXT NOT NULL,
    record_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 11. 市场状态表
CREATE TABLE IF NOT EXISTS market_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    is_open INTEGER NOT NULL,
    market_name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 12. 警报历史表
CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    alert_level INTEGER NOT NULL,
    alert_content TEXT NOT NULL,
    is_pushed INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 13. 数据源健康表
CREATE TABLE IF NOT EXISTS data_source_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL,
    last_success_at DATETIME,
    last_error_at DATETIME,
    error_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 14. 任务调度状态表
CREATE TABLE IF NOT EXISTS scheduler_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL UNIQUE,
    last_run_at DATETIME,
    next_run_at DATETIME,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入初始系统配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('sge_premium_threshold', '15', 'SGE溢价阈值（元/克）'),
('sge_premium_percent_threshold', '0.5', 'SGE溢价百分比阈值'),
('us10y_drop_threshold', '0.1', '美债收益率下跌阈值'),
('us10y_time_window', '3600', '美债监控时间窗口（秒）'),
('rss_political_threshold', '7', 'RSS政治事件推送阈值'),
('rss_war_threshold', '7', 'RSS战争事件推送阈值'),
('data_update_interval', '300', '数据更新间隔（秒）'),
('market_open_time', '09:00', '市场开盘时间'),
('market_close_time', '15:30', '市场收盘时间'),
('system_name', '黄金监控中台', '系统名称'),
('system_version', '1.0.0', '系统版本');

-- 插入初始RSS源配置（与原系统一致）
INSERT INTO rss_sources (name, url, category, is_active) VALUES
('虎嗅网', 'https://rss.huxiu.com/', 'political', 1),
('彭博经济', 'https://quanwenrss.com/bloomberg/economics', 'political', 1),
('金十数据1', 'http://rss.jintiankansha.me/rss/GM3DSNZUGJ6DOYTEG5RWENZRGUZDENLDGAYGMMDGMRSTONBRMUYWMM3FMQ2DGYZXMZSTGNDGG4YQ====', 'political', 1),
('Beehiiv订阅', 'https://rss.beehiiv.com/feeds/4aF2pGVAEN.xml', 'war', 1),
('金十数据2', 'http://rss.jintiankansha.me/rss/GM4DKMRUG56DIYZTHE2TAY3EGNTDAMLGMQZWKMRRGNRWCZBQMY2TSZLEGEYTQN3DMQYDSNZUGQYA====', 'war', 1);

-- 插入初始推送目标配置（需要用户填写实际的webhook_url和secret）
INSERT INTO push_targets (name, type, webhook_url, secret, is_active) VALUES
('钉钉机器人-主群', 'dingtalk', 'https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN', 'YOUR_SECRET', 1);

-- 插入初始数据源健康记录
INSERT INTO data_source_health (source_name, status) VALUES
('Sina Finance API', 'unknown'),
('RSS Sources', 'unknown'),
('DingTalk Push', 'unknown');

-- 插入初始任务调度状态
INSERT INTO scheduler_status (task_name, status) VALUES
('sge_monitor', 'pending'),
('us10y_monitor', 'pending'),
('rss_collector', 'pending'),
('reversal_detector', 'pending');
