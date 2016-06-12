from flask import Flask
from werkzeug.contrib.fixers import ProxyFix
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config, Config
from celery import Celery

bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    celery.conf.update(app.config)
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    app.wsgi_app = ProxyFix(app.wsgi_app)

    return app
