from flask import session, current_app, render_template
import logging

from info.models import User, News
from . import index_bp
from info import redis_store, models
from info import constants

# 使用蓝图对象
@index_bp.route('/')
def index():

    # 1. 获取session中保存的用户信息
    user_id = session.get("user_id")
    # 2. 根据获取到的id去数据库查询用户的信息
    user = None  # type:  User
    if user_id:
        user = User.query.get(user_id)


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

    # 3. 将模型信息转化为字典信息
    data = {
        "user_info": user.to_dict() if user else None,
        "news_info": news_dict_list
    }
    # 4. 渲染

    return render_template("index.html", data=data)

@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file("news/favicon.ico")
