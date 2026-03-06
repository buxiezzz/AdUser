import openpyxl
wb = openpyxl.Workbook()
ws = wb.active
ws.append(["资产编号", "当前状态", "设备分类", "使用者AD账号", "MAC地址", "备注信息"])
ws.append(["TEST-001", "借用中", "笔记本", "admin", "00:11:22:33:44:55", "新员工入职"])
ws.append(["TEST-002", "在库", "显示器", "", "", "仓库备用"])
wb.save("test_assets.xlsx")
