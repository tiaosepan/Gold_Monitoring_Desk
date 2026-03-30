# 数据源切换使用指南

## 快速开始

### 1. 测试数据源状态

```bash
python test_data_sources.py
```

**预期输出**：
```
============================================================
黄金监控系统 - 数据源测试
============================================================

测试主数据源: Gold-API.com
[OK] 获取成功
  金价: $4492.80/盎司

测试备用数据源: 新浪财经
[OK] 国际金价获取成功
[OK] 沪金和汇率获取成功

[OK] 所有数据源工作正常！
```

---

## 数据源配置

### 主数据源：Gold-API

**无需配置**，免费版可直接使用。

如果有付费 API Key（可选）：
```python
# backend/utils/goldapi_client.py
client = GoldAPIClient(api_key="your_api_key_here")
```

### 备用数据源：新浪财经

**无需配置**，默认启用。

---

## 查看数据源使用情况

### 方法 1: 查看日志

```bash
# 查看最新日志
tail -f logs/sge_monitor.log

# 查找主数据源使用记录
grep "主数据源 Gold-API 成功" logs/sge_monitor.log

# 查找备用数据源使用记录
grep "备用数据源 新浪财经 成功" logs/sge_monitor.log
```

### 方法 2: 查看数据库

```bash
# 启动 SQLite 客户端
sqlite3 database/gold_monitor.db

# 查看数据源健康状态
SELECT source_name, status, last_success_at, error_count 
FROM data_source_health;

# 查看最近使用的数据源
SELECT fetched_at, note 
FROM sge_prices 
ORDER BY fetched_at DESC 
LIMIT 10;
```

### 方法 3: 通过 API

```bash
# 访问系统状态 API
curl http://localhost:8000/api/status | python -m json.tool
```

---

## 故障排查

### 问题 1: 主数据源 Gold-API 总是失败

**可能原因**：
- 网络问题（无法访问国际网站）
- Gold-API 服务器维护

**解决方案**：
1. 检查网络连接：`curl https://api.gold-api.com/price/XAU`
2. 系统会自动切换到备用数据源，无需干预
3. 如果需要禁用主数据源，修改 `sge_monitor.py`：
   ```python
   # 临时禁用主数据源，直接使用备用源
   async def _fetch_international_gold_price(self):
       # 跳过主数据源，直接使用备用
       try:
           data = await self.backup_api.fetch_data(['xauusd'])
           return data['xauusd']['price'], '新浪财经', raw_data
       except Exception as e:
           raise Exception("备用数据源失败")
   ```

### 问题 2: 备用数据源新浪财经也失败

**可能原因**：
- 新浪财经 API 维护
- 请求被限流（403 错误）

**解决方案**：
1. 检查请求头设置（已在代码中配置）
2. 等待几分钟后重试
3. 查看错误日志：`logs/sge_monitor.log`

### 问题 3: 两个数据源价格差异大

**正常情况**：
- 差异通常在 $1-5 /盎司（0.1-0.2%）
- Gold-API 更新频率更高，可能有秒级差异

**异常情况**：
- 差异 > $20 /盎司（>0.5%）
- 可能原因：数据源延迟、市场剧烈波动

**解决方案**：
1. 运行测试脚本对比：`python test_data_sources.py`
2. 查看其他金价网站验证：
   - https://www.gold-price.org/
   - https://www.kitco.com/
3. 如果确认某个源错误，临时禁用该源

---

## 性能指标

### 正常情况

| 指标 | 主数据源（Gold-API） | 备用数据源（新浪财经） |
|------|---------------------|---------------------|
| 响应时间 | 1-2 秒 | 0.5-1 秒 |
| 成功率 | >99% | >98% |
| 数据格式 | JSON | GBK CSV |
| 更新频率 | 实时 | 实时 |

### 监控建议

每小时检查一次数据源健康状态：
```sql
SELECT 
    source_name,
    status,
    last_success_at,
    error_count,
    ROUND(JULIANDAY('now') - JULIANDAY(updated_at), 2) as hours_since_update
FROM data_source_health
WHERE hours_since_update < 1;
```

---

## 常见问题 FAQ

### Q1: 可以完全禁用某个数据源吗？

A: 可以，修改 `sge_monitor.py` 中的 `_fetch_international_gold_price` 方法。

### Q2: 如何添加第三个数据源？

A: 按照以下步骤：
1. 创建新的 API 客户端类（参考 `goldapi_client.py`）
2. 在 `sge_monitor.py` 中添加到切换逻辑
3. 更新数据源健康监控表

### Q3: 数据源切换会影响历史数据吗？

A: 不会。每条记录的 `note` 字段会标注使用的数据源，便于追溯。

### Q4: 如何验证数据准确性？

A: 运行测试脚本对比两个数据源的价格：
```bash
python test_data_sources.py
```

### Q5: 主备切换需要多长时间？

A: 约 10-15 秒（主数据源超时 10 秒 + 备用源响应 1-2 秒）

---

## 联系支持

如有问题，请查看：
- [完整更新日志](./CHANGELOG_数据源升级.md)
- [项目文档](./CLAUDE.md)
- 或提交 GitHub Issue
