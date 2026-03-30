# 监控系统部署指南

## 概述
本系统集成了Prometheus + Grafana监控方案，提供实时性能监控和告警功能。

## 快速启动

### 1. 安装Prometheus

**Windows:**
```bash
# 下载Prometheus
# https://prometheus.io/download/

# 解压后，将prometheus.yml替换为本目录的prometheus.yml
# 启动Prometheus
prometheus.exe --config.file=prometheus.yml
```

**访问**: http://localhost:9090

### 2. 安装Grafana

**Windows:**
```bash
# 下载Grafana
# https://grafana.com/grafana/download

# 启动Grafana
grafana-server.exe
```

**访问**: http://localhost:3000
- 默认用户名/密码: admin/admin

### 3. 配置Grafana

1. 添加Prometheus数据源:
   - Configuration → Data Sources → Add data source
   - 选择Prometheus
   - URL: http://localhost:9090
   - 点击"Save & Test"

2. 导入仪表盘:
   - Create → Import
   - 上传 `grafana_dashboard.json`
   - 选择Prometheus数据源
   - 点击"Import"

## 可用指标

### SGE监控指标
- `sge_fetch_total{status}` - 采集总次数
- `sge_fetch_duration_seconds` - 采集耗时
- `sge_premium_cny_per_g` - 当前溢价
- `sge_shfe_price_cny_per_g` - 沪金价格
- `sge_london_price_usd_per_oz` - 伦敦金价格
- `sge_market_open{market}` - 市场开盘状态
- `sge_actual_frequency_seconds` - 实际采集间隔

### 反转检测指标
- `reversal_detect_total{status}` - 检测总次数
- `reversal_detect_duration_seconds` - 检测耗时
- `reversal_signal_level` - 当前等级
- `reversal_signal_active{signal_type}` - 各类信号状态

### RSS采集指标
- `rss_collect_total{source,status}` - 采集总次数
- `rss_collect_duration_seconds` - 采集耗时
- `rss_new_events_total{event_type}` - 新增事件数
- `rss_high_score_events_total{event_type}` - 高分事件数
- `rss_events_count{event_type}` - 当前事件总数

### 美债监控指标
- `us10y_fetch_total{tenor,status}` - 采集总次数
- `us10y_fetch_duration_seconds` - 采集耗时
- `us10y_yield_pct{tenor}` - 收益率

### API性能指标
- `api_requests_total{method,endpoint,status}` - 请求总数
- `api_response_duration_seconds{endpoint}` - 响应时间

### 数据源健康指标
- `data_source_health{source_name}` - 健康状态（1=健康，0=异常）
- `data_source_errors_total{source_name}` - 错误总数

## 告警规则

系统预配置了以下告警规则（见`alert_rules.yml`）：

1. **SGECollectionFailureRate**: SGE采集失败率>10%（5分钟）
2. **SGECollectionDown**: SGE采集完全失败（10分钟）
3. **SGECollectionSlow**: SGE采集P95耗时>5秒（5分钟）
4. **ReversalDetectionFailureRate**: 反转检测失败率>10%（5分钟）
5. **RSSSourceDown**: RSS源持续失败（15分钟）
6. **DataSourceUnhealthy**: 数据源异常（10分钟）
7. **HighLevelReversalSignal**: 高等级反转信号（Level≥3）
8. **APIResponseSlow**: API P95响应时间>2秒（5分钟）

## 常用查询

### 查询SGE采集频率
```promql
# 每分钟采集次数
rate(sge_fetch_total[1m]) * 60

# 实际采集间隔
sge_actual_frequency_seconds
```

### 查询API性能
```promql
# P50响应时间
histogram_quantile(0.50, rate(api_response_duration_seconds_bucket[5m]))

# P95响应时间
histogram_quantile(0.95, rate(api_response_duration_seconds_bucket[5m]))

# P99响应时间
histogram_quantile(0.99, rate(api_response_duration_seconds_bucket[5m]))
```

### 查询数据源健康
```promql
# 所有数据源健康状态
data_source_health

# 错误率
rate(data_source_errors_total[5m])
```

## 告警配置

### 配置钉钉告警
编辑`prometheus.yml`，添加Alertmanager配置:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

创建`alertmanager.yml`:
```yaml
route:
  receiver: 'dingtalk'

receivers:
  - name: 'dingtalk'
    webhook_configs:
      - url: 'YOUR_DINGTALK_WEBHOOK'
```

## 仪表盘说明

Grafana仪表盘包含以下面板：

1. **SGE采集成功率**: 实时显示采集成功率
2. **SGE采集频率**: 每分钟实际采集次数
3. **SGE当前溢价**: 溢价实时曲线
4. **反转信号等级**: 等级变化趋势
5. **API响应时间**: 各端点P95响应时间
6. **任务执行耗时**: 各任务执行时间对比
7. **RSS源状态**: 各RSS源采集状态表格
8. **数据源健康**: 所有数据源健康状态
9. **反转信号分布**: 四类信号的触发情况

## Docker部署（可选）

使用Docker Compose快速部署监控栈:

```yaml
# docker-compose.yml
version: '3'
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alert_rules.yml:/etc/prometheus/alert_rules.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

启动命令:
```bash
docker-compose up -d
```

## 访问地址

- **应用系统**: http://localhost:8000
- **Prometheus指标**: http://localhost:8000/metrics
- **Prometheus UI**: http://localhost:9090
- **Grafana**: http://localhost:3000

## 故障排查

### 问题1: Prometheus无法抓取指标
**检查**:
1. 确认应用服务器运行在8000端口
2. 访问 http://localhost:8000/metrics 验证指标端点
3. 检查prometheus.yml中的targets配置

### 问题2: Grafana无数据显示
**检查**:
1. 确认Prometheus数据源配置正确
2. 在Prometheus UI查询指标是否有数据
3. 检查仪表盘的时间范围设置

### 问题3: 告警不触发
**检查**:
1. 确认alert_rules.yml已加载（Prometheus UI → Status → Rules）
2. 检查告警条件是否满足
3. 确认Alertmanager配置正确
