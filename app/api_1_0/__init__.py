import redis
from flask import Blueprint

api = Blueprint('api', __name__)
command = redis.StrictRedis()

from . import player, system
