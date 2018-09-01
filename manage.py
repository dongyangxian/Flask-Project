from flask import current_app
from flask_script import Manager
from info import create_app, db
from flask_migrate import Migrate, MigrateCommand

from info.models import User

app = create_app("development")

# 7 创建manager管理类
manager = Manager(app)

# 创建数据库迁移对象
Migrate(app, db)
# 添加指令到manager对象
manager.add_command("db", MigrateCommand)

# useage: python manage.py createsuperuser -n "admin" -p "123456"
@manager.option("-n", "-name", dest="name")
@manager.option("-p", "-password", dest="password")
def createsuperuser(name, password):
    """创建管理员用户"""
    if not all([name, password]):
        return "参数不足"
    user = User()
    user.is_admin = True
    user.nick_name = name
    user.mobile = name
    user.password = password

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        print("创建管理员失败")

    print("创建管理员用户成功")

if __name__ == '__main__':
    manager.run()
