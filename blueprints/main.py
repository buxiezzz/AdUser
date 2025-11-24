# /blueprints/main.py
import csv
import io
import ssl
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, current_app, \
    send_from_directory
from ldap3 import Server, Connection, Tls, ALL
from utils import login_required, simplify_dn, load_positions, CONFIG
from ad_utils import create_ad_user, get_ou_list, get_group_list, get_base_dn

main_bp = Blueprint('main', __name__, template_folder='../templates')


@main_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    result_message, result_type = None, None
    if request.method == 'POST':
        ou_path = request.form.get('ou_path', '').strip()
        new_username = request.form.get('new_username', '').strip()
        new_display_name = request.form.get('new_display_name', '').strip()

        if not all([ou_path, new_username, new_display_name]):
            result_message, result_type = "所有必填字段都必须填写。", 'error'
        else:
            success, message = create_ad_user(
                domain_controller_ip=CONFIG['DOMAIN_CONTROLLER_IP'],
                bind_username=session['bind_username'], bind_password=session['bind_password'],
                username=new_username, display_name=new_display_name,
                password=CONFIG['DEFAULT_USER_PASSWORD'], ou_path=ou_path, domain_name=CONFIG['DOMAIN_NAME'],
                position_name=request.form.get('position_name'), groups_to_add=request.form.getlist('groups')
            )
            result_message, result_type = message, 'success' if success else 'error'

    base_dn = get_base_dn(CONFIG['DOMAIN_NAME'])
    ou_options_raw = get_ou_list()
    ou_options_display = [{'dn': dn, 'name': simplify_dn(dn, base_dn)} for dn in ou_options_raw]
    group_options = get_group_list()

    return render_template('dashboard.html', config=CONFIG, result_message=result_message, result_type=result_type,
                           ou_options=ou_options_display, group_options=group_options, positions=load_positions())


@main_bp.route('/batch_create', methods=['POST'])
@login_required
def batch_create():
    if 'user_file' not in request.files:
        flash('未找到上传的文件部分。', 'error')
        return redirect(url_for('main.dashboard'))

    file = request.files['user_file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        flash('请选择一个有效的 .csv 文件。', 'error')
        return redirect(url_for('main.dashboard'))

    batch_results = []
    conn = None
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
        server = Server(CONFIG['DOMAIN_CONTROLLER_IP'], port=636, use_ssl=True, get_info=ALL, tls=tls_config)
        conn = Connection(server, user=session['bind_username'], password=session['bind_password'], auto_bind=True)

        if not conn.bound:
            flash(f"LDAP 连接失败: {conn.result}", 'error')
            return redirect(url_for('main.dashboard'))

        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        csv_reader = csv.reader(stream)

        next(csv_reader, None)

        for i, row in enumerate(csv_reader, 2):
            try:
                if len(row) < 3:
                    batch_results.append(f"第 {i} 行: 格式错误，至少需要 姓名,登录名,OU路径 三列。")
                    continue

                display_name, username, ou_path = row[0].strip(), row[1].strip(), row[2].strip()
                position_name = row[3].strip() if len(row) > 3 and row[3] else None

                if not all([display_name, username, ou_path]):
                    batch_results.append(f"第 {i} 行 ({display_name}): 跳过，姓名、登录名或 OU 路径为空。")
                    continue

                positions_data = load_positions()
                groups_to_add = positions_data.get(position_name, [])

                success, message = create_ad_user(
                    domain_controller_ip=CONFIG['DOMAIN_CONTROLLER_IP'],
                    bind_username=session['bind_username'], bind_password=session['bind_password'],
                    username=username, display_name=display_name,
                    password=CONFIG['DEFAULT_USER_PASSWORD'], ou_path=ou_path, domain_name=CONFIG['DOMAIN_NAME'],
                    position_name=position_name, groups_to_add=groups_to_add,
                    conn_external=conn
                )

                result_prefix = "✅ 成功" if success else "❌ 失败"
                batch_results.append(f"第 {i} 行 [{display_name}]: {result_prefix} - {message}")

            except Exception as e:
                batch_results.append(f"第 {i} 行: 处理时发生意外错误 - {e}")

    except Exception as e:
        flash(f'处理文件时出错: {e}', 'error')
    finally:
        if conn and conn.bound:
            conn.unbind()

    base_dn = get_base_dn(CONFIG['DOMAIN_NAME'])
    ou_options_raw = get_ou_list()
    ou_options_display = [{'dn': dn, 'name': simplify_dn(dn, base_dn)} for dn in ou_options_raw]
    group_options = get_group_list()

    return render_template('dashboard.html', config=CONFIG, batch_results=batch_results,
                           ou_options=ou_options_display, group_options=group_options, positions=load_positions())


@main_bp.route('/download_template')
@login_required
def download_template():
    try:
        return send_from_directory(
            directory=current_app.static_folder,
            path='template.csv',
            as_attachment=True,
            download_name='批量创建用户模板.csv'
        )
    except FileNotFoundError:
        flash("模板文件 'template.csv' 未在 'static' 文件夹中找到。", 'error')
        return redirect(url_for('main.dashboard'))