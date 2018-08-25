import redis

# 配置信息
class Config(object):
    DEBUG = True

    # 1. mysql数据库配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:5000/information"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # 2. redis数据库配置
    HOST = "127.0.0.1"
    POST = 6379
    NUM = 1

    # 4.1 Session配置
    SECRET_KEY = "fasdhnfjasf"

    SESSION_TYPE = "redis"  # 指定 session 保存到 redis 中
    SESSION_USE_SIGNER = True  # 让 cookie 中的 session_id 被加密签名处理
    SESSION_REDIS = redis.StrictRedis(host=HOST, port=POST)  # 使用 redis 的实例
    SESSION_PERMANENT = 86400  # session 的有效期，单位是秒

# 5 创建两个不同的开发环境类
class DevelopmentConfig(Config):
    """线下模式"""
    DEBUG = True

class ProductConfig(Config):
    """线上模式"""
    DEBUG = False
    # 可修改线上的部署地址
    # SQLALCHEMY_DATABASE_URI = "mysql://登录名:密码@服务器ip:3306/数据库名"

# 6. 创建一个接口，供外部调用
config_dict = {
    "development": DevelopmentConfig,
    "product": ProductConfig
}
