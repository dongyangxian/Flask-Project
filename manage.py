from flask import session
from flask_script import Manager
from info import create_app

app = create_app("development")

# 7 创建manager管理类
manager = Manager(app)

@app.route('/')
def index():
    session["name"] = "Curry"

    return 'hello'

if __name__ == '__main__':
    manager.run()
