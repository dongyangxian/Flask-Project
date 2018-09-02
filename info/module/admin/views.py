import time
from datetime import datetime, timedelta

from flask import current_app, jsonify
from flask import g
from flask import session, redirect, url_for

from info import constants, db
from info.models import User, News, Category
from info.module.admin import admin_bp
from flask import render_template, request
from info.utlis.common import login_user_data
from info.utlis.image_store import qiniu_image_store
from info.utlis.response_code import RET

@admin_bp.route('/news_edit_detail', methods=["POST", "GET"])
def news_edit_detail():
    """新闻编辑修改接口"""
    if request.method == "GET":
        # 1. 获取参数
        news_id = request.args.get("news_id")
        # 2. 根据新闻的id去查询新闻的内容
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
        # 3. 转换为字典列表
        news_dict = news.to_dict() if news else None

        # 查询所有分类
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
        # 移除最新分类
        categories.pop(0)
        category_dict_list = []
        for category in categories if categories else []:
            # 分类对象转换成字典
            category_dict = category.to_dict()

            # 添加is_selected=False不选择
            category_dict["is_selected"] = False
            # is_selected=True选择中category对应的分类
            if news.category_id == category.id:
                    category_dict["is_selected"] = True
            category_dict_list.append(category_dict)

        # 4. 返回值
        data = {
            "news": news_dict,
            "categories": category_dict_list
        }
        return render_template("admin/news_edit_detail.html", data=data)

    # 1. 获取参数
    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")
    # 2. 校验
    if not all([title, digest, content, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    news = None  # type:News
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")
    # 3. 逻辑处理
    # 3.1 如果有图片，就上传
    if index_image:
        index_image_data = index_image.read()
        try:
            image_name = qiniu_image_store(index_image_data)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg="主图片保存到七牛云失败")
        # 有修改图片才保存
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
    # 3.2 修改新闻对象
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.content = content

    # 3.3 提交数据
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="修改新闻对象失败")
    # 4. 返回值
    return jsonify(errno=RET.OK, errmsg="新闻编辑成功")

@admin_bp.route('/news_edit')
@login_user_data
def news_edit():
    """新闻编辑页面展示"""
    """新闻审核页面展示"""
    # 1.获取参数
    p = request.args.get("p", 1)
    keywords = request.args.get("keywords")

    # 2.参数校验
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    # 3.逻辑处理
    news_list = []
    current_page = 1
    total_page = 1
    # 3.1 查询审核未通过的&未审核的新闻条件
    filter = []

    # 3.2 判断是否有关键字
    if keywords:
        filter.append(News.title.contains(keywords))

    # 3.3 查询数据库
    try:
        paginate = News.query.filter(*filter).order_by(News.create_time.desc()).paginate(p,constants.ADMIN_NEWS_PAGE_MAX_COUNT,False)
        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    # 3.4 转换为字典列表
    news_dict_list = []
    for news in news_list if news_list else []:
        news_dict_list.append(news.to_review_dict())

    data = {
        "news_list": news_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }
    # 4. 返回值
    return render_template("admin/news_edit.html", data=data)
# /admin/news_review_detail?news_id=1
@admin_bp.route('/news_review_detail', methods=['POST', 'GET'])
@login_user_data
def news_review_detail():
    """新闻审核的详情页面"""
    if request.method == "GET":
        # 1. 获取参数
        news_id = request.args.get("news_id")
        # 2. 根据新闻的id去查询新闻的内容
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
        # 3. 转换为字典列表
        news_dict = news.to_dict() if news else None
        # 4. 返回值
        data = {
            "news": news_dict
        }
        return render_template("admin/news_review_detail.html", data=data)

    # 1. 获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")
    # 2. 校验
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    if action not in ["accept", "reject"]:
        return jsonify(errno=RET.PARAMERR, errmsg="action参数有误")
    # 3. 逻辑处理
    news = None
    # 3.1 判断新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻为空")

    # 3.2 根据点击行为去判断是通过还是拒绝
    if action == "accept":
        news.status = 0
    else:
        reason = request.json.get("reason")
        if reason:
            news.status = -1
            news.reason = reason
        else:
            return jsonify(errno=RET.PARAMERR, errmsg="请填写拒绝原因")

    # 3.3 提交数据
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存新闻状态异常")
    # 4. 返回值
    return jsonify(errno=RET.OK, errmsg="OK")

# 第一次请求： /admin/news_review
# 后面分页请求： /admin/news_review?p=1
@admin_bp.route('/user_review')
@login_user_data
def user_review():
    """新闻审核页面展示"""
    # 1.获取参数
    p = request.args.get("p", 1)
    keywords = request.args.get("keywords")
    user = g.user
    # 2.参数校验
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    # 3.逻辑处理
    news_list = []
    current_page = 1
    total_page = 1
    # 3.1 查询审核未通过的&未审核的新闻条件
    filter = [News.status != 0]

    # 3.2 判断是否有关键字
    if keywords:
        filter.append(News.title.contains(keywords))

    # 3.3 查询数据库
    try:
        paginate = News.query.filter(*filter).order_by(News.create_time.desc()).paginate(p, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    # 3.4 转换为字典列表
    news_dict_list = []
    for news in news_list if news_list else []:
        news_dict_list.append(news.to_review_dict())

    data = {
        "news_list": news_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }
    # 4. 返回值
    return render_template("admin/news_review.html", data=data)

@admin_bp.route('/user_list')
@login_user_data
def user_list():
    """用户列表展示"""
    # 1. 获取页码参数
    p = request.args.get("p")
    user = g.user
    # 2. 校验页码，如果不正确，赋值为1
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    user_list = []
    current_page = 1
    total_page = 1
    if user:
        # 3. 逻辑处理
        try:
            paginates = User.query.filter(User.is_admin == False).paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
            # 3.1 获取相关数据
            user_list = paginates.items
            current_page = paginates.page
            total_page = paginates.pages
        except Exception as e:
            current_app.logger.error(e)

        # 3.2 转化为字典列表
        user_dict_list = []
        for user in user_list if user_list else []:
            user_dict_list.append(user.to_dict())

        # 4. 返回值
        data = {
            "users": user_dict_list,
            "current_page": current_page,
            "total_page": total_page
        }
        return render_template("admin/user_list.html", data=data)

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
