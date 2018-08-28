from flask import current_app
from flask import session

from info import constants
from info.models import User, News, Category
from info.module.news import news_bp
from flask import render_template

# 127.0.0.1:5000/news/1
@news_bp.route('/<int:news_id>')
def news_detail(news_id):
    """新闻详情首页"""
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
    return render_template("news/detail.html", data=data)
