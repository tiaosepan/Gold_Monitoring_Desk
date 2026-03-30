"""
详细系统对比脚本
"""
import requests
import json
from datetime import datetime

ORIGINAL_BASE = "http://rev.sccit.com.cn:8000"
REPLICA_BASE = "http://localhost:8000"

def compare_structures(obj1, obj2, path="root"):
    """递归对比两个对象的结构"""
    differences = []
    
    if type(obj1) != type(obj2):
        differences.append(f"{path}: 类型不同 ({type(obj1).__name__} vs {type(obj2).__name__})")
        return differences
    
    if isinstance(obj1, dict):
        keys1 = set(obj1.keys())
        keys2 = set(obj2.keys())
        
        # 检查缺失的键
        missing_in_replica = keys1 - keys2
        extra_in_replica = keys2 - keys1
        
        if missing_in_replica:
            differences.append(f"{path}: 复刻系统缺少键 {missing_in_replica}")
        
        if extra_in_replica:
            differences.append(f"{path}: 复刻系统多余键 {extra_in_replica}")
        
        # 递归检查共同键
        for key in keys1 & keys2:
            differences.extend(compare_structures(obj1[key], obj2[key], f"{path}.{key}"))
    
    elif isinstance(obj1, list) and len(obj1) > 0 and len(obj2) > 0:
        # 只比较第一个元素的结构
        differences.extend(compare_structures(obj1[0], obj2[0], f"{path}[0]"))
    
    return differences

