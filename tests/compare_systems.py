"""
系统对比测试脚本
对比原系统和复刻系统的差异
"""
import requests
import json
from datetime import datetime

ORIGINAL_BASE = "http://rev.sccit.com.cn:8000"
REPLICA_BASE = "http://localhost:8000"

class SystemComparator:
    def __init__(self):
        self.differences = []
        self.summary = {
            'total_checks': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }
    
    def log_diff(self, category, item, status, message):
        """记录差异"""
        self.differences.append({
            'category': category,
            'item': item,
            'status': status,
            'message': message
        })
        self.summary['total_checks'] += 1
        if status == 'PASS':
            self.summary['passed'] += 1
        elif status == 'FAIL':
            self.summary['failed'] += 1
        else:
            self.summary['warnings'] += 1
    
    def compare_api_structure(self):
        """对比API结构"""
        print("\n=== API结构对比 ===")
        
        try:
            # 获取原系统状态
            original = requests.get(f"{ORIGINAL_BASE}/api/status", timeout=10).json()
            
            # 检查原系统的API结构
            print("\n原系统API结构:")
            print(f"- settings: {len(original.get('settings', {}))} 个配置项")
            print(f"- market_state: {len(original.get('market_state', {}))} 个市场状态")
            print(f"- latest_sample: {'存在' if 'latest_sample' in original else '不存在'}")
            print(f"- recent_alerts: {len(original.get('recent_alerts', []))} 条")
            print(f"- recent_fetch_runs: {len(original.get('recent_fetch_runs', []))} 条")
            print(f"- recent_samples: {len(original.get('recent_samples', []))} 条")
            print(f"- gold_reversal: {'存在' if 'gold_reversal' in original else '不存在'}")
            print(f"- us10y_reversal: {'存在' if 'us10y_reversal' in original else '不存在'}")
            
            # 分析原系统的数据结构
            print("\n原系统核心数据结构:")
            if 'latest_sample' in original:
                sample = original['latest_sample']
                print(f"  SGE数据字段: {list(sample.keys())}")
            
            if 'gold_reversal' in original and 'latest_sample' in original['gold_reversal']:
                reversal = original['gold_reversal']['latest_sample']
                print(f"  反转数据字段: {list(reversal.keys())}")
            
            self.log_diff('API', '原系统API结构', 'PASS', '成功获取原系统API结构')
            
        except Exception as e:
            self.log_diff('API', '原系统API', 'FAIL', f'无法访问原系统: {str(e)}')
    
    def compare_data_fields(self):
        """对比数据字段"""
        print("\n=== 数据字段对比 ===")
        
        try:
            original = requests.get(f"{ORIGINAL_BASE}/api/status", timeout=10).json()
            
            # 原系统的SGE数据字段
            if 'latest_sample' in original:
                original_fields = set(original['latest_sample'].keys())
                print(f"\n原系统SGE数据字段: {sorted(original_fields)}")
                
                required_fields = {
                    'shfe_price_cny_per_g',  # 沪金价格
                    'london_price_usd_per_oz',  # 伦敦金价格
                    'usdcny_rate',  # 汇率
                    'premium_cny_per_g',  # 溢价
                    'fetched_at',  # 采集时间
                    'both_markets_open',  # 市场开盘状态
                    'shfe_market_open',
                    'london_market_open',
                    'alert_triggered'
                }
                
                print(f"\n关键字段检查:")
                for field in required_fields:
                    if field in original_fields:
                        print(f"  ✓ {field}")
                        self.log_diff('字段', field, 'PASS', '原系统包含此字段')
                    else:
                        print(f"  ✗ {field}")
                        self.log_diff('字段', field, 'FAIL', '原系统缺少此字段')
            
            # 反转检测字段
            if 'gold_reversal' in original and 'latest_sample' in original['gold_reversal']:
                reversal_fields = set(original['gold_reversal']['latest_sample'].keys())
                print(f"\n原系统反转数据字段: {sorted(reversal_fields)}")
                
                required_reversal_fields = {
                    'price_signal',
                    'political_signal',
                    'war_signal',
                    'us10y_signal',
                    'signal_level',
                    'triggered_conditions'
                }
                
                print(f"\n反转字段检查:")
                for field in required_reversal_fields:
                    if field in reversal_fields:
                        print(f"  ✓ {field}")
                        self.log_diff('反转字段', field, 'PASS', '原系统包含此字段')
                    else:
                        print(f"  ✗ {field}")
                        self.log_diff('反转字段', field, 'FAIL', '原系统缺少此字段')
        
        except Exception as e:
            self.log_diff('字段对比', '数据字段', 'FAIL', f'对比失败: {str(e)}')
    
    def analyze_rss_sources(self):
        """分析RSS源配置"""
        print("\n=== RSS源分析 ===")
        
        try:
            original = requests.get(f"{ORIGINAL_BASE}/api/status", timeout=10).json()
            
            if 'settings' in original and 'rss_feed_urls' in original['settings']:
                rss_urls = original['settings']['rss_feed_urls']
                print(f"\n原系统配置的RSS源 ({len(rss_urls)} 个):")
                for i, url in enumerate(rss_urls, 1):
                    print(f"  {i}. {url}")
                    self.log_diff('RSS源', f'RSS源{i}', 'INFO', url)
            
            # 检查RSS事件结构
            if 'gold_reversal' in original and 'recent_events' in original['gold_reversal']:
                events = original['gold_reversal']['recent_events']
                if events:
                    event = events[0]
                    print(f"\nRSS事件数据结构: {list(event.keys())}")
                    print(f"  - event_type: {event.get('event_type')}")
                    print(f"  - impact_score: {event.get('impact_score')}")
                    print(f"  - impact_level: {event.get('impact_level')}")
                    print(f"  - matched_keywords: {event.get('matched_keywords')}")
        
        except Exception as e:
            self.log_diff('RSS', 'RSS源分析', 'FAIL', f'分析失败: {str(e)}')
    
    def analyze_configuration(self):
        """分析配置参数"""
        print("\n=== 配置参数分析 ===")
        
        try:
            original = requests.get(f"{ORIGINAL_BASE}/api/status", timeout=10).json()
            
            if 'settings' in original:
                settings = original['settings']
                print(f"\n原系统配置参数:")
                
                key_settings = {
                    'premium_threshold': '溢价阈值',
                    'poll_interval_seconds': '轮询间隔',
                    'alert_cooldown_seconds': '警报冷却时间',
                    'reversal_cooldown_seconds': '反转冷却时间',
                    'reversal_price_lookback_minutes': '价格回看分钟数',
                    'reversal_price_rebound_pct': '价格反弹百分比',
                    'reversal_price_ma_window': '价格MA窗口',
                    'reversal_signal_window_minutes': '信号窗口分钟数',
                    'us10y_drop_threshold_bp': '美债下跌阈值(bp)',
                    'us10y_drop_lookback_hours': '美债回看小时数',
                    'rss_poll_interval_seconds': 'RSS轮询间隔'
                }
                
                for key, name in key_settings.items():
                    if key in settings:
                        value = settings[key]
                        print(f"  {name} ({key}): {value}")
                        self.log_diff('配置', key, 'INFO', f'{name} = {value}')
                    else:
                        print(f"  {name} ({key}): 未配置")
                        self.log_diff('配置', key, 'WARN', f'{name} 未配置')
        
        except Exception as e:
            self.log_diff('配置', '配置分析', 'FAIL', f'分析失败: {str(e)}')
    
    def identify_missing_features(self):
        """识别缺失的功能"""
        print("\n=== 缺失功能识别 ===")
        
        try:
            original = requests.get(f"{ORIGINAL_BASE}/api/status", timeout=10).json()
            
            # 检查原系统特有的功能
            features = {
                'both_markets_open': '双市场开盘检测',
                'shfe_market_open': '沪金市场开盘检测',
                'london_market_open': '伦敦市场开盘检测',
                'alert_cooldown': '警报冷却机制',
                'reversal_cooldown': '反转冷却机制',
                'price_ma_window': '价格移动平均',
                'price_rebound_detection': '价格反弹检测',
                'rss_impact_scoring': 'RSS影响评分',
                'rss_keyword_matching': 'RSS关键词匹配',
                'us10y_fred_fallback': '美债FRED回退'
            }
            
            print("\n原系统特有功能:")
            for feature, desc in features.items():
                print(f"  - {desc} ({feature})")
                self.log_diff('功能', feature, 'WARN', f'需要实现: {desc}')
        
        except Exception as e:
            self.log_diff('功能', '功能识别', 'FAIL', f'识别失败: {str(e)}')
    
    def generate_report(self):
        """生成对比报告"""
        print("\n" + "="*60)
        print("系统对比报告")
        print("="*60)
        print(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n总检查项: {self.summary['total_checks']}")
        print(f"通过: {self.summary['passed']}")
        print(f"失败: {self.summary['failed']}")
        print(f"警告: {self.summary['warnings']}")
        
        # 按类别分组显示差异
        categories = {}
        for diff in self.differences:
            cat = diff['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(diff)
        
        print("\n详细差异:")
        for cat, diffs in categories.items():
            print(f"\n【{cat}】")
            for diff in diffs:
                status_symbol = {
                    'PASS': '[PASS]',
                    'FAIL': '[FAIL]',
                    'WARN': '[WARN]',
                    'INFO': '[INFO]'
                }.get(diff['status'], '[?]')
                print(f"  {status_symbol} {diff['item']}: {diff['message']}")
        
        # 保存报告
        report_file = 'd:\\www\\prototype\\Gold_Monitoring_Desk\\tests\\comparison_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': self.summary,
                'differences': self.differences
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n报告已保存到: {report_file}")

def main():
    comparator = SystemComparator()
    
    print("开始系统对比测试...")
    print(f"原系统: {ORIGINAL_BASE}")
    print(f"复刻系统: {REPLICA_BASE}")
    
    comparator.compare_api_structure()
    comparator.compare_data_fields()
    comparator.analyze_rss_sources()
    comparator.analyze_configuration()
    comparator.identify_missing_features()
    comparator.generate_report()

if __name__ == "__main__":
    main()
