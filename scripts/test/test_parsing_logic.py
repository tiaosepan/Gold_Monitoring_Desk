import re

# 模拟新浪API返回的数据
test_data = 'var hq_str_gds_AU9999="1005.50,0,1004.60,1005.00,1012.00,986.00,11:56:35,993.90,990.00,502834,1.00,40.00,2026-03-30,黄金99";'

match = re.search(r'"([^"]*)"', test_data)
if match:
    data_str = match.group(1)
    fields = data_str.split(',')
    
    print("=== 字段内容 ===")
    for i in range(min(15, len(fields))):
        print(f"字段{i}: {fields[i]}")
    
    print("\n=== 当前解析逻辑测试 ===")
    
    # 模拟当前代码逻辑
    price = 0.0
    try:
        if len(fields) > 2 and fields[2]:
            price = float(fields[2])
            print(f"✓ 步骤1: 使用字段2(现价) = {price}")
    except Exception as e:
        print(f"✗ 步骤1失败: {e}")
    
    if price == 0.0:
        try:
            if len(fields) > 3 and fields[3]:
                price = float(fields[3])
                print(f"✓ 步骤2: 使用字段3(开盘) = {price}")
        except Exception as e:
            print(f"✗ 步骤2失败: {e}")
    
    if price == 0.0:
        try:
            if len(fields) > 6 and fields[6]:
                price = float(fields[6])
                print(f"⚠️ 步骤3: 使用字段6 = {price}")
        except Exception as e:
            print(f"✗ 步骤3失败(字段6是时间): {e}")
    
    print(f"\n最终选择的价格: {price}")
    
    print("\n=== 正确的字段映射（推断） ===")
    print(f"昨收: 字段0 = {fields[0]}")
    print(f"开盘: 字段8? = {fields[8] if len(fields) > 8 else 'N/A'}")
    print(f"现价/买价: 字段2 = {fields[2]}")
    print(f"卖价: 字段3 = {fields[3]}")
    print(f"最高: 字段4 = {fields[4]}")
    print(f"最低: 字段5 = {fields[5]}")
    print(f"时间: 字段6 = {fields[6]}")
