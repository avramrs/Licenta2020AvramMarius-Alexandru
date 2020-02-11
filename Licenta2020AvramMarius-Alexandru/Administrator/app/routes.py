import json
from app import app
from flask import make_response, request, abort
import app.database as db
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256


def int_to_bytes(i):
    return i.to_bytes((i.bit_length() + 7) // 8, 'big')


def sign(key, msg):
    msg_i = msg
    signature = pow(msg_i, key.d, key.n)
    return signature


def verify(key, msg, sig):
    signer = pkcs1_15.new(key)
    msg_hash = SHA256.new()
    msg_hash.update(msg)
    try:
        signer.verify(msg_hash, sig)
    except ValueError:
        return False
    else:
        return True


@app.route('/key', methods=['GET'])
def get_pub_key():
    pv_key = app.config["SECRET_KEY"]
    pub_key = pv_key.export_key("OpenSSH").hex()
    return dict(key=pub_key)


@app.route('/sign', methods=['POST'])
def sign_message():
    # req={ID:str,e:hex,s:str}
    if app.config["OPEN"] is False:
        abort(403)
    req_json = json.loads(request.get_data())
    ID = req_json["ID"]
    voter = db.get_by_voter_id(ID)
    if voter is None:
        print("Voter not registered")
        abort(401)
    if voter["voted"] == "True":
        print("Already Voted")
        abort(403)
    voter_key_str = voter["key"]
    voter_key_bytes = voter_key_str.encode()
    voter_key = RSA.import_key(voter_key_bytes)
    # Hashul Votului
    e = req_json["e"]
    # Semnătura Votului
    s = req_json["s"]
    if verify(voter_key, int_to_bytes(e), bytes.fromhex(s)) is False:
        print("Wrong signature")
        abort(403)
    db.update_voter(ID, hex(e), s)
    pv_key = app.config["SECRET_KEY"]
    signature = sign(pv_key, e)
    return dict(sig=signature)


@app.route('/', methods=['POST'])
def get_vote_nr():
    req_json = json.loads(request.get_data())
    if "pass" in req_json:
        if req_json["pass"] == app.config["PASS"]:
            vote_nr = len(db.get_voters())
        else:
            abort(403)
    else:
        abort(403)
    return {"vote_nr": vote_nr}


@app.route('/stop', methods=['POST'])
def stop_requests():
    req_json = json.loads(request.get_data())
    if app.config["OPEN"] is False:
        abort(403)
    if "pass" in req_json:
        if req_json["pass"] == app.config["PASS"]:
            app.config["OPEN"] = False
        else:
            abort(403)
    else:
        abort(403)
    return make_response()


if __name__ == '__main__':
    app.run()
