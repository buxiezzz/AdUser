# /utils.py
import os
import sys
import json
from functools import wraps
from flask import session, flash, redirect, url_for

CONFIG_FILE, POSITIONS_FILE, RULES_FILE = 'config.json', 'positions.json', 'description_rules.json'


def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content: raise FileNotFoundError  # 将空文件视作未找到
            return json.loads(content), False
    except FileNotFoundError:
        print(f"INFO: '{CONFIG_FILE}' not found. Creating a new one...")
        DEFAULT_CONFIG = {
            "DOMAIN_CONTROLLER_IP": "your_dc.your_domain.com",
            "DOMAIN_NAME": "your_domain.com",
            "DEFAULT_USER_PASSWORD": "ChangeMePlease123!",
            "REGION_OPTIONS": [
                {"code": "all", "name": "显示所有地区 (Default)", "keywords": []},
                {"code": "wuhan", "name": "仅显示武汉 (Wuhan)", "keywords": ["武汉", "Wuhan"]},
                {"code": "shanghai", "name": "仅显示上海 (Shanghai)", "keywords": ["上海", "Shanghai"]},
                {"code": "changsha", "name": "仅显示长沙 (Changsha)", "keywords": ["长沙", "Changsha"]}
            ]
        }
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG, True  # 返回 True 表示是首次运行
    except json.JSONDecodeError:
        print(f"FATAL ERROR: '{CONFIG_FILE}' is corrupted.")
        sys.exit(1)


def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)


def load_positions():
    try:
        with open(POSITIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_positions(data):
    with open(POSITIONS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)


def load_rules():
    default_rules = {"battalion_rules": {}, "position_rules": {}, "department_rules": {}, "ou_group_rules": {}}
    try:
        with open(RULES_FILE, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            # 确保所有键都存在，防止旧文件格式出错
            for key in default_rules:
                if key in loaded_data:
                    default_rules[key] = loaded_data[key]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return default_rules


def save_rules(data):
    with open(RULES_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)


def simplify_dn(dn_string, base_dn):
    readable_part = dn_string.replace(f',{base_dn}', '').replace(f'{base_dn}', '')
    parts = readable_part.split(',')
    cleaned_parts = [p.split('=')[1] for p in parts if p]
    cleaned_parts.reverse()
    return ' / '.join(cleaned_parts) if cleaned_parts else "Domain Root"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'bind_username' not in session:
            flash('请先登录才能访问该页面。', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)

    return decorated_function


# 在模块加载时读取一次配置，供其他模块导入使用
CONFIG, _ = load_config()