from flask import abort, jsonify
from flask import current_app, g, request
from flask import session

from info import constants, db
from info.models import User, News, Category, Comment, CommentLike
from info.module.news import news_bp
from flask import render_template
from info.utlis.common import login_user_data
from info.utlis.response_code import RET

# 127.0.0.1:5000/news/comment_like
@news_bp.route('/comment_like', methods=["POST"])
@login_user_data
def comment_like():
    # 1. 获取参数
    params_dict = request.json
    news_id = params_dict.get("news_id")
    comment_id = params_dict.get("comment_id")
    action = params_dict.get("action")
    user = g.user

    # 2. 参数校验
    #  2.1 非空判断
    if not all([news_id, comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    # 2.2 用户判断
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 2.3 点击行为判断
    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="action数据填写错误")

    # 3. 逻辑处理
    # 3.1 根据评论的id获取评论模型对象（只有评论存在的时候才能去点赞和取消）
    try:
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify(errno=RET.NODATA, errmsg="评论不存在")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询评论数据异常")

    # 3.2 根据行为去判断点赞或者取消点赞
    if action == "add":
        # 根据用户id和评论的id来查询CommentLike是否存在。不存在才能点赞
        comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                CommentLike.user_id == user.id
                                                ).first()
        if not comment_like:
            # 如果不存在，就新建一个点赞的评论模型到数据库保存
            comment_like1 = CommentLike()
            comment_like1.user_id = user.id
            comment_like1.comment_id = comment_id
            db.session.add(comment_like1)

            # 点赞的数量加1
            comment.like_count += 1
    else:
        # 根据用户id和评论的id来查询CommentLike是否存在。不存在才能点赞
        comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                CommentLike.user_id == user.id
                                                ).first()
        # CommentLike存在时，才能取消点赞
        if comment_like:
            db.session.delete(comment_like)

            # 点赞的数量减1
            comment.like_count -= 1
    # 3.3 将修改的评论模型对象保存到数据库中
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据异常")

    # 4. 返回值
    return jsonify(errno=RET.OK, errmsg="OK")

# 127.0.0.1:5000/news/news_comment
@news_bp.route('/news_comment', methods=["POST"])
@login_user_data
def news_comment():
    # 1. 获取参数
    params_dict = request.json
    news_id = params_dict.get("news_id")
    comment = params_dict.get("comment")
    parent_id = params_dict.get("parent_id")  # 如果前端没有传，表示当前是评论新闻，不是评论别人
    user = g.user
    # 2. 校验参数
    # 2.1 非空判断
    if not all([news_id, comment]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    # 2.2 用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 3. 逻辑处理
    # 3.1 获取要评论的新闻，判断是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻不存在")

    # 3.2 创建评论模型
    comment_model = Comment()
    comment_model.user_id = user.id
    comment_model.news_id = news_id
    comment_model.content = comment

    # 3.3 判断parent_id是否有值
    if parent_id:
        comment_model.parent_id = parent_id

    # 3.4 将模型对象保存到数据库
    try:
        db.session.add(comment_model)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存评论对象到数据库异常")

    # 4. 返回值
    return jsonify(errno=RET.OK, errmsg="评论成功", data=comment_model.to_dict())

# 127.0.0.1:5000/news/news_collect
@news_bp.route('/news_collect', methods=["POST"])
@login_user_data
def news_collect():
    # 1. 获取参数
    params_dict = request.json
    news_id = params_dict.get("news_id")
    action = params_dict.get("action")
    user = g.user
    # 2. 校验参数
    # 2.1 非空判断
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    # 2.2 判断用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 2.3 判断前端传送过来的行为是取消还是收藏[collect, cancel_collect]
    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数填写错误")

    # 3. 逻辑处理
    # 3.1 由新闻的id获取该新闻
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻数据异常")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻不存在")
    # 3.2 根据action来判断是取消还是收藏
    if action == "collect":
        # 3.3 如果是取消就从用户的新闻中移除
        user.collection_news.append(news)
    else:
        # 3.4 如果是收藏就添加进去
        user.collection_news.remove(news)
    # 3.5 保存数据到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="提交数据到数据库异常")

    # 4. 返回值
    return jsonify(errno=RET.OK, errmsg="OK")

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

    # -----------查询用户是否收藏过该新闻----------
    # 1. 使用id_collected 来判断
    # True：用户收藏过   False：未收藏
    is_collected = False

    # False 当前登录用户未关注该新闻的作者 反之
    is_followed = False

    # 2. 如果用户在登录的情况下,查询该用户是否收藏过
    if user:
        if news in user.collection_news:
            is_collected = True

    # user 当前登录用户 ； news.user 新闻的作者
    # 如果当前作者在用户的偶像列表中，表示关注了
    if user and news.user:
        if user in news.user.followers:
            is_followed = True

    # -----------评论列表数据展现----------
    # 1. 在评论列表查询所有的评论
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    # # 2. 将模型列表转换为字典列表
    # comment_dict_list = []
    # for comment in comments if comments else []:
    #     comment_dict_list.append(comment.to_dict())

    # -----------查询该用户对这个新闻的哪些评论点过赞----------
    commentlike_id_list = []
    if user:
        # 1. 根据新闻id获取所属的所有评论id  —>  list[1,2,3,4,5,6]
        comment_id_list = [comment.id for comment in comments]
        # 2. 使用点赞评论模型去查询所有点过赞的评论
        commentlike_model_list = CommentLike.query.filter(CommentLike.comment_id.in_(comment_id_list),
                                                      CommentLike.user_id == user.id
                                                      )
        # 3. 根据查到的评论模型列表获取点过赞的评论id
        commentlike_id_list = [commentlike.comment_id for commentlike in commentlike_model_list]

    # 2. 将模型列表转换为字典列表
    comment_dict_list = []
    for comment in comments if comments else []:
        comment_dict = comment.to_dict()

        # 4. 评论点赞的标志位
        comment_dict["is_like"] = False

        # 5. 如果当前评论的id与点赞的id一致，就让它显示
        if comment.id in commentlike_id_list:
            comment_dict["is_like"] = True

        comment_dict_list.append(comment_dict)

    # 3. 将模型信息转化为字典信息
    data = {
        "comments": comment_dict_list,
        "is_collected": is_collected,
        "news": news.to_dict(),
        "user_info": user.to_dict() if user else None,
        "news_info": news_dict_list,
        "is_followed": is_followed
    }

    # 4. 渲染
    return render_template("news/detail.html", data=data)
