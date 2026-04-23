import re

with open('ITOM/backend/api/routers/ad.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace config = load_config() with config = load_config(current_user.id)
content = content.replace("config = load_config()", "config = load_config(current_user.id)")

# Regex replacements for function calls
content = re.sub(r'(toggle_ad_user_status\(.*?sys_bind_pass, payload\.user_dn, payload\.enabled)(\))', r'\1, user_id=current_user.id\2', content)
content = re.sub(r'(create_ad_user\([^)]*?groups_to_add=payload\.groups)(\s*\))', r'\1, user_id=current_user.id\2', content)
content = re.sub(r'(search_ad_users\(sys_bind_user, sys_bind_pass, keyword)(\))', r'\1, user_id=current_user.id\2', content)
content = re.sub(r'(get_ad_user_detail\(sys_bind_user, sys_bind_pass, username)(\))', r'\1, user_id=current_user.id\2', content)
content = re.sub(r'(change_user_password\(sys_bind_user, sys_bind_pass, payload\.user_dn, payload\.new_password)(\))', r'\1, user_id=current_user.id\2', content)
content = re.sub(r'(move_user_ou\(sys_bind_user, sys_bind_pass, payload\.user_dn, payload\.new_ou_dn)(\))', r'\1, user_id=current_user.id\2', content)
content = re.sub(r'(update_user_groups\(sys_bind_user, sys_bind_pass, payload\.user_dn, payload\.old_groups, payload\.new_groups)(\))', r'\1, user_id=current_user.id\2', content)
content = re.sub(r'(get_ou_list\(sys_bind_user, sys_bind_pass)(\))', r'\1, user_id=current_user.id\2', content)
content = re.sub(r'(get_group_list\(sys_bind_user, sys_bind_pass)(\))', r'\1, user_id=current_user.id\2', content)
content = re.sub(r'(get_group_members\(sys_bind_user, sys_bind_pass, payload\.group_dn)(\))', r'\1, user_id=current_user.id\2', content)
content = re.sub(r'(update_group_members\(sys_bind_user, sys_bind_pass, payload\.group_dn, payload\.old_members, payload\.new_members)(\))', r'\1, user_id=current_user.id\2', content)

with open('ITOM/backend/api/routers/ad.py', 'w', encoding='utf-8') as f:
    f.write(content)
