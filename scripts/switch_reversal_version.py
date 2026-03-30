"""
反转检测版本切换脚本

用途: 在V1、V2、V2加权版本之间切换

使用方法:
    python scripts/switch_reversal_version.py --version v2
    python scripts/switch_reversal_version.py --version v2_weighted
    python scripts/switch_reversal_version.py --version v1
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database import SessionLocal, SystemConfig
import argparse


def switch_version(target_version: str):
    """切换反转检测版本"""
    
    # 验证版本参数
    valid_versions = ['v1', 'v2', 'v2_weighted']
    if target_version not in valid_versions:
        print(f"❌ 无效的版本: {target_version}")
        print(f"✅ 有效版本: {', '.join(valid_versions)}")
        return False
    
    db = SessionLocal()
    try:
        # 查找或创建配置项
        config = db.query(SystemConfig).filter_by(
            config_key='reversal_detector_version'
        ).first()
        
        if config:
            old_version = config.config_value
            config.config_value = target_version
            config.updated_at = datetime.now()
        else:
            old_version = 'v1 (默认)'
            config = SystemConfig(
                config_key='reversal_detector_version',
                config_value=target_version,
                description='反转检测器版本: v1/v2/v2_weighted'
            )
            db.add(config)
        
        db.commit()
        
        print("=" * 60)
        print("✅ 反转检测版本切换成功！")
        print("=" * 60)
        print(f"旧版本: {old_version}")
        print(f"新版本: {target_version}")
        print("")
        
        # 显示版本说明
        version_info = {
            'v1': {
                'name': '原始版本',
                'logic': 'Level 4=仅政治, Level 3=政治+战争, Level 2=仅战争, Level 1=其他',
                'push': 'Level 1/2推送',
                'desc': '复刻原系统逻辑，等级定义较复杂'
            },
            'v2': {
                'name': 'V2简单计数版',
                'logic': 'Level = 触发信号数量 (0-4)',
                'push': 'Level 3/4推送',
                'desc': '逻辑简单直观，推荐使用'
            },
            'v2_weighted': {
                'name': 'V2加权评分版',
                'logic': 'Level = 加权评分/20 (考虑信号强度)',
                'push': '评分>=65推送',
                'desc': '考虑信号强度，更精确但复杂'
            }
        }
        
        info = version_info[target_version]
        print(f"版本名称: {info['name']}")
        print(f"判定逻辑: {info['logic']}")
        print(f"推送策略: {info['push']}")
        print(f"说明: {info['desc']}")
        print("")
        print("⚠️ 注意: 需要重启服务才能生效")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 切换失败: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def show_current_version():
    """显示当前版本"""
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter_by(
            config_key='reversal_detector_version'
        ).first()
        
        current = config.config_value if config else 'v1 (默认)'
        
        print("=" * 60)
        print("当前反转检测版本:")
        print("=" * 60)
        print(f"版本: {current}")
        print("")
        
        # 查询最近的反转记录
        from backend.database import ReversalCondition
        latest = db.query(ReversalCondition).order_by(
            ReversalCondition.fetched_at.desc()
        ).first()
        
        if latest:
            print(f"最新检测时间: {latest.fetched_at}")
            print(f"反转等级: Level {latest.signal_level}")
            print(f"触发条件: {latest.triggered_conditions or '无'}")
            
            # 判断版本
            if '[V2]' in (latest.note or ''):
                print(f"记录版本: V2")
            else:
                print(f"记录版本: V1")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
    finally:
        db.close()


def compare_versions():
    """对比不同版本的判定结果"""
    from datetime import datetime, timedelta
    from backend.database import ReversalCondition
    
    db = SessionLocal()
    try:
        # 查询最近7天的数据
        cutoff_time = datetime.now() - timedelta(days=7)
        records = db.query(ReversalCondition).filter(
            ReversalCondition.fetched_at >= cutoff_time
        ).order_by(ReversalCondition.fetched_at.desc()).all()
        
        v1_records = [r for r in records if '[V2]' not in (r.note or '')]
        v2_records = [r for r in records if '[V2]' in (r.note or '')]
        
        print("=" * 60)
        print("反转检测版本对比 (最近7天)")
        print("=" * 60)
        print(f"V1记录数: {len(v1_records)}")
        print(f"V2记录数: {len(v2_records)}")
        print("")
        
        # 统计等级分布
        def get_level_distribution(records):
            dist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
            for r in records:
                level = r.signal_level
                if level in dist:
                    dist[level] += 1
            return dist
        
        if v1_records:
            print("V1 等级分布:")
            v1_dist = get_level_distribution(v1_records)
            for level, count in sorted(v1_dist.items()):
                pct = count / len(v1_records) * 100
                print(f"  Level {level}: {count} ({pct:.1f}%)")
            print("")
        
        if v2_records:
            print("V2 等级分布:")
            v2_dist = get_level_distribution(v2_records)
            for level, count in sorted(v2_dist.items()):
                pct = count / len(v2_records) * 100
                print(f"  Level {level}: {count} ({pct:.1f}%)")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 对比失败: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='反转检测版本管理工具')
    parser.add_argument('--version', '-v', 
                       choices=['v1', 'v2', 'v2_weighted'],
                       help='目标版本')
    parser.add_argument('--current', '-c', 
                       action='store_true',
                       help='显示当前版本')
    parser.add_argument('--compare', 
                       action='store_true',
                       help='对比不同版本的结果')
    
    args = parser.parse_args()
    
    if args.current:
        show_current_version()
    elif args.compare:
        compare_versions()
    elif args.version:
        switch_version(args.version)
    else:
        parser.print_help()
        print("\n示例:")
        print("  查看当前版本:  python scripts/switch_reversal_version.py --current")
        print("  切换到V2:      python scripts/switch_reversal_version.py --version v2")
        print("  对比版本:      python scripts/switch_reversal_version.py --compare")
