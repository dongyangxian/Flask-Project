from info.module.profile import profile_bp
from flask import render_template

@profile_bp.route('/base_info')
def user_info():
    return render_template('news/user.html')
