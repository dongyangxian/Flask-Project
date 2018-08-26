from info.module.passport import passport_bp
from flask import request, abort, make_response, jsonify, current_app
from info.utlis.captcha.captcha import captcha
from info import redis_store
from info import constants
from info.utlis.response_code import RET
import re
from info.models import User
import random
from info.lib.yuntongxun.sms import CCP

# 127.0.0.1:5000/passport/image_code
@passport_bp.route("/image_code")
def send_mes():
    # 1. 获取前端发送的编码
    imageCodeId = request.args.get("imageCodeId")
    # 2. 校验编码是否为空.为空就报错
    if not imageCodeId:
        abort(404)
    # 3. 逻辑处理
    # 使用第三方库来处理验证码的生成
    name, text, image = captcha.generate_captcha()

    # 然后使用redis存储编号，验证码及过期时长的信息
    try:
        redis_store.set("imageCode_%s" % imageCodeId, text, ex=constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        abort(505)

    # 4. 返回图片
    # 使用make_response来返回一个图片对象，还可以设置返回值的一些http的一些属性
    response = make_response(image)
    response.headers["Content-Type"] = "image/jpeg"
    return response

# 127.0.0.1:5000/passport/sms_code
@passport_bp.route("/sms_code", methods=["POST"])
def send_sms():
    # 1. 获取数据
    param_dict = request.json
    mobile = param_dict.get("mobile")
    imagecode = param_dict.get("imageCode")
    imagecodeId = param_dict.get("imageCodeId")

    # 2. 数据判断
    # 2.1 判断值是否都已经输入了
    if not all([mobile, imagecode, imagecodeId]):
        return jsonify(erron=RET.PARAMERR, errmes="参数不足")
    # 2.2 验证手机号码格式
    if not re.match("^1[356789][0-9]{9}$", mobile):
        return jsonify(erron=RET.PARAMERR, errmes="手机格式有误")

    # 3. 逻辑处理

    try:
        # 3.1 根据image_code_id编号去redis中获取验证码的真实值
        # 注意一定要在redis创建的时候设置这个decode_responses=True属性
        real_image_code = redis_store.get("imageCode_%s" % imagecodeId)  # (上一个方法中设置了值的加密格式)
        # 3.2 如果值存在就把它删除
        if real_image_code:
            redis_store.delete(real_image_code)
    except Exception as e:
        current_app.logger.error(e)

    # 3.3 如果不存在，说明验证码已过期
    if not real_image_code:
        return jsonify(erron=RET.NODATA, errmes="验证码已过期")
    # 3.4 根据取出的验证码值与输入的进行比较.如果失败，报错。
    if imagecode.lower() != real_image_code.lower():
        return jsonify(erron=RET.DATAERR, errmes="验证码填写错误")

    try:
        # 3.5 比较成功，进行用户查询是否已经存在
        user = User.query.filter_by(mobile=mobile).first()
        # 3.6 如用户存在，报错。
        if user:
            return jsonify(erron=RET.DATAEXIST, errmes="用户已存在")
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")

    # 3.7 用户不存在，就准备调用第三方接口，生成6为随机数
    sms_code = random.randint(0, 999999)
    sms_code = "%06d" % sms_code

    # 3.8 使用云通讯的发送短信接口进行发送
    result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES/5/60], 1)

    # 3.9 判断是否发送成功
    if result:
        return jsonify(erron=RET.THIRDERR, errmes="短信验证码发送失败")

    # 3.10 如果发送成功，就使用redis保存
    try:
        redis_store.set("sms_%s" % mobile, sms_code, ex=constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码到数据库异常")

    # 4. 返回结果
    return jsonify(erron=RET.OK, errmes="短信验证码发送成功")
