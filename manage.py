from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

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

app.config.from_object(Config)

# 1.2 创建数据库对象
db = SQLAlchemy(app)

# 2.2 创建redis实例对象及配置
redis_store = StrictRedis(host=Config.HOST, port=Config.POST, db=Config.NUM)

@app.route('/')
def index():
    return 'hello'

if __name__ == '__main__':
    app.run()