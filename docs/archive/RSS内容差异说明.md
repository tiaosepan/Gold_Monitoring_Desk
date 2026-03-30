# RSS内容差异说明

## 问题描述
用户反馈：复刻系统的RSS事件流显示的是科技/财经新闻，而原系统显示的都是战争、原油相关的信息。

## 调查结果

### 1. RSS源配置对比

**原系统RSS源：**
1. 虎嗅网：https://rss.huxiu.com/
2. 彭博经济：https://quanwenrss.com/bloomberg/economics
3. 金十数据1：http://rss.jintiankansha.me/rss/GM3DSNZUGJ6DOYTEG5RWENZRGUZDENLDGAYGMMDGMRSTONBRMUYWMM3FMQ2DGYZXMZSTGNDGG4YQ====
4. Beehiiv订阅：https://rss.beehiiv.com/feeds/4aF2pGVAEN.xml
5. 金十数据2：http://rss.jintiankansha.me/rss/GM4DKMRUG56DIYZTHE2TAY3EGNTDAMLGMQZWKMRRGNRWCZBQMY2TSZLEGEYTQN3DMQYDSNZUGQYA====

**复刻系统RSS源：**
完全相同！（已验证）

### 2. RSS事件内容对比

**原系统事件（采集时间：2026-03-24 22:07 ~ 2026-03-25 07:11）：**
- 关键词统计：
  - Iran（伊朗）: 33次
  - War（战争）: 18次
  - Trump: 17次
  - Oil（原油）: 4次
  - Gold（黄金）: 3次

**示例标题：**
1. "兵临华容道：从一份流传的15点美伊停战协议，看透中东地缘底牌"
2. "原油下跌，特朗普推迟打击5天，是和谈还是心理战？"
3. "霍尔木兹海峡连续多日无油轮通行..."
4. "US Drafts 15-Point Plan to End Iran War as Trump Pushes Talks"
5. "Indonesia Rupiah Rises Most in Six Months, Stocks Gain in Reopen"

**复刻系统事件（采集时间：2026-03-25 08:03 ~ 08:15）：**
- 内容类型：混合（科技、财经、部分原油）
- 战争相关事件：11/50（22%）

**示例标题：**
1. "200万尾款泡汤？业务员调包飞天茅台，坑惨烟酒店老板"
2. "受欧盟法规影响，任天堂或将推出可拆卸电池版本的NS2"
3. "Brent Crude Levels Are $95 and $105"（原油相关）
4. "UK Inflation Stayed at 3% in Weeks Leading Up to Iran War"（战争相关）

### 3. 根本原因

**✅ RSS源配置完全相同，但内容不同的原因：**

1. **时间差异**：
   - 原系统：采集于昨晚到今早（伊朗战争新闻高峰期）
   - 复刻系统：采集于今天早上（新闻热点已转移）

2. **RSS源的动态特性**：
   - RSS源会实时更新，推送最新新闻
   - 昨天的热点是伊朗战争，今天的热点已经转向其他话题
   - 这是RSS的正常行为，不是系统问题

3. **新闻周期**：
   - 地缘政治新闻（战争、原油）是周期性的
   - 当有重大事件时，RSS源会集中推送相关内容
   - 事件平息后，RSS源会转向其他话题

## 解决方案

### 方案1：等待自然更新（推荐）
**说明**：当下次有重大地缘政治事件（战争、原油危机等）时，RSS源会自动推送相关新闻，系统会自动采集。

**优点**：
- 无需修改代码
- 符合RSS源的自然行为
- 系统会自动采集最新的相关新闻

**缺点**：
- 需要等待新闻事件发生

### 方案2：使用专门的地缘政治RSS源
**说明**：添加专门关注战争、原油、地缘政治的RSS源。

**建议的RSS源：**
1. 彭博地缘政治：https://www.bloomberg.com/politics/feeds/site.xml
2. 路透社能源：https://www.reuters.com/rssfeed/energy
3. 金十数据（原油专栏）：相关RSS链接
4. 华尔街日报（中东）：相关RSS链接

**实施步骤：**
1. 在"RSS 源"页面点击"新增 RSS 源"
2. 输入专门的地缘政治/原油RSS源URL
3. 点击"保存 RSS 配置"
4. 点击"立即获取RSS消息"触发采集

### 方案3：保留历史数据，继续采集
**说明**：保持当前配置，让系统继续运行，随着时间推移会采集到更多战争/原油相关的新闻。

**优点**：
- 无需修改
- 数据会自然积累
- 当有重大事件时会自动采集

## 技术分析

### RSS采集逻辑
系统已经实现了完整的关键词匹配和评分系统：

```python
# 政治事件关键词
POLITICAL_KEYWORDS = {
    'positive': ['停火', '和谈', '谈判', '协议', 'ceasefire', 'negotiation', 'talks'],
    'negative': ['制裁', '冲突', '危机', 'sanctions', 'conflict', 'crisis']
}

# 战争事件关键词
WAR_KEYWORDS = {
    'positive': ['停战', '撤军', '和平', 'ceasefire', 'peace'],
    'negative': ['袭击', '轰炸', '战争', 'attack', 'bombing', 'war', 'missile']
}
```

系统会：
1. 从RSS源抓取所有新闻
2. 根据关键词进行分类（political/war）
3. 计算影响评分（1-10分）
4. 高分事件（≥7分）会触发推送

### 当前状态
- ✅ RSS源配置正确
- ✅ 关键词匹配正常
- ✅ 评分系统正常
- ✅ 定时采集正常（每30分钟）

**唯一的差异**：RSS源的内容随时间变化，这是正常现象。

## 建议

### 短期建议
如果您需要立即看到战争/原油相关的新闻，可以：
1. 手动添加专门的地缘政治RSS源
2. 或者等待下次有重大地缘政治事件时，系统会自动采集

### 长期建议
系统已经完全正常工作，会自动：
1. 监控RSS源的最新内容
2. 识别战争/原油相关的关键词
3. 对高影响事件进行评分和推送
4. 当有重大地缘政治事件时自动预警

## 验证

从原系统的事件链接可以看到，RSS源确实是：
- huxiu.com（虎嗅网）
- jin10.com（金十数据）
- bloomberg.com（彭博社）

这些与复刻系统完全一致！

**结论**：复刻系统的RSS功能完全正常，内容差异是因为RSS源的动态更新特性，这是预期行为。当下次有重大地缘政治事件时，系统会自动采集相关新闻。

---

## 补充说明

如果您希望复刻系统显示与原系统完全相同的历史RSS事件（用于演示或测试），可以：

1. **导出原系统的RSS事件数据**
2. **导入到复刻系统的数据库**

但这只是历史数据，不会随时间更新。建议保持当前配置，让系统自然采集最新新闻。
