
from flask_script import Manager
from info import create_app, db
from flask_migrate import Migrate, MigrateCommand

app = create_app("development")

# 7 创建manager管理类
manager = Manager(app)

# 创建数据库迁移对象
Migrate(app, db)
# 添加指令到manager对象
manager.add_command("db", MigrateCommand)

if __name__ == '__main__':
    print(app.url_map)
    manager.run()
