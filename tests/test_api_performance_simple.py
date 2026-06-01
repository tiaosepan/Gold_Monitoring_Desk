"""
API性能测试（简化版，无emoji）
"""
import time
import requests

def test_endpoint(url, name):
    """测试单个端点"""
    times = []
    for i in range(5):
        start = time.time()
        try:
            response = requests.get(url, timeout=10)
            elapsed_ms = (time.time() - start) * 1000
            times.append(elapsed_ms)
        except Exception as e:
            print(f"  请求{i+1}失败: {str(e)}")
            return None
    
    if times:
        avg = sum(times) / len(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        print(f"\n{name}")
        print(f"  平均: {avg:.0f}ms")
        print(f"  P95: {p95:.0f}ms")
        print(f"  状态: {'[OK]' if p95 < 500 else '[SLOW]'}")
        return p95
    
    return None

BASE_URL = "http://localhost:8000"
endpoints = [
    ("/api/status", "系统状态"),
    ("/api/reversal/latest", "反转最新"),
    ("/api/sge/latest", "SGE最新"),
    ("/api/us10y/latest", "美债最新")
]

print("="*60)
print("API性能测试 - 索引优化后")
print("="*60)

p95_values = []
for path, name in endpoints:
    p95 = test_endpoint(f"{BASE_URL}{path}", name)
    if p95:
        p95_values.append(p95)

if p95_values:
    avg_p95 = sum(p95_values) / len(p95_values)
    print("\n" + "="*60)
    print(f"平均P95延迟: {avg_p95:.0f}ms")
    print(f"目标: P95 < 500ms")
    print(f"状态: {'[OK]' if avg_p95 < 500 else '[需优化]'}")
    print("="*60)
