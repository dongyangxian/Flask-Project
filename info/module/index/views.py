from flask import session, current_app, render_template
import logging

from info.models import User
from . import index_bp
from info import redis_store, models

# 使用蓝图对象
@index_bp.route('/')
def index():

    # 1. 获取session中保存的用户信息
    user_id = session.get("user_id")
    # 2. 根据获取到的id去数据库查询用户的信息
    user = None  # type:  User
    if user_id:
        user = User.query.get(user_id)

    # 3. 将模型信息转化为字典信息
    data = {
        "user_info": user.to_dict() if user else None
    }
    # 4. 渲染

    return render_template("index.html", data=data)

@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file("news/favicon.ico")
