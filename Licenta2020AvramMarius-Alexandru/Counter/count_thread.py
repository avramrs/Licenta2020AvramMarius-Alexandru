from threading import Thread
import requests
import time
import json
import os


def get_timestamp():
    return time.asctime(time.gmtime())


class CountThread(Thread):
    def __init__(self, event, writer, answers, BBOARD, counter_addr,admin_key):
        Thread.__init__(self)
        self.stopped = event
        self.writer = writer
        self.last_id = 0
        self.answers = answers
        self.counter_addr = counter_addr
        self.BBOARD = BBOARD
        self.admin_key = admin_key

    def run(self):
        while not self.stopped.wait(5):
            print("Getting Votes")
            messages = self.get_messages()
            if messages:
                for message in messages:
                    batch = message.split("|")
                    valid_msgs = self.check_batch(batch)
                    for msg in valid_msgs:
                        self.send_counter(msg)

    def check_batch(self, batch):
        valid_msgs = []
        for message in batch:
            x, y = map(int, message.split(","))
            rest = pow(y, self.admin_key.e, self.admin_key.n)
            if rest == x:
                valid_msgs.append(dict(x=str(x), y=str(y)))
        return valid_msgs

    def send_counter(self, vote):
        vote_s = json.dumps(vote)
        data = {"pass": os.environ['C_PASS'], "vote": vote_s}
        response = requests.post(self.counter_addr + 'vote', data=json.dumps(data))
        print(response.status_code)

    def get_messages(self):
        param = {"id": self.last_id + 1}
        response = requests.get(self.BBOARD+"writers/" + self.writer, param)

        response_json = json.loads(response.content)
        if not response_json:
            return None
        self.last_id = max([m["id"] for m in response_json])
        msg_list = [m["m"] for m in response_json]
        return msg_list
