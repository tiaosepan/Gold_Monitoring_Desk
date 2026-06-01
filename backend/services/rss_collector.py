"""
RSS采集服务 - 完全匹配原系统（包含关键词匹配和影响评分）
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import feedparser
import aiohttp
import hashlib

from ..database import RSSSource, RSSEvent, UpdateRecord, DataSourceHealth
from ..utils import safe_float, rss_logger


class RSSCollectorService:
    """RSS采集服务"""
    
    # 政治事件关键词（完全匹配原系统）
    POLITICAL_KEYWORDS = {
        'positive': ['talks', '谈判', '停火', 'ceasefire', '外交', 'mediat', '斡旋', '会谈', 'corridor', '对话', 'dialogue', '协商', '磋商'],
        'negative': ['制裁', '冲突', '危机', '紧张', 'sanctions', 'conflict', 'crisis', 'tension'],
        'uncertain': ['可能', '或许', '据称', '传闻', 'may', 'might', 'reportedly', 'allegedly']
    }
    
    # 战争事件关键词（完全匹配原系统）
    WAR_KEYWORDS = {
        'positive': ['停战', '撤军', '和平', '重开', '休战', '护航', 'ceasefire', 'withdraw', 'peace', 'reopen', 'stabilize', 'stable', 'stabilizing', 'reclaim', 'reclaims', 'treaty', 'arms', 'truce', 'resum', 'shipping lane', '航道', '恢复', 'corridor'],
        'negative': ['袭击', '轰炸', '战争', '军事', '导弹', 'attack', 'bombing', 'war', 'military', 'missile', 'crisis', 'ration', 'reserves', 'shortage', 'loses', 'territory', 'conflict', 'invasion', 'strike', 'combat'],
        'uncertain': ['威胁', '警告', 'threat', 'warning', 'forces', 'nations', 'access', 'control']
    }
    
    # 负面词组（优先级最高，直接判定为负面）
    NEGATIVE_PHRASES = {
        'political': [
            '停火失败', '谈判破裂', '谈判失败', '外交破裂', '协议作废', '协议失效',
            'ceasefire failed', 'ceasefire collapse', 'talks collapsed', 'talks failed',
            'negotiations broke down', 'agreement void', 'treaty void'
        ],
        'war': [
            '停战失败', '和平破裂', '撤军失败', '重开受阻', '航道关闭',
            'peace failed', 'peace collapse', 'withdrawal failed', 'reopen blocked',
            'shipping lane closed', 'stabilization failed'
        ]
    }
    
    # 否定词（与正面词组合时变为负面）
    NEGATION_WORDS = ['不', '未', '没', '无', '非', 'not', 'no', 'never', 'without', 'failed', 'collapse']
    
    # 关键词权重（重要性不同）
    KEYWORD_WEIGHTS = {
        # 政治关键词权重
        '停火': 3.0,
        'ceasefire': 3.0,
        '谈判': 2.5,
        'talks': 2.5,
        '外交': 2.0,
        'mediat': 2.5,  # mediation/mediator
        '斡旋': 2.5,
        '会谈': 2.3,
        'corridor': 2.0,  # humanitarian/shipping corridor
        '对话': 1.8,
        'dialogue': 1.8,
        '协商': 2.0,
        '磋商': 2.0,
        '制裁': 2.5,
        'sanctions': 2.5,
        '危机': 2.0,
        'crisis': 2.0,
        '冲突': 2.0,
        'conflict': 2.0,
        # 战争关键词权重
        '停战': 3.0,
        '撤军': 2.8,
        'withdraw': 2.8,
        '和平': 2.5,
        'peace': 2.5,
        '袭击': 2.5,
        'attack': 2.5,
        '轰炸': 3.0,
        'bombing': 3.0,
        '导弹': 2.5,
        'missile': 2.5
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    def _match_keywords(self, text: str, event_type: str) -> tuple[List[str], int, int]:
        """
        匹配关键词并计算影响评分（增强版：支持上下文分析）
        
        改进点:
        1. 优先检测负面词组（如"停火失败"）
        2. 检测否定词+正面词组合（如"未能停火"）
        3. 使用关键词权重（重要关键词权重更高）
        4. 考虑时效性（新事件权重更高）
        
        Args:
            text: 文本内容
            event_type: 事件类型
            
        Returns:
            (匹配的关键词列表, 基础分, 调整分)
        """
        text_lower = text.lower()
        matched = []
        
        # 选择关键词集
        keywords = self.POLITICAL_KEYWORDS if event_type == 'political' else self.WAR_KEYWORDS
        negative_phrases = self.NEGATIVE_PHRASES.get(event_type, [])
        
        # === 阶段1: 优先检测负面词组（直接判定为负面） ===
        for phrase in negative_phrases:
            if phrase.lower() in text_lower:
                rss_logger.debug(f"检测到负面词组: {phrase}")
                # 负面词组直接返回低分
                return [f"[负面词组]{phrase}"], 5, -3
        
        # === 阶段2: 检测否定词+正面词组合 ===
        negation_found = False
        for neg_word in self.NEGATION_WORDS:
            for pos_keyword in keywords['positive']:
                # 检测否定词在正面词前5个字符内
                pattern1 = f"{neg_word}{pos_keyword}"
                pattern2 = f"{neg_word} {pos_keyword}"
                pattern3 = f"{neg_word}  {pos_keyword}"
                
                if pattern1.lower() in text_lower or pattern2.lower() in text_lower or pattern3.lower() in text_lower:
                    matched.append(f"[否定]{neg_word}+{pos_keyword}")
                    negation_found = True
                    rss_logger.debug(f"检测到否定上下文: {neg_word} + {pos_keyword}")
        
        if negation_found:
            # 有否定上下文，扣分
            return matched, 5, -2
        
        # === 阶段3: 正常关键词匹配（带权重） ===
        positive_score = 0.0
        negative_score = 0.0
        uncertain_count = 0
        
        # 匹配正面关键词（带权重）
        for keyword in keywords['positive']:
            if keyword.lower() in text_lower:
                weight = self.KEYWORD_WEIGHTS.get(keyword, 1.0)
                matched.append(keyword)
                positive_score += weight
                rss_logger.debug(f"正面关键词: {keyword} (权重: {weight})")
        
        # 匹配负面关键词（带权重）
        for keyword in keywords['negative']:
            if keyword.lower() in text_lower:
                weight = self.KEYWORD_WEIGHTS.get(keyword, 1.0)
                matched.append(keyword)
                negative_score += weight
                rss_logger.debug(f"负面关键词: {keyword} (权重: {weight})")
        
        # 匹配不确定关键词
        for keyword in keywords['uncertain']:
            if keyword.lower() in text_lower:
                uncertain_count += 1
        
        # === 阶段4: 计算最终分数 ===
        base_score = 5
        
        # 调整分数（基于权重加总）
        adjustment = 0
        
        # 正面分数转换：每1.0权重 = +1分
        adjustment += int(positive_score)
        
        # 负面分数转换：每1.0权重 = -1分
        adjustment -= int(negative_score)
        
        # 不确定词：每2个-1分
        adjustment -= uncertain_count // 2
        
        # 地缘缓和信号：如果有正面词且权重>2.0，额外+1分
        if positive_score >= 2.0:
            adjustment += 1
            rss_logger.debug("地缘缓和信号，额外+1分")
        
        # 地缘紧张升级：如果负面权重>正面权重，额外-1分
        if negative_score > positive_score:
            adjustment -= 1
            rss_logger.debug("地缘紧张升级，额外-1分")
        
        rss_logger.debug(f"评分计算: 基础分={base_score}, 正面权重={positive_score:.1f}, 负面权重={negative_score:.1f}, 调整分={adjustment}")
        
        return matched, base_score, adjustment
    
    def classify_event(self, title: str, summary: str, source_category: str) -> str:
        """
        分类RSS事件（完全匹配原系统逻辑）
        
        原系统分类规则（通过数据分析得出）：
        1. 优先检查"谈判类"关键词（talks, negotiation, ceasefire等）→ political
        2. 再检查"战争恢复类"关键词（resum, reopen, restore等）→ war
        3. 其他战争关键词（attack, bombing, military等）→ war
        4. 其他政治关键词 → political
        5. 都不匹配 → 使用源分类
        
        Args:
            title: 标题
            summary: 摘要
            source_category: 源分类
            
        Returns:
            事件类型 (political/war)
        """
        # 合并标题和摘要用于关键词匹配
        content = f"{title} {summary}".lower()
        
        # 定义"谈判类"关键词（优先归为political）
        negotiation_keywords = ['talks', '谈判', '停火', 'ceasefire', '外交', 'mediat', '斡旋', '会谈', '对话', 'dialogue', '协商', '磋商']
        
        # 定义"战争恢复类"关键词（归为war）
        war_recovery_keywords = ['resum', 'reopen', 'restore', '恢复', '重开', 
                                 'shipping lane', '航道', '护航', 'corridor']
        
        # 定义"纯战争类"关键词（归为war）
        pure_war_keywords = ['attack', 'bombing', 'war', 'military', 'missile', 
                            '袭击', '轰炸', '战争', '军事', '导弹', 
                            'invasion', 'strike', 'combat', 'conflict']
        
        # 优先级1: 检查谈判类关键词
        for kw in negotiation_keywords:
            if kw.lower() in content:
                return 'political'
        
        # 优先级2: 检查纯战争类关键词
        for kw in pure_war_keywords:
            if kw.lower() in content:
                return 'war'
        
        # 优先级3: 检查战争恢复类关键词
        for kw in war_recovery_keywords:
            if kw.lower() in content:
                return 'war'
        
        # 优先级4: 检查其他政治关键词
        for category in ['positive', 'negative', 'uncertain']:
            for keyword in self.POLITICAL_KEYWORDS[category]:
                if keyword.lower() in content:
                    return 'political'
        
        # 优先级5: 使用源分类
        return source_category
    
    def score_event(self, title: str, summary: str, event_type: str) -> tuple[int, str, List[str]]:
        """
        评估RSS事件影响分数
        
        Args:
            title: 标题
            summary: 摘要
            event_type: 事件类型
            
        Returns:
            (影响分数, 影响等级, 匹配的关键词)
        """
        # 合并标题和摘要
        text = f"{title} {summary}"
        
        # 匹配关键词并计算分数
        matched_keywords, base_score, adjustment = self._match_keywords(text, event_type)
        
        # 最终分数
        final_score = max(1, min(10, base_score + adjustment))
        
        # 确定影响等级
        if final_score >= 8:
            impact_level = '高'
        elif final_score >= 5:
            impact_level = '中'
        else:
            impact_level = '低'
        
        return final_score, impact_level, matched_keywords
    
    def _generate_impact_note(self, matched_keywords: List[str], base_score: int, adjustment: int, event_type: str) -> str:
        """
        生成影响说明
        
        Args:
            matched_keywords: 匹配的关键词
            base_score: 基础分
            adjustment: 调整分
            event_type: 事件类型
            
        Returns:
            影响说明
        """
        keywords = self.POLITICAL_KEYWORDS if event_type == 'political' else self.WAR_KEYWORDS
        
        positive_count = sum(1 for kw in matched_keywords if kw in keywords['positive'])
        negative_count = sum(1 for kw in matched_keywords if kw in keywords['negative'])
        
        notes = []
        
        if positive_count > 0:
            notes.append(f"利好词命中{positive_count}个")
        
        if negative_count > 0:
            notes.append(f"利空词命中{negative_count}个")
        
        # 检查不确定词
        text = ' '.join(matched_keywords)
        uncertain_count = sum(1 for kw in keywords['uncertain'] if kw in text.lower())
        if uncertain_count > 0:
            notes.append(f"低可信表态词命中{uncertain_count}个")
        
        # 地缘信号
        if positive_count > 0:
            notes.append("地缘缓和信号，升分")
        
        if negative_count > positive_count:
            notes.append("地缘紧张升级，降分")
        
        if not notes:
            notes.append("未命中明显风险词，按基础分")
        
        return '；'.join(notes)
    
    async def fetch_rss_feed(self, url: str) -> List[Dict]:
        """
        获取RSS源数据
        
        Args:
            url: RSS源地址
            
        Returns:
            事件列表
        """
        # 添加请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            
            content = await response.text()
        
        # 解析RSS
        feed = feedparser.parse(content)
        
        events = []
        for entry in feed.entries:
            events.append({
                'title': entry.get('title', ''),
                'summary': entry.get('summary', entry.get('description', '')),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'published_parsed': entry.get('published_parsed', None)
            })
        
        return events
    
    async def collect_from_source(self, source: RSSSource) -> Dict:
        """
        从单个RSS源采集数据
        
        Args:
            source: RSS源
            
        Returns:
            采集结果
        """
        rss_logger.debug(f"开始采集RSS源: {source.name} - {source.url}")
        
        try:
            feed_start = datetime.now()
            events = await self.fetch_rss_feed(source.url)
            feed_duration = int((datetime.now() - feed_start).total_seconds() * 1000)
            
            rss_logger.debug(f"RSS源响应 - {source.name} - 耗时: {feed_duration}ms - 获取 {len(events)} 条原始事件")
            
            new_count = 0
            
            for event_data in events:
                # 生成内容哈希（用于去重）
                content = f"{event_data['title']}{event_data['summary']}"
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                content_hash_with_type = f"{content_hash}:{source.category}"
                
                # 检查是否已存在
                existing = self.db.query(RSSEvent).filter_by(
                    content_hash=content_hash_with_type
                ).first()
                
                if existing:
                    continue
                
                # 分类和评分
                event_type = self.classify_event(
                    event_data['title'],
                    event_data['summary'],
                    source.category
                )
                
                impact_score, impact_level, matched_keywords = self.score_event(
                    event_data['title'],
                    event_data['summary'],
                    event_type
                )
                
                # 【关键筛选】只保存命中关键词的事件（完全匹配原系统）
                if not matched_keywords:
                    continue
                
                # 生成影响说明
                _, base_score, adjustment = self._match_keywords(content, event_type)
                impact_note = self._generate_impact_note(matched_keywords, base_score, adjustment, event_type)
                
                # 解析发布时间（带时区信息）
                published_at = None
                if event_data['published_parsed']:
                    try:
                        from time import struct_time
                        import time
                        from datetime import timezone
                        # 使用UTC时区
                        published_at = datetime.fromtimestamp(
                            time.mktime(event_data['published_parsed']),
                            tz=timezone.utc
                        )
                    except:
                        pass
                
                # 保存事件
                rss_event = RSSEvent(
                    fetched_at=datetime.now(),
                    source_id=source.id,
                    feed_url=source.url,
                    title=event_data['title'],
                    link=event_data['link'],
                    summary=event_data['summary'],
                    published_at=published_at,
                    event_type=event_type,
                    matched_keywords=','.join(matched_keywords),
                    content_hash=content_hash_with_type,
                    impact_score=impact_score,
                    impact_level=impact_level,
                    impact_note=impact_note,
                    is_pushed=0
                )
                
                self.db.add(rss_event)
                new_count += 1
            
            self.db.commit()
            
            rss_logger.info(f"RSS源采集完成 - {source.name} - 新增: {new_count}/{len(events)}")
            
            return {
                'source': source.name,
                'success': True,
                'new_count': new_count,
                'total_count': len(events)
            }
            
        except Exception as e:
            rss_logger.error(f"RSS采集错误 - {source.name} - URL: {source.url} - 错误: {str(e)}", exc_info=True)
            return {
                'source': source.name,
                'success': False,
                'error': str(e),
                'new_count': 0,
                'total_count': 0
            }
    
    async def collect_all(self) -> Dict:
        """
        从所有活跃的RSS源采集数据
        
        Returns:
            采集结果汇总
        """
        start_time = datetime.now()
        rss_logger.info("开始RSS采集任务")
        
        # 获取所有活跃的RSS源
        sources = self.db.query(RSSSource).filter_by(is_active=1).all()
        
        if not sources:
            rss_logger.warning("没有配置活跃的RSS源")
            return {
                'success': False,
                'message': '没有活跃的RSS源',
                'total_sources': 0,
                'success_count': 0,
                'total_new_events': 0,
                'results': []
            }
        
        rss_logger.info(f"找到 {len(sources)} 个活跃RSS源")
        
        results = []
        success_count = 0
        total_new_events = 0
        error_count = 0
        
        for source in sources:
            result = await self.collect_from_source(source)
            results.append(result)
            
            if result['success']:
                success_count += 1
                total_new_events += result['new_count']
            else:
                error_count += 1
        
        # 记录更新日志
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        update_record = UpdateRecord(
            data_type='rss_events',
            status='success' if success_count > 0 else 'failed',
            record_count=total_new_events,
            error_message=f'{error_count}个源失败' if error_count > 0 else None
        )
        self.db.add(update_record)
        
        # 更新数据源健康状态
        self._update_data_source_health(
            'RSS Sources',
            'healthy' if success_count > 0 else 'error',
            f'{error_count}个源失败' if error_count > 0 else None
        )
        
        self.db.commit()
        
        rss_logger.info(
            f"RSS采集任务完成 - 耗时: {duration_ms}ms - "
            f"成功源: {success_count}/{len(sources)} - 新增事件: {total_new_events} - 错误: {error_count}"
        )
        
        return {
            'success': True,
            'message': f'RSS采集完成',
            'duration_ms': duration_ms,
            'item_count': total_new_events,
            'error_count': error_count,
            'total_sources': len(sources),
            'success_count': success_count,
            'total_new_events': total_new_events,
            'results': results
        }
    
    def _update_data_source_health(self, source_name: str, status: str, error_message: Optional[str]):
        """更新数据源健康状态"""
        health = self.db.query(DataSourceHealth).filter_by(source_name=source_name).first()
        
        if health:
            health.status = status
            health.updated_at = datetime.now()
            
            if status == 'healthy':
                health.last_success_at = datetime.now()
                health.error_count = 0
            else:
                health.last_error_at = datetime.now()
                health.error_count += 1
        else:
            health = DataSourceHealth(
                source_name=source_name,
                status=status,
                last_success_at=datetime.now() if status == 'healthy' else None,
                last_error_at=datetime.now() if status != 'healthy' else None,
                error_count=0 if status == 'healthy' else 1
            )
            self.db.add(health)
    
    def get_recent_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict]:
        """
        获取最近的RSS事件
        
        Args:
            limit: 返回记录数
            event_type: 事件类型过滤
            
        Returns:
            事件列表
        """
        query = self.db.query(RSSEvent)
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        records = query.order_by(RSSEvent.fetched_at.desc()).limit(limit).all()
        
        return [{
            'id': r.id,
            'fetched_at': r.fetched_at.isoformat(),
            'published_at': r.published_at.isoformat() if r.published_at else None,
            'source': r.source.name if r.source else 'Unknown',
            'feed_url': r.feed_url,
            'title': r.title,
            'link': r.link,
            'summary': r.summary,
            'event_type': r.event_type,
            'matched_keywords': r.matched_keywords,
            'content_hash': r.content_hash,
            'impact_score': r.impact_score,
            'impact_level': r.impact_level,
            'impact_note': r.impact_note,
            'is_pushed': r.is_pushed
        } for r in records]
    
    def get_high_score_events(self, threshold: int = 7, limit: int = 50) -> List[Dict]:
        """
        获取高分事件
        
        Args:
            threshold: 分数阈值
            limit: 返回记录数
            
        Returns:
            高分事件列表
        """
        records = self.db.query(RSSEvent).filter(
            RSSEvent.impact_score >= threshold
        ).order_by(RSSEvent.impact_score.desc()).limit(limit).all()
        
        return [{
            'id': r.id,
            'fetched_at': r.fetched_at.isoformat(),
            'title': r.title,
            'event_type': r.event_type,
            'category': r.event_type,  # 别名，用于调度器
            'impact_score': r.impact_score,
            'score': r.impact_score,  # 别名，用于调度器
            'impact_level': r.impact_level,
            'matched_keywords': r.matched_keywords,
            'source_name': r.source.name if r.source else 'Unknown',
            'link': r.link
        } for r in records]
    
    def mark_as_pushed(self, event_id: int):
        """
        标记事件为已推送
        
        Args:
            event_id: 事件ID
        """
        event = self.db.query(RSSEvent).filter_by(id=event_id).first()
        if event:
            event.is_pushed = 1
            self.db.commit()
