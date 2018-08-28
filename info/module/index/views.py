from flask import session, current_app, render_template, request, jsonify, g
import logging

from info.models import User, News, Category
from info.utlis.response_code import RET
from . import index_bp
from info import redis_store, models
from info import constants
from info.utlis.common import login_user_data

# 127.0.0.1:5000/news_list
@index_bp.route('/news_list')
def get_news_list():
    """首页新闻分类排行显示"""
    # 1. 获取参数
    cid = request.args.get("cid")
    page = request.args.get("cur_page", 1)
    per_page = request.args.get("total_page", constants.HOME_PAGE_MAX_NEWS)

    # 2. 参数校验
    # 2.1 非空判断
    if not all([cid, page, per_page]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    # 2.2 数据类型判断
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="数据类型错误")

    # 3. 逻辑处理
    # 3.1 根据分类id查询数据，以时间降序，分页处理

    filters = []
    if cid != 1:
        filters.append(News.category_id == cid)

    try:
        paginate = News.query.filter(*filters).\
            order_by(News.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询首页新闻列表数据异常")

    # 3.2 获取当前页码，当前页码的所有数据，总页数
    current_page = paginate.page
    items = paginate.items
    total_page = paginate.pages

    # 3.3 将模型对象转化为字典对象
    news_dict_list = []

    for news in items if items else []:
        news_dict_list.append(news.to_dict())

    # 3.4 组织响应数据
    data = {
        "newsList": news_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }

    # 4. 返回值
    return jsonify(errno=RET.OK, errmsg="查询新闻列表数据成功", data=data)

# 使用蓝图对象
@index_bp.route('/')
@login_user_data
def index():
    # 获取用户
    user = g.user

    # -----------新闻点击排行----------
    # 1. 查询出新闻的排序及限制模型列表
    try:
        news_model_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
    # 2. 将模型列表转化为字典列表
    news_dict_list = []

    for news in news_model_list if news_model_list else []:
        news_dict_list.append(news.to_dict())

    # -----------新闻列表分类----------
    # 1. 取出所有分类数据
    try:
        categgories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)

    # 2. 模型列表转化为字典列表
    categgory_dict_list = []
    for category in categgories if categgories else []:
        categgory_dict_list.append(category.to_dict())

    # 3. 将模型信息转化为字典信息
    data = {
        "category_dict_list": categgory_dict_list,
        "user_info": user.to_dict() if user else None,
        "news_info": news_dict_list
    }
    # 4. 渲染

    return render_template("index.html", data=data)

@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file("news/favicon.ico")
