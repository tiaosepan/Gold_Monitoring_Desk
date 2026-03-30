# 🛠️ 工具脚本说明

本文件夹包含项目维护和测试用的工具脚本。

## 📂 脚本分类

```
scripts/
├── check/      # 检查类脚本 - 数据验证、状态检查
├── test/       # 测试类脚本 - 功能测试、数据测试
├── clean/      # 清理类脚本 - 数据清理、维护工具
├── analyze/    # 分析类脚本 - 数据分析、对比工具
└── utils/      # 通用工具 - 辅助脚本、配置工具
```

---

## 🔍 检查类脚本 (check/)

用于验证数据和系统状态

| 脚本 | 用途 | 用法 |
|------|------|------|
| `check_latest_data.py` | 检查最新数据 | `python scripts\check\check_latest_data.py` |
| `check_sge_data.py` | 检查SGE数据完整性 | `python scripts\check\check_sge_data.py` |
| `check_raw_data.py` | 检查原始数据 | `python scripts\check\check_raw_data.py` |
| `check_1h_data.py` | 检查1小时数据 | `python scripts\check\check_1h_data.py` |
| `check_anomaly.py` | 检查数据异常 | `python scripts\check\check_anomaly.py` |
| `check_extremes.py` | 检查极值数据 | `python scripts\check\check_extremes.py` |
| `check_au9999_range.py` | 检查AU9999数据范围 | `python scripts\check\check_au9999_range.py` |
| `check_high_frequency_data.py` | 检查高频数据问题 | `python scripts\check\check_high_frequency_data.py` |

### 常用检查命令

```bash
# 快速检查最新数据状态
python scripts\check\check_latest_data.py

# 检查SGE数据质量
python scripts\check\check_sge_data.py

# 检查是否有异常数据
python scripts\check\check_anomaly.py
```

---

## 🧪 测试类脚本 (test/)

用于功能测试和数据验证

| 脚本 | 用途 | 用法 |
|------|------|------|
| `test_au9999.py` | 测试AU9999数据采集 | `python scripts\test\test_au9999.py` |
| `test_au9999_detailed.py` | AU9999详细测试 | `python scripts\test\test_au9999_detailed.py` |
| `test_data_sources.py` | 测试所有数据源 | `python scripts\test\test_data_sources.py` |
| `test_parsing_logic.py` | 测试解析逻辑 | `python scripts\test\test_parsing_logic.py` |
| `test_parsing_simple.py` | 测试简单解析 | `python scripts\test\test_parsing_simple.py` |

### 常用测试命令

```bash
# 测试所有数据源连通性
python scripts\test\test_data_sources.py

# 测试AU9999数据采集
python scripts\test\test_au9999.py

# 测试数据解析逻辑
python scripts\test\test_parsing_logic.py
```

---

## 🧹 清理类脚本 (clean/)

用于数据库维护和清理

| 脚本 | 用途 | 用法 |
|------|------|------|
| `clean_old_data.py` | 清理旧数据 | `python scripts\clean\clean_old_data.py` |
| `clean_reversal_data.py` | 清理反转数据 | `python scripts\clean\clean_reversal_data.py` |
| `clean_high_frequency_data.py` | 清理高频重复数据 | `python scripts\clean\clean_high_frequency_data.py` |

### 常用清理命令

```bash
# 清理7天前的旧数据
python scripts\clean\clean_old_data.py

# 清理高频重复数据（同一分钟内的重复数据）
python scripts\clean\clean_high_frequency_data.py

# 清理反转检测数据
python scripts\clean\clean_reversal_data.py
```

---

## 📊 分析类脚本 (analyze/)

用于数据分析和系统对比

查看 `analyze/` 文件夹内的脚本文件

---

## 🔧 通用工具 (utils/)

通用辅助脚本和配置工具

| 脚本 | 用途 |
|------|------|
| `check_data_sources.py` | 检查所有数据源健康状态 |
| `disable_bad_rss_sources.py` | 禁用异常的RSS源 |
| `test_scheduler.py` | 测试调度器性能 |
| `add_database_indexes.py` | 添加数据库索引 |

### 常用工具命令

```bash
# 检查数据源状态
python scripts\utils\check_data_sources.py

# 禁用失败的RSS源
python scripts\utils\disable_bad_rss_sources.py

# 测试调度器执行时间
python scripts\utils\test_scheduler.py --mode timing

# 添加数据库性能索引
python scripts\utils\add_database_indexes.py
```

---

## 💡 使用建议

### 日常维护流程

1. **启动前检查**
   ```bash
   python scripts\check\check_latest_data.py
   ```

2. **定期清理**（每周）
   ```bash
   python scripts\clean\clean_old_data.py
   python scripts\clean\clean_high_frequency_data.py
   ```

3. **数据源监控**（每天）
   ```bash
   python scripts\utils\check_data_sources.py
   ```

### 故障排查流程

1. 检查最新数据状态
2. 检查是否有异常数据
3. 查看系统日志
4. 测试数据源连通性

```bash
python scripts\check\check_latest_data.py
python scripts\check\check_anomaly.py
python scripts\test\test_data_sources.py
```

---

## 🔗 相关文档

- [项目主文档](../README.md) - 系统概述和安装指南
- [文档导航](../docs/README.md) - 完整文档索引
- [快速参考](../docs/guides/快速参考.md) - 常用命令速查

---

**最后更新**: 2026-03-30
