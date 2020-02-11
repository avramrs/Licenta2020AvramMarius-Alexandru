import socket
import json
import hmac
import requests
import server_th
import re
import time
from message import Message
from pickle import dumps
from os import urandom
from pickle import dumps, loads
from elgamal import *

BBOARD = "http://127.0.0.1:5000/"


def create_request(action, value):
    if action == "register":
        return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, public_key=value[0].hex(), address=value[1])
        )
    elif action == "validate":
        return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, value=value)
        )
    elif action == "share":
        return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, share=value[0], W=value[1])
        )
    else:
        return dict(
            type="binary/custom-client-binary-type",
            encoding="binary",
            content=bytes(action + value, encoding="utf-8"),
        )


def send_shares(f, peers_adr, peers_index, key_pair, PUBLIC_KEY):
    for peer_ident, adr in peers_adr.items():
        receiver_i = peers_index[peer_ident] + 1
        peer_addr = link_to_addr(adr)
        success = False
        while success is False:
            success = send_share(peer_addr, receiver_i, f, key_pair["publicKey"].p, get_hex_key(PUBLIC_KEY))


def send_share(addr, i, f, p, W):
    host, port = addr
    s = calc_poly(f, i, (p - 1) // 2)
    data = (s, W)
    action, value = "share", data
    request = create_request(action, value)
    try:
        message = start_connection(host, port, request)
    except Exception as e:
        return False
    try:
        message.process_events()
    except Exception as e:
        message.close()
        return False
    return True


def check_shares(req_list, Fi, i, p, g):
    for req in req_list:
        commits = Fi[req["W"]]
        si = req["share"]

        a = 1
        power = 0
        for c in commits:
            xi = pow(i, power, p)
            a = mul_mod(a, pow(c, xi, p), p)
            power += 1
        gsi = pow(g, si, p)
        if gsi != a:
            return False
    return True


def start_connection(host, port, request):
    addr = (host, port)
    print("starting connection to", addr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)
    message = Message(sock, addr, request, "w")
    return message


def register(stats_address, pk, my_address):
    host, port = stats_address
    action, value = "register", (dumps(pk), my_address)
    request = create_request(action, value)
    message = start_connection(host, port, request)
    try:
        message.process_events()
    except Exception as e:
        message.close()
        raise e
    return message.response


def validate(stats_address, pk, my_addres, mix_key):
    host, port = stats_address
    action, value = "validate", {"W": get_hex_key(pk), "address": my_addres, "PK": mix_key}
    request = create_request(action, value)
    message = start_connection(host, port, request)
    try:
        message.process_events()
    except Exception as e:
        message.close()
        raise e
    return message.response


def listen_shares(my_address, peers_dic):
    peers = peers_dic[:]
    sv_t = server_th.sv_thread(my_address, peers)
    sv_t.start()
    time.sleep(3)
    return sv_t


def get_register_info(response, writer_key):
    network_ts = response.get("T")
    peers_dic = response.get("peers")
    peers_pk = []
    peers_adr = dict()
    peers_index = dict()
    identity = None
    for j, peer in enumerate(peers_dic):
        peers_pk.append(peer['public_key'])
        if get_hex_key(writer_key) == peer['public_key']:
            identity = j
            continue
        peers_adr[peer['public_key']] = peer['address']
        peers_index[peer['public_key']] = j
    if identity is None:
        raise AttributeError("Server not found in mixnet")
    return peers_dic, peers_pk, peers_adr, peers_index, identity, network_ts


def get_hex_key(key):
    return dumps(key).hex()


def load_key(key_s):
    key_b = bytes.fromhex(key_s)
    pb = loads(key_b)
    return pb


def open_commit(r, h, pub_key):
    message = json.dumps({"r": r.hex(), "h": h})
    tstamp = get_timestamp()
    W = get_hex_key(pub_key)
    data = json.dumps({"m": message, "T": tstamp, "W": W})
    requests.post(BBOARD, data=data)


def verify_commit(c, r, h):
    rbytes = bytes.fromhex(r)
    h256 = generate_hash_commit(h, rbytes)
    return hmac.compare_digest(h256, c)


def verify_commits(commits, peers, t):
    messages, f_t = get_messages(peers, t)
    verifiable_commits = []
    for message in messages:
        m = json.loads(message['m'])
        c = None
        for commit in commits:
            if commit["W"] == message["W"]:
                c = commit["m"]
                break
        if c is None:
            raise AttributeError("Commit not found")
        verifiable_commits.append({"r": m["r"], "h": m["h"], "c": c, "W": message["W"]})
    for commit in verifiable_commits:
        c, r, h = commit["c"], commit["r"], commit["h"]
        if verify_commit(c, r, str(h).encode()) is False:
            return False
    return [{"h": c["h"], "W": c["W"]} for c in verifiable_commits], f_t


def get_network_pub_key(p, g, network_pub_keys):
    network_pub_key = 1
    for key in network_pub_keys:
        network_pub_key = mul_mod(network_pub_key, key["h"], p)
    return network_pub_key


def generate_hash_commit(m, r):
    h = hmac.new(r, digestmod="sha256")
    h.update(m)
    commit = h.hexdigest()
    return commit


def commit_poly_coefs(pol, g, p):
    commits = []
    for coef in pol:
        commit = pow(g, coef, p)
        commits.append(commit)
    return commits


def send_commit(commit_l, PUBLIC_KEY):
    commit = " ".join(str(x) for x in commit_l)
    tstamp = get_timestamp()
    W = get_hex_key(PUBLIC_KEY)
    data = json.dumps({"m": commit, "T": tstamp, "W": W})
    requests.post(BBOARD, data=data)


def send_network_pub_key(response, writer_key):
    p = int(response.get('p'))
    g = int(response.get('g'))
    key_pair = get_keys(p, g)
    r = urandom(128)
    pkh = str(key_pair["publicKey"].h).encode()
    commit = generate_hash_commit(pkh, r)
    W = get_hex_key(writer_key)
    tstamp = get_timestamp()
    data = json.dumps({"m": commit, "T": tstamp, "W": W})
    requests.post(BBOARD, data=data)
    return r, key_pair


def get_dict_list(response):
    return json.loads(response.headers["data"])


def get_time_obj(time_str):
    return time.strptime(time_str)


def get_timestamp():
    return time.asctime(time.gmtime())


def link_to_addr(link):
    parts = link.split(":")
    host = parts[1].lstrip("//")
    port = parts[2].rstrip("/")
    return host, int(port)


def get_max_timestamp(messages):
    ts = max([time.strptime(message["T"]) for message in messages])
    ts_string = time.asctime(ts)
    return ts_string


def get_messages(peers_l, timestamp):
    messages = []
    peers = peers_l[:]
    time.sleep(1)
    t = get_time_obj(timestamp)
    while True:
        for peer in peers:
            response = requests.get(BBOARD + "writers/" + peer)
            writer_messages = get_dict_list(response)
            for message in writer_messages:
                m_t = get_time_obj(message["T"])
                if m_t < t:
                    writer_messages.remove(message)
            if writer_messages:
                messages.append(writer_messages[-1])
                peers.remove(peer)
        if not peers:
            break
        else:
            time.sleep(5)
    ts = get_max_timestamp(messages)
    return messages, ts
