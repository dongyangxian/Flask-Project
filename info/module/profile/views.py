from info.module.profile import profile_bp
from flask import render_template, g, request

from info.utlis.common import login_user_data

@profile_bp.route('/base_info')
@login_user_data
def base_info():
    """获取用户基本资料，修改用户进本资料页面"""
    user = g.user
    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template('news/user_base_info.html', data=data)

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
