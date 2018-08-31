from flask import current_app
from flask import session

from info import db
from info.module.profile import profile_bp
from flask import render_template, g, request, jsonify

from info.utlis.common import login_user_data
from info.utlis.response_code import RET
from info.utlis.image_store import qiniu_image_store
from info import constants

@profile_bp.route('/pic_info', methods=["POST", "GET"])
@login_user_data
def pic_info():
    """展示用户头像及修改头像接口"""
    user = g.user

    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else []
        }
        return render_template('news/user_pic_info.html',data=data)

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
