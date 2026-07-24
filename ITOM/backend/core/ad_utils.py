# /ad_utils.py
import ssl
import re
from ldap3 import Server, Connection, Tls, ALL, SUBTREE, LEVEL, BASE, MODIFY_ADD, MODIFY_REPLACE

from .utils import load_rules
from api.routers.settings import load_config


def get_base_dn(domain_name):
    """根据域名生成 Base DN"""
    return ",".join([f"DC={part}" for part in domain_name.split('.')])


def extract_department(dn: str):
    """从 DN 中提取最直接的所属部门/OU名称"""
    if not dn:
        return ""
    parts = dn.split(',')
    # 优先查找第一个 OU=
    for p in parts:
        if p.upper().startswith('OU='):
            return p.split('=')[1]
    # 其次查找第一个 CN= (如果是容器而非 OU)
    for p in parts:
        if p.upper().startswith('CN='):
            return p.split('=')[1]
    # 最后兜底取第一段
    return parts[0].split('=')[-1] if '=' in parts[0] else parts[0]


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
                   domain_name, position_name=None, groups_to_add=None, conn_external=None, location_id: int = None):
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

        # --- 规则应用逻辑 (自动生成 Description) ---
        config = load_config(location_id)
        ou_prefix_mapping = config.get("OU_PREFIX_MAPPING", {})
        positions = config.get("POSITIONS", [])

        # 1. 解析 AA (部门标识)
        # 增加继承逻辑：如果当前 OU 没配，则向上一级查找
        aa_code = None
        current_check_ou = ou_path
        while "," in current_check_ou:
            aa_code = ou_prefix_mapping.get(current_check_ou)
            if aa_code:
                break
            # 向上移动一级
            parts = current_check_ou.split(',')
            parts.pop(0)
            current_check_ou = ",".join(parts)
            # 停止条件：如果不再包含 OU=，说明到了域根部
            if "OU=" not in current_check_ou:
                break
        
        if not aa_code:
             try:
                 # 回退逻辑：'OU=Dev,OU=Tech,DC=example,DC=com' -> 'Dev'
                 first_part = ou_path.split(',')[0]
                 if first_part.startswith('OU='):
                     aa_code = first_part[3:]
                 else:
                     aa_code = "NA"
             except:
                 aa_code = "NA"
                 
        # 2. 解析 BB (职位后缀)
        bb_code = "NA"
        if position_name:
             for pos in positions:
                 if pos.get("name") == position_name:
                     bb_code = pos.get("suffix", "NA")
                     break

        # 3. 拼装 description (AA-BB-CC)
        description = f"{aa_code}-{bb_code}-{display_name}"

        # 4. 加组逻辑 (沿用之前的自动勾选和接口传值)
        if groups_to_add is None:
            groups_to_add = []
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


def get_ou_list(bind_username: str, bind_password: str, location_id: int = None, apply_filter: bool = False):
    """从 AD 获取所有组织单元 (OU) 列表"""
    ou_list = []
    conn = None
    if not bind_username or not bind_password: return []
    
    config = load_config(location_id)
    dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    domain_name = config.get('DOMAIN_NAME', '')
    
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return []
        search_base = get_base_dn(domain_name)
        conn.search(search_base, '(objectClass=organizationalUnit)', SUBTREE, attributes=['distinguishedName'])
        for entry in conn.entries: ou_list.append(str(entry.distinguishedName))
    except Exception as e:
        print(f"Error fetching OU list: {e}")
    finally:
        if conn and conn.bound: conn.unbind()
        
    # 使用全局配置过滤 OU
    region_filter = config.get('ACTIVE_REGION_CODE', 'all')
    
    # 查找匹配的配置项
    selected_region_config = next((item for item in config.get('REGION_OPTIONS', []) if item.get("code") == region_filter), None)

    if apply_filter and selected_region_config and selected_region_config.get('keywords'):
        keywords = selected_region_config['keywords']
        # 只要 DN 中包含任意一个关键词即保留
        ou_list = [dn for dn in ou_list if any(k in dn for k in keywords)]

    return sorted(list(set(ou_list)))


