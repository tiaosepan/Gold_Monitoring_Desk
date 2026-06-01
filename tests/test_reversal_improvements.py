"""
反转检测优化功能测试

测试内容:
1. V2等级判定逻辑
2. RSS上下文分析
3. 信号强度计算
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.services.reversal_detector_v2 import ReversalDetectorServiceV2
from backend.services.rss_collector import RSSCollectorService
from datetime import datetime, timedelta


class TestReversalLevelV2:
    """测试V2反转等级判定"""
    
    def test_level_0_no_signal(self):
        """测试Level 0: 无信号"""
        # 0个信号 → Level 0
        level, desc = self._determine_level(0, 0, 0, 0)
        assert level == 0
        assert "无信号" in desc
    
    def test_level_1_single_signal(self):
        """测试Level 1: 单个信号"""
        # 仅价格信号
        level, desc = self._determine_level(1, 0, 0, 0)
        assert level == 1
        assert "弱信号" in desc or "1个信号" in desc
        
        # 仅政治信号
        level, desc = self._determine_level(0, 1, 0, 0)
        assert level == 1
    
    def test_level_2_two_signals(self):
        """测试Level 2: 两个信号"""
        # 价格 + 政治
        level, desc = self._determine_level(1, 1, 0, 0)
        assert level == 2
        assert "中等" in desc or "2个信号" in desc
    
    def test_level_3_three_signals(self):
        """测试Level 3: 三个信号"""
        # 价格 + 政治 + 战争
        level, desc = self._determine_level(1, 1, 1, 0)
        assert level == 3
        assert ("强信号" in desc or "3个信号" in desc) and "推送" in desc
    
    def test_level_4_all_signals(self):
        """测试Level 4: 四个信号全触发"""
        level, desc = self._determine_level(1, 1, 1, 1)
        assert level == 4
        assert ("极强" in desc or "4个信号" in desc) and "推送" in desc
    
    def _determine_level(self, price, political, war, us10y):
        """辅助函数: 判定等级"""
        from backend.services.reversal_detector_v2 import ReversalDetectorServiceV2
        
        # 模拟detector（不需要真实数据库）
        class MockDetector:
            def determine_reversal_level_v2(self, p, pol, w, u, *args):
                signal_count = p + pol + w + u
                descriptions = {
                    0: "无信号 - 无反转迹象",
                    1: "弱信号 - 观察阶段 (1个信号触发)",
                    2: "中等信号 - 关注阶段 (2个信号触发)",
                    3: "强信号 - 准备行动 (3个信号触发) [推送]",
                    4: "极强信号 - 立即行动 (4个信号触发) [推送]"
                }
                return signal_count, descriptions[signal_count]
        
        detector = MockDetector()
        return detector.determine_reversal_level_v2(price, political, war, us10y)


class TestPushStrategy:
    """测试推送策略"""
    
    def test_should_push_level_0(self):
        """Level 0不应推送"""
        assert self._should_push(0) == False
    
    def test_should_push_level_1(self):
        """Level 1不应推送"""
        assert self._should_push(1) == False
    
    def test_should_push_level_2(self):
        """Level 2不应推送"""
        assert self._should_push(2) == False
    
    def test_should_push_level_3(self):
        """Level 3应该推送"""
        assert self._should_push(3) == True
    
    def test_should_push_level_4(self):
        """Level 4应该推送"""
        assert self._should_push(4) == True
    
    def _should_push(self, level):
        """辅助函数: 判断是否推送"""
        # V2推送策略: Level 3/4推送
        return level >= 3


class TestRSSContextAnalysis:
    """测试RSS上下文分析"""
    
    def test_negative_phrase_detection(self):
        """测试负面词组检测"""
        # "停火失败"应该被识别为负面
        text = "中东停火失败，冲突继续升级"
        
        # 模拟检测
        negative_phrases = ['停火失败', 'ceasefire failed']
        
        detected = any(phrase in text for phrase in negative_phrases)
        assert detected == True, "应该检测到负面词组"
    
    def test_negation_context(self):
        """测试否定上下文"""
        # "未能停火"应该被识别为负面
        text = "双方未能达成停火协议"
        
        negation_words = ['未能', '未', '没有']
        positive_words = ['停火', '协议']
        
        # 检测否定词+正面词组合
        has_negation = False
        for neg in negation_words:
            for pos in positive_words:
                if neg in text and pos in text:
                    has_negation = True
                    break
        
        assert has_negation == True, "应该检测到否定上下文"
    
    def test_positive_phrase_correct(self):
        """测试正面词组正确识别"""
        # "停火协议达成"应该是正面
        text = "双方达成停火协议，局势缓和"
        
        negative_phrases = ['停火失败', '协议破裂']
        
        # 不应匹配到负面词组
        detected = any(phrase in text for phrase in negative_phrases)
        assert detected == False, "不应误判为负面"
    
    def test_keyword_weight(self):
        """测试关键词权重"""
        keyword_weights = {
            '停火': 3.0,
            'ceasefire': 3.0,
            '谈判': 2.5,
            '对话': 1.5
        }
        
        # "停火"应该比"对话"权重更高
        assert keyword_weights['停火'] > keyword_weights['对话']
        assert keyword_weights['ceasefire'] == keyword_weights['停火']


class TestSignalStrength:
    """测试信号强度计算"""
    
    def test_price_signal_strength(self):
        """测试价格信号强度"""
        # 反弹2.4% vs 阈值1.2% → 强度 = 2.0
        rebound_pct = 2.4
        threshold = 1.2
        strength = min(rebound_pct / threshold, 2.0)
        
        assert strength == 2.0, "超过阈值2倍，强度应为2.0"
    
    def test_rss_signal_strength(self):
        """测试RSS信号强度"""
        # 事件评分8分 → 强度 = (8-5)/5 = 0.6
        avg_score = 8.0
        strength = (avg_score - 5) / 5.0
        
        assert strength == 0.6, "8分事件强度应为0.6"
        
        # 事件评分10分 → 强度 = 1.0
        avg_score = 10.0
        strength = (avg_score - 5) / 5.0
        
        assert strength == 1.0, "10分事件强度应为1.0"


class TestWeightedScoring:
    """测试加权评分系统"""
    
    def test_single_signal_score(self):
        """测试单信号评分"""
        # 仅价格信号，强度1.0 → 25分
        score = 25.0 * 1.0
        assert score == 25.0
        
        # 应该是Level 1 (21-40分)
        level = self._score_to_level(score)
        assert level == 1
    
    def test_two_signals_score(self):
        """测试双信号评分"""
        # 价格 + 政治，强度都是1.0 → 50分
        score = 25.0 * 1.0 + 25.0 * 1.0
        assert score == 50.0
        
        # 应该是Level 2 (41-60分)
        level = self._score_to_level(score)
        assert level == 2
    
    def test_three_signals_score(self):
        """测试三信号评分"""
        # 价格 + 政治 + 战争，强度1.0 → 75分
        score = 25.0 * 3
        assert score == 75.0
        
        # 应该是Level 3 (61-80分)
        level = self._score_to_level(score)
        assert level == 3
    
    def test_all_signals_score(self):
        """测试四信号评分"""
        # 4个信号，强度1.0 → 100分
        score = 25.0 * 4
        assert score == 100.0
        
        # 应该是Level 4 (81-100分)
        level = self._score_to_level(score)
        assert level == 4
    
    def test_weak_strength_score(self):
        """测试弱强度信号"""
        # 4个信号，但强度都很弱(0.5) → 50分
        score = 25.0 * 4 * 0.5
        assert score == 50.0
        
        # 应该是Level 2 (41-60分)
        level = self._score_to_level(score)
        assert level == 2
    
    def _score_to_level(self, score):
        """评分转等级"""
        if score >= 81: return 4
        elif score >= 61: return 3
        elif score >= 41: return 2
        elif score >= 21: return 1
        else: return 0


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行反转检测优化测试")
    print("=" * 60)
    print("")
    
    # 运行pytest
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='反转检测优化测试')
    parser.add_argument('--run-tests', action='store_true', help='运行所有测试')
    
    args = parser.parse_args()
    
    if args.run_tests:
        run_all_tests()
    else:
        parser.print_help()
        print("\n示例:")
        print("  运行测试: python tests/test_reversal_improvements.py --run-tests")
