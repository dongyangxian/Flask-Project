from flask import abort
from flask import current_app, g
from flask import session

from info import constants, db
from info.models import User, News, Category
from info.module.news import news_bp
from flask import render_template
from info.utlis.common import login_user_data

# 127.0.0.1:5000/news/1
@news_bp.route('/<int:news_id>')
@login_user_data
def news_detail(news_id):
    """新闻详情首页"""
    # 调用装饰器函数，获取用户
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

    # -----------新闻详情内容取出----------
    # 1. 根据前端发送的新闻编号，查找对应的新闻数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    if not news:
        abort(404)

    # 2. 浏览量增加及数据库提交操作
    news.clicks += 1
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        abort(404)

    # 3. 将模型信息转化为字典信息
    data = {
        "news": news.to_dict(),
        "user_info": user.to_dict() if user else None,
        "news_info": news_dict_list
    }

    # 4. 渲染
    return render_template("news/detail.html", data=data)