def get_group_list(bind_username: str, bind_password: str, location_id: int = None):
    """从 AD 获取所有安全组列表"""
    group_list = []
    conn = None
    if not bind_username or not bind_password: return []
    
    config = load_config(location_id)
    dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    domain_name = config.get('DOMAIN_NAME', '')
    
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return []
        search_base = get_base_dn(domain_name)
        conn.search(search_base, '(&(objectClass=group)(groupType:1.2.840.113556.1.4.803:=-2147483648))', SUBTREE,
                    attributes=['distinguishedName'])
        for entry in conn.entries: group_list.append(str(entry.distinguishedName))
    except Exception as e:
        print(f"Error fetching group list: {e}")
    finally:
        if conn and conn.bound: conn.unbind()
        
    # 已移除全局地区过滤器支持，改由调用方决定是否过滤 (目前组列表不启用过滤)
    return sorted(list(set(group_list)))


def search_ad_users(bind_username: str, bind_password: str, keyword: str = "", location_id: int = None):
    """从 AD 检索用户列表，支持按显示名或账号过滤"""
    users = []
    conn = None
    if not bind_username or not bind_password: return []
    
    config = load_config(location_id)
    dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    domain_name = config.get('DOMAIN_NAME', '')
    
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return []
        
        # 自动探测 Base DN，避免由于域名解析不准导致的路径缺失
        search_base = None
        if server.info and server.info.other:
            contexts = server.info.other.get('defaultNamingContext')
            if contexts:
                search_base = contexts[0] if isinstance(contexts, list) else contexts
        
        if not search_base:
            search_base = get_base_dn(domain_name)
        
        # 采用更专业的 AD 用户过滤语法：sAMAccountType=805306368 专指人员用户
        filter_str = '(&(objectClass=user)(sAMAccountType=805306368)'
        if keyword:
            # 支持使用空格、逗号、分号、换行符分隔的多个关键词批量检索
            k_list = [k.strip() for k in re.split(r'[,;\s\n\r]+', keyword) if k.strip()]
            if k_list:
                sub_filters = []
                for k in k_list:
                    sub_filters.append(f'(sAMAccountName=*{k}*)')
                    sub_filters.append(f'(displayName=*{k}*)')
                filter_str += f"(|{''.join(sub_filters)})"
        filter_str += ')'

        
        # 执行分页搜索，generator=False 可以直接从 conn.entries 获取全量合并后的结果
        conn.extend.standard.paged_search(
            search_base=search_base,
            search_filter=filter_str,
            search_scope=SUBTREE,
            attributes=['distinguishedName', 'sAMAccountName', 'displayName', 'description', 'userPrincipalName', 'userAccountControl'],
            paged_size=1000,
            generator=False
        )
        
        for entry in conn.entries:
            # 访问属性并处理列表值
            uac = int(entry.userAccountControl.value) if 'userAccountControl' in entry else 512
            
            user_info = {
                'dn': str(entry.distinguishedName) if 'distinguishedName' in entry else '',
                'username': str(entry.sAMAccountName) if 'sAMAccountName' in entry else '',
                'display_name': str(entry.displayName) if 'displayName' in entry else '',
                'description': str(entry.description) if 'description' in entry else '',
                'upn': str(entry.userPrincipalName) if 'userPrincipalName' in entry else '',
                'enabled': not (uac & 0x02)
            }
            users.append(user_info)
    except Exception as e:
        print(f"Error searching users: {e}")
    finally:
        if conn and conn.bound: conn.unbind()
    
    # 已移除全局地区过滤器支持，用户搜索应当显示所有地区
    return users


def get_ad_user_detail(bind_username: str, bind_password: str, sAMAccountName: str, location_id: int = None):
    """获取单个域用户的详细信息，包括他所在的 memberOf 安全组"""
    config = load_config(location_id)
    dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    domain_name = config.get('DOMAIN_NAME', '')
    
    conn = None
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return None
        
        search_base = get_base_dn(domain_name)
        conn.search(search_base, f'(sAMAccountName={sAMAccountName})', SUBTREE, 
                    attributes=['distinguishedName', 'sAMAccountName', 'displayName', 'description', 'userPrincipalName', 'memberOf', 'userAccountControl'])
        
        if conn.entries:
            entry = conn.entries[0]
            member_of = entry.memberOf.values if 'memberOf' in entry and entry.memberOf else []
            # LDAP库返回的memberOf如果是单个可能会不是list，这里保证它是list
            if not isinstance(member_of, list):
                member_of = [member_of]
                
            uac = int(entry.userAccountControl.value) if 'userAccountControl' in entry else 512
                
            return {
                'dn': str(entry.distinguishedName),
                'username': str(entry.sAMAccountName),
                'display_name': str(entry.displayName) if 'displayName' in entry else '',
                'description': str(entry.description) if 'description' in entry else '',
                'upn': str(entry.userPrincipalName) if 'userPrincipalName' in entry else '',
                'groups': [str(g) for g in member_of],
                'enabled': not (uac & 0x02)
            }
        return None
    except Exception as e:
        print(f"Error getting user detail: {e}")
        return None
    finally:
        if conn and conn.bound: conn.unbind()

