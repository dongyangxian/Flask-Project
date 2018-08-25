from flask import Blueprint

# 创建蓝图对象
index_bp = Blueprint("index", __name__)

# 切忌要让模块发现views
from .views import *