def main():
    print("="*80)
    print("系统详细对比测试")
    print("="*80)
    print(f"\n原系统: {ORIGINAL_BASE}")
    print(f"复刻系统: {REPLICA_BASE}\n")
    
    # 获取两个系统的状态
    print("正在获取系统状态...")
    
    try:
        original_status = requests.get(f"{ORIGINAL_BASE}/api/status", timeout=10).json()
        print("[OK] 原系统状态获取成功")
    except Exception as e:
        print(f"[FAIL] 原系统状态获取失败: {e}")
        return
    
    try:
        replica_status = requests.get(f"{REPLICA_BASE}/api/status", timeout=10).json()
        print("[OK] 复刻系统状态获取成功")
    except Exception as e:
        print(f"[FAIL] 复刻系统状态获取失败: {e}")
        return
    
    # 对比结构
    print("\n" + "="*80)
    print("结构对比")
    print("="*80)
    
    differences = compare_structures(original_status, replica_status)
    
    if not differences:
        print("\n[OK] API结构完全一致！")
    else:
        print(f"\n发现 {len(differences)} 处差异:\n")
        for diff in differences:
            print(f"  - {diff}")
    
    # 对比配置参数
    print("\n" + "="*80)
    print("配置参数对比")
    print("="*80)
    
    orig_settings = original_status.get('settings', {})
    repl_settings = replica_status.get('settings', {})
    
    key_params = [
        'premium_threshold',
        'poll_interval_seconds',
        'alert_cooldown_seconds',
        'reversal_cooldown_seconds',
        'reversal_price_lookback_minutes',
        'reversal_price_rebound_pct',
        'reversal_price_ma_window',
        'reversal_signal_window_minutes',
        'us10y_drop_threshold_bp',
        'us10y_drop_lookback_hours',
        'rss_poll_interval_seconds'
    ]
    
    config_matches = 0
    config_total = 0
    
    for param in key_params:
        config_total += 1
        orig_val = orig_settings.get(param)
        repl_val = repl_settings.get(param)
        
        if orig_val == repl_val:
            print(f"  [OK] {param}: {orig_val}")
            config_matches += 1
        else:
            print(f"  [DIFF] {param}: 原={orig_val}, 复刻={repl_val}")
    
    print(f"\n配置匹配度: {config_matches}/{config_total} ({config_matches/config_total*100:.1f}%)")
    
    # 对比RSS源
    print("\n" + "="*80)
    print("RSS源对比")
    print("="*80)
    
    orig_rss = set(orig_settings.get('rss_feed_urls', []))
    repl_rss = set(repl_settings.get('rss_feed_urls', []))
    
    if orig_rss == repl_rss:
        print(f"\n[OK] RSS源完全一致 ({len(orig_rss)} 个)")
        for url in orig_rss:
            print(f"  - {url}")
    else:
        print(f"\n原系统RSS源 ({len(orig_rss)} 个):")
        for url in orig_rss:
            print(f"  - {url}")
        
        print(f"\n复刻系统RSS源 ({len(repl_rss)} 个):")
        for url in repl_rss:
            print(f"  - {url}")
        
        missing = orig_rss - repl_rss
        extra = repl_rss - orig_rss
        
        if missing:
            print(f"\n缺少的RSS源:")
            for url in missing:
                print(f"  - {url}")
        
        if extra:
            print(f"\n多余的RSS源:")
            for url in extra:
                print(f"  - {url}")
    
    # 对比数据字段
    print("\n" + "="*80)
    print("数据字段对比")
    print("="*80)
    
    # SGE数据字段
    if original_status.get('latest_sample'):
        orig_sge_fields = set(original_status['latest_sample'].keys())
        print(f"\n原系统SGE字段 ({len(orig_sge_fields)} 个):")
        for field in sorted(orig_sge_fields):
            print(f"  - {field}")
    
    if replica_status.get('latest_sample'):
        repl_sge_fields = set(replica_status['latest_sample'].keys())
        print(f"\n复刻系统SGE字段 ({len(repl_sge_fields)} 个):")
        for field in sorted(repl_sge_fields):
            print(f"  - {field}")
        
        if original_status.get('latest_sample'):
            if orig_sge_fields == repl_sge_fields:
                print("\n[OK] SGE字段完全一致")
            else:
                missing = orig_sge_fields - repl_sge_fields
                extra = repl_sge_fields - orig_sge_fields
                if missing:
                    print(f"\n缺少字段: {missing}")
                if extra:
                    print(f"\n多余字段: {extra}")
    else:
        print("\n[WARN] 复刻系统暂无SGE数据（需要先采集数据）")
    
    # 反转数据字段
    if original_status.get('gold_reversal', {}).get('latest_sample'):
        orig_reversal_fields = set(original_status['gold_reversal']['latest_sample'].keys())
        print(f"\n原系统反转字段 ({len(orig_reversal_fields)} 个):")
        for field in sorted(orig_reversal_fields):
            print(f"  - {field}")
    
    if replica_status.get('gold_reversal', {}).get('latest_sample'):
        repl_reversal_fields = set(replica_status['gold_reversal']['latest_sample'].keys())
        print(f"\n复刻系统反转字段 ({len(repl_reversal_fields)} 个):")
        for field in sorted(repl_reversal_fields):
            print(f"  - {field}")
        
        if original_status.get('gold_reversal', {}).get('latest_sample'):
            if orig_reversal_fields == repl_reversal_fields:
                print("\n[OK] 反转字段完全一致")
            else:
                missing = orig_reversal_fields - repl_reversal_fields
                extra = repl_reversal_fields - orig_reversal_fields
                if missing:
                    print(f"\n缺少字段: {missing}")
                if extra:
                    print(f"\n多余字段: {extra}")
    else:
        print("\n[WARN] 复刻系统暂无反转数据（需要先执行反转检测）")
    
    # 生成总结报告
    print("\n" + "="*80)
    print("对比总结")
    print("="*80)
    
    print(f"\n1. API结构: {'[OK] 一致' if not differences else f'[DIFF] 发现{len(differences)}处差异'}")
    print(f"2. 配置参数: {config_matches}/{config_total} 匹配 ({config_matches/config_total*100:.1f}%)")
    print(f"3. RSS源: {'[OK] 一致' if orig_rss == repl_rss else '[DIFF] 不一致'}")
    
    # 保存详细报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'structure_differences': differences,
        'config_comparison': {
            'matches': config_matches,
            'total': config_total,
            'match_rate': config_matches/config_total
        },
        'rss_comparison': {
            'original_count': len(orig_rss),
            'replica_count': len(repl_rss),
            'match': orig_rss == repl_rss
        }
    }
    
    with open('tests/detailed_comparison_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细报告已保存到: tests/detailed_comparison_report.json")

if __name__ == "__main__":
    main()
