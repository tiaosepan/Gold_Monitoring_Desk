"""
日志系统配置
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(name: str, log_dir: str = 'logs') -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_dir: 日志文件目录
        
    Returns:
        配置好的日志记录器
    """
    # 创建日志目录
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), log_dir)
    os.makedirs(log_path, exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器（INFO及以上）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 - 所有日志（DEBUG及以上）
    all_log_file = os.path.join(log_path, f'{name}.log')
    file_handler = RotatingFileHandler(
        all_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 文件处理器 - 错误日志（ERROR及以上）
    error_log_file = os.path.join(log_path, f'{name}_error.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


# 性能日志装饰器
def log_performance(logger: logging.Logger):
    """
    性能监控装饰器
    
    Args:
        logger: 日志记录器
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            func_name = func.__name__
            
            try:
                logger.debug(f"开始执行: {func_name}")
                result = await func(*args, **kwargs)
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                logger.info(f"执行完成: {func_name} - 耗时 {duration_ms}ms")
                return result
            except Exception as e:
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                logger.error(f"执行失败: {func_name} - 耗时 {duration_ms}ms - 错误: {str(e)}", exc_info=True)
                raise
        
        return wrapper
    return decorator


# 预定义的日志记录器
main_logger = setup_logger('main')
scheduler_logger = setup_logger('scheduler')
sge_logger = setup_logger('sge_monitor')
reversal_logger = setup_logger('reversal_detector')
rss_logger = setup_logger('rss_collector')
us10y_logger = setup_logger('us10y_monitor')
api_logger = setup_logger('api')
