"""
缓存工具 - 减少数据库查询
"""
import time
from typing import Optional, Callable, Any
from functools import wraps


class SimpleCache:
    """简单的内存缓存（带TTL）"""
    
    def __init__(self):
        self._cache = {}
        self._expire_times = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            if time.time() < self._expire_times[key]:
                return self._cache[key]
            else:
                # 过期，删除
                del self._cache[key]
                del self._expire_times[key]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 60):
        """设置缓存值"""
        self._cache[key] = value
        self._expire_times[key] = time.time() + ttl_seconds
    
    def delete(self, key: str):
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]
            del self._expire_times[key]
    
    def clear(self):
        """清空所有缓存"""
        self._cache.clear()
        self._expire_times.clear()


# 全局缓存实例
_global_cache = SimpleCache()


def cached(ttl_seconds: int = 60, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl_seconds: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            _global_cache.set(cache_key, result, ttl_seconds)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            _global_cache.set(cache_key, result, ttl_seconds)
            return result
        
        # 根据函数类型返回对应的wrapper
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_cache() -> SimpleCache:
    """获取全局缓存实例"""
    return _global_cache
