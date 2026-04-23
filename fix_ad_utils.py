import re

with open('ITOM/backend/core/ad_utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace config = load_config() with config = load_config(user_id)
content = content.replace("config = load_config()", "config = load_config(user_id)")

# Replace function signatures to add user_id: int = None
funcs = [
    r'(def create_ad_user\(domain_controller_ip, bind_username, bind_password, username, display_name, password, ou_path,.*?domain_name, position_name=None, groups_to_add=None, conn_external=None)(\):)',
    r'(def get_ou_list\(bind_username: str, bind_password: str)(\):)',
    r'(def get_group_list\(bind_username: str, bind_password: str)(\):)',
    r'(def search_ad_users\(bind_username: str, bind_password: str, keyword: str = "")(\):)',
    r'(def get_ad_user_detail\(bind_username: str, bind_password: str, sAMAccountName: str)(\):)',
    r'(def change_user_password\(bind_username: str, bind_password: str, user_dn: str, new_password: str)(\):)',
    r'(def move_user_ou\(bind_username: str, bind_password: str, user_dn: str, new_ou_dn: str)(\):)',
    r'(def update_user_groups\(bind_username: str, bind_password: str, user_dn: str, old_groups: list, new_groups: list)(\):)',
    r'(def get_group_members\(bind_username: str, bind_password: str, group_dn: str)(\):)',
    r'(def update_group_members\(bind_username: str, bind_password: str, group_dn: str, old_members: list, new_members: list)(\):)',
    r'(def toggle_ad_user_status\(bind_username: str, bind_password: str, user_dn: str, enabled: bool)(\):)'
]

for fp in funcs:
    content = re.sub(fp, r'\1, user_id: int = None\2', content, flags=re.DOTALL)

with open('ITOM/backend/core/ad_utils.py', 'w', encoding='utf-8') as f:
    f.write(content)
