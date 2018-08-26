from flask import session, current_app, render_template
import logging
from . import index_bp
from info import redis_store, models

# 使用蓝图对象
@index_bp.route('/')
def index():
    session["name"] = "Curry"

    redis_store.set("name", "laowang")

    logging.debug("debug 日志信息")
    logging.info("info 日志信息")
    logging.warning("warning 日志信息")
    logging.error("error 日志信息")
    logging.critical("critical 日志信息")

    current_app.logger.debug("flask封装的logger日志")

    return render_template("index.html")

@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file("news/favicon.ico")
