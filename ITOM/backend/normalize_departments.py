import os
import sys

# 将当前目录加入系统路径以加载模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models.asset import Employee, Asset
from core.ad_utils import extract_department

def normalize():
    db = SessionLocal()
    try:
        print("开始归一化人员部门信息...")
        employees = db.query(Employee).all()
        emp_count = 0
        for emp in employees:
            if emp.department and (',' in emp.department or '=' in emp.department):
                new_dept = extract_department(emp.department)
                if new_dept != emp.department:
                    print(f"  [人员] {emp.name}: {emp.department} -> {new_dept}")
                    emp.department = new_dept
                    emp_count += 1
        
        print(f"\n开始归一化资产台账中的冗余组织路径...")
        assets = db.query(Asset).all()
        asset_count = 0
        for asset in assets:
            if asset.dynamic_attributes and '所属组织' in asset.dynamic_attributes:
                old_dept = asset.dynamic_attributes['所属组织']
                if old_dept and (',' in old_dept or '=' in old_dept):
                    new_dept = extract_department(old_dept)
                    if new_dept != old_dept:
                        print(f"  [资产] {asset.asset_code}: {old_dept} -> {new_dept}")
                        # SQLAlchemy 会自动检测字典变化（如果是 JSONB/MutableDict）
                        # 强行更新以确保触发变更
                        new_attrs = dict(asset.dynamic_attributes)
                        new_attrs['所属组织'] = new_dept
                        asset.dynamic_attributes = new_attrs
                        asset_count += 1
        
        db.commit()
        print(f"\n归一化完成！")
        print(f"成功更新人员记录: {emp_count} 条")
        print(f"成功更新资产记录: {asset_count} 条")
    except Exception as e:
        print(f"发生错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    normalize()
