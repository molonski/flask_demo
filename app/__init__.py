import os
import logging
import redis
import rq
import app.config as config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
# from flask_cors import CORS
from logging.handlers import RotatingFileHandler
from flask_bootstrap import Bootstrap
from flask_collect import Collect


# factory app pattern
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
bootstrap = Bootstrap()     # Twitter bootstrap for styling
collect = Collect()
# cors = CORS()   # Cross-Origin Resource Sharing for Single Page Applications


def create_app(config_class=config.Config):

    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    login.init_app(app)
    bootstrap.init_app(app)
    collect.init_app(app)       # collect static files from blueprints
    # collect.collect(verbose=True)
    # cors.init_app(app)

    # define redis worker
    redis_url = os.environ.get('REDIS_URL')
    app.redis = redis.from_url(redis_url)
    # app.task_queue_listen = os.environ.get('REDIS_WORKER_NAME')
    # app.task_queue = rq.Queue(app.task_queue_listen, connection=app.redis, default_timeout=900)
    app.task_queue = rq.Queue(connection=app.redis, default_timeout=900)

    # register blueprints of additional app packages
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.testrunner import bp as testrunner_bp
    app.register_blueprint(testrunner_bp, url_prefix='/test-runner')

    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/production-reports')

    # add file logging to the app
    if not app.debug and not app.testing:
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/webapp.log',
                                               maxBytes=10240,
                                               backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        # app.logger.info('ArtiWebApp startup')

    return app


# define database models
import app.main.models
import app.auth.models
