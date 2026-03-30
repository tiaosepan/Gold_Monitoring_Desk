"""
分析RSS事件差距
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from datetime import datetime
from dateutil import parser as date_parser

# 获取原系统最新10条
print("获取原系统最新10条事件...")
orig_resp = requests.get("http://rev.sccit.com.cn:8000/api/reversal/events?limit=10")
orig_data = orig_resp.json()

# 获取本地系统最新10条
print("获取本地系统最新10条事件...")
local_resp = requests.get("http://localhost:8001/api/reversal/events?limit=10")
local_data = local_resp.json()

print("\n" + "=" * 80)
print("原系统最新事件")
print("=" * 80)

for i, item in enumerate(orig_data['items'][:5], 1):
    fetched = date_parser.parse(item['fetched_at'])
    published = date_parser.parse(item['published_at'])
    print(f"\n[{i}] ID:{item['id']} | 来源:{item['source']}")
    print(f"    采集: {fetched.strftime('%m-%d %H:%M')}")
    print(f"    发布: {published.strftime('%m-%d %H:%M')}")
    print(f"    标题: {item['title'][:60]}...")

print("\n" + "=" * 80)
print("本地系统最新事件")
print("=" * 80)

for i, item in enumerate(local_data['items'][:5], 1):
    fetched = date_parser.parse(item['fetched_at'])
    published = date_parser.parse(item['published_at'])
    print(f"\n[{i}] ID:{item['id']} | 来源:{item['source']}")
    print(f"    采集: {fetched.strftime('%m-%d %H:%M')}")
    print(f"    发布: {published.strftime('%m-%d %H:%M')}")
    print(f"    标题: {item['title'][:60]}...")

# 分析差异
print("\n" + "=" * 80)
print("差异分析")
print("=" * 80)

orig_titles = {item['title'] for item in orig_data['items']}
local_titles = {item['title'] for item in local_data['items']}

only_in_orig = orig_titles - local_titles
only_in_local = local_titles - orig_titles

print(f"\n原系统独有事件数: {len(only_in_orig)}")
if only_in_orig:
    print("原系统独有事件（前3条）:")
    for title in list(only_in_orig)[:3]:
        print(f"  - {title[:70]}...")

print(f"\n本地系统独有事件数: {len(only_in_local)}")
if only_in_local:
    print("本地系统独有事件（前3条）:")
    for title in list(only_in_local)[:3]:
        print(f"  - {title[:70]}...")

# 检查原系统最新事件的发布时间
if orig_data['items']:
    orig_latest_published = date_parser.parse(orig_data['items'][0]['published_at'])
    print(f"\n原系统最新事件发布时间: {orig_latest_published}")
    
    # 检查本地系统是否有这个时间之后发布的事件
    local_latest_published = date_parser.parse(local_data['items'][0]['published_at'])
    print(f"本地系统最新事件发布时间: {local_latest_published}")
    
    # 移除时区信息进行比较
    orig_pub_naive = orig_latest_published.replace(tzinfo=None)
    local_pub_naive = local_latest_published.replace(tzinfo=None) if local_latest_published.tzinfo else local_latest_published
    
    time_diff_minutes = (orig_pub_naive - local_pub_naive).total_seconds() / 60
    print(f"\n发布时间差: {time_diff_minutes:.1f} 分钟")
    
    if time_diff_minutes > 60:
        print("\n[问题] 原系统有更新的内容（发布时间晚1小时以上）")
        print("       可能原因：")
        print("       1. RSS源发布了新内容，但本地系统尚未采集")
        print("       2. 本地系统采集频率不够高")
        print("       3. 本地系统的关键词过滤太严格，过滤掉了一些事件")
    elif time_diff_minutes > 10:
        print("\n[注意] 原系统有稍新的内容（发布时间晚10分钟以上）")
    else:
        print("\n[正常] 两系统内容基本同步")
