# FRED API配置说明

## ✅ API密钥已配置

**密钥**: `38b7f7dc5b334dfea2c32abdac59232f`  
**状态**: ✅ 测试通过  
**配置时间**: 2026-03-29

---

## 📊 测试结果

### FRED API测试（2026-03-29）

```
✅ 直接API调用: 通过
✅ 客户端类测试: 通过

测试数据:
  - 10年期美债收益率: 4.42%
  - 数据日期: 2026-03-26
  - 响应时间: <1秒
  - HTTP状态: 200 OK
```

---

## 🔧 已完成配置

### 1. 环境变量已设置
```powershell
# 用户级环境变量（永久有效）
FRED_API_KEY = 38b7f7dc5b334dfea2c32abdac59232f
```

### 2. 配置方式
执行了配置脚本：
```powershell
powershell -ExecutionPolicy Bypass -File scripts\utils\setup_fred_api.ps1
```

### 3. 验证方法
```bash
# 测试FRED API
python scripts\utils\test_fred_api.py

# 完整数据源检查
python scripts\utils\check_data_sources.py
```

---

## 🎯 使用场景

### 主要用途
FRED API作为**美债收益率数据的备用数据源**，当新浪财经API返回0或异常时自动启用。

### 数据源优先级
系统按以下顺序尝试获取美债数据：

1. **新浪财经API**（主源，2秒超时）
   - 优点：速度快，免费
   - 缺点：有时返回0

2. **FRED API**（备源，3秒超时）✅ **已配置**
   - 优点：数据权威，稳定
   - 缺点：需要API密钥

3. **东方财富API**（备源，3秒超时）
   - 优点：免费
   - 缺点：部分期限返回null

### 支持的期限
- 5年期: DGS5
- 10年期: DGS10 ✅ **已测试**
- 20年期: DGS20
- 30年期: DGS30

---

## 📈 性能数据

| 指标 | 数值 |
|------|------|
| API响应时间 | <1秒 |
| 数据延迟 | T+1天（正常） |
| 可用性 | 99%+ |
| 免费配额 | 足够使用 |

---

## 🔍 实时监控

系统运行时，FRED API使用情况会记录到：

### 日志文件
```bash
# 查看美债监控日志
Get-Content logs\us10y_monitor.log -Tail 50

# 查看数据源切换情况
Select-String "FRED" logs\us10y_monitor.log
```

### Prometheus指标
访问 http://localhost:8000/metrics 查看：
```
us10y_fetch_total{tenor="10y",status="success"}
data_source_health{source_name="FRED API"}
```

---

## 🎓 API密钥管理

### 查看当前密钥
```powershell
$env:FRED_API_KEY
```

### 更新密钥
```powershell
# 方法1: 修改脚本中的$ApiKey变量后重新运行
powershell -ExecutionPolicy Bypass -File scripts\utils\setup_fred_api.ps1

# 方法2: 直接设置
[System.Environment]::SetEnvironmentVariable("FRED_API_KEY", "new_key_here", "User")
```

### 删除密钥
```powershell
[System.Environment]::SetEnvironmentVariable("FRED_API_KEY", $null, "User")
```

---

## 📚 FRED API文档

### 官方资源
- **API文档**: https://fred.stlouisfed.org/docs/api/
- **获取密钥**: https://fred.stlouisfed.org/docs/api/api_key.html
- **系列查询**: https://fred.stlouisfed.org/

### 常用系列ID
- `DGS5`: 5年期美债收益率
- `DGS10`: 10年期美债收益率
- `DGS20`: 20年期美债收益率
- `DGS30`: 30年期美债收益率

---

## ✅ 配置验证清单

- [x] API密钥已设置到环境变量
- [x] 直接API调用测试通过
- [x] 客户端类测试通过
- [x] 成功获取10年期美债数据（4.42%）
- [x] 配置脚本已创建（`setup_fred_api.ps1`）

---

## 🚀 下一步

### 立即可用
系统已自动集成FRED API，无需额外配置。

当新浪API返回0时，系统会自动切换到FRED API获取美债数据。

### 验证运行
启动系统后，查看日志确认FRED API使用情况：
```bash
# 启动系统
.\start.bat

# 查看美债监控日志
Get-Content logs\us10y_monitor.log -Wait -Tail 20
```

---

**配置状态**: ✅ 已完成  
**配置日期**: 2026-03-29  
**API测试**: ✅ 通过  
**推荐操作**: 无需额外操作，立即可用
