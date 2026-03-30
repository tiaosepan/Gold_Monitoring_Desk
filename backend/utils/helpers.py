"""
辅助工具函数
"""
from datetime import datetime, time
from typing import Dict


def check_market_status() -> Dict:
    """
    检查市场开盘状态
    
    Returns:
        包含市场状态信息的字典
    """
    now = datetime.now()
    current_time = now.time()
    
    # 市场开盘时间: 09:00 - 15:30 (周一至周五)
    market_open = time(9, 0)
    market_close = time(15, 30)
    
    # 检查是否为工作日
    is_weekday = now.weekday() < 5  # 0-4 为周一至周五
    
    # 检查是否在交易时间内
    is_trading_time = market_open <= current_time <= market_close
    
    # 市场开盘状态
    is_open = is_weekday and is_trading_time
    
    return {
        'is_open': is_open,
        'timestamp': now,
        'market_name': 'SGE',
        'current_time': current_time.strftime('%H:%M:%S'),
        'is_weekday': is_weekday,
        'is_trading_time': is_trading_time
    }


def format_price(price: float, decimals: int = 2) -> str:
    """
    格式化价格显示
    
    Args:
        price: 价格
        decimals: 小数位数
        
    Returns:
        格式化后的价格字符串
    """
    return f"{price:.{decimals}f}"


def calculate_change_percent(current: float, previous: float) -> float:
    """
    计算涨跌幅
    
    Args:
        current: 当前值
        previous: 之前值
        
    Returns:
        涨跌幅百分比
    """
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def oz_to_gram(oz_price: float) -> float:
    """
    盎司价格转换为克价格
    
    Args:
        oz_price: 盎司价格
        
    Returns:
        克价格
    """
    return oz_price / 31.1035


def gram_to_oz(gram_price: float) -> float:
    """
    克价格转换为盎司价格
    
    Args:
        gram_price: 克价格
        
    Returns:
        盎司价格
    """
    return gram_price * 31.1035


def is_market_holiday(date: datetime = None) -> bool:
    """
    判断是否为节假日
    
    Args:
        date: 日期，默认为当前日期
        
    Returns:
        是否为节假日
    """
    if date is None:
        date = datetime.now()
    
    # 简化版本：只判断周末
    # 实际应用中应该维护一个节假日列表
    return date.weekday() >= 5  # 5,6 为周六、周日


def safe_float(value, default: float = 0.0) -> float:
    """
    安全转换为浮点数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        浮点数
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default: int = 0) -> int:
    """
    安全转换为整数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        整数
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def timestamp_to_str(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    时间戳转字符串
    
    Args:
        timestamp: 时间戳
        format_str: 格式字符串
        
    Returns:
        格式化的时间字符串
    """
    if timestamp is None:
        return ""
    return timestamp.strftime(format_str)


def str_to_timestamp(time_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    字符串转时间戳
    
    Args:
        time_str: 时间字符串
        format_str: 格式字符串
        
    Returns:
        时间戳
    """
    try:
        return datetime.strptime(time_str, format_str)
    except ValueError:
        return datetime.now()
