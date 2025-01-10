from flask import Flask
from config.chat2graph_sqilte_config import Config
from app.models.sqlite_models import db
from app.api import register_blueprints
import os
from app.toolkit.api_tool import make_error_response, BaseException


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 确保 instance 文件夹存在
    instance_path = os.path.join(app.root_path, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图
    register_blueprints(app)

    # 注册全局异常处理器
    @app.errorhandler(BaseException)
    def handle_base_exception(e):
        return make_error_response(e.status_code, e.message)

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)