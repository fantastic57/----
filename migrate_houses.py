#!/usr/bin/env python3
"""data.json 迁移：加 houses 字段和 house_weights 顶层字段"""
import json
import os
import shutil

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
BAK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json.bak.houses")

DEFAULT_HOUSE_WEIGHTS = {
    "built_year": 3,
    "price_tier": 3,
    "area_sqm": 3,
    "internal_area_sqm": 3,
    "floor_num": 3,
    "has_elevator": 3,
    "stairwell": 3,
    "households_per_floor": 3,
    "room_layout": 3,
    "layout_type": 3,
    "daylight": 3,
    "north_south_transparent": 3,
    "noise": 3,
    "privacy": 3,
    "decoration": 3,
    "seller_mood": 3,
}

def migrate():
    if not os.path.exists(DATA_FILE):
        print("no data.json")
        return
    shutil.copy(DATA_FILE, BAK_FILE)
    print(f"backup: {BAK_FILE}")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "house_weights" not in data:
        data["house_weights"] = DEFAULT_HOUSE_WEIGHTS.copy()
        print(f"added house_weights ({len(DEFAULT_HOUSE_WEIGHTS)} fields)")
    n = 0
    for m in data.get("markers", []):
        if "houses" not in m:
            m["houses"] = []
            n += 1
    print(f"added houses=[] to {n} markers")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("done")

if __name__ == "__main__":
    migrate()