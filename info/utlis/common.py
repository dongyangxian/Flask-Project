from flask import session, current_app, g




def do_index_class(index):
    if index == 1:
        return "first"
    elif index == 2:
        return "second"
    elif index == 3:
        return "third"
    else:
        return ""

# 只要调用该装饰器就能获取用户对象数据
def login_user_data(view_func):
    def wrapper(*args, **kwargs):
        # 1. 获取session中保存的用户信息
        user_id = session.get("user_id")
        # 2. 根据获取到的id去数据库查询用户的信息
        user = None  # type:  User
        
        from info.models import User
        try:
            if user_id:
                user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

        # 3.保存用户对象给被装饰的视图函数使用
        g.user = user

        # 在视图函数中使用g对象获取user对象进而使用
        # 只要在本次请求范围内，就能获取g对象的内容
        result = view_func(*args, **kwargs)
        return result
    return wrapper