def change_user_password(bind_username: str, bind_password: str, user_dn: str, new_password: str, location_id: int = None):
    """强制重置目标用户的密码"""
    config = load_config(location_id)
    dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    
    conn = None
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return False, "连接域控失败"
        
        encoded_password = f'"{new_password}"'.encode('utf-16-le')
        # 强制替换 unicodePwd
        conn.modify(user_dn, {'unicodePwd': [(2, [encoded_password])]}) # 2 is MODIFY_REPLACE
        
        if conn.result['result'] == 0:
            return True, "密码修改成功"
        else:
            return False, f"修改失败: {conn.result['description']}"
    except Exception as e:
        return False, f"发生异常: {str(e)}"
    finally:
        if conn and conn.bound: conn.unbind()

def move_user_ou(bind_username: str, bind_password: str, user_dn: str, new_ou_dn: str, location_id: int = None):
    """转移用户到新的 OU"""
    config = load_config(location_id)
    dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    
    conn = None
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return False, "连接域控失败"
        
        # 提取用户的 CN 部分, 例如 CN=张三
        cn_part = user_dn.split(',')[0]
        
        conn.modify_dn(user_dn, cn_part, new_superior=new_ou_dn)
        
        if conn.result['result'] == 0:
            return True, "部门调整成功"
        else:
            return False, f"调整失败: {conn.result['description']}"
    except Exception as e:
        return False, f"发生异常: {str(e)}"
    finally:
        if conn and conn.bound: conn.unbind()

from ldap3 import MODIFY_DELETE
def update_user_groups(bind_username: str, bind_password: str, user_dn: str, old_groups: list, new_groups: list, location_id: int = None):
    """差异化更新用户的安全组"""
    config = load_config(location_id)
    dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    
    conn = None
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return False, "连接域控失败"
        
        old_set = set(old_groups)
        new_set = set(new_groups)
        
        to_add = new_set - old_set
        to_remove = old_set - new_set
        
        errors = []
        for group in to_add:
            conn.modify(group, {'member': [(MODIFY_ADD, [user_dn])]})
            if conn.result['result'] != 0 and conn.result['result'] != 68: # 68 is already exists
                errors.append(f"加入组 {group} 失败: {conn.result['description']}")
                
        for group in to_remove:
            conn.modify(group, {'member': [(MODIFY_DELETE, [user_dn])]})
            if conn.result['result'] != 0:
                errors.append(f"移出组 {group} 失败: {conn.result['description']}")
                
        if errors:
            return False, "; ".join(errors)
        return True, "安全组权限更新成功"
    except Exception as e:
        return False, f"发生异常: {str(e)}"
    finally:
        if conn and conn.bound: conn.unbind()


def get_group_members(bind_username: str, bind_password: str, group_dn: str, location_id: int = None):
    """获取指定安全组的成员"""
    config = load_config(location_id)
    dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    
    conn = None
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return []
        
        conn.search(group_dn, '(objectClass=group)', BASE, attributes=['member'])
        
        if conn.entries:
            entry = conn.entries[0]
            if 'member' in entry and entry.member:
                members = entry.member.values
                if not isinstance(members, list):
                     members = [members]
                return [str(m) for m in members]
        return []
    except Exception as e:
        print(f"Error getting group members: {e}")
        return []
    finally:
        if conn and conn.bound: conn.unbind()

def update_group_members(bind_username: str, bind_password: str, group_dn: str, old_members: list, new_members: list, location_id: int = None):
    """批量调整安全组内成员，自动分担移除和新增操作"""
    config = load_config(location_id)
    dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    
    conn = None
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return False, "连接域控失败"
        
        old_set = set(old_members)
        new_set = set(new_members)
        
        to_add = new_set - old_set
        to_remove = old_set - new_set
        
        errors = []
        if to_add:
            conn.modify(group_dn, {'member': [(MODIFY_ADD, list(to_add))]})
            if conn.result['result'] != 0 and conn.result['result'] != 68:
                errors.append(f"添加新成员失败: {conn.result['description']}")
                
        if to_remove:
            conn.modify(group_dn, {'member': [(MODIFY_DELETE, list(to_remove))]})
            if conn.result['result'] != 0:
                errors.append(f"移出旧成员失败: {conn.result['description']}")
                
        if errors:
            return False, "; ".join(errors)
        return True, "群组成员清单更新分布成功"
    except Exception as e:
        return False, f"发生异常: {str(e)}"
    finally:
        if conn and conn.bound: conn.unbind()

