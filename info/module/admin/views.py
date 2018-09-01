import time
from datetime import datetime, timedelta

from flask import current_app
from flask import g
from flask import session, redirect, url_for

from info.models import User
from info.module.admin import admin_bp
from flask import render_template, request
from info.utlis.common import login_user_data

@admin_bp.route('/user_count')
@login_user_data
def user_count():
    """展示用户统计页面"""
    # 查询总人数
    total_count = 0
    try:
        # 10001
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
    # 查询月新增数
    mon_count = 0

    try:
        # 2018-8-31号
        now = time.localtime()
        # 2018-08-01月初  2018-09-01
        mon_begin = '%d-%02d-01' % (now.tm_year, now.tm_mon)
        # 使用strptime将字符串转成时间date格式 '%Y-%m-%d'
        mon_begin_date = datetime.strptime(mon_begin, '%Y-%m-%d')
        # 用户的创建时间 > 每一个月的第一天 -->每一个月的新增人数
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询日新增数
    day_count = 0

    try:
        # 2018-08-31-0:0
        day_begin = '%d-%02d-%02d' % (now.tm_year, now.tm_mon, now.tm_mday)
        day_begin_date = datetime.strptime(day_begin, '%Y-%m-%d')
        # 当前时间 > 2018-08-31-0:0(一天的开始时间)
        day_count = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询图表信息
    # 获取到当天00:00:00时间
    # 2018-08-31
    now_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    # 定义空数组，保存数据
    active_date = []
    active_count = []

    # 依次添加数据，再反转
    for i in range(0, 31):
        # 2018-08-31 - 1  =  2018-08-30:0:0
        # 2018-08-31 - 2  =  2018-08-29:0:0
        begin_date = now_date - timedelta(days=i)
        # now_date - timedelta(days=(i))  + timedelta(days=(1))
        # begin_date + timedelta(days=(1))
        # 2018-08-30:24:00
        # 2018-08-29:24:00
        end_date = begin_date + timedelta(days=1)
        # 记录这个月的每一天  30 29 ....01
        # strftime将date格式转换成字符串
        active_date.append(begin_date.strftime('%Y-%m-%d'))
        count = 0

        try:
            count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                      User.last_login < end_date).count()
        except Exception as e:
            current_app.logger.error(e)
        # 记录一个月的每天的用户活跃数
        active_count.append(count)
    # 日期反转
    active_date.reverse()
    # 数据反转
    active_count.reverse()
    data = {"total_count": total_count, "mon_count": mon_count, "day_count": day_count, "active_date": active_date,
            "active_count": active_count}
    return render_template('admin/user_count.html', data=data)

@admin_bp.route('/index')
@login_user_data
def admin_index():
    user = g.user
    data = {
        "user_info": user.to_dict() if user else []
    }
    return render_template("admin/index.html", data=data)

@admin_bp.route('/login', methods=["POST", "GET"])
@login_user_data
def login():
    if request.method == "GET":
        # 从session中获取管理员的信息
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", None)
        if user_id and is_admin:
            return redirect(url_for("admin.admin_index"))
        # if not is_admin:
        #     return redirect(url_for("index.index"))
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
