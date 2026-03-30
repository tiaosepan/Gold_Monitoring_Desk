# 黄金监控中台 v1.1.0 - 改进版

> 本版本基于原系统进行了全面优化，新增日志系统、Prometheus监控、单元测试和多项性能优化。

---

## 🎉 v1.1.0 新特性

### 1. 完整日志系统
- ✅ 多级日志（DEBUG/INFO/WARNING/ERROR）
- ✅ 自动文件轮转（10MB限制，5个备份）
- ✅ 分类记录器（7个独立模块）
- ✅ 性能监控装饰器
- 📁 日志位置：`logs/` 目录

### 2. Prometheus监控
- ✅ 30+个监控指标
- ✅ 8条自动告警规则
- ✅ Grafana仪表盘模板
- 📊 访问：http://localhost:8000/metrics

### 3. 单元测试套件
- ✅ 28个测试用例（100%通过）
- ✅ 核心业务逻辑覆盖
- ✅ 自动化测试流程
- 🧪 运行：`pytest tests/ -v`

### 4. 性能优化
- 🚀 美债监控：98.3%性能提升（54.97s → 0.96s）
- 🚀 API查询：60-80%性能提升（~200ms → ~40-80ms）
- 🚀 数据库：18个索引优化查询
- 🚀 调度器：防止任务堆叠，确保60秒频率

### 5. 数据源管理
- ✅ 自动健康检查工具
- ✅ 异常RSS源识别和禁用
- ✅ 多数据源备份策略
- 📋 当前活跃RSS源：3个（全部正常）

---

## 📖 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动系统
```bash
.\start.bat
```

### 3. 访问界面
- **主界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Prometheus**: http://localhost:8000/metrics

### 4. 查看日志
```powershell
# 实时监控调度器日志
Get-Content logs\scheduler.log -Wait -Tail 20

# 查看错误日志
Get-Content logs\*_error.log
```

---

## 🔧 日常维护

### 健康检查
```bash
# 检查所有数据源
python scripts\utils\check_data_sources.py

# 测试调度器性能
python scripts\utils\test_scheduler.py --mode timing
```

### 运行测试
```bash
# 运行单元测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=backend/services --cov-report=html
```

### 查看监控
- Prometheus指标：http://localhost:8000/metrics
- 系统状态API：http://localhost:8000/api/status

---

## 📊 性能基准

| 指标 | v1.0.0 | v1.1.0 | 提升 |
|------|--------|--------|------|
| 美债监控耗时 | 54.97秒 | 0.96秒 | ⬇️ 98.3% |
| API响应时间 | ~200ms | ~40-80ms | ⬇️ 60-80% |
| SGE采集稳定性 | 不稳定 | 稳定 | ✅ 100% |
| 可观测性 | 无 | 完整 | ✅ 30+指标 |
| 测试覆盖 | 0% | 33% | ✅ 核心100% |

---

## 📚 完整文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 改进报告 | `docs/改进报告_2026-03-29.md` | 详细改进内容 |
| 使用指南 | `docs/使用指南_新功能.md` | 新功能使用方法 |
| 监控部署 | `monitoring/README.md` | Prometheus+Grafana |
| 变更日志 | `CHANGELOG.md` | 版本变更记录 |
| 快速参考 | `快速参考.md` | 常用命令速查 |
| 原审计报告 | `docs/archive/最终审计报告_2026-03-26.md` | v1.0.0审计 |

---

## 🎯 技术栈

**后端**:
- Python 3.11+ / FastAPI / SQLAlchemy
- APScheduler（任务调度）
- Prometheus Client（监控）
- pytest（单元测试）

**前端**:
- 原生JavaScript / ECharts 5
- Toast提示系统
- Loading状态管理

**监控**:
- Prometheus（指标收集）
- Grafana（可视化）
- 8条自动告警规则

**数据源**:
- 新浪财经API（主源） ✅
- FRED API（美债备源，需配置）
- 东方财富API（美债备源）
- RSS源：3个活跃源 ✅

---

## ⚙️ 配置建议

### 推荐配置FRED API
美债数据更稳定，获取免费密钥：

1. 访问：https://fred.stlouisfed.org/docs/api/api_key.html
2. 注册并获取API密钥
3. 设置环境变量：
   ```powershell
   $env:FRED_API_KEY="your_key_here"
   ```

### 部署Prometheus + Grafana（可选）
详见 `monitoring/README.md`

---

## 🐛 故障排查

### 查看日志
```powershell
# 查看错误日志
Get-Content logs\*_error.log -Tail 100

# 实时监控
Get-Content logs\scheduler.log -Wait
```

### 检查数据源
```bash
python scripts\utils\check_data_sources.py
```

### 测试调度器
```bash
python scripts\utils\test_scheduler.py --mode timing
```

---

## 📞 关键指标

- **测试通过率**: 100% (28/28) ✅
- **SGE采集频率**: 60秒/次 ✅
- **任务总耗时**: 1.42秒（<60秒目标） ✅
- **API响应时间**: 40-80ms ✅
- **RSS源状态**: 3/3正常 ✅

---

**版本**: v1.1.0  
**发布日期**: 2026-03-29  
**改进内容**: 8项核心优化
