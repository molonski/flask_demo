from flask import Blueprint


bp = Blueprint('errors', __name__,
               template_folder='templates',
               static_folder='static',
               static_url_path='/static/errors')

from app.errors import handlers
