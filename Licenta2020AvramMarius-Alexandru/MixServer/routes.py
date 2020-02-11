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


def check_commit(post_id):
    resp = requests.get(BBOARD, params=dict(id=post_id))
    data = resp.json()[0]
    # dict(id=batch_info["challenge_id"], c=batch_info["commit_s"], perm=batch_info["challenge"])
    m = json.loads(data["m"])
    post_id = m["id"]
    c = m["c"]
    perm = bytes.fromhex(m["perm"])
    resp = requests.get(BBOARD, params=dict(id=post_id))
    data = resp.json()[0]
    bb_commit = json.loads(data["m"])["commit"]
    h = hmac.new(bytes.fromhex(c))
    h.update(perm)
    h = h.hexdigest()
    if hmac.compare_digest(h, bb_commit):
        return perm, c
    return None, None


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


# challenge,commit_s(r_hex),challenge_id
# perm

@app.route('/proof', methods=["POST"])
def get_proof():
    r_json = json.loads(request.get_data())
    response = requests.get(BBOARD, {"id": r_json["post_id"]})
    batch_info = d.get_batch_info(r_json["batch_id"])
    m = dict(id=batch_info["challenge_id"], c=batch_info["commit_s"], perm=batch_info["challenge"])
    W = app.config["BBOARD_KEY"]
    T = get_timestamp()
    resp = requests.post(BBOARD, data=json.dumps(dict(W=W, T=T, m=json.dumps(m))))
    post_id = resp.json()["id"]
    return dict(id=post_id)


@app.route('/prove', methods=["POST"])
def prove():
    r_json = json.loads(request.get_data())
    proof = json.loads(r_json["proof"])
    post_id = proof["post_id"]
    z = proof["z"]
    p_inv = proof["p_inv"]
    batch_id = proof["batch_id"]
    chall, c = check_commit(proof["decommit_id"])
    resp = requests.get(BBOARD, params=dict(id=post_id))
    data = resp.json()[0]
    k, kk = map(int, data["m"].split("|"))
    p = app.config["P"]
    g = app.config["G"]
    h = app.config["NET_H"]
    pub_key = PublicKey(p, g, h)
    verified = True
    batch_info = d.get_batch_info(batch_id)
    batch_len = batch_info["batch_len"]
    vmessages = d.get_batch_messages(batch_id)[-batch_len:]
    umessages = d.get_unverified_messages(batch_id)
    if chall and c:
        c1up = 1
        c2up = 1
        c1vp = 1
        c2vp = 1
        for i, pos in enumerate(chall):
            if pos:
                if not p_inv[i]:
                    verified = False
                    break
                else:
                    c1v, c2v = map(int, vmessages[i]["m"].split("|"))
                    c1u, c2u = map(int, umessages[p_inv[i] - 1]["m"].split("|"))
                    c1up *= c1u
                    c2up *= c2u
                    c1vp *= c1v
                    c2vp *= c2v
        if verified:
            c1up %= p
            c2up %= p
            c1vp %= p
            c2vp %= p
            c1p = c1up * mod_inv(c1vp, p) % p
            c2p = c2up * mod_inv(c2vp, p) % p
            c = int(c, 16)
            if pow(g, z, p) == k * pow(c1p, c, p) % p:
                verified = False
            if pow(h, z, p) == kk * pow(c1p, c, p) % p:
                verified = False
        if verified is True:
            d.approve_messages(batch_id)
    return make_response()


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
        req = dict(W=app.config["BBOARD_KEY"], T=get_timestamp(), m=json.dumps(dict(batch_id=batch_id, commit=commit)))
        resp = requests.post(BBOARD, data=json.dumps(req))
        challenge_id = resp.json()["id"]
        perm = generate_perm(batch_len)
        batch = dict(batch_id=batch_id, commit_s=commit_s, perm=perm, challenge=challenge,
                     challenge_id=str(challenge_id), batch_len=batch_len, peers=peers)
        d.insert_batch(batch)
    if exists is False:
        verified = "True"
    else:
        verified = "False"
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
    peers = json.loads(batch_info["peers"])
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
    W = app.config["BBOARD_KEY"]
    T = get_timestamp()
    resp = requests.post(BBOARD, json.dumps({"W": W, "T": T, "m": m_list}))
    post_id = resp.json()["id"]
    for peer in peers:
        try:
            requests.post(peer["address"] + "ping",
                          data=json.dumps({"batch_id": batch_id, "id": post_id, "peers": json.dumps(peers)}))
        except Exception:
            print("Server down")
    # requests.post(my_address + "ping", data=json.dumps({"batch_id": batch_id, "id": id, "peers": peers}))

    addresses = [peer["address"] for peer in peers]
    next_addr_i = addresses.index(my_address) + 1
    if next_addr_i == len(addresses):
        next_addr = addresses[0]
        r = get_random()
        k = pow(pub_key.g, r, pub_key.p)
        kk = pow(pub_key.h, r, pub_key.p)
        T = get_timestamp()
        resp = requests.post(BBOARD, json.dumps({"W": W, "T": T, "m": str(k) + "|" + str(kk)}))
        post_id = resp.json()["id"]
        resp = requests.post(next_addr + "proof", data=json.dumps(dict(batch_id=batch_id, post_id=post_id)))
        decommit_id = resp.json()["id"]
        chall, c = check_commit(decommit_id)
        p_inv = [0] * batch_len
        if chall:
            for i, pos in enumerate(chall):
                if pos:
                    p_inv[i] = perm[i]
            messages = d.get_batch_messages(batch_id)[-batch_len:]
            x = 0
            for m in messages:
                if int(m["i"]) in p_inv:
                    x += int(m["r"], 16)
            x %= (pub_key.p - 1) // 2
            z = r + x * int(c, 16)
            z %= (pub_key.p - 1) // 2
            proof = dict(z=z, p_inv=p_inv, decommit_id=decommit_id, batch_id=batch_id, post_id=post_id)
            for peer in peers:
                try:
                    requests.post(peer["address"] + "prove",
                                  data=json.dumps(dict(proof=json.dumps(proof))))
                except Exception:
                    print("Server down")

        requests.post(next_addr + "decrypt", data=json.dumps(dict(post_ids=[], batch_id=batch_id)))
    else:
        next_addr = addresses[next_addr_i]

        r = get_random()
        k = pow(pub_key.g, r, pub_key.p)
        kk = pow(pub_key.h, r, pub_key.p)
        T = get_timestamp()
        resp = requests.post(BBOARD, json.dumps({"W": W, "T": T, "m": str(k) + "|" + str(kk)}))
        post_id = resp.json()["id"]
        resp = requests.post(next_addr + "proof", data=json.dumps(dict(batch_id=batch_id, post_id=post_id)))
        decommit_id = resp.json()["id"]
        chall, c = check_commit(decommit_id)
        p_inv = [0] * batch_len
        if chall:
            for i, pos in enumerate(chall):
                if pos:
                    p_inv[i] = perm[i]
            messages = d.get_batch_messages(batch_id)[-batch_len:]
            x = 0
            for m in messages:
                if int(m["i"]) in p_inv:
                    x += int(m["r"], 16)
            x %= (pub_key.p - 1) // 2
            z = r + x * int(c, 16)
            z %= (pub_key.p - 1) // 2
            proof = dict(z=z, p_inv=p_inv, decommit_id=decommit_id, batch_id=batch_id, post_id=post_id)
            for peer in peers:
                try:
                    requests.post(peer["address"] + "prove",
                                  data=json.dumps(dict(proof=json.dumps(proof))))
                except Exception:
                    print("Server down")

        requests.post(next_addr + "mix", data=json.dumps(dict(batch_id=batch_id)))
    return make_response()


