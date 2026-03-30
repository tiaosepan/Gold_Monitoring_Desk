"""
调度器单元测试
"""
import pytest
import asyncio
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database import Base, SystemConfig, SchedulerStatus
from backend.scheduler import TaskScheduler


@pytest.fixture
def test_db():
    """创建测试数据库"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    # 添加测试配置
    configs = [
        SystemConfig(config_key='premium_threshold', config_value='20.0', description='溢价阈值'),
        SystemConfig(config_key='poll_interval_seconds', config_value='60', description='轮询间隔'),
        SystemConfig(config_key='us10y_drop_threshold_bp', config_value='1.0', description='美债阈值'),
        SystemConfig(config_key='reversal_price_rebound_pct', config_value='0.8', description='价格反弹阈值'),
    ]
    db.add_all(configs)
    db.commit()
    
    yield db
    
    db.close()


class TestSchedulerLifecycle:
    """调度器生命周期测试"""
    
    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        scheduler = TaskScheduler()
        assert scheduler is not None
        assert scheduler.scheduler is not None
        assert not scheduler.scheduler.running
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self):
        """测试调度器启动和停止"""
        scheduler = TaskScheduler()
        
        # 启动
        await scheduler.start()
        assert scheduler.scheduler.running
        
        # 等待一小段时间
        await asyncio.sleep(0.5)
        
        # 停止
        await scheduler.stop()
        assert not scheduler.scheduler.running


class TestTaskRegistration:
    """任务注册测试"""
    
    @pytest.mark.asyncio
    async def test_all_tasks_registered(self):
        """测试所有任务都已注册"""
        scheduler = TaskScheduler()
        await scheduler.start()
        
        # 检查所有任务是否注册
        jobs = scheduler.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]
        
        expected_jobs = [
            'sge_monitor',
            'us10y_monitor',
            'rss_collector',
            'reversal_detector'
        ]
        
        for job_id in expected_jobs:
            assert job_id in job_ids, f"任务 {job_id} 应该被注册"
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_task_intervals(self):
        """测试任务间隔设置"""
        scheduler = TaskScheduler()
        await scheduler.start()
        
        jobs = {job.id: job for job in scheduler.scheduler.get_jobs()}
        
        # 验证任务间隔（注意：这些值可能根据配置调整）
        assert jobs['sge_monitor'].trigger.interval.total_seconds() == 60
        assert jobs['us10y_monitor'].trigger.interval.total_seconds() == 60
        assert jobs['reversal_detector'].trigger.interval.total_seconds() == 60
        
        await scheduler.stop()


class TestTaskExecution:
    """任务执行测试"""
    
    @pytest.mark.asyncio
    async def test_task_status_update(self, test_db):
        """测试任务状态更新"""
        scheduler = TaskScheduler()
        
        # 模拟任务状态更新
        scheduler._update_task_status(test_db, 'test_task', 'running')
        
        status = test_db.query(SchedulerStatus).filter_by(task_name='test_task').first()
        assert status is not None
        assert status.status == 'running'
        
        # 更新为成功
        scheduler._update_task_status(test_db, 'test_task', 'success')
        
        status = test_db.query(SchedulerStatus).filter_by(task_name='test_task').first()
        assert status.status == 'success'
        assert status.error_message is None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
