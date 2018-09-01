from info.module.admin import admin_bp
from flask import render_template
from info.utlis.common import login_user_data

@admin_bp.route('/login')
@login_user_data
def login():
    return render_template("admin/login.html")
