from flask import Blueprint

profile_bp = Blueprint("profile", __name__, url_prefix="/passport")

from .views import *
