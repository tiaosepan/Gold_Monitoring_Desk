#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

print("=" * 80)
print("RSS Events Comparison")
print("=" * 80)

# 获取原系统的RSS事件
print("\n[Original System] RSS Events:")
try:
    resp = requests.get("http://rev.sccit.com.cn:8000/api/reversal/events?limit=10", timeout=10)
    data = resp.json()
    items = data.get('items', [])
    print(f"Total: {len(items)} events\n")
    for i, event in enumerate(items[:10], 1):
        title = event.get('title', 'No title')
        event_type = event.get('event_type', 'unknown')
        print(f"{i}. [{event_type}] {title}")
except Exception as e:
    print(f"Error: {e}")

# 获取复刻系统的RSS事件
print("\n" + "=" * 80)
print("[Replicated System] RSS Events:")
try:
    resp = requests.get("http://localhost:8001/api/reversal/events?limit=10", timeout=10)
    data = resp.json()
    items = data.get('items', [])
    print(f"Total: {len(items)} events\n")
    for i, event in enumerate(items[:10], 1):
        title = event.get('title', 'No title')
        event_type = event.get('event_type', 'unknown')
        print(f"{i}. [{event_type}] {title}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
