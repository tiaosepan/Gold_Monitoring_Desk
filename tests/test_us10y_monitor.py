"""
美债监控服务单元测试
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database import Base, USTreasury, SystemConfig
from backend.services.us10y_monitor import US10YMonitorService


@pytest.fixture
def test_db():
    """创建测试数据库"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    # 添加测试配置
    configs = [
        SystemConfig(
            config_key='us10y_drop_threshold_bp',
            config_value='1.0',
            description='美债下跌阈值'
        ),
        SystemConfig(
            config_key='us10y_drop_lookback_hours',
            config_value='24.0',
            description='美债回看时长'
        )
    ]
    db.add_all(configs)
    db.commit()
    
    yield db
    
    db.close()


class TestUS10YDataCollection:
    """美债数据采集测试"""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, test_db):
        """测试服务初始化"""
        async with US10YMonitorService(test_db) as service:
            assert service is not None
            assert service.db == test_db


class TestUS10YYieldDropDetection:
    """美债收益率下跌检测测试"""
    
    @pytest.mark.asyncio
    async def test_no_drop_stable_yield(self, test_db):
        """测试收益率稳定时不触发警报"""
        async with US10YMonitorService(test_db) as service:
            # 添加稳定数据（24小时内收益率变化小于1bp）
            now = datetime.now()
            for i in range(5):
                record = USTreasury(
                    fetched_at=now - timedelta(hours=i*5),
                    yield_pct=4.50 + i * 0.0005,  # 变化0.05bp
                    source='Test',
                    tenor='10y'
                )
                test_db.add(record)
            test_db.commit()
            
            alert = service.detect_yield_drop()
            assert alert is None, "稳定收益率不应触发警报"
    
    @pytest.mark.asyncio
    async def test_drop_detection_threshold(self, test_db):
        """测试下跌超过阈值触发警报"""
        async with US10YMonitorService(test_db) as service:
            # 添加下跌数据（24小时内下跌2bp > 1bp阈值）
            now = datetime.now()
            records = [
                USTreasury(
                    fetched_at=now,
                    yield_pct=4.48,
                    source='Test',
                    tenor='10y'
                ),
                USTreasury(
                    fetched_at=now - timedelta(hours=12),
                    yield_pct=4.50,
                    source='Test',
                    tenor='10y'
                )
            ]
            test_db.add_all(records)
            test_db.commit()
            
            alert = service.detect_yield_drop()
            assert alert is not None, "超过阈值应触发警报"
            assert alert['level'] == 2, "警报等级应为2"
            assert '2.00' in alert['content'], "警报应包含下跌幅度"
    
    @pytest.mark.asyncio
    async def test_no_drop_insufficient_data(self, test_db):
        """测试数据不足时不触发警报"""
        async with US10YMonitorService(test_db) as service:
            # 只添加1条数据
            record = USTreasury(
                fetched_at=datetime.now(),
                yield_pct=4.50,
                source='Test',
                tenor='10y'
            )
            test_db.add(record)
            test_db.commit()
            
            alert = service.detect_yield_drop()
            assert alert is None, "数据不足不应触发警报"


class TestUS10YMultipleTenors:
    """多期限美债测试"""
    
    @pytest.mark.asyncio
    async def test_different_tenors_in_db(self, test_db):
        """测试数据库中不同期限的美债数据"""
        # 直接添加测试数据
        tenors_data = [
            {'tenor': '5y', 'yield': 4.2},
            {'tenor': '10y', 'yield': 4.5},
            {'tenor': '20y', 'yield': 5.0}
        ]
        
        for data in tenors_data:
            record = USTreasury(
                fetched_at=datetime.now(),
                yield_pct=data['yield'],
                source='Test',
                tenor=data['tenor']
            )
            test_db.add(record)
        test_db.commit()
        
        # 验证每个期限都被保存
        for data in tenors_data:
            record = test_db.query(USTreasury).filter_by(tenor=data['tenor']).first()
            assert record is not None, f"{data['tenor']}数据应该被保存"
            assert record.yield_pct == data['yield'], f"{data['tenor']}收益率值应该正确"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
