from flask import render_template, request
from flask_login import login_required
from app.errors import bp
from app import db
from app.api.errors import error_response as api_error_response


@bp.app_errorhandler(400)
@login_required
def bad_request_error(e):
    if 'api' in request.url:
        return api_error_response(400)
    return render_template('errors/errors.html', error_code=400), 400


@bp.app_errorhandler(401)
@login_required
def unathorized_error(e):
    if 'api' in request.url:
        return api_error_response(401)
    return render_template('errors/errors.html', error_code=401), 401


@bp.app_errorhandler(403)
@login_required
def forbidden_error(e):
    if 'api' in request.url:
        return api_error_response(403)
    return render_template('errors/errors.html', error_code=403), 403


@bp.app_errorhandler(404)
@login_required
def not_found_error(e):
    if 'api' in request.url:
        return api_error_response(404)
    return render_template('errors/errors.html', error_code=404), 404


@bp.app_errorhandler(410)
@login_required
def gone_away_error(e):
    if 'api' in request.url:
        return api_error_response(410)
    return render_template('errors/errors.html', error_code=410), 410


@bp.app_errorhandler(500)
@login_required
def internal_error(e):
    db.session.rollback()
    if 'api' in request.url:
        return api_error_response(500)
    return render_template('errors/errors.html', error_code=500), 500


@bp.app_errorhandler(502)
def bad_gateway_error(e):
    db.session.rollback()
    if 'api' in request.url:
        return api_error_response(502)
    return render_template('errors/errors.html', error_code=502), 502


@bp.app_errorhandler(503)
@login_required
def unavailable_error(e):
    db.session.rollback()
    if 'api' in request.url:
        return api_error_response(503)
    return render_template('errors/errors.html', error_code=503), 503


@bp.app_errorhandler(504)
@login_required
def gateway_timeout_error(e):
    db.session.rollback()
    if 'api' in request.url:
        return api_error_response(504)
    return render_template('errors/errors.html', error_code=504), 504
