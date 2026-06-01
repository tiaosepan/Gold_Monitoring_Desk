"""
RSS采集服务单元测试
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database import Base, RSSSource, RSSEvent
from backend.services.rss_collector import RSSCollectorService


@pytest.fixture
def test_db():
    """创建测试数据库"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    yield db
    
    db.close()


class TestEventClassification:
    """事件分类测试"""
    
    def test_classify_negotiation_as_political(self, test_db):
        """测试谈判类事件分类为political"""
        service = RSSCollectorService(test_db)
        
        # 测试用例1：包含"talks"
        event_type = service.classify_event(
            "Peace talks resume in Geneva",
            "Negotiators meet to discuss ceasefire",
            "war"  # 源分类为war
        )
        assert event_type == 'political', "包含talks应归为political"
        
        # 测试用例2：包含"停火"
        event_type = service.classify_event(
            "各方达成停火协议",
            "经过谈判达成共识",
            "war"
        )
        assert event_type == 'political', "包含停火应归为political"
    
    def test_classify_pure_war_event(self, test_db):
        """测试纯战争事件分类"""
        service = RSSCollectorService(test_db)
        
        # 测试用例：包含"attack"
        event_type = service.classify_event(
            "Military strike continues",
            "Attack on strategic targets",
            "political"  # 源分类为political
        )
        assert event_type == 'war', "包含attack应归为war"
    
    def test_classify_war_recovery(self, test_db):
        """测试战争恢复类事件分类"""
        service = RSSCollectorService(test_db)
        
        # 测试用例：包含"resum"
        event_type = service.classify_event(
            "Shipping lanes resume operations",
            "Trade routes reopen after conflict",
            "political"
        )
        assert event_type == 'war', "包含resum应归为war"
    
    def test_classify_fallback_to_source(self, test_db):
        """测试回退到源分类"""
        service = RSSCollectorService(test_db)
        
        # 测试用例：无关键词
        event_type = service.classify_event(
            "Economic report released",
            "GDP growth data",
            "political"
        )
        assert event_type == 'political', "无关键词应使用源分类"


class TestEventScoring:
    """事件评分测试"""
    
    def test_score_high_positive_event(self, test_db):
        """测试高分利好事件"""
        service = RSSCollectorService(test_db)
        
        # 测试用例：停火+谈判+协议（3个利好词）
        score, level, keywords = service.score_event(
            "停火谈判达成协议",
            "各方同意停火并开始外交谈判",
            "political"
        )
        
        # 基础分5 + 利好词3个+1 + 有利好词+1 = 9分
        assert score >= 8, f"多个利好词应得高分，实际: {score}"
        assert level == '高', f"高分事件应为'高'等级，实际: {level}"
        assert len(keywords) >= 3, f"应匹配至少3个关键词，实际: {keywords}"
    
    def test_score_negative_event(self, test_db):
        """测试低分利空事件"""
        service = RSSCollectorService(test_db)
        
        # 测试用例：制裁+冲突+危机（3个利空词）
        score, level, keywords = service.score_event(
            "制裁升级引发冲突",
            "地缘危机加剧紧张局势",
            "political"
        )
        
        # 基础分5 - 利空词4个-1 - 利空多于利好-1 = 0分 → 最低1分
        assert score <= 3, f"多个利空词应得低分，实际: {score}"
        assert level == '低', f"低分事件应为'低'等级，实际: {level}"
    
    def test_score_neutral_event(self, test_db):
        """测试中性事件"""
        service = RSSCollectorService(test_db)
        
        # 测试用例：无明显关键词
        score, level, keywords = service.score_event(
            "Economic data released",
            "Latest statistics published",
            "political"
        )
        
        # 无关键词会被过滤，但这里测试评分逻辑
        assert 1 <= score <= 10, f"评分应在1-10之间，实际: {score}"


class TestKeywordMatching:
    """关键词匹配测试"""
    
    def test_match_political_positive(self, test_db):
        """测试政治利好词匹配"""
        service = RSSCollectorService(test_db)
        
        text = "停火谈判取得重大进展，各方同意外交对话"
        matched, base_score, adjustment = service._match_keywords(text, 'political')
        
        assert len(matched) >= 3, f"应匹配至少3个关键词，实际: {matched}"
        assert adjustment > 0, f"利好词应增加分数，实际adjustment: {adjustment}"
    
    def test_match_war_positive(self, test_db):
        """测试战争利好词匹配"""
        service = RSSCollectorService(test_db)
        
        text = "停战协议签署，军队撤军，和平进程重开"
        matched, base_score, adjustment = service._match_keywords(text, 'war')
        
        assert len(matched) >= 3, f"应匹配至少3个关键词，实际: {matched}"
        assert adjustment > 0, f"利好词应增加分数，实际adjustment: {adjustment}"
    
    def test_match_mixed_keywords(self, test_db):
        """测试混合关键词匹配"""
        service = RSSCollectorService(test_db)
        
        text = "谈判取得进展但制裁仍在继续"
        matched, base_score, adjustment = service._match_keywords(text, 'political')
        
        # 包含利好词（谈判）和利空词（制裁）
        assert len(matched) >= 2, f"应匹配至少2个关键词，实际: {matched}"


class TestEventFiltering:
    """事件筛选测试"""
    
    def test_filter_events_without_keywords(self, test_db):
        """测试过滤无关键词的事件"""
        service = RSSCollectorService(test_db)
        
        # 无关键词的事件
        score, level, keywords = service.score_event(
            "Economic growth continues",
            "GDP data shows positive trend",
            "political"
        )
        
        # 虽然会返回评分，但在collect_from_source中会被过滤
        # 这里验证关键词列表为空
        assert len(keywords) == 0, "无关键词事件应返回空关键词列表"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
