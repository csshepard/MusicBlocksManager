import redis
from flask import Blueprint

api = Blueprint('api', __name__)
red = redis.StrictRedis()
status = red.pubsub(ignore_subscribe_messages=True)

from . import player, system
