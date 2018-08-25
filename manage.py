import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf import CSRFProtect
from flask_session import Session

app = Flask(__name__)

class Config(object):
    DEBUG = True

    # 1. mysql数据库配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:5000/information"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # 2. redis数据库配置
    HOST = "127.0.0.1"
    POST = 6379
    NUM = 1

    # 4 session配置
    SECRET_KEY = "fasdhnfjasf"

    SESSION_TYPE = "redis"  # 指定 session 保存到 redis 中
    SESSION_USE_SIGNER = True  # 让 cookie 中的 session_id 被加密签名处理
    SESSION_REDIS = redis.StrictRedis(host=HOST, port=POST)  # 使用 redis 的实例
    SESSION_PERMANENT = 86400  # session 的有效期，单位是秒


app.config.from_object(Config)

# 1.2 创建数据库对象
db = SQLAlchemy(app)

# 2.2 创建redis实例对象及配置
redis_store = StrictRedis(host=Config.HOST, port=Config.POST, db=Config.NUM)

# 3 开启flask后端csrf保护机制
csrf = CSRFProtect(app)
@app.route('/')
def index():

    return 'hello'

if __name__ == '__main__':
    app.run()