# /blueprints/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from ldap3 import Server, Connection, Tls, ALL
import ssl
from utils import CONFIG

auth_bp = Blueprint('auth', __name__, template_folder='../templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'bind_username' in session: return redirect(url_for('main.dashboard'))

    if current_app.config.get('IS_FIRST_RUN'):
        flash(f"首次运行：已自动创建 'config.json'。请前往'服务器设置'填写配置。", "warning")
        current_app.config['IS_FIRST_RUN'] = False  # 重置标志

    if request.method == 'POST':
        username_input, bind_pass = request.form.get('username'), request.form.get('password')
        if not all([username_input, bind_pass]):
            flash('请填写用户名和密码。', 'error')
            return render_template('login.html', config=CONFIG)

        bind_user = f"{username_input}@{CONFIG['DOMAIN_NAME']}" if '@' not in username_input else username_input
        try:
            tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
            server = Server(CONFIG['DOMAIN_CONTROLLER_IP'], port=636, use_ssl=True, get_info=ALL, tls=tls_config)
            conn = Connection(server, user=bind_user, password=bind_pass, auto_bind=True)
            if conn.bound:
                conn.unbind()
                session.update(bind_username=bind_user, bind_password=bind_pass,
                               display_username=bind_user.split('@')[0])
                return redirect(url_for('main.dashboard'))
            else:
                flash(f"登录失败: {conn.result['description']}", 'error')
        except Exception as e:
            flash(f"连接或认证失败: {e}", 'error')
    return render_template('login.html', config=CONFIG)


@auth_bp.route('/logout')
def logout():
    [session.pop(key, None) for key in ['bind_username', 'bind_password', 'display_username']]
    flash('您已安全退出。', 'success')
    return redirect(url_for('auth.login'))