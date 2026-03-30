#!/usr/bin/env python3
"""检查路由注册情况"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from backend.api.routes import router

print(f"路由总数: {len(router.routes)}\n")
print("所有路由路径:")
print("-" * 60)

routes_info = []
for r in router.routes:
    path = r.path
    methods = list(r.methods) if hasattr(r, 'methods') else []
    routes_info.append((path, methods))

for path, methods in sorted(routes_info):
    methods_str = ', '.join(methods) if methods else 'N/A'
    print(f"{path:40} [{methods_str}]")
