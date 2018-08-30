from info.module.profile import profile_bp
from flask import render_template, g

from info.utlis.common import login_user_data

@profile_bp.route('/base_info')
@login_user_data
def user_info():
    user = g.user
    data = {
        "user_info": user.to_dict() if user else None
    }
    return render_template('news/user.html', data=data)
