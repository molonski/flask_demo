import redis
from flask import request, jsonify, current_app
from rq.job import Job
from app.main import database_queries
from app.api import bp
from app.api.auth import token_auth


@bp.route("/redis-connection/", methods=['GET'])
@token_auth.login_required
def is_redis_worker_available():
    # check redis connection
    redis_server_running = False

    try:
        # getting None returns None or throws an exception
        _ = current_app.redis.client_list()
        redis_server_running = True
    except (redis.exceptions.ConnectionError, redis.exceptions.BusyLoadingError):
        pass

    return jsonify({'redis_server_running': redis_server_running})


@bp.route('/job-submission/', methods=['POST'])
@token_auth.login_required
def post_result():

    result = request.get_json()

    job = current_app.task_queue.enqueue_call(
        func=database_queries.enter_new_test_result,
        args=(result,),
        result_ttl=5000
    )
    job_id = job.get_id()

    return jsonify({'job_id': job_id})


@bp.route("/job-status/<job_key>/", methods=['GET'])
@token_auth.login_required
def get_submission_status(job_key):

    job = Job.fetch(job_key, connection=current_app.redis)

    if job.is_finished:
        return jsonify({'status': job.get_status(), 'testlog_id': job.result})
    else:
        return jsonify({'status': job.get_status()})