# pool mix-> sv1 last?mix-> sv2 last?mix-> sv3 last?decrypt[]-> sv1 (peers/2)+1?decrypt[a1] -> sv2 (peers/2)+1?post MSGBOARD
# decrypt(post_ids:[],batch_id:int)
@app.route('/decrypt', methods=["POST"])
def decrypt_messages():
    data = json.loads(request.get_data())
    post_ids = data["post_ids"]
    batch_id = data["batch_id"]
    batch_info = d.get_batch_info(batch_id)
    if batch_info is None:
        abort(404)
    batch_len = batch_info["batch_len"]
    peers = json.loads(batch_info["peers"])
    threshold = (len(peers) // 2) + 1
    messages = d.get_batch_messages(batch_id)
    if len(messages) // batch_len < threshold:
        abort(403)
    batch = messages[-batch_len:]
    p = app.config["P"]
    identity = app.config["IDENTITY"]
    dec_key = app.config["NET_X"]
    c1_list = []
    c2_list = []
    for message in batch:
        c1, c2 = map(int, message["m"].split("|"))
        c2_list.append(c2)
        shadow = pow(c1, dec_key, p)
        c1_list.append(shadow)
    post_msg = json.dumps(dict(idx=identity, c1="|".join(map(str, c1_list))))
    t_stamp = get_timestamp()
    W = app.config["BBOARD_KEY"]
    response = requests.post(BBOARD, data=json.dumps(dict(W=W, T=t_stamp, m=post_msg)))
    post_id = response.json()["id"]
    post_ids.append(post_id)
    if len(post_ids) == threshold:
        encrypted_messages = dict()
        decrypted_messages = [1] * batch_len
        for post_id in post_ids:
            response = requests.get(BBOARD, {"id": post_id})
            data = response.json()[0]
            m = json.loads(data["m"])
            encrypted_messages[int(m["idx"])] = list(map(int, m["c1"].split("|")))

        idx_list = list(map(int, encrypted_messages.keys()))
        for idx in idx_list:
            r = partial_interpol(idx_list, idx, (p - 1) // 2)
            for i, c1 in enumerate(encrypted_messages[idx]):
                decrypted_messages[i] *= pow(c1, r, p)
                decrypted_messages[i] %= p
        for i, message in enumerate(decrypted_messages):
            try:
                decrypted_messages[i] = partial_decrypt(message, c2_list[i], p)
            except:
                print("Decryption Failed")
        t_stamp = get_timestamp()
        W = hex(app.config["NET_H"])
        m = "|".join(decrypted_messages)
        requests.post(BBOARD, data=json.dumps(dict(W=W, T=t_stamp, m=m)))
    else:
        addresses = [peer["address"] for peer in peers]
        next_addr_i = addresses.index(my_address) + 1
        if next_addr_i == len(addresses):
            abort(403)
        next_addr = addresses[next_addr_i]
        requests.post(next_addr + "decrypt", data=json.dumps(dict(post_ids=post_ids, batch_id=batch_id)))

    return make_response()
