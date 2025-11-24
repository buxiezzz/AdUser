# /run.py
import os
from flask import Flask, redirect, url_for, session
from utils import load_config
from blueprints.auth import auth_bp
from blueprints.main import main_bp
from blueprints.management import management_bp

# 加载配置并检查是否是首次运行
CONFIG, IS_FIRST_RUN = load_config()

# 创建 Flask 应用实例，并指定 static 文件夹
app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)
app.config['IS_FIRST_RUN'] = IS_FIRST_RUN

# 注册蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(management_bp)

# 添加根路径重定向，以处理初始访问
@app.route('/')
def initial_redirect():
    if 'bind_username' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    # 使用 host='0.0.0.0' 使其可被局域网内其他设备访问
    print("Flask App is running. Access it via http://127.0.0.1:5001/")
    app.run(host='0.0.0.0', port=5001, debug=True)