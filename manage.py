
from flask_script import Manager
from info import create_app


app = create_app("development")

# 7 创建manager管理类
manager = Manager(app)

if __name__ == '__main__':
    manager.run()
