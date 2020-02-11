from app import app
from flask import request, make_response, abort
import json
import app.database as v_db


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/question', methods=["GET"])
def get_question():
    if app.config["VOTING"] is True:
        text = app.config["TEXT"]
        return dict(question=text[0], answers=text[1:])
    else:
        return dict(question="Voting finished.", answers=None)


@app.route('/results', methods=["POST"])
def set_results():
    req_json = json.loads(request.get_data())
    if "pass" not in req_json:
        abort(403)
    elif req_json["pass"] != app.config['PASS']:
        abort(403)
    app.config["RESULTS"] = req_json["results"]


@app.route('/results', methods=["GET"])
def get_results():
    if app.config["RESULTS"] is None:
        abort(404)
    return {"results": app.config["RESULTS"]}


@app.route('/vote', methods=["POST"])
def add_vote():
    req_json = json.loads(request.get_data())
    if "pass" not in req_json or "vote" not in req_json:
        abort(403)
    elif req_json["pass"] != app.config['PASS']:
        abort(403)
    vote = json.loads(req_json["vote"])
    v_id = v_db.insert(vote)
    return {"id": v_id}


@app.route('/stop', methods=["POST"])
def stop_voting():
    req_json = json.loads(request.get_data())
    if "pass" not in req_json:
        abort(403)
    elif req_json["pass"] != app.config['PASS']:
        abort(403)
    else:
        app.config["VOTING"] = False
    return make_response()


@app.route('/get_vote', methods=["POST"])
def get_vote():
    req_json = json.loads(request.get_data())
    if "pass" not in req_json or "id" not in req_json:
        abort(403)
    elif req_json["pass"] != app.config['PASS']:
        abort(403)
    v_id = req_json["id"]
    vote = v_db.get_id(v_id)
    return {"vote": vote}


@app.route('/get_voters', methods=["GET"])
def get_voters():
    if app.config["VOTING"] is True:
        abort(403)
    voters = v_db.get_all()
    return {"voters": voters}


if __name__ == '__main__':
    app.run()
