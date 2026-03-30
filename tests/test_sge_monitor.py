"""
SGE监控服务单元测试
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database import Base, SGEPrice, SystemConfig
from backend.services.sge_monitor import SGEMonitorService
from backend.utils import oz_to_gram


@pytest.fixture
def test_db():
    """创建测试数据库"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    # 添加测试配置
    config = SystemConfig(
        config_key='premium_threshold',
        config_value='20.0',
        description='测试阈值'
    )
    db.add(config)
    db.commit()
    
    yield db
    
    db.close()


class TestPremiumCalculation:
    """溢价计算测试"""
    
    def test_oz_to_gram_conversion(self):
        """测试盎司转克换算"""
        # 1盎司 = 31.1035克
        result = oz_to_gram(100)
        expected = 100 / 31.1035
        assert abs(result - expected) < 0.0001, f"换算错误: {result} != {expected}"
    
    def test_premium_calculation_positive(self):
        """测试正常溢价计算"""
        # 沪金价格: 500元/克
        # 伦敦金: 2500美元/盎司 = 80.3763元/克
        # 汇率: 7.0
        # 伦敦金折算: 80.3763 * 7.0 = 562.6341元/克
        # 溢价: 500 - 562.6341 = -62.6341元/克（负溢价）
        
        shfe_price = 500.0
        london_oz = 2500.0
        usdcny = 7.0
        
        london_cny_per_g = oz_to_gram(london_oz) * usdcny
        premium = shfe_price - london_cny_per_g
        
        assert premium < 0, "负溢价计算错误"
        assert abs(premium + 62.6341) < 0.01, f"溢价值错误: {premium}"
    
    def test_premium_calculation_realistic(self):
        """测试真实场景溢价计算"""
        # 真实数据：沪金1009.33元/克，伦敦金4530.19美元/盎司，汇率6.9045
        shfe_price = 1009.33
        london_oz = 4530.19
        usdcny = 6.9045
        
        london_cny_per_g = oz_to_gram(london_oz) * usdcny
        premium = shfe_price - london_cny_per_g
        
        # 期望溢价约3-4元/克
        assert 0 < premium < 10, f"溢价异常: {premium}"
        assert abs(premium - 3.5) < 2.0, f"溢价偏差过大: {premium}"


class TestMarketStatus:
    """市场状态判断测试"""
    
    def test_market_open_weekday_daytime(self, test_db):
        """测试工作日日盘"""
        service = SGEMonitorService(test_db)
        
        # 模拟周一 10:00
        from unittest.mock import patch
        mock_now = datetime(2026, 3, 31, 10, 0, 0)  # 周一
        
        with patch('backend.services.sge_monitor.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            status = service._check_market_open()
        
        assert status['shfe_market_open'] == 1, "SHFE应该开盘"
        assert status['london_market_open'] == 1, "London应该开盘"
        assert status['both_markets_open'] == 1, "双市场应该开盘"
    
    def test_market_closed_weekend(self, test_db):
        """测试周末休市"""
        service = SGEMonitorService(test_db)
        
        # 模拟周六 10:00
        from unittest.mock import patch
        mock_now = datetime(2026, 3, 28, 10, 0, 0)  # 周六
        
        with patch('backend.services.sge_monitor.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            status = service._check_market_open()
        
        assert status['shfe_market_open'] == 0, "SHFE应该休市"
        assert status['london_market_open'] == 0, "London应该休市"
        assert status['both_markets_open'] == 0, "双市场应该休市"
    
    def test_market_night_session(self, test_db):
        """测试夜盘"""
        service = SGEMonitorService(test_db)
        
        # 模拟周一 22:00（夜盘）
        from unittest.mock import patch
        mock_now = datetime(2026, 3, 31, 22, 0, 0)
        
        with patch('backend.services.sge_monitor.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            status = service._check_market_open()
        
        assert status['shfe_market_open'] == 1, "SHFE夜盘应该开盘"
        assert status['london_market_open'] == 1, "London应该开盘"


class TestPremiumAlert:
    """溢价警报测试"""
    
    def test_no_alert_below_threshold(self, test_db):
        """测试低于阈值不触发警报"""
        service = SGEMonitorService(test_db)
        
        # 添加测试数据（溢价10元/克，低于阈值20）
        sge_record = SGEPrice(
            fetched_at=datetime.now(),
            shfe_price_cny_per_g=500.0,
            london_price_usd_per_oz=2500.0,
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
        
        alert = service.check_premium_alert()
        assert alert is None, "低于阈值不应触发警报"
    
    def test_alert_above_threshold(self, test_db):
        """测试超过阈值触发警报"""
        service = SGEMonitorService(test_db)
        
        # 添加测试数据（溢价25元/克，超过阈值20）
        sge_record = SGEPrice(
            fetched_at=datetime.now(),
            shfe_price_cny_per_g=515.0,
            london_price_usd_per_oz=2500.0,
            usdcny_rate=7.0,
            london_price_cny_per_g=490.0,
            premium_cny_per_g=25.0,
            poll_interval_seconds=60,
            both_markets_open=1,
            shfe_market_open=1,
            london_market_open=1,
            alert_triggered=0
        )
        test_db.add(sge_record)
        test_db.commit()
        
        alert = service.check_premium_alert()
        assert alert is not None, "超过阈值应触发警报"
        assert alert['level'] == 3, "警报等级应为3"
        assert '25.0' in alert['content'], "警报内容应包含溢价值"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
