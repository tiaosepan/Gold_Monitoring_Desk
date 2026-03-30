"""
API性能剖析 - 定位瓶颈
"""
import time
import requests

def benchmark(url, name, times=10):
    """基准测试"""
    latencies = []
    for _ in range(times):
        start = time.time()
        try:
            response = requests.get(url, timeout=10)
            elapsed_ms = (time.time() - start) * 1000
            latencies.append(elapsed_ms)
        except Exception as e:
            print(f"  错误: {e}")
            return None
    
    if latencies:
        avg = sum(latencies) / len(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        print(f"{name:30} 平均={avg:6.0f}ms  P95={p95:6.0f}ms")
        return p95
    return None

print("="*70)
print("API性能剖析 - 逐层测试")
print("="*70)
print()

BASE = "http://localhost:8000"

print("层次1: 框架基线（无数据库）")
print("-" * 70)
benchmark(f"{BASE}/api/ping", "无数据库查询")
print()

print("层次2: 单次数据库查询")
print("-" * 70)
benchmark(f"{BASE}/api/db_test", "单次ORDER BY+FIRST")
print()

print("层次3: 完整端点")
print("-" * 70)
benchmark(f"{BASE}/api/status", "系统状态（37个查询）")
benchmark(f"{BASE}/api/reversal/latest", "反转最新")
benchmark(f"{BASE}/api/sge/latest", "SGE最新")
print()

print("="*70)
print("诊断结论:")
print("  如果ping很快但db_test慢 -> 数据库连接问题")
print("  如果db_test快但status慢 -> 查询数量过多")
print("="*70)
