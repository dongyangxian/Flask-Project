from flask import session, current_app
from flask_script import Manager
from info import create_app
import logging

app = create_app("development")

# 7 创建manager管理类
manager = Manager(app)

@app.route('/')
def index():
    session["name"] = "Curry"

    logging.debug("debug 日志信息")
    logging.info("info 日志信息")
    logging.warning("warning 日志信息")
    logging.error("error 日志信息")
    logging.critical("critical 日志信息")

    current_app.logger.debug("flask封装的logger日志")

    return 'hello'

if __name__ == '__main__':
    manager.run()
