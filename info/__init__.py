from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf import CSRFProtect
from flask_session import Session
from config import config_dict

def create_app(config_name):
    app = Flask(__name__)

    # 6.1 调用收取的配置文件中的类
    config_class = config_dict[config_name]
    app.config.from_object(config_class)

    # 1.2 创建数据库对象
    db = SQLAlchemy(app)

    # 2.2 创建redis实例对象及配置
    redis_store = StrictRedis(host=config_dict[config_name].HOST, port=config_dict[config_name].POST,
                              db=config_dict[config_name].NUM)

    # 3 开启flask后端csrf保护机制
    csrf = CSRFProtect(app)

    # 4 借助第三方Session类区调整flask中session的存储位置
    Session(app)

    return app
