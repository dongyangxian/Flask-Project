from flask import current_app
from flask import g
from flask import session, redirect, url_for

from info.models import User
from info.module.admin import admin_bp
from flask import render_template, request
from info.utlis.common import login_user_data

@admin_bp.route('/index')
@login_user_data
def admin_index():
    return render_template("admin/index.html")

@admin_bp.route('/login', methods=["POST", "GET"])
@login_user_data
def login():
    if request.method == "GET":
        return render_template("admin/login.html")

    # 1. 获取参数
    params_dict = request.form
    username = params_dict.get("username")
    password = params_dict.get("password")
    # 2. 校验参数
    # 2.1 非空判断
    if not all([username, password]):
        return render_template("admin/login.html", errmsg="参数不足")
    # 3. 逻辑处理
    # 3.1 查询用户是否存在
    try:
        user = User.query.filter(User.mobile == username, User.is_admin == True).first()
        if not user:
            return render_template("admin/login.html", errmsg="该管理员不存在")
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/login.html", errmsg="查询管理员失败")

    # 3.2 判断密码是否正确
    if not user.check_passowrd(password):
        return render_template("admin/login.html", errmsg="密码错误")

    # 3.3 判断完成，使用session保存信息
    session["user_id"] = user.id
    session["is_admin"] = True
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    # 4. 返回值
    return redirect(url_for("admin.admin_index"))
