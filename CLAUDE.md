# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

黄金监控中台（Gold Monitoring Desk）- 复刻自 http://rev.sccit.com.cn:8000 的实时黄金价格监控系统。

核心功能：监控 SGE（上海黄金交易所）溢价、检测黄金价格反转信号、追踪美债收益率变化、采集地缘政治/战争 RSS 事件；**不**进行钉钉等外发消息推送（警报仅日志与站内展示）。

## 快速启动

```bash
# Windows 启动（推荐 - 自动清理旧进程）
.\start.bat

# 或手动安全启动
python safe_start.py

# 或直接启动（不推荐 - 可能导致多进程）
cd backend
python main.py

# 访问系统
http://localhost:8000
```

**⚠️ 重要提示**：
- 推荐使用 `start.bat` 或 `safe_start.py` 启动，自动防止多进程
- 避免直接运行 `python main.py`，除非确认没有旧进程
- 系统使用进程锁，启动时会自动检测并拒绝多实例运行

## 技术栈

**后端**：Python 3.11+ / FastAPI / SQLAlchemy / aiohttp / APScheduler
**前端**：原生 JavaScript / ECharts 5
**数据库**：SQLite

## 项目结构

```
backend/
├── main.py              # FastAPI 入口，端口 8000
├── database.py          # SQLAlchemy 模型和初始化
├── scheduler.py         # APScheduler 定时任务调度器
├── api/routes.py        # API 路由定义
├── services/
│   ├── sge_monitor.py       # SGE 价格采集和溢价计算
│   ├── reversal_detector.py # 黄金反转信号检测（4级）
│   ├── us10y_monitor.py     # 美债收益率监控
│   └── rss_collector.py     # RSS 新闻采集和评分
├── utils/
│   ├── goldapi_client.py # Gold-API 客户端（国际金价主源）
│   ├── sina_api.py      # 新浪财经 API 客户端（备用+国内数据）
│   └── fred_api.py      # FRED API 客户端（美债备源）
static/
├── index.html           # 前端页面
├── app.js               # 前端逻辑（ECharts 图表）
└── style.css            # 样式表
```

## 常用命令

```bash
# 初始化/重建数据库
python recreate_db.py

# 激活虚拟环境
.\venv\Scripts\activate.bat

# 安装依赖
pip install -r requirements.txt

# API 文档
http://localhost:8000/docs
```

## 核心数据流

1. **SGE 溢价监控**：主备数据源架构（2026-03-30 优化）
 - **国际金价**：新浪财经 hf_XAU（主，~10秒更新）→ Gold-API（备，5分钟更新） - 自动切换
 - **沪金价格**：新浪财经 nf_AU0（沪金连续）
 - **汇率**：新浪财经 USDCNY
 - **采集频率**：60秒一次
 - **计算溢价** = 沪金价格 - (国际金价 × 汇率 ÷ 31.1035)
 - 注意：nf_AU0 在非交易时段仍有有效报价，始终使用 API 返回值计算溢价
 - 仅当溢价异常（<0 或 >20 元/克）且市场关闭时，才使用历史平均溢价作为代理
2. **反转检测**：4 类信号（价格 MA15 反弹/政治 RSS/战争 RSS/美债下跌）→ 综合评级 Level 0-4
3. **RSS 评分**：关键词匹配 → 1-10 分体系 → 高分事件参与反转评分
4. **警报**：调度器对满足条件的信号写日志（`scheduler` 日志），不调用外发 Webhook

## API 端点

- `GET /api/status` - 完整系统状态
- `GET /api/sge/latest` - 最新 SGE 数据
- `GET /api/reversal/latest` - 最新反转状态
- `GET /api/us10y/latest` - 最新美债数据
- `GET /api/rss/events` - RSS 事件列表

## 配置说明

- FRED API 密钥（可选）：`$env:FRED_API_KEY="your_key"` 用于美债备用数据源
- 阈值参数：存储在 `system_config` 表（溢价/轮询间隔/信号窗口等）

## 数据源（主备架构）

### 国际金价数据源
- **主数据源：新浪财经 hf_XAU** - `hq.sinajs.cn` - 伦敦金(hf_XAU)
 - 优势：准实时更新（约10秒）、响应极快（~15ms）
 - 更新频率：约10秒一次
 - 稳定性高，适合实时监控
 - GBK 编码，需要特殊处理
- **备用数据源：Gold-API.com** - `api.gold-api.com` - XAU 现货价格（美元/盎司）
 - 主数据源失败时自动切换
 - 更新频率：5分钟一次
 - 标准 JSON 格式、稳定性高
 - 响应速度：~1-2 秒
 - 免费版无需 API 密钥

### 国内黄金和汇率数据源
- **新浪财经**：`hq.sinajs.cn` - 沪金(nf_AU0 沪金连续)、汇率(USDCNY)、美债(GB10YR)
  - 国内独有数据，无其他数据源可替代

### 其他数据源
- **东方财富**：美债收益率备用数据源
- **FRED API**：美债备用数据源，需要 API 密钥
