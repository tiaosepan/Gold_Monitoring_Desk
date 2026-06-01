"""
反转检测服务单元测试
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database import Base, ReversalCondition, SGEPrice, RSSEvent, RSSSource, USTreasury, SystemConfig
from backend.services.reversal_detector import ReversalDetectorService


@pytest.fixture
def test_db():
    """创建测试数据库"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    # 添加测试配置
    configs = [
        SystemConfig(config_key='reversal_price_lookback_minutes', config_value='60'),
        SystemConfig(config_key='reversal_price_rebound_pct', config_value='1.2'),
        SystemConfig(config_key='reversal_price_ma_window', config_value='15'),
        SystemConfig(config_key='reversal_signal_window_minutes', config_value='180'),
        SystemConfig(config_key='us10y_drop_threshold_bp', config_value='1.0'),
        SystemConfig(config_key='us10y_drop_lookback_hours', config_value='24.0'),
    ]
    db.add_all(configs)
    db.commit()
    
    yield db
    
    db.close()


class TestReversalLevel:
    """反转等级计算测试"""
    
    def test_level_4_political_only(self, test_db):
        """测试Level 4：仅政治信号"""
        service = ReversalDetectorService(test_db)
        level = service.determine_reversal_level(
            price_signal=0,
            political_signal=1,
            war_signal=0,
            us10y_signal=0
        )
        assert level == 4, f"仅政治信号应为Level 4，实际: {level}"
    
    def test_level_3_political_and_war(self, test_db):
        """测试Level 3：政治+战争信号"""
        service = ReversalDetectorService(test_db)
        level = service.determine_reversal_level(
            price_signal=0,
            political_signal=1,
            war_signal=1,
            us10y_signal=0
        )
        assert level == 3, f"政治+战争信号应为Level 3，实际: {level}"
    
    def test_level_2_war_only(self, test_db):
        """测试Level 2：仅战争信号"""
        service = ReversalDetectorService(test_db)
        level = service.determine_reversal_level(
            price_signal=0,
            political_signal=0,
            war_signal=1,
            us10y_signal=0
        )
        assert level == 2, f"仅战争信号应为Level 2，实际: {level}"
    
    def test_level_1_price_or_us10y(self, test_db):
        """测试Level 1：仅价格或美债信号"""
        service = ReversalDetectorService(test_db)
        
        # 仅价格信号
        level = service.determine_reversal_level(
            price_signal=1,
            political_signal=0,
            war_signal=0,
            us10y_signal=0
        )
        assert level == 1, f"仅价格信号应为Level 1，实际: {level}"
        
        # 仅美债信号
        level = service.determine_reversal_level(
            price_signal=0,
            political_signal=0,
            war_signal=0,
            us10y_signal=1
        )
        assert level == 1, f"仅美债信号应为Level 1，实际: {level}"
    
    def test_level_0_no_signal(self, test_db):
        """测试Level 0：无信号"""
        service = ReversalDetectorService(test_db)
        level = service.determine_reversal_level(
            price_signal=0,
            political_signal=0,
            war_signal=0,
            us10y_signal=0
        )
        assert level == 0, f"无信号应为Level 0，实际: {level}"


class TestPriceCondition:
    """价格条件检测测试"""
    
    def test_price_rebound_trigger(self, test_db):
        """测试价格反弹触发"""
        service = ReversalDetectorService(test_db)
        
        # 添加15条价格数据，模拟反弹
        base_price = 2500.0
        for i in range(15):
            # 先下跌到2450，再反弹到2530（反弹3.3%）
            if i < 5:
                price = base_price - i * 10  # 下跌到2450
            else:
                price = 2450 + (i - 4) * 8  # 反弹
            
            sge_record = SGEPrice(
                fetched_at=datetime.now() - timedelta(minutes=15-i),
                shfe_price_cny_per_g=500.0,
                london_price_usd_per_oz=price,
                usdcny_rate=7.0,
                london_price_cny_per_g=490.0,
                premium_cny_per_g=10.0,
                poll_interval_seconds=60,
                both_markets_open=1,
                shfe_market_open=1,
                london_market_open=1,
                alert_triggered=0
            )
            test_db.add(sge_record)
        
        test_db.commit()
        
        signal, note = service.detect_price_condition()
        assert signal == 1, f"价格反弹超过1.2%应触发信号，note: {note}"


class TestPoliticalCondition:
    """政治条件检测测试"""
    
    def test_high_score_political_event(self, test_db):
        """测试高分政治事件触发"""
        service = ReversalDetectorService(test_db)
        
        # 添加RSS源
        source = RSSSource(
            name='测试源',
            url='http://test.com',
            category='political',
            is_active=1
        )
        test_db.add(source)
        test_db.commit()
        
        # 添加高分政治事件
        event = RSSEvent(
            fetched_at=datetime.now(),
            source_id=source.id,
            title='停火谈判达成协议',
            link='http://test.com/1',
            summary='测试摘要',
            published_at=datetime.now(),
            event_type='political',
            matched_keywords='停火,谈判,协议',
            content_hash='test123',
            impact_score=9,
            impact_level='高',
            impact_note='测试',
            is_pushed=0
        )
        test_db.add(event)
        test_db.commit()
        
        signal, note = service.detect_political_condition()
        assert signal == 1, f"高分政治事件应触发信号，note: {note}"


class TestWarCondition:
    """战争条件检测测试"""
    
    def test_high_score_war_event(self, test_db):
        """测试高分战争事件触发"""
        service = ReversalDetectorService(test_db)
        
        # 添加RSS源
        source = RSSSource(
            name='测试源',
            url='http://test.com',
            category='war',
            is_active=1
        )
        test_db.add(source)
        test_db.commit()
        
        # 添加高分战争事件
        event = RSSEvent(
            fetched_at=datetime.now(),
            source_id=source.id,
            title='战争停战协议签署',
            link='http://test.com/1',
            summary='测试摘要',
            published_at=datetime.now(),
            event_type='war',
            matched_keywords='停战,和平',
            content_hash='test456',
            impact_score=8,
            impact_level='高',
            impact_note='测试',
            is_pushed=0
        )
        test_db.add(event)
        test_db.commit()
        
        signal, note = service.detect_war_condition()
        assert signal == 1, f"高分战争事件应触发信号，note: {note}"


class TestUS10YCondition:
    """美债条件检测测试"""
    
    def test_us10y_drop_trigger(self, test_db):
        """测试美债下跌触发"""
        service = ReversalDetectorService(test_db)
        
        # 添加历史数据：从4.5%下跌到4.48%（下跌2bp）
        us10y_high = USTreasury(
            fetched_at=datetime.now() - timedelta(hours=12),
            yield_pct=4.50,
            yield_signal=0,
            source='Sina',
            tenor='10y'
        )
        test_db.add(us10y_high)
        
        us10y_low = USTreasury(
            fetched_at=datetime.now(),
            yield_pct=4.48,
            yield_signal=0,
            source='Sina',
            tenor='10y'
        )
        test_db.add(us10y_low)
        test_db.commit()
        
        signal, note = service.detect_us10y_condition()
        assert signal == 1, f"美债下跌2bp应触发信号（阈值1bp），note: {note}"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
