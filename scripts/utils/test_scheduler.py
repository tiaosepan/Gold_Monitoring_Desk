"""
测试调度器性能和采集频率
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database import SessionLocal, SGEPrice, SchedulerStatus
from backend.scheduler import TaskScheduler


async def monitor_scheduler_performance(duration_seconds=180):
    """
    监控调度器性能
    
    Args:
        duration_seconds: 监控时长（秒）
    """
    print("=" * 60)
    print("调度器性能监控测试")
    print(f"监控时长: {duration_seconds}秒")
    print("=" * 60)
    
    # 启动调度器
    scheduler = TaskScheduler()
    scheduler.start()
    
    print("\n调度器已启动，开始监控...\n")
    
    # 记录初始状态
    db = SessionLocal()
    initial_count = db.query(SGEPrice).count()
    start_time = datetime.now()
    
    try:
        # 每10秒检查一次
        for i in range(duration_seconds // 10):
            await asyncio.sleep(10)
            
            # 查询最新数据
            latest = db.query(SGEPrice).order_by(SGEPrice.fetched_at.desc()).first()
            current_count = db.query(SGEPrice).count()
            new_records = current_count - initial_count
            
            # 计算实际频率
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            actual_frequency = new_records / (elapsed_seconds / 60) if elapsed_seconds > 0 else 0
            
            # 查询调度器状态
            sge_status = db.query(SchedulerStatus).filter_by(task_name='sge_monitor').first()
            
            print(f"[{i*10+10}秒] 新增记录: {new_records} | "
                  f"实际频率: {actual_frequency:.2f}次/分钟 | "
                  f"最新数据: {latest.fetched_at.strftime('%H:%M:%S') if latest else 'N/A'} | "
                  f"任务状态: {sge_status.status if sge_status else 'N/A'}")
            
            # 刷新数据库会话
            db.expire_all()
        
        # 最终报告
        print("\n" + "=" * 60)
        print("监控结果汇总")
        print("=" * 60)
        
        final_count = db.query(SGEPrice).count()
        total_new_records = final_count - initial_count
        total_elapsed = (datetime.now() - start_time).total_seconds()
        avg_frequency = total_new_records / (total_elapsed / 60)
        
        print(f"监控时长: {total_elapsed:.1f}秒")
        print(f"新增记录: {total_new_records}条")
        print(f"平均频率: {avg_frequency:.2f}次/分钟")
        print(f"期望频率: 1次/分钟（60秒）")
        
        # 检查是否达标
        if avg_frequency >= 0.9:
            print("\n[通过] 采集频率正常")
        else:
            print(f"\n[警告] 采集频率偏低（期望>=0.9次/分钟，实际{avg_frequency:.2f}次/分钟）")
        
        # 查询最近的采集记录，分析间隔
        recent_records = db.query(SGEPrice).order_by(
            SGEPrice.fetched_at.desc()
        ).limit(10).all()
        
        if len(recent_records) >= 2:
            print("\n最近10次采集间隔分析:")
            intervals = []
            for i in range(len(recent_records) - 1):
                interval = (recent_records[i].fetched_at - recent_records[i+1].fetched_at).total_seconds()
                intervals.append(interval)
                print(f"  {recent_records[i].fetched_at.strftime('%H:%M:%S')} - "
                      f"{recent_records[i+1].fetched_at.strftime('%H:%M:%S')}: {interval:.1f}秒")
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                max_interval = max(intervals)
                min_interval = min(intervals)
                print(f"\n平均间隔: {avg_interval:.1f}秒")
                print(f"最大间隔: {max_interval:.1f}秒")
                print(f"最小间隔: {min_interval:.1f}秒")
        
        print("=" * 60)
        
    finally:
        scheduler.shutdown()
        db.close()
        print("\n调度器已关闭")


async def check_task_execution_time():
    """检查各任务的执行时间"""
    print("\n" + "=" * 60)
    print("任务执行时间分析")
    print("=" * 60)
    
    scheduler = TaskScheduler()
    db = SessionLocal()
    
    try:
        # 手动执行各任务，测量耗时
        print("\n测试SGE监控任务...")
        start = datetime.now()
        await scheduler.sge_monitor_task()
        sge_duration = (datetime.now() - start).total_seconds()
        print(f"SGE监控耗时: {sge_duration:.2f}秒")
        
        print("\n测试反转检测任务...")
        start = datetime.now()
        await scheduler.reversal_detector_task()
        reversal_duration = (datetime.now() - start).total_seconds()
        print(f"反转检测耗时: {reversal_duration:.2f}秒")
        
        print("\n测试美债监控任务...")
        start = datetime.now()
        await scheduler.us10y_monitor_task()
        us10y_duration = (datetime.now() - start).total_seconds()
        print(f"美债监控耗时: {us10y_duration:.2f}秒")
        
        print("\n" + "-" * 60)
        print("分析结果:")
        
        total_time = sge_duration + reversal_duration + us10y_duration
        print(f"单次完整周期耗时: {total_time:.2f}秒")
        
        if total_time < 60:
            print(f"[通过] 任务执行时间在60秒内（剩余{60-total_time:.1f}秒缓冲）")
        else:
            print(f"[警告] 任务执行时间超过60秒，会影响采集频率")
            print("建议:")
            print("  1. 优化API调用超时时间")
            print("  2. 减少数据库查询次数")
            print("  3. 使用异步并发执行")
        
        print("=" * 60)
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='调度器性能测试')
    parser.add_argument('--mode', choices=['monitor', 'timing'], default='timing',
                       help='测试模式: monitor=长时间监控, timing=执行时间测试')
    parser.add_argument('--duration', type=int, default=180,
                       help='监控时长（秒），仅在monitor模式下有效')
    
    args = parser.parse_args()
    
    if args.mode == 'monitor':
        asyncio.run(monitor_scheduler_performance(args.duration))
    else:
        asyncio.run(check_task_execution_time())
