"""
API路由单元测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.main import app
from backend.database import Base, SystemConfig, SGEPrice, RSSEvent, ReversalCondition, get_db


# 创建测试数据库
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
TestingSessionLocal = sessionmaker(bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_test_data():
    """设置测试数据"""
    db = TestingSessionLocal()
    
    # 添加系统配置
    configs = [
        SystemConfig(config_key='premium_threshold', config_value='20.0', description='溢价阈值'),
        SystemConfig(config_key='poll_interval_seconds', config_value='60', description='轮询间隔'),
    ]
    db.add_all(configs)
    
    # 添加SGE测试数据
    now = datetime.now()
    sge_records = [
        SGEPrice(
            fetched_at=now - timedelta(minutes=i),
            shfe_price_cny_per_g=1000.0 + i,
            london_price_usd_per_oz=4500.0,
            usdcny_rate=7.0,
            london_price_cny_per_g=995.0,
            premium_cny_per_g=5.0 + i,
            both_markets_open=1,
            shfe_market_open=1,
            london_market_open=1
        )
        for i in range(5)
    ]
    db.add_all(sge_records)
    
    # 添加反转条件测试数据
    reversal = ReversalCondition(
        detected_at=now,
        signal_level=2,
        price_signal=1,
        political_signal=0,
        war_signal=0,
        us10y_signal=1,
        conditions_met='price,us10y'
    )
    db.add(reversal)
    
    # 添加RSS事件测试数据
    rss_event = RSSEvent(
        collected_at=now,
        title='测试事件',
        description='测试描述',
        link='http://test.com',
        published_at=now,
        source='测试源',
        event_type='political',
        impact_score=8,
        keywords_matched='加息,货币政策'
    )
    db.add(rss_event)
    
    db.commit()
    db.close()
    
    yield
    
    # 清理测试数据
    db = TestingSessionLocal()
    db.query(SystemConfig).delete()
    db.query(SGEPrice).delete()
    db.query(ReversalCondition).delete()
    db.query(RSSEvent).delete()
    db.commit()
    db.close()


class TestHealthCheck:
    """健康检查API测试"""
    
    def test_health_check(self):
        """测试健康检查端点"""
        with TestClient(app) as client:
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data


class TestSGEAPI:
    """SGE价格API测试"""
    
    def test_get_latest_sge(self):
        """测试获取最新SGE数据"""
        with TestClient(app) as client:
            response = client.get("/api/sge/latest")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'data' in data
        assert len(data['data']) > 0
        
        # 验证数据字段
        first_record = data['data'][0]
        assert 'shfe_price_cny_per_g' in first_record
        assert 'premium_cny_per_g' in first_record
    
    def test_get_sge_with_limit(self):
        """测试带limit参数的SGE数据"""
        with TestClient(app) as client:
            response = client.get("/api/sge/latest?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) <= 2


class TestReversalAPI:
    """反转检测API测试"""
    
    def test_get_reversal_latest(self):
        """测试获取最新反转状态"""
        with TestClient(app) as client:
            response = client.get("/api/reversal/latest")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'data' in data
        
        # 验证数据字段
        reversal = data['data']
        assert 'signal_level' in reversal
        assert 'price_signal' in reversal
        assert 'political_signal' in reversal
        assert 'war_signal' in reversal
        assert 'us10y_signal' in reversal
    
    def test_get_reversal_history(self):
        """测试获取反转历史"""
        with TestClient(app) as client:
            response = client.get("/api/reversal/history?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'data' in data
        assert len(data['data']) > 0


class TestRSSAPI:
    """RSS事件API测试"""
    
    def test_get_rss_events(self):
        """测试获取RSS事件"""
        with TestClient(app) as client:
            response = client.get("/api/rss/events?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'data' in data
        assert len(data['data']) > 0
        
        # 验证事件字段
        event = data['data'][0]
        assert 'title' in event
        assert 'event_type' in event
        assert 'impact_score' in event
    
    def test_get_rss_events_filter_by_type(self):
        """测试按类型筛选RSS事件"""
        with TestClient(app) as client:
            response = client.get("/api/rss/events?event_type=political&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        
        # 验证所有事件都是political类型
        for event in data['data']:
            assert event['event_type'] == 'political'


class TestConfigAPI:
    """配置API测试"""
    
    def test_get_config(self):
        """测试获取配置"""
        with TestClient(app) as client:
            response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert 'premium_threshold' in data
        assert 'poll_interval_seconds' in data
    
    def test_update_config(self):
        """测试更新配置"""
        with TestClient(app) as client:
            new_config = {
                'premium_threshold': 25.0,
                'poll_interval_seconds': 90
            }
            response = client.post("/api/config", json=new_config)
            assert response.status_code == 200
            
            # 验证更新
            response = client.get("/api/config")
            data = response.json()
            assert data['premium_threshold'] == 25.0
            assert data['poll_interval_seconds'] == 90


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
