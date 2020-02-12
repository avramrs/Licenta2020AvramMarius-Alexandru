from Crypto.PublicKey import RSA
import requests
import time
import math
import secrets
import random
import json

MSGBOARD = "http://127.0.0.1:5001/"
BBOARD = "http://127.0.0.1:5000/"
REFRESH_RATE = 60
BATCH_SIZE = 5
THRESHOLD = 7

with open("stats_server_addr.txt", "r") as f:
    writer_key = f.readline()


def load_key():
    with open("sv_key.pem", "rb") as f:
        key = RSA.import_key(f.read())
    return key


def get_text_key():
    key = load_key()
    return str(key.publickey().export_key("OpenSSH")).strip("b")


def get_timestamp():
    return time.asctime(time.gmtime())


def get_messages(bboard_id):
    param = {"id": bboard_id}
    response = requests.get(MSGBOARD, param)
    response_json = response.json()
    if not response_json:
        return None, bboard_id
    last_msg_id = max([m["id"] for m in response_json])
    return response_json, last_msg_id


def post_mix(batch, batch_id, mixnet):
    # mix = [{W:"ceva",address:"link"}]
    # mesaj = {W:rsa_key,T:time_string,m:c1|c2}
    """m_list = id=batch_id|c1|c2|c1|c2..."""
    print("Batch:")
    print(batch)
    m_list = "|".join([m["m"] for m in batch])
    m_list = "id=" + str(batch_id) + "|" + m_list
    W = get_text_key()
    data = {"W": W, "T": get_timestamp(), "m": m_list}
    response = requests.post(BBOARD, data=json.dumps(data))
    peers = json.dumps(mixnet)
    print(response.text)
    if response.ok:
        id = response.json()["id"]
        for sv in mixnet:
            try:
                requests.post(sv["address"] + "ping", data=json.dumps({"batch_id": batch_id, "id": id,"peers":peers}))
            except Exception:
                print("Server down")
        start_addr = mixnet[0]["address"]
        requests.post(start_addr+"mix",data = json.dumps(dict(batch_id=batch_id)))
        print("New mix started!")
        quit(0)
        time.sleep(2)


def find_value(v, l):
    search = l[:]
    p = random.randint(0, len(search) - 1)
    while len(search) > 2:
        if v > search[p]:
            search = search[p:]
        elif v < search[p]:
            search = search[:p + 1]
        else:
            return l.index(search[p])
        p = random.randint(0, len(search) - 1)
    if v < search[p]:
        return l.index(search[p])
    else:
        return l.index(search[p - 1])


def select_batch(messages):
    batch = []
    messages.sort(key=lambda x: time.strptime(x["T"]))
    elite = math.ceil((BATCH_SIZE * 10) / 100)
    for _ in range(elite):
        batch.append(messages.pop(0))
    fitness = [time.mktime(time.strptime(x["T"])) for x in messages]
    total = sum(fitness)
    fitness = [x / total for x in fitness]
    wheel = [0]
    for i, x in enumerate(fitness):
        wheel.append(wheel[i] + x)
    for _ in range(BATCH_SIZE - elite):
        r = random.random()
        index = find_value(r, wheel)
        wheel.pop(index)
        batch.append(messages.pop(index - 1))
    return batch


messages = []
unique_messages = []
last_id = 0
while True:
    data, last_id = get_messages(last_id)
    messages.extend(data)
    for message in messages:
        if message["m"] not in unique_messages:
            unique_messages.append(message["m"])
        else:
            messages.remove(message)
    print("New messages:{m}".format(m=unique_messages))
    if len(messages) >= THRESHOLD
        response = requests.get(BBOARD + "writers/" + writer_key)
        if response:
            m = json.loads(response.headers["data"])[-1]["m"].split("|")
            mix = [json.loads(sv) for sv in m[1:]]
            if mix:
                try:
                    batch = select_batch(messages)
                except Exception as e:
                    print(e)
                else:
                    batch_id = secrets.token_hex(32)
                    post_mix(batch, batch_id, mix)
    time.sleep(REFRESH_RATE)
# mix = [{svinfo}]
# mesaj = {W:rsa_key,T:time_string,m:c1|c2}
