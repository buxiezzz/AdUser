import sys
import os

from sqlalchemy.orm import Session
from database import SessionLocal
from models.asset import Asset, Category

db = SessionLocal()

try:
    # 1. Update Asset records to remove "MAC地址" from dynamic_attributes if it exists
    assets = db.query(Asset).all()
    count = 0
    for asset in assets:
        if asset.dynamic_attributes is not None and "MAC地址" in asset.dynamic_attributes:
            new_attrs = dict(asset.dynamic_attributes)
            del new_attrs["MAC地址"]
            asset.dynamic_attributes = new_attrs
            count += 1
    
    # 2. Update Categories to remove "MAC地址" from default_attributes
    categories = db.query(Category).all()
    cat_count = 0
    for cat in categories:
        if cat.default_attributes is not None and "MAC地址" in cat.default_attributes:
            new_attrs = dict(cat.default_attributes)
            del new_attrs["MAC地址"]
            cat.default_attributes = new_attrs
            cat_count += 1
            
    db.commit()
    print(f"Removed MAC address from {count} assets and {cat_count} categories.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
