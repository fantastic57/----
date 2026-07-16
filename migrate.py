#!/usr/bin/env python3
"""data.json 迁移脚本：
1. 把现有 array 格式转为 {weights, markers} 结构
2. 给每个 marker 追加 13 个新字段
"""
import json
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
BAK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json.bak.migrate")

# 13 个新字段默认值
NEW_FIELDS = {
    "school_elementary": "",
    "school_middle": "",
    "school_quality": "",
    "metro_line3_walk_min": None,
    "metro_lines": [],
    "metro_nearest_walk_min": None,
    "school_cycling_min": None,
    "work_bus_min": None,
    "work_car_min": None,
    "amenities_level": "",
    "environment": "",
    "prev_price_wan": None,
    "price_drop_pct": None,
}

# 10 个评分字段的权重默认值
DEFAULT_WEIGHTS = {
    "school_quality": 3,
    "metro_lines": 3,
    "metro_line3_walk_min": 3,
    "metro_nearest_walk_min": 3,
    "school_cycling_min": 3,
    "work_bus_min": 3,
    "work_car_min": 3,
    "parking": 3,
    "environment": 3,
    "amenities_level": 3,
}

def migrate():
    if not os.path.exists(DATA_FILE):
        print(f"未找到 {DATA_FILE}")
        return

    # 备份
    import shutil
    shutil.copy(DATA_FILE, BAK_FILE)
    print(f"已备份到 {BAK_FILE}")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # 兼容旧 array 格式
    if isinstance(raw, list):
        all_items = raw
    elif isinstance(raw, dict) and "items" in raw:
        print("data.json 已是新格式，跳过迁移")
        return
    else:
        print(f"未知格式: {type(raw)}")
        return

    # 分离 markers 和其他数据（circles/lines/pois）
    markers = []
    others = []
    for item in all_items:
        if item.get('type') in ('circle', 'polyline', 'poi'):
            others.append(item)
        else:
            markers.append(item)

    # 给每个 marker 追加 13 个新字段
    for m in markers:
        for k, v in NEW_FIELDS.items():
            if k not in m:
                m[k] = v

    new_data = {
        "weights": DEFAULT_WEIGHTS.copy(),
        "markers": markers,
        "others": others,   # circles/polylines/pois 保留兼容
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print(f"迁移完成：")
    print(f"  - markers: {len(markers)} 个（每个追加了 13 个字段）")
    print(f"  - others (circles/lines/pois): {len(others)} 个")
    print(f"  - weights: {len(DEFAULT_WEIGHTS)} 项")

if __name__ == "__main__":
    migrate()
