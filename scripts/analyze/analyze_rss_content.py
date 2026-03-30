#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.database import SessionLocal, RSSEvent

db = SessionLocal()

print("=" * 80)
print("RSS Content Analysis - Replicated System")
print("=" * 80)

# 检查所有RSS事件的类型和关键词
events = db.query(RSSEvent).order_by(RSSEvent.published_at.desc()).limit(50).all()

political_count = 0
war_count = 0
other_count = 0

war_related_keywords = ['war', 'iran', 'oil', 'crude', 'military', 'conflict', 'peace', 'ceasefire', '战争', '伊朗', '原油', '军事', '停火', '和谈']

print(f"\nTotal events analyzed: {len(events)}")
print("\nEvent type distribution:")

for event in events:
    if event.event_type == 'political':
        political_count += 1
    elif event.event_type == 'war':
        war_count += 1
    else:
        other_count += 1

print(f"  Political: {political_count}")
print(f"  War: {war_count}")
print(f"  Other: {other_count}")

# 检查是否有战争相关内容
print("\nWar/Oil related events:")
war_related = []
for event in events:
    title_lower = event.title.lower()
    summary_lower = (event.summary or '').lower()
    content = f"{title_lower} {summary_lower}"
    
    for keyword in war_related_keywords:
        if keyword.lower() in content:
            war_related.append(event)
            break

print(f"Found {len(war_related)} war/oil related events")
for i, event in enumerate(war_related[:10], 1):
    print(f"\n{i}. [{event.event_type}] {event.title[:80]}")
    if event.matched_keywords:
        print(f"   Keywords: {event.matched_keywords}")

# 显示一些非战争相关的事件
print("\n" + "=" * 80)
print("Non-war related events (tech/finance news):")
print("=" * 80)
non_war = [e for e in events if e not in war_related]
for i, event in enumerate(non_war[:10], 1):
    print(f"\n{i}. [{event.event_type}] {event.title[:80]}")

print("\n" + "=" * 80)
print("CONCLUSION:")
print("=" * 80)
print("\nThe RSS sources are collecting general financial/tech news,")
print("not specifically war/oil related content like the original system.")
print("\nThis is because:")
print("1. RSS feed content changes over time")
print("2. Original system may have collected during war news peak")
print("3. Current RSS feeds have shifted to tech/finance topics")
print("\nTo match original system, we need RSS sources that focus on:")
print("  - Geopolitical news (war, conflict, peace talks)")
print("  - Oil/energy markets")
print("  - Gold-related economic news")
print("=" * 80)

db.close()