def toggle_ad_user_status(bind_username: str, bind_password: str, user_dn: str, enabled: bool, location_id: int = None):
    """启用或禁用 AD 用户"""
    config = load_config(location_id)
    dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    
    conn = None
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound: return False, "连接域控失败"
        
        # 1. 获取当前的 userAccountControl
        conn.search(user_dn, '(objectClass=user)', BASE, attributes=['userAccountControl'])
        if not conn.entries:
            return False, "未找到目标用户对象"
            
        current_uac = int(conn.entries[0].userAccountControl.value)
        
        # 2. 位运算修改
        # 0x02 是 ACCOUNTDISABLE 位
        if enabled:
            # 启用: 去掉 0x02 位
            new_uac = current_uac & ~0x02
        else:
            # 禁用: 加上 0x02 位
            new_uac = current_uac | 0x02
            
        conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, [str(new_uac)])]})
        
        if conn.result['result'] == 0:
            status_text = "启用" if enabled else "禁用"
            return True, f"用户已成功{status_text}"
        else:
            return False, f"操作失败: {conn.result['description']}"
    except Exception as e:
        return False, f"发生异常: {str(e)}"
    finally:
        if conn and conn.bound: conn.unbind()


def batch_disable_ad_users(bind_username: str, bind_password: str, users: list, target_ou_dn: str = None, location_id: int = None):
    """批量禁用 AD 域用户，并将其移动至选定的目标 OU（保留所有原有安全组权限）"""
    config = load_config(location_id)
    dc_ip = config.get('DOMAIN_CONTROLLER_IP', '')
    
    conn = None
    results = []
    success_count = 0
    fail_count = 0

    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(dc_ip, port=636, use_ssl=True, tls=tls_config)
        conn = Connection(server, user=bind_username, password=bind_password, auto_bind=True)
        if not conn.bound:
            return False, "连接域控失败", []

        for item in users:
            username = item.get('username', '')
            user_dn = item.get('user_dn', '')
            if not user_dn:
                fail_count += 1
                results.append({'username': username, 'success': False, 'message': '未提供有效的用户 DN'})
                continue

            try:
                # 1. 查询用户当前的 UAC
                conn.search(user_dn, '(objectClass=user)', BASE, attributes=['userAccountControl'])
                if not conn.entries:
                    fail_count += 1
                    results.append({'username': username, 'success': False, 'message': 'AD 中未检索到目标用户对象'})
                    continue

                entry = conn.entries[0]
                current_uac = int(entry.userAccountControl.value) if 'userAccountControl' in entry else 512

                # 2. 修改 userAccountControl 禁用账号 (加上 0x02 位)
                new_uac = current_uac | 0x02
                conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, [str(new_uac)])]})
                if conn.result['result'] != 0:
                    fail_count += 1
                    results.append({'username': username, 'success': False, 'message': f"禁用账号失败: {conn.result['description']}"})
                    continue

                msg = "账号已成功禁用"

                # 3. 如果指定了目标 OU，则执行部门移动
                if target_ou_dn:
                    cn_part = user_dn.split(',')[0]
                    conn.modify_dn(user_dn, cn_part, new_superior=target_ou_dn)
                    if conn.result['result'] == 0:
                        msg += f"，已平滑转移至新 OU"
                    else:
                        msg += f"，但转移 OU 失败: {conn.result['description']}"

                success_count += 1
                results.append({'username': username, 'success': True, 'message': msg})
            except Exception as user_err:
                fail_count += 1
                results.append({'username': username, 'success': False, 'message': f"处理异常: {str(user_err)}"})

        summary_msg = f"批量禁用完成：成功 {success_count} 人，失败 {fail_count} 人"
        return True, summary_msg, results
    except Exception as e:
        return False, f"发生致命异常: {str(e)}", []
    finally:
        if conn and conn.bound:
            conn.unbind()