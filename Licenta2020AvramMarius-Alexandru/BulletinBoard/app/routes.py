from flask import make_response, request, abort
from app.utils import wrap_html
from app import app
from app.model import ItemTable
import json
import app.database as bb


@app.route('/', methods=['GET'])
def get_history():
    if "id" not in request.args:
        data = bb.get_all()
        table = ItemTable(data)
        response = make_response(wrap_html(table.__html__()))
        response.headers['data'] = json.dumps(data)
    else:
        id = request.args["id"]
        data = bb.get_id(id)
        response = make_response(json.dumps(data))
    return response


@app.route('/writers/<W>', methods=['GET'])
def get_writer(W):
    data = bb.get_writer(W)
    table = ItemTable(data)
    response = make_response(wrap_html(table.__html__()))
    response.headers['data'] = json.dumps(data)
    return response


@app.route('/', methods=['POST'])
def post_message():
    data = json.loads(request.data)
    try:
        id = bb.insert(data)
    except Exception as err:
        bb.error(err)
        raise err
    response = make_response({"id": id})
    return response


@app.route('/del', methods=['GET'])
def empty_table():
    bb.delete()
    response = make_response()
    return response


@app.route('/last_id', methods=['GET'])
def get_last_id():
    last_id = bb.get_last_id()
    response = make_response()
    response.headers["data"] = last_id
    return response


@app.errorhandler(500)
def internal_error(error):
    bb.error(error)
    abort(500)


if __name__ == '__main__':
    app.run()
