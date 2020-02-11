import requests
import json
import pickle
import os
import elgamal
import time
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256, HMAC
from Crypto.Signature import pkcs1_15
from Crypto.Util.Padding import *
from Crypto.Util.number import GCD, inverse
from Crypto.Random.random import randint
from Crypto.Random import get_random_bytes

ADMIN_ADDRESS = "http://127.0.0.1:7000/"
MSG_BOARD = "http://127.0.0.1:5001/"
BBOARD = "http://127.0.0.1:5000/"


def int_to_bytes(i):
    return i.to_bytes((i.bit_length() + 7) // 8, 'big')


def int_from_bytes(i_b):
    return int.from_bytes(i_b, 'big')


def get_timestamp():
    return time.asctime(time.gmtime())


class Client:
    def __init__(self, address):
        try:
            self.load_key()
        except FileNotFoundError:
            self.key = None
        try:
            self.load_sig()
        except FileNotFoundError:
            self.admin_sig = None
        self.counter_address = address
        self.message = None
        self.ID = None
        self.k = None
        self.x = None
        self.y = None
        self.p = int(os.environ["P"])
        self.g = int(os.environ["G"])
        self.voters = None

    def set_ID(self, ID):
        self.ID = ID

    def get_results(self):
        resp = requests.get(self.counter_address + "results")
        if resp.status_code != 200:
            print(resp.status_code)
            return None
        else:
            resp_json = json.loads(resp.content)
            return resp_json["results"]

    def get_question(self):
        resp = requests.get(self.counter_address + "question").json()
        return resp

    def get_voters(self):
        resp = requests.get(self.counter_address + "get_voters")
        if resp.status_code != 200:
            return None
        else:
            self.voters = resp.json()["voters"]
            return self.voters

    def load_sig(self, filename="admin_sig"):
        with open(filename, "rb") as f:
            self.admin_sig = pickle.load(f)

    def get_mix_key(self):
        with open("stats_server_addr.txt", "r") as f:
            writer_key = f.readline().strip()
        response = requests.get(BBOARD + "writers/" + writer_key)
        PK = json.loads(response.headers["data"])[-1]["m"].split("|")[0].strip("PK=")
        return int(PK)

    def load_key(self, file_name="key.pem"):
        with open(file_name, "r") as f:
            self.key = RSA.import_key(f.read())

    def sign(self, key, msg):
        signer = pkcs1_15.new(key)
        msg_hash = SHA256.new()
        msg_hash.update(msg)
        signature = signer.sign(msg_hash)
        return signature

    def verify(self, key, msg, sig):
        rest = pow(sig, key.e, key.n)
        return rest == msg

    def blind(self, key, msg):
        r = randint(2, key.n)
        while GCD(r, key.n) != 1:
            r = randint(2, key.n)
        blinded_msg = (msg * pow(r, key.e, key.n)) % key.n
        return blinded_msg, r

    def unblind(self, key, r, msg):
        r_inv = inverse(r, key.n)
        return (msg * r_inv) % key.n

    def get_hashmac(self, msg):
        r = get_random_bytes(32)
        msg_hash = HMAC.new(r)
        msg_hash.update(msg)
        return msg_hash.hexdigest(), r

    def load_message(self, msg_str: str):
        msg = msg_str.encode()
        self.message = msg

    def get_admin_sig(self):
        response = requests.get(ADMIN_ADDRESS + "key").json()
        admin_key = RSA.import_key(bytes.fromhex(response["key"]))
        # hex,bytes
        x_h, self.k = self.get_hashmac(self.message.encode())
        self.x = int(x_h, 16)
        # int int
        e, r = self.blind(admin_key, self.x)
        # bytes
        s = self.sign(self.key, int_to_bytes(e))
        admin_req = dict(ID=self.ID, e=e, s=s.hex())
        response = requests.post(ADMIN_ADDRESS + 'sign', data=json.dumps(admin_req))
        if response.status_code != 200:
            raise AttributeError
        admin_sig = response.json()["sig"]
        self.y = self.unblind(admin_key, r, admin_sig)
        if self.verify(admin_key, self.x, self.y) is True:
            voter_secrets = dict(e=e, y=self.y, x=self.x, k=self.k)
            with open("admin_sig", "wb+") as f:
                pickle.dump(voter_secrets, f)
        return self.send_vote()

    def send_vote(self):
        """Send vote after getting signature"""
        with open("admin_sig", "rb") as f:
            voter_secrets = pickle.load(f)
        message = str(voter_secrets["x"]) + ',' + str(voter_secrets["y"])
        h = self.get_mix_key()
        key = elgamal.PublicKey(self.p, self.g, h)
        enc_vote = elgamal.encrypt(key, message)
        m = "|".join([str(c) for c in enc_vote])
        msg = dict(m=m, T=get_timestamp(), W=str(self.key.publickey().export_key("OpenSSH")).strip("b"))
        data = json.dumps(msg)
        requests.post(MSG_BOARD, data)

    def open_vote(self):
        if self.voters is None:
            return None
        assert self.admin_sig
        found = False
        idx = None
        for voter in self.voters:
            if voter["x"] == str(self.admin_sig["x"]):
                if voter["y"] == str(self.admin_sig["y"]):
                    found = True
                    idx = voter["l"]
                    break
        if found:
            msg = "open=" + str(idx) + "," + self.admin_sig["k"].hex()
            h = self.get_mix_key()
            key = elgamal.PublicKey(self.p, self.g, h)
            enc_vote = elgamal.encrypt(key, msg)
            m = "|".join([str(c) for c in enc_vote])
            msg = dict(m=m, T=get_timestamp(), W=str(self.key.publickey().export_key("OpenSSH")).strip("b"))
            data = json.dumps(msg)
            requests.post(MSG_BOARD, data)
            print("Done")
        else:
            print(self.admin_sig)
            print(self.voters)
            raise NotImplementedError
