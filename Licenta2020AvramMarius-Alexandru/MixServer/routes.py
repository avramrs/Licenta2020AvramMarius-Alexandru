from flask import make_response, request, abort
from config import app
from random import shuffle
from communication import get_timestamp
from elgamal import *
import database as d
import requests
import json
import random
import os
import hmac

BBOARD = app.config["BBOARD"]
my_address = app.config["ADDRESS"]


def get_random():
    q = app.config["Q"]
    r_b = random.SystemRandom().randint(2, q - 2)
    return r_b


def generate_perm(length):
    perm = list(range(1, length + 1))
    shuffle(perm)
    return "|".join([str(el) for el in perm])


def generate_commit(length):
    bit_nr = (length // 2)
    l = list(range(1, length + 1))
    shuffle(l)
    perm = l[:bit_nr]
    challenge = [0] * length
    for el in perm:
        challenge[el - 1] = 1
    challenge = bytes(challenge)
    r = os.urandom(32)
    r_hex = r.hex()
    hash = hmac.new(r)
    hash.update(challenge)
    hash = hash.hexdigest()
    return challenge.hex(), hash, r_hex


@app.route('/ping', methods=["POST"])
def ping():
    """{batch_id:str,id=int,peers=[{W:c,address:link},...]}"""
    exists = False
    r_json = json.loads(request.get_data())
    post_id = r_json["id"]
    batch_id = r_json["batch_id"]
    peers = r_json["peers"]
    resp = requests.get(BBOARD, {"id": post_id})
    data = resp.json()
    assert data
    msg = data[0]["m"].split("|")
    msg_batch_id = msg[0].strip("id=")
    assert msg_batch_id == batch_id
    rest = msg[1:]
    msg_list = []
    for i in range(0, len(rest), 2):
        msg_list.append(str(rest[i]) + "|" + str(rest[i + 1]))
    batch_len = len(msg_list)
    batch_info = d.get_batch_info(batch_id)
    if batch_info is not None:
        exists = True
    else:
        challenge, commit, commit_s = generate_commit(batch_len)
        req = dict(W=hex(app.config["NET_H"]), T=get_timestamp(), m=json.dumps(dict(batch_id=batch_id, commit=commit)))
        resp = requests.post(BBOARD, data=json.dumps(req))
        challenge_id = resp.json()["id"]
        perm = generate_perm(batch_len)
        batch = dict(batch_id=batch_id, commit_s=commit_s, perm=perm, challenge=challenge,
                     challenge_id=str(challenge_id), batch_len=batch_len, peers=peers)
        d.insert_batch(batch)
    # if exists is False:
    #     verified = "True"
    # else:
    #     verified = "False"
    verified = "True"
    m_insert = []
    for i, m in enumerate(msg_list):
        m_insert.append(dict(batch_id=batch_id, i=i + 1, m=m, r=hex(get_random()), verified=verified))
    d.insert_messages(m_insert)
    return make_response()


@app.route('/mix', methods=["POST"])
def mix_messages():
    r_json = json.loads(request.get_data())
    batch_id = r_json["batch_id"]
    batch_info = d.get_batch_info(batch_id)
    if batch_info is None:
        abort(404)
    # todo:get verified messages
    peers = batch_info["peers"]
    batch_len = batch_info["batch_len"]
    messages = d.get_batch_messages(batch_id)[-batch_len:]
    perm = [int(el) for el in batch_info["perm"].split("|")]
    mixed_messages = []
    for i in perm:
        mixed_messages.append((messages[i - 1]["m"], messages[i - 1]["r"]))
    pub_key = PublicKey(app.config["P"], app.config["G"], app.config["NET_H"])
    reenc_messages = []
    for m, r in mixed_messages:
        c1, c2 = map(int, m.split("|"))
        u = int(r, 16)
        c1, c2 = reencrypt(pub_key, c1, c2, u)
        reenc_messages.append(str(c1) + "|" + str(c2))
    m_list = "|".join(m for m in reenc_messages)
    m_list = "id=" + str(batch_id) + "|" + m_list
    W = hex(app.config["NET_H"])
    T = get_timestamp()
    resp = requests.post(BBOARD, json.dumps({"W": W, "T": T, "m": m_list}))
    id = resp.json()["id"]
    for peer in peers:
        try:
            requests.post(peer["address"] + "ping", data=json.dumps({"batch_id": batch_id, "id": id, "peers": peers}))
        except Exception:
            print("Server down")
    # requests.post(my_address + "ping", data=json.dumps({"batch_id": batch_id, "id": id, "peers": peers}))
    return make_response()


# pool mix-> sv1 last?mix-> sv2 last?mix-> sv3 last?decrypt[]-> sv1 (peers/2)+1?decrypt[a1] -> sv2 (peers/2)+1?post MSGBOARD
# decrypt(a_list,batch_id)
@app.route('/decrypt', methods=["POST"])
def decrypt_messages():
    data = request.json()
    shares = data["shares"]
    batch_id = data["batch_id"]
    batch_info = d.get_batch_info(batch_id)
    batch_len = batch_info["batch_len"]
    peers = batch_info["peers"]
    # todo:verified messages
    messages = d.get_batch_messages(batch_id)
    batch = messages[-batch_len:]
    threshold = (len(peers) // 2) + 1
    shadow = app.config["NET_X"]
    shares.append(shadow)
    if len(shares) == threshold:
        key = sum(shares) % app.config["Q"]
        key = PrivateKey(app.config["P"], app.config["G"], key)
        plaintexts = []
        for message in batch:
            c1, c2 = map(int, message["m"].split("|"))
            try:
                plaintext = decrypt(key, c1, c2)
                plaintexts.append(plaintext)
            except Exception:
                print("Corrupted message")
        print(plaintexts)
