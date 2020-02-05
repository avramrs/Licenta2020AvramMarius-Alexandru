import socket
import selectors
import traceback
import requests
from pickle import load, dumps
from utils import get_timestamp
import json
from message import Message

HOST = "127.0.0.1"
PORT = 8999
BBOARD = "http://127.0.0.1:5000/"
try:
    with open("secret.txt", "rb") as kf:
        PUBLIC_KEY = load(kf)
        PRIVATE_KEY = load(kf)
        print("Keys loaded successfully")
except:
    print("Keys failed to load")
    raise

sel = selectors.DefaultSelector()


def get_hex_key(k):
    return dumps(k).hex()


def accept_wrapper(sock):
    conn, addr = sock.accept()
    print("Accepted connection from", addr)
    conn.setblocking(False)
    msg = Message(sel, conn, addr)
    sel.register(conn, selectors.EVENT_READ, data=msg)


def publish(sv_list,mix_key):
    ts = get_timestamp()
    PK = get_hex_key(PUBLIC_KEY)
    for sv in sv_list:
        del sv["PK"]
    l = [json.dumps(sv) for sv in sv_list]
    msg = "PK="+str(mix_key)+"|"+"|".join(l)
    data = json.dumps({"m": msg, "T": ts, "W": PK})
    requests.post(BBOARD, data=data)


def registered(events):
    keys = list(zip(*events))[0]
    data_l = [k.data for k in keys if k.data is not None]
    register_candidates = [{"public_key": data.request["public_key"], "address": data.request["address"]} for data in
                           data_l if
                           data.register is True]
    return register_candidates


lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.bind((HOST, PORT))
lsock.listen()
print("listening on", (HOST, PORT))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

threshold = 3
registration_open = False
mix_nets = dict()

try:
    while True:

        events = sel.select(timeout=None)
        registered_l = registered(events)
        if threshold <= len(registered_l):
            registration_open = True

        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                message = key.data
                if message.register is True:
                    if not registration_open:
                        continue
                try:
                    if message.register is True:
                        message.peers = registered_l
                    if message.validate is True:
                        m = message.request.get("value")
                        if m["PK"] in mix_nets:
                            mix_nets[m["PK"]].append(m)
                        else:
                            mix_nets[m["PK"]] = [m]
                        if len(mix_nets[m["PK"]]) == threshold:
                            publish(mix_nets[m["PK"]],m["PK"])
                    message.process_events(mask)
                except Exception:
                    print(
                        "main: error: exception for",
                        f"{message.addr}:\n{traceback.format_exc()}",
                    )
                    message.close()

        registration_open = False

except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
except Exception as e:
    print(e)
finally:
    sel.close()
