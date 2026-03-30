-- 数据库性能优化：添加复合索引

-- 1. update_records表：按类型+时间查询（routes.py多处使用）
CREATE INDEX IF NOT EXISTS idx_update_records_type_created 
ON update_records(data_type, created_at DESC);

-- 2. alert_history表：按类型+时间查询
CREATE INDEX IF NOT EXISTS idx_alert_history_type_created 
ON alert_history(alert_type, created_at DESC);

-- 3. rss_events表：按event_type+fetched_at查询
CREATE INDEX IF NOT EXISTS idx_rss_events_type_fetched 
ON rss_events(event_type, fetched_at DESC);

-- 4. reversal_conditions表：按signal_level+fetched_at查询（用于高级别信号快速检索）
CREATE INDEX IF NOT EXISTS idx_reversal_level_fetched 
ON reversal_conditions(signal_level, fetched_at DESC);

-- 5. us_treasury表：按tenor+fetched_at查询（用于计算回落）
CREATE INDEX IF NOT EXISTS idx_treasury_tenor_fetched 
ON us_treasury(tenor, fetched_at DESC);

-- 查看创建的索引
SELECT name, tbl_name FROM sqlite_master 
WHERE type='index' AND name LIKE 'idx_%' 
ORDER BY tbl_name, name;
