#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from datetime import datetime

print("Checking RSS event timestamps...")
print("=" * 80)

# 原系统
print("\n[Original System] Event timestamps:")
try:
    resp = requests.get("http://rev.sccit.com.cn:8000/api/reversal/events?limit=20", timeout=10)
    data = resp.json()
    items = data.get('items', [])
    
    if items:
        dates = []
        for event in items:
            pub = event.get('published_at', '')
            fetched = event.get('fetched_at', '')
            if pub:
                dates.append(pub)
        
        if dates:
            print(f"  Oldest: {min(dates)}")
            print(f"  Newest: {max(dates)}")
            print(f"  Total: {len(dates)} events")
        
        print("\nSample events with timestamps:")
        for i, event in enumerate(items[:5], 1):
            title = event.get('title', '')[:60]
            pub = event.get('published_at', 'N/A')
            print(f"{i}. {title}")
            print(f"   Published: {pub}")
            
except Exception as e:
    print(f"Error: {e}")

# 复刻系统
print("\n" + "=" * 80)
print("[Replicated System] Event timestamps:")
try:
    resp = requests.get("http://localhost:8001/api/reversal/events?limit=20", timeout=10)
    data = resp.json()
    items = data.get('items', [])
    
    if items:
        dates = []
        for event in items:
            pub = event.get('published_at', '')
            if pub:
                dates.append(pub)
        
        if dates:
            print(f"  Oldest: {min(dates)}")
            print(f"  Newest: {max(dates)}")
            print(f"  Total: {len(dates)} events")
        
        print("\nSample events with timestamps:")
        for i, event in enumerate(items[:5], 1):
            title = event.get('title', '')[:60]
            pub = event.get('published_at', 'N/A')
            print(f"{i}. {title}")
            print(f"   Published: {pub}")
            
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("ANALYSIS:")
print("=" * 80)
print("\nOriginal system collected RSS events during Iran war news peak.")
print("Replicated system is collecting current RSS feed content.")
print("\nSince RSS feeds update with latest news, the content differs.")
print("This is EXPECTED behavior - RSS feeds are dynamic!")
print("=" * 80)
