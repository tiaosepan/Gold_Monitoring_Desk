"""
使用aiohttp测试API性能（替代requests）
"""
import asyncio
import aiohttp
import time


async def benchmark_endpoint(session, url, name):
    """基准测试单个端点"""
    times = []
    
    for _ in range(10):
        start = time.time()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                await response.read()
                elapsed_ms = (time.time() - start) * 1000
                times.append(elapsed_ms)
        except Exception as e:
            print(f"  错误: {e}")
            return None
    
    if times:
        avg = sum(times) / len(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        print(f"{name:30} 平均={avg:6.0f}ms  P95={p95:6.0f}ms  状态={'[OK]' if p95 < 500 else '[SLOW]'}")
        return p95
    
    return None


async def main():
    print("="*70)
    print("API性能测试 - aiohttp客户端")
    print("="*70)
    print()
    
    BASE = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        p95_values = []
        
        endpoints = [
            ("/api/ping", "Ping端点（无DB）"),
            ("/api/db_test", "单次查询"),
            ("/api/status", "系统状态（37查询）"),
            ("/api/reversal/latest", "反转最新"),
            ("/api/sge/latest", "SGE最新"),
            ("/api/us10y/latest", "美债最新")
        ]
        
        for path, name in endpoints:
            p95 = await benchmark_endpoint(session, f"{BASE}{path}", name)
            if p95:
                p95_values.append(p95)
        
        if p95_values:
            avg_p95 = sum(p95_values) / len(p95_values)
            print()
            print("="*70)
            print(f"平均P95延迟: {avg_p95:.0f}ms")
            print(f"目标: P95 < 500ms")
            print(f"状态: {'[OK] 性能达标' if avg_p95 < 500 else '[SLOW] 需优化'}")
            print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
