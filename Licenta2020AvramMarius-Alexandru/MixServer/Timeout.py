from threading import Timer
import re
import requests


class TimerError(Exception):
    pass


class Timeout:
    def __init__(self, peers, identity, board, timeout=120.0):
        self.peers = peers
        self.identity = identity
        self.timeout = timeout
        self.board = board
        self.threshold = len(self.peers) // 2 + 1
        self.current = 0
        self.t = None
        self.batch_id = None
        self.id = None
        self.loaded = False
        self.decrypt = False

    def __check(self):
        response = requests.get(self.board + "writers/" + self.peers[self.current]["public_key"])
        found = False
        for m in response.json():
            m_id = re.match(r"id=(\w+)|", m["m"])
            if m_id:
                if m_id == self.batch_id:
                    found = True
                    break
        if not found:
            self.kick()
            self.start()

    def start(self):
        if self.current == self.identity:
            my_info = self.peers[self.identity]
            if self.decrypt is False:
                requests.post(my_info["address"] + "/mix", {"id": self.id, "batch_id": self.batch_id})
            else:
                requests.post(my_info["address"] + "/decrypt", {"id": self.id, "batch_id": self.batch_id})
        else:
            self.t = Timer(self.timeout, self.__check())
            self.t.start()

    def set_id(self, batch_id, b_id):
        self.batch_id = batch_id
        self.id = b_id

    def next(self):
        if self.current + 1 < len(self.peers):
            self.current += 1
            if self.t:
                self.t.cancel()
            self.start()
        else:
            if self.decrypt is False:
                self.decrypt = True
                self.current = 0
                self.next()
            else:
                self.stop()

    def kick(self):
        self.peers.remove(self.current)
        if self.identity > self.current:
            self.identity -= 1
        if len(self.peers) < self.threshold:
            raise ValueError("Not enough servers in mix")

    def stop(self):
        if self.t is None:
            raise TimerError("No timer active")
        self.t.cancel()
        self.t = None
