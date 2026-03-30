"""
添加数据库索引以优化查询性能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database import engine
from sqlalchemy import text


def add_indexes():
    """添加数据库索引"""
    print("=" * 60)
    print("开始添加数据库索引...")
    print("=" * 60)
    
    indexes = [
        # SGE价格表索引
        ("idx_sge_fetched_at", "CREATE INDEX IF NOT EXISTS idx_sge_fetched_at ON sge_prices(fetched_at DESC)"),
        ("idx_sge_alert", "CREATE INDEX IF NOT EXISTS idx_sge_alert ON sge_prices(alert_triggered, fetched_at DESC)"),
        ("idx_sge_market", "CREATE INDEX IF NOT EXISTS idx_sge_market ON sge_prices(both_markets_open, fetched_at DESC)"),
        
        # RSS事件表索引
        ("idx_rss_fetched_at", "CREATE INDEX IF NOT EXISTS idx_rss_fetched_at ON rss_events(fetched_at DESC)"),
        ("idx_rss_published_at", "CREATE INDEX IF NOT EXISTS idx_rss_published_at ON rss_events(published_at DESC)"),
        ("idx_rss_event_type", "CREATE INDEX IF NOT EXISTS idx_rss_event_type ON rss_events(event_type, fetched_at DESC)"),
        ("idx_rss_impact_score", "CREATE INDEX IF NOT EXISTS idx_rss_impact_score ON rss_events(impact_score DESC)"),
        ("idx_rss_content_hash", "CREATE INDEX IF NOT EXISTS idx_rss_content_hash ON rss_events(content_hash)"),
        ("idx_rss_is_pushed", "CREATE INDEX IF NOT EXISTS idx_rss_is_pushed ON rss_events(is_pushed, impact_score DESC)"),
        
        # 反转条件表索引
        ("idx_reversal_fetched_at", "CREATE INDEX IF NOT EXISTS idx_reversal_fetched_at ON reversal_conditions(fetched_at DESC)"),
        ("idx_reversal_level", "CREATE INDEX IF NOT EXISTS idx_reversal_level ON reversal_conditions(signal_level, fetched_at DESC)"),
        
        # 美债表索引
        ("idx_treasury_fetched_at", "CREATE INDEX IF NOT EXISTS idx_treasury_fetched_at ON us_treasury(fetched_at DESC)"),
        ("idx_treasury_tenor", "CREATE INDEX IF NOT EXISTS idx_treasury_tenor ON us_treasury(tenor, fetched_at DESC)"),
        
        # 警报历史表索引
        ("idx_alert_type", "CREATE INDEX IF NOT EXISTS idx_alert_type ON alert_history(alert_type, created_at DESC)"),
        ("idx_alert_created", "CREATE INDEX IF NOT EXISTS idx_alert_created ON alert_history(created_at DESC)"),
        
        # 更新记录表索引
        ("idx_update_type", "CREATE INDEX IF NOT EXISTS idx_update_type ON update_records(data_type, created_at DESC)"),
        
        # 推送日志表索引
        ("idx_push_log_created", "CREATE INDEX IF NOT EXISTS idx_push_log_created ON push_logs(created_at DESC)"),
        
        # 系统配置表索引
        ("idx_config_key", "CREATE INDEX IF NOT EXISTS idx_config_key ON system_config(config_key)"),
    ]
    
    with engine.connect() as conn:
        for index_name, sql in indexes:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"[OK] 已创建索引: {index_name}")
            except Exception as e:
                print(f"[SKIP] 索引已存在或跳过: {index_name}")
    
    print("=" * 60)
    print(f"索引添加完成！共处理 {len(indexes)} 个索引")
    print("=" * 60)


if __name__ == "__main__":
    add_indexes()
