from info.module.passport import passport_bp
from flask import request, abort, make_response
from info.utlis.captcha.captcha import captcha
from info import redis_store
from info import constants

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
@passport_bp.route("/sms_code")
def send_sms():
    pass
