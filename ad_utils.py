# /ad_utils.py
import ssl
from flask import session
from ldap3 import Server, Connection, Tls, ALL, SUBTREE, LEVEL, MODIFY_ADD
from utils import load_rules, CONFIG


def get_base_dn(domain_name):
    """根据域名生成 Base DN"""
    return ",".join([f"DC={part}" for part in domain_name.split('.')])


def create_ou_if_not_exists(conn, ou_dn, domain_name):
    """递归检查并创建不存在的组织单元 (OU)。"""
    if ou_dn.lower() == get_base_dn(domain_name).lower():
        return True, "Base DN always exists."

    conn.search(search_base=ou_dn, search_filter='(objectClass=organizationalUnit)', search_scope=LEVEL,
                attributes=['ou'])
    if conn.entries:
        return True, f"OU '{ou_dn}' already exists."

    parent_dn = ','.join(ou_dn.split(',')[1:])

    parent_exists, parent_message = create_ou_if_not_exists(conn, parent_dn, domain_name)
    if not parent_exists:
        return False, f"Failed to create parent OU '{parent_dn}': {parent_message}"

    conn.add(ou_dn, 'organizationalUnit')
    if conn.result['result'] == 0:
        return True, f"Successfully created OU '{ou_dn}'."
    else:
        if conn.result['result'] == 68:
            return True, f"OU '{ou_dn}' already exists (race condition)."
        return False, f"Failed to create OU '{ou_dn}': {conn.result['description']}"


def create_ad_user(domain_controller_ip, bind_username, bind_password, username, display_name, password, ou_path,
                   domain_name, position_name=None, groups_to_add=None, conn_external=None):
    """在 AD 中创建新用户的核心函数。"""
    conn = conn_external
    try:
        if not conn:
            tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
            server = Server(domain_controller_ip, port=636, use_ssl=True, get_info=ALL, tls=tls_config)
            conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)

        if not conn.bound:
            return False, f"错误: LDAP 认证失败。 {conn.result}"

        ou_exists, ou_message = create_ou_if_not_exists(conn, ou_path, domain_name)
        if not ou_exists:
            return False, f"OU 创建失败: {ou_message}"

        # 最终修正：使用正确、简洁的逻辑来检查用户是否存在
        conn.search(
            search_base=get_base_dn(domain_name),
            search_filter=f'(sAMAccountName={username})',
            search_scope=SUBTREE,
            attributes=['distinguishedName', 'objectClass']
        )
        # 核心逻辑：只有当 conn.entries 列表不为空时，才代表用户真正存在。
        if conn.entries:
            found_object = conn.entries[0]
            dn = found_object.distinguishedName.value if 'distinguishedName' in found_object else 'N/A'
            oc = found_object.objectClass.value if 'objectClass' in found_object else 'N/A'
            details = f" 系统发现了一个冲突对象: DN='{dn}', 类型='{oc}'."
            return False, f"错误: 登录名 '{username}' 已被占用。{details}"

        if conn.search(search_base=ou_path, search_filter=f'(cn={display_name})', search_scope=LEVEL):
            return False, f"错误: 用户姓名 '{display_name}' 已存在于此组织单元中。"

        # --- 规则应用逻辑 ---
        rules_data = load_rules()
        battalion_rules = rules_data.get('battalion_rules', {})
        position_rules = rules_data.get('position_rules', {})
        department_rules = rules_data.get('department_rules', {})
        ou_group_rules = rules_data.get('ou_group_rules', {})

        description = ""
        is_battalion = False

        # 1. 优先应用单位规则
        for ou_keyword, ou_code in battalion_rules.items():
            if ou_keyword in ou_path:
                current_position_name = position_name if position_name else ""
                position_code = position_rules.get(current_position_name, "NA")
                description = f"{ou_code}-{position_code}-{display_name}"
                is_battalion = True
                break

        # 2. 如果单位规则未匹配，再应用部门规则
        if not is_battalion:
            for ou_keyword, dept_prefix in department_rules.items():
                if ou_keyword in ou_path:
                    description = f"{dept_prefix}-{display_name}"
                    break

        # 3. 应用自动加组规则
        if groups_to_add is None:
            groups_to_add = []
        for ou_keyword, group_dn in ou_group_rules.items():
            if ou_keyword in ou_path:
                groups_to_add.append(group_dn)
                break

        # --- 规则应用结束 ---

        user_dn = f"CN={display_name},{ou_path}"
        user_principal_name = f"{username}@{domain_name}"
        encoded_password = f'"{password}"'.encode('utf-16-le')
        user_account_control = 512 + 65536
        attributes = {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'cn': display_name, 'sAMAccountName': username,
            'userPrincipalName': user_principal_name, 'givenName': display_name,
            'sn': display_name, 'displayName': display_name,
            'unicodePwd': encoded_password, 'userAccountControl': str(user_account_control)
        }
        if description:
            attributes['description'] = description

        conn.add(user_dn, attributes=attributes)
        if conn.result['result'] != 0:
            return False, f"创建用户 '{username}' 时出错: {conn.result['description']}"

        if groups_to_add:
            groups_to_add = list(set(groups_to_add))
            for group_dn in groups_to_add:
                conn.modify(group_dn, {'member': [(MODIFY_ADD, [user_dn])]})
                if conn.result['result'] != 0 and conn.result['result'] != 68:
                    return True, f"用户 '{display_name}' 创建成功，但添加到组 '{group_dn}' 时失败: {conn.result['description']}"

        success_message = f"用户 '{display_name}' (登录名: {username}) 创建成功。"
        if description:
            success_message += f" 描述已自动设为 '{description}'。"

        return True, success_message
    except Exception as e:
        return False, f"发生意外错误: {e}"
    finally:
        if not conn_external and conn and conn.bound:
            conn.unbind()


def get_ou_list():
    """从 AD 获取所有组织单元 (OU) 列表"""
    ou_list = []
    conn = None
    bind_username, bind_password = session.get('bind_username'), session.get('bind_password')
    if not bind_username or not bind_password: return []
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(CONFIG['DOMAIN_CONTROLLER_IP'], port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return []
        search_base = get_base_dn(CONFIG['DOMAIN_NAME'])
        conn.search(search_base, '(objectClass=organizationalUnit)', SUBTREE, attributes=['distinguishedName'])
        for entry in conn.entries: ou_list.append(str(entry.distinguishedName))
    except Exception as e:
        print(f"Error fetching OU list: {e}")
    finally:
        if conn and conn.bound: conn.unbind()
    return sorted(list(set(ou_list)))


def get_group_list():
    """从 AD 获取所有安全组列表"""
    group_list = []
    conn = None
    bind_username, bind_password = session.get('bind_username'), session.get('bind_password')
    if not bind_username or not bind_password: return []
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(CONFIG['DOMAIN_CONTROLLER_IP'], port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return []
        search_base = get_base_dn(CONFIG['DOMAIN_NAME'])
        conn.search(search_base, '(&(objectClass=group)(groupType:1.2.840.113556.1.4.803:=-2147483648))', SUBTREE,
                    attributes=['distinguishedName'])
        for entry in conn.entries: group_list.append(str(entry.distinguishedName))
    except Exception as e:
        print(f"Error fetching group list: {e}")
    finally:
        if conn and conn.bound: conn.unbind()
    return sorted(list(set(group_list)))