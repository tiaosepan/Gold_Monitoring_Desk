"""
API性能测试
验证数据库索引优化效果
"""
import time
import requests
import statistics


def test_api_performance():
    """测试API性能"""
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/api/status",
        "/api/reversal/status",
        "/api/reversal/history?limit=100",
        "/api/reversal/events?limit=50",
        "/api/sge/latest?limit=100",
    ]
    
    results = {}
    
    print("=" * 60)
    print("API性能测试")
    print("=" * 60)
    print()
    
    for endpoint in endpoints:
        print(f"测试端点: {endpoint}")
        times = []
        
        # 预热请求
        try:
            requests.get(f"{base_url}{endpoint}", timeout=10)
        except:
            pass
        
        # 执行5次测试
        for i in range(5):
            try:
                start = time.time()
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                duration = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    times.append(duration)
                    print(f"  第{i+1}次: {duration:.2f}ms")
                else:
                    print(f"  第{i+1}次: 失败 (HTTP {response.status_code})")
            except Exception as e:
                print(f"  第{i+1}次: 错误 - {str(e)}")
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            p95_time = statistics.quantiles(times, n=20)[18] if len(times) >= 5 else max_time
            
            results[endpoint] = {
                'avg': avg_time,
                'min': min_time,
                'max': max_time,
                'p95': p95_time
            }
            
            print(f"  平均: {avg_time:.2f}ms")
            print(f"  最小: {min_time:.2f}ms")
            print(f"  最大: {max_time:.2f}ms")
            print(f"  P95: {p95_time:.2f}ms")
        
        print()
    
    # 生成报告
    print("=" * 60)
    print("性能测试汇总")
    print("=" * 60)
    print()
    
    print(f"{'端点':<40} {'平均':<12} {'P95':<12} {'评级'}")
    print("-" * 80)
    
    for endpoint, perf in results.items():
        avg = perf['avg']
        p95 = perf['p95']
        
        # 性能评级
        if p95 < 100:
            rating = "优秀"
        elif p95 < 500:
            rating = "良好"
        elif p95 < 1000:
            rating = "一般"
        elif p95 < 2000:
            rating = "较慢"
        else:
            rating = "慢"
        
        print(f"{endpoint:<40} {avg:>8.0f}ms    {p95:>8.0f}ms    {rating}")
    
    print()
    print("性能目标: P95 < 500ms (良好), P95 < 100ms (优秀)")
    print()
    
    # 评估总体性能
    avg_p95 = statistics.mean([p['p95'] for p in results.values()])
    if avg_p95 < 100:
        overall = "⭐⭐⭐⭐⭐ 优秀"
    elif avg_p95 < 500:
        overall = "⭐⭐⭐⭐ 良好"
    elif avg_p95 < 1000:
        overall = "⭐⭐⭐ 一般"
    else:
        overall = "⭐⭐ 需优化"
    
    print(f"总体性能评级: {overall} (平均P95: {avg_p95:.0f}ms)")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    test_api_performance()
