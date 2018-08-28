from logging.handlers import RotatingFileHandler

from flask import Flask
from flask.ext.wtf.csrf import generate_csrf
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf import CSRFProtect
from flask_session import Session
from config import config_dict
import logging

def create_log(config_name):
    """记录日志信息"""
    # 设置日志的记录等级
    # config_dict[config_name].LOG_LEVEL 获取配置类中对象日志的级别
    logging.basicConfig(level=config_dict[config_name].LOG_LEVEL)  # 调试debug级

    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)

    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')

    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)

    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)

# 将数据库对象升级为全局
# 1.2 创建数据库对象  如果app对象为空，就什么也不做，后期用的时候我们调用 init_app方法
db = SQLAlchemy()

redis_store = None  # type: StrictRedis

def create_app(config_name):
    app = Flask(__name__)

    # 补充日志功能
    create_log(config_name)

    # 6.1 调用收取的配置文件中的类
    config_class = config_dict[config_name]
    app.config.from_object(config_class)

    # 1.2 创建数据库对象
    # db = SQLAlchemy(app)
    # 懒加载，延迟加载。用的时候在加载
    db.init_app(app)

    # 2.2 创建redis实例对象及配置
    global redis_store
    redis_store = StrictRedis(host=config_dict[config_name].HOST, port=config_dict[config_name].POST,
                              db=config_dict[config_name].NUM, decode_responses=True)

    # 3 开启flask后端csrf保护机制
    csrf = CSRFProtect(app)

    # 4 借助第三方Session类区调整flask中session的存储位置
    Session(app)

    # 完善CSRF_Token保护机制
    @app.after_request
    def after_request(response):
        # 1. 生成csrf_token值
        csrf_token = generate_csrf()
        # 2. 将值传送给前端浏览器.借助response对象设置到cookie中
        response.set_cookie("csrf_token", csrf_token)

        # 3. 返回值
        return response

    # 注册蓝图对象
    # 为了解决循环导入，使用蓝图时在导入
    from info.module.index import index_bp
    app.register_blueprint(index_bp)

    from info.module.passport import passport_bp
    app.register_blueprint(passport_bp)

    return app
