from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf import CSRFProtect
from flask_session import Session
from config import config_dict
from flask_script import Manager

app = Flask(__name__)

# 6.1 调用收取的配置文件中的类
config_name = config_dict["development"]
app.config.from_object(config_name)

# 1.2 创建数据库对象
db = SQLAlchemy(app)

# 2.2 创建redis实例对象及配置
redis_store = StrictRedis(host=config_dict["development"].HOST, port=config_dict["development"].POST, db=config_dict["development"].NUM)

# 3 开启flask后端csrf保护机制
csrf = CSRFProtect(app)

# 4 借助第三方Session类区调整flask中session的存储位置
Session(app)

# 7 创建manager管理类
manager = Manager(app)

@app.route('/')
def index():
    session["name"] = "Curry"

    return 'hello'

if __name__ == '__main__':
    manager.run()
