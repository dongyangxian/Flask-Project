from info.module.news import news_bp
from flask import render_template

# 127.0.0.1:5000/news/1
@news_bp.route('/<int:news_id>')
def news_detail(news_id):
    """新闻详情首页"""
    return render_template("news/detail.html")
