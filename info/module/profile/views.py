from flask import abort
from flask import current_app
from flask import session

from info import db
from info.models import News, Category, User
from info.module.profile import profile_bp
from flask import render_template, g, request, jsonify

from info.utlis.common import login_user_data
from info.utlis.response_code import RET
from info.utlis.image_store import qiniu_image_store
from info import constants

@profile_bp.route('/other_cancel_followed', methods=["POST"])
@login_user_data
def other_cancel_followed():
    """我的关注中取消关注"""
    user = g.user
    # 1. 获取用户
    author_id = request.json.get("user_id")
    action = request.json.get("action")

    #  2.1 非空判断
    if not all([author_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    # 2.2 用户是否登录判断
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    if action not in ["follow", "unfollow"]:
        return jsonify(errno=RET.PARAMERR, errmsg="action参数错误")

    # 2. 获取作者模型
    try:
        author = User.query.get(author_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询作者异常")
    if action == "unfollow":
        if author in user.followed:
            user.followed.remove(author)
        # 3. 提交数据
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="用户保存到数据库异常")

    return jsonify(errno=RET.OK, errmsg="OK")

# 127.0.0.1:5000/profile/other_info?user_id=1
@profile_bp.route('/other_info')
@login_user_data
def other_info():
    """点击我的关注跳转至关注的用户的主页"""
    user = g.user
    # 1. 获取用户
    user_id = request.args.get("user_id")

    if not user_id:
        abort(404)
    # 2. 查询用户模型
    other = None
    try:
        other = User.query.get(user_id)
        if not other:
            abort(404)
    except Exception as e:
        current_app.logger.error(e)

    # 3. 判断当前登录用户是否关注过该用户
    is_followed = False
    if user:
        if other.followers.filter(User.id == user.id).count() > 0:
            is_followed = True
    data = {
        "user_info": user.to_dict(),
        "other_info": other.to_dict(),
        "is_followed": is_followed
    }
    return render_template("news/other.html", data=data)

@profile_bp.route('/user_follow')
@login_user_data
def user_followed_list():
    """当前用户关注列表"""
    # 1. 获取页码参数
    p = request.args.get("p", 1)
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
            paginates = user.followed.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
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
        return render_template("news/user_follow.html", data=data)

@profile_bp.route('/news_list')
@login_user_data
def news_list():
    """展示用户发布的所有新闻列表接口"""
    # 1. 获取页码参数
    p = request.args.get("p")
    user = g.user
    # 2. 校验页码，如果不正确，赋值为1
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    news_list = []
    current_page = 1
    total_page = 1
    if user:
        # 3. 逻辑处理
        try:
            paginates = News.query.filter(News.user_id == user.id).paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
            # 3.1 获取相关数据
            news_list = paginates.items
            current_page = paginates.page
            total_page = paginates.pages
        except Exception as e:
            current_app.logger.error(e)

        # 3.2 转化为字典列表
        news_dict_list = []
        for news in news_list if news_list else []:
            news_dict_list.append(news.to_dict())

        # 4. 返回值
        data = {
            "news": news_dict_list,
            "current_page": current_page,
            "total_page": total_page
        }
        return render_template("news/user_news_list.html", data=data)

@profile_bp.route('/news_release', methods=["POST", "GET"])
@login_user_data
def news_release():
    """展示新闻发布页面，及功能实现接口"""
    if request.method == "GET":
        # 去数据库查询新闻的分类，返回给前端处理
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
        # 转换为字典列表
        category_dict_list = []
        for category in categories if categories else []:
            category_dict_list.append(category.to_dict())

        # 因为第一个分类不是真正的分类信息，所以要删除
        category_dict_list.pop(0)
        # 组织数据
        data = {
            "categories": category_dict_list
        }
        return render_template("news/user_news_release.html", data=data)

    # 1. 获取参数
    params_dict = request.form
    title = params_dict.get("title")
    category_id = params_dict.get("category_id")
    digest = params_dict.get("digest")
    index_image = request.files.get("index_image")
    content = params_dict.get("content")
    source = "个人发布"
    user = g.user
    # 2. 校验参数
    # 2.1 非空判断
    if not all([title, category_id, digest, index_image, content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    # 2.2 用户登录判断
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 3. 逻辑处理
    # 3.1 获取图片数据
    image_data = index_image.read()
    # 3.2 上传图片
    try:
        image_name = qiniu_image_store(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片到七牛云失败")
    # 3.3 创建新闻模型
    news = News()
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
    news.content = content
    news.source = source
    news.user_id = user.id
    # 标记为审核状态
    news.status = 1
    # 3.4 保存到数据库
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存新闻对象到数据库异常")

    # 4. 返回值
    return jsonify(errno=RET.OK, errmsg="新闻发布成功")

@profile_bp.route('/collection')
@login_user_data
def news_collection():
    """展示用户收藏新闻列表接口"""
    # 1. 获取页码参数
    p = request.args.get("p")
    user = g.user
    # 2. 校验页码，如果不正确，赋值为1
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    news_list = []
    current_page = 1
    total_page = 1
    if user:
        # 3. 逻辑处理
        try:
            paginates = user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
            # 3.1 获取相关数据
            news_list = paginates.items
            current_page = paginates.page
            total_page = paginates.pages
        except Exception as e:
            current_app.logger.error(e)

        # 3.2 转化为字典列表
        news_dict_list = []
        for news in news_list if news_list else []:
            news_dict_list.append(news.to_dict())

        # 4. 返回值
        data = {
            "collections": news_dict_list,
            "current_page": current_page,
            "total_page": total_page
        }
        return render_template("news/user_collection.html", data=data)

@profile_bp.route('/pass_info', methods=["POST", "GET"])
@login_user_data
def pass_info():
    """展示修改密码接口"""
    if request.method == "GET":
        return render_template("news/user_pass_info.html")

    # 1. 获取参数
    params_dict = request.json
    old_password = params_dict.get("old_password")
    new_password = params_dict.get("new_password")
    user = g.user
    # 2. 校验参数
    # 2.1 非空判断
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    # 2.2 用户登录判断
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 3. 逻辑处理
    # 3.1 检查旧密码是否正确
    if user.check_passowrd(old_password):
        # 3.2 将新密码赋值
        user.password = new_password
    else:
        return jsonify(errno=RET.PARAMERR, errmsg="旧密码填写错误")

    # 3.2 提交数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户对象异常")
    # 4. 返回值
    return jsonify(errno=RET.OK, errmsg="修改密码成功")

@profile_bp.route('/pic_info', methods=["POST", "GET"])
@login_user_data
def pic_info():
    """展示用户头像及修改头像接口"""
    user = g.user

    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else []
        }
        return render_template('news/user_pic_info.html', data=data)

    # 1. 获取参数
    # POST获取用户上传的图片二进制数据上传到七牛云
    avatar_data = request.files.get("avatar").read()

    # 2. 校验参数
    if not avatar_data:
        return jsonify(errno=RET.NODATA, errmsg="图片数据不能为空")
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 3. 逻辑处理
    # 3.1 调用封装好的方法将图片上传到七牛云
    try:
        image_name = qiniu_image_store(avatar_data)
        print(image_name)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片到七牛云失败")

    # 3.2 只将图片名称存储，防止后期修改七牛云域名
    user.avatar_url = image_name

    # 3.3 提交保存数据
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户url失败")

    # 3.4 组织响应对象
    full_url = constants.QINIU_DOMIN_PREFIX + image_name
    data = {
        "avatar_url": full_url
    }
    # 4. 返回值
    return jsonify(errno=RET.OK, errmsg="上传图片到七牛云成功", data=data)

@profile_bp.route('/base_info', methods=["POST", "GET"])
@login_user_data
def base_info():
    """获取用户基本资料，修改用户进本资料页面"""
    user = g.user
    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template('news/user_base_info.html', data=data)

    # 如果不是get请求，那就是post请求了
    # 1. 获取参数
    params_dict = request.json
    nick_name = params_dict.get("nick_name")
    signature = params_dict.get("signature")
    gender = params_dict.get("gender")
    # 2. 校验参数
    #  2.1 非空判断
    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    # 2.2 用户是否登录判断
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 2.3 判断性别
    if gender not in ["MAN", "WOMAN"]:
        return jsonify(errno=RET.PARAMERR, errmsg="action数据填写错误")
    # 3. 逻辑处理
    # 3.1 用户信息赋值
    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender

    # 3.2 修改session中的昵称
    session["nick_name"] = nick_name

    # 3.3 保存修改的操作到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="修改用户数据异常")
    # 4. 返回值
    return jsonify(errno=RET.OK, errmsg="修改用户数据成功")

# /user/info
@profile_bp.route('/info')
@login_user_data
def user_info():
    """返回用户个人中心页面"""
    user = g.user
    data = {
        "user_info": user.to_dict() if user else None,
    }
    return render_template("news/user.html", data=data)
