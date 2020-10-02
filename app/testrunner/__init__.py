from flask import Blueprint


bp = Blueprint('testrunner', __name__,
               template_folder='templates',
               static_folder='static')

from app.testrunner import routes
