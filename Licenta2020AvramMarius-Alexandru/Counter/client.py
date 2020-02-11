from threading import Event
from count_thread import CountThread
import time
import requests
import json
import re
import os
import hmac
from Crypto.PublicKey import RSA
import pickle

counter_addr = "http://127.0.0.1:7500/"
BBOARD = "http://127.0.0.1:5000/"
ADMIN_ADDRESS = "http://127.0.0.1:7000/"



def stop_admin():
    requests.post(counter_addr + "stop", data=json.dumps({"pass": os.environ["PASS"]}))


def get_question():
    resp = requests.get(counter_addr + "question").json()
    return resp


def get_mix_key():
    with open("stats_server_addr.txt", "r") as f:
        writer_key = f.readline().strip()
    response = requests.get(BBOARD + "writers/" + writer_key)
    PK = json.loads(response.headers["data"])[-1]["m"].split("|")[0].strip("PK=")
    return int(PK)


def send_vote(vote):
    vote_s = json.dumps(vote)
    data = {"pass": os.environ['C_PASS'], "vote": vote_s}
    response = requests.post(counter_addr + 'vote', data=json.dumps(data))
    print(response.status_code)


def stop_voting():
    requests.post(counter_addr + "stop", data=json.dumps({"pass": os.environ["C_PASS"]}))


def get_voters():
    resp = requests.get(counter_addr + "get_voters")
    print(resp.json())


def get_vote_nr():
    resp = requests.post(ADMIN_ADDRESS, data=json.dumps({"pass": os.environ["PASS"]})).json()
    return resp["vote_nr"]


def get_voter(l):
    resp = requests.post(counter_addr + 'get_vote', data=json.dumps({"pass": os.environ["C_PASS"], "id": l}))
    voter = resp.json()["vote"]
    return voter


def check_hash(msg, key, hash):
    h = hmac.new(key)
    h.update(msg)
    print(int(hash))
    print(int(h.hexdigest(), 16))
    return int(hash) == int(h.hexdigest(), 16)


def check_valid(l, k, answers, results):
    voter_info = get_voter(l)
    for answer in answers:
        if check_hash(answer.encode(), k, voter_info["x"]):
            print(answer)
            results[answers.index(answer)] += 1
            return


answers = get_question()["answers"]
print(get_question())
response = requests.get(ADMIN_ADDRESS + "key").json()
admin_key = RSA.import_key(bytes.fromhex(response["key"]))
mix_key = hex(get_mix_key())

stop_flag = Event()
count_th = CountThread(stop_flag, mix_key, answers, BBOARD, counter_addr, admin_key)
count_th.start()
time.sleep(10)

stop_admin()
vote_nr = get_vote_nr()

stop_flag.set()
stop_voting()

opened_votes = 0
last_id = 0
results = [0] * len(answers)
while opened_votes < vote_nr:
    param = {"id": last_id + 1}
    response = requests.get(BBOARD + "writers/" + mix_key, param)
    response_json = json.loads(response.content)
    if not response_json:
        continue
    last_id = max([m["id"] for m in response_json])
    msg_list = [m["m"] for m in response_json]
    for msg in msg_list:
        if re.match(r"open=", msg):
            for m in msg.split("|"):
                m = m.lstrip("open=")
                l, k = m.split(",")
                l = int(l)
                k = bytes.fromhex(k)
                check_valid(l, k, answers, results)
    print(results)
    opened_votes = sum(results)
print(results)
with open("results.txt", "wb+") as f:
    pickle.dump(results, f)
with open("results.txt", "rb") as f:
    results = pickle.load(f)
requests.post(counter_addr + "results", data=json.dumps({"results": results,"pass":os.environ["C_PASS"]}))
