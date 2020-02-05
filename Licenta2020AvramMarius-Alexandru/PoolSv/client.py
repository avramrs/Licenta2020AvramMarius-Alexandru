import requests
import json
import elgamal
import re
from Crypto.PublicKey import RSA

BBOARD = "http://127.0.0.1:5000/"
MSGBOARD = "http://127.0.0.1:5001/"

with open("stats_server_addr.txt", "r") as f:
    writer_key = f.readline()


def post(msg):
    data = json.dumps(msg)
    requests.post(MSGBOARD, data)


response = requests.get(BBOARD + "writers/" + writer_key)
m = json.loads(response.headers["data"])[-1]["m"].split("|")

h= int(m[0].lstrip("PK="))
mix = [json.loads(sv) for sv in m[1:]]
# de schimbat p si g
p = 159894130690866518715676700679914580048989761067929251232658984640241370656048819478970540172400824940676291914583930673450312079276754347590810962921127772180565467551108089545135195352292977608077158096313520573423992659974844915883976947063226056290758241311189459697842977699382649575548521103800914436539
g = 10547051139819993035592588960585696514283723775938929413997989209319437855922291713060634847770885464456928156715275810980285468399273837176928041648262992562944600479250061123430862195569257263768267354281654377031027540419882670397742045164524593294540815253254444894526442136154969275137541190123317586897


pk = elgamal.PublicKey(p, g, h)

# for i in range(7):
#     with open("key"+str(i)+".pem","wb+") as f:
#         key_pair = RSA.generate(1024)
#         f.write(key_pair.export_key("PEM"))

keys = []
for i in range(7):
    with open("key" + str(i) + ".pem", "rb") as f:
        keys.append(RSA.import_key(f.read()))

msgs = [{"W": "1", "T": "Sat Feb 1 09:59:35 2020", "m": "m1"},
        {"W": "2", "T": "Sat Feb 1 09:45:51 2020", "m": "m2"},
        {"W": "3", "T": "Sat Feb 1 09:45:45 2020", "m": "m3"},
        {"W": "4", "T": "Sat Feb 1 09:45:57 2020", "m": "m4"},
        {"W": "5", "T": "Sat Feb 1 09:45:57 2020", "m": "m5"},
        {"W": "6", "T": "Sat Feb 1 09:45:57 2020", "m": "m6"},
        {"W": "7", "T": "Sat Feb 1 09:45:57 2020", "m": "m7"}]

for i, msg in enumerate(msgs):
    msg["W"] = str(keys[i].publickey().export_key("OpenSSH")).strip("b")

print(msgs)

for msg in msgs:
    plaintext = msg["m"]
    crypto = elgamal.encrypt(pk, plaintext)
    msg["m"] = "|".join([str(c) for c in crypto])
    post(msg)

#{W:rsa_key,T:time_string,m:c1|c2}