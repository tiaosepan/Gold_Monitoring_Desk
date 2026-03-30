# 贡献指南

感谢你对黄金监控中台项目的关注！本文档将指导你如何参与项目开发。

## 开发环境设置

### 1. 克隆仓库
```bash
git clone <repository-url>
cd Gold_Monitoring_Desk
```

### 2. 创建虚拟环境
```bash
python -m venv venv
.\venv\Scripts\activate.bat  # Windows
source venv/bin/activate     # Linux/Mac
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 初始化数据库
```bash
python recreate_db.py
```

### 5. 启动开发服务器
```bash
.\start.bat  # Windows
cd backend && python main.py  # Linux/Mac
```

## 项目结构

```
Gold_Monitoring_Desk/
├── backend/              # 后端核心代码
│   ├── api/             # API 路由
│   ├── services/        # 业务服务（监控、采集、检测）
│   ├── utils/           # 工具类（API 客户端、钉钉推送）
│   ├── database.py      # 数据库模型
│   ├── scheduler.py     # 定时任务调度
│   └── main.py          # 应用入口
├── static/              # 前端静态文件
├── database/            # SQLite 数据库文件
├── docs/                # 项目文档
│   ├── design/          # 设计文档
│   ├── guides/          # 使用指南
│   ├── issues/          # 问题记录
│   ├── assets/          # 文档资源
│   └── archive/         # 历史文档
├── scripts/             # 工具脚本
│   ├── check/           # 检查类脚本
│   ├── analyze/         # 分析类脚本
│   └── utils/           # 工具脚本
└── tests/               # 测试文件
```

## 代码规范

### Python 代码规范
- 遵循 PEP 8 规范
- 使用 4 个空格缩进
- 函数和类必须有文档字符串（docstring）
- 变量命名使用下划线命名法（snake_case）
- 类命名使用驼峰命名法（PascalCase）

### 示例
```python
def calculate_sge_premium(shfe_price: float, london_price: float, usd_cny: float) -> dict:
    """
    计算 SGE 溢价
    
    Args:
        shfe_price: 沪金价格（元/克）
        london_price: 伦敦金价格（美元/盎司）
        usd_cny: 美元兑人民币汇率
        
    Returns:
        包含溢价和溢价率的字典
    """
    international_price_cny = (london_price / 31.1035) * usd_cny
    premium = shfe_price - international_price_cny
    premium_rate = (premium / international_price_cny) * 100
    
    return {
        "premium": round(premium, 2),
        "premium_rate": round(premium_rate, 2)
    }
```

### JavaScript 代码规范
- 使用 2 个空格缩进
- 使用 const/let，避免使用 var
- 使用箭头函数
- 添加必要的注释

## 提交规范

### Commit Message 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型
- `feat`: 新功能
- `fix`: 修复 Bug
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 重构代码
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具链相关

### 示例
```
feat(sge): 添加沪金夜盘时段判断

- 新增 is_shfe_night_session() 函数
- 支持 21:00-02:30 夜盘交易时段
- 更新溢价计算逻辑

Closes #123
```

## 分支管理

### 主分支
- `main`: 生产环境代码，保持稳定

### 开发分支
- `develop`: 开发主分支
- `feature/*`: 功能开发分支
- `bugfix/*`: Bug 修复分支
- `hotfix/*`: 紧急修复分支

### 工作流程
1. 从 `develop` 创建功能分支
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. 开发并提交代码
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

3. 推送分支并创建 Pull Request
   ```bash
   git push origin feature/your-feature-name
   ```

4. 代码审查通过后合并到 `develop`

## 测试规范

### 单元测试
- 新功能必须包含单元测试
- 测试覆盖率应 > 80%
- 使用 pytest 框架

### 运行测试
```bash
pytest tests/
```

### 集成测试
- 在提交 PR 前进行完整的集成测试
- 确保所有 API 端点正常工作
- 验证定时任务正常执行

## 文档更新

### 何时更新文档
- 添加新功能时
- 修改 API 接口时
- 更改配置项时
- 修复重要 Bug 时

### 文档位置
- API 文档：自动生成（访问 `/docs`）
- 使用指南：`docs/guides/`
- 设计文档：`docs/design/`
- 问题记录：`docs/issues/`

## 问题反馈

### 提交 Issue
请在 Issue 中包含以下信息：
- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（Python 版本、操作系统等）
- 相关日志或截图

### Issue 模板
```markdown
## 问题描述
简要描述遇到的问题

## 复现步骤
1. 打开系统首页
2. 点击...
3. 观察到...

## 预期行为
应该显示...

## 实际行为
实际显示...

## 环境信息
- Python 版本: 3.11
- 操作系统: Windows 11
- 浏览器: Chrome 120

## 相关日志
粘贴相关日志
```

## 代码审查

### 审查要点
- 代码是否符合规范
- 逻辑是否正确
- 性能是否优化
- 安全性是否考虑
- 文档是否完整
- 测试是否充分

### 审查清单
- [ ] 代码符合规范
- [ ] 功能实现正确
- [ ] 包含单元测试
- [ ] 文档已更新
- [ ] 无安全隐患
- [ ] 性能可接受

## 版本发布

### 版本号规则
遵循语义化版本（Semantic Versioning）：
- `MAJOR.MINOR.PATCH`
- MAJOR: 不兼容的 API 修改
- MINOR: 向下兼容的功能新增
- PATCH: 向下兼容的问题修正

### 发布流程
1. 更新 `CHANGELOG.md`
2. 更新版本号（前端 + 后端）
3. 创建 Release Tag
4. 部署到生产环境

## 获取帮助

如有任何问题，欢迎通过以下方式联系：
- 提交 Issue
- 发送邮件到项目维护者
- 加入开发者讨论群

再次感谢你的贡献！🎉
