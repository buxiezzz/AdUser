# /blueprints/management.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils import (login_required, load_config, save_config, load_positions,
                   save_positions, load_rules, save_rules, CONFIG)
from ad_utils import get_group_list, get_ou_list

management_bp = Blueprint('management', __name__, template_folder='../templates')


@management_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    # ... 此函数无变化 ...
    if request.method == 'POST':
        current_config, _ = load_config()
        current_config.update(
            {'DOMAIN_CONTROLLER_IP': request.form.get('dc_ip'), 'DOMAIN_NAME': request.form.get('domain_name'),
             'DEFAULT_USER_PASSWORD': request.form.get('default_user_password')})
        save_config(current_config)
        CONFIG.update(current_config)
        flash('服务器配置已更新。', 'success')
        return redirect(url_for('main.dashboard') if 'bind_username' in session else url_for('auth.login'))
    current_config, _ = load_config()
    return render_template('settings.html', config=current_config)


@management_bp.route('/positions', methods=['GET', 'POST'])
@login_required
def positions():
    positions_data = load_positions()
    edit_data = None

    # --- 新增：处理 GET 请求的编辑模式 ---
    if request.method == 'GET' and request.args.get('action') == 'edit':
        position_name_to_edit = request.args.get('name')
        if position_name_to_edit in positions_data:
            edit_data = {
                "name": position_name_to_edit,
                "groups": positions_data[position_name_to_edit]
            }

    if request.method == 'POST':
        action = request.form.get('action')
        position_name = request.form.get('position_name', '').strip()

        if action == 'create':
            selected_groups = request.form.getlist('groups')
            if position_name and selected_groups:
                if position_name in positions_data:
                    flash(f"创建失败：职位 '{position_name}' 已存在。", 'error')
                else:
                    positions_data[position_name] = selected_groups
                    save_positions(positions_data)
                    flash(f"职位 '{position_name}' 创建成功。", 'success')
            else:
                flash("创建失败：职位名称和所选组不能为空。", 'error')

        # --- 新增：处理 POST 请求的编辑逻辑 ---
        elif action == 'edit':
            original_name = request.form.get('original_name')
            new_name = position_name
            selected_groups = request.form.getlist('groups')

            if not all([original_name, new_name, selected_groups]):
                flash("更新失败：所有字段均为必填。", 'error')
            elif new_name != original_name and new_name in positions_data:
                flash(f"更新失败：新的职位名称 '{new_name}' 已被占用。", 'error')
            elif original_name not in positions_data:
                flash(f"更新失败：找不到原始职位 '{original_name}'。", 'error')
            else:
                # 先删除旧条目，再添加新条目，以处理职位名称可能被修改的情况
                del positions_data[original_name]
                positions_data[new_name] = selected_groups
                save_positions(positions_data)
                flash(f"职位 '{original_name}' 已成功更新为 '{new_name}'。", 'success')

        elif action == 'delete':
            p_name_to_delete = request.form.get('position_name_to_delete')
            if p_name_to_delete in positions_data:
                del positions_data[p_name_to_delete]
                save_positions(positions_data)
                flash(f"职位 '{p_name_to_delete}' 已被删除。", 'success')

        return redirect(url_for('management.positions'))

    return render_template('positions.html',
                           positions=positions_data,
                           group_options=get_group_list(),
                           config=CONFIG,
                           edit_data=edit_data)  # 将待编辑数据传给模板


@management_bp.route('/rules', methods=['GET', 'POST'])
@login_required
def rules():
    rules_data = load_rules()
    rule_map = {'battalion': 'battalion_rules', 'position': 'position_rules',
                'department': 'department_rules', 'ou_group': 'ou_group_rules'}
    edit_data = None

    # --- 新增：处理 GET 请求的编辑模式 ---
    if request.method == 'GET' and request.args.get('action') == 'edit':
        rule_type = request.args.get('type')
        key_to_edit = request.args.get('key')
        target_dict_name = rule_map.get(rule_type)
        if target_dict_name and key_to_edit in rules_data[target_dict_name]:
            edit_data = {
                "type": rule_type,
                "key": key_to_edit,
                "value": rules_data[target_dict_name][key_to_edit]
            }

    if request.method == 'POST':
        action = request.form.get('action')
        rule_type = request.form.get('rule_type', '').strip()
        key = request.form.get('key', '').strip()
        target_dict_name = rule_map.get(rule_type)

        if action == 'create':
            value = request.form.get('value', '').strip()
            if target_dict_name and key and value:
                if key in rules_data[target_dict_name]:
                    flash(f"创建失败：关键字 '{key}' 在该规则类型中已存在。", 'error')
                else:
                    rules_data[target_dict_name][key] = value
                    save_rules(rules_data)
                    flash('规则添加成功。', 'success')
            else:
                flash('创建失败：键和值都不能为空。', 'error')

        # --- 新增：处理 POST 请求的编辑逻辑 ---
        elif action == 'edit':
            original_key = request.form.get('original_key')
            new_key = key
            new_value = request.form.get('value', '').strip()
            if not all([target_dict_name, original_key, new_key, new_value]):
                flash('更新失败：所有字段均为必填。', 'error')
            elif new_key != original_key and new_key in rules_data[target_dict_name]:
                flash(f"更新失败：新的关键字 '{new_key}' 已被占用。", 'error')
            elif original_key not in rules_data[target_dict_name]:
                flash(f"更新失败：找不到原始规则关键字 '{original_key}'。", 'error')
            else:
                del rules_data[target_dict_name][original_key]
                rules_data[target_dict_name][new_key] = new_value
                save_rules(rules_data)
                flash(f"规则 '{original_key}' 已成功更新。", 'success')

        elif action == 'delete':
            if target_dict_name and key in rules_data[target_dict_name]:
                del rules_data[target_dict_name][key]
                save_rules(rules_data)
                flash('规则删除成功。', 'success')

        return redirect(url_for('management.rules'))

    ou_options = get_ou_list()
    position_options = load_positions().keys()
    group_options = get_group_list()

    return render_template('rules.html',
                           rules=rules_data,
                           config=CONFIG,
                           ou_options=ou_options,
                           position_options=position_options,
                           group_options=group_options,
                           edit_data=edit_data)  # 将待编辑数据传给模板