from model import Perm, Messages
from config import db


def get_all_messages():
    messages = Messages.query.all()
    data = [
        dict(id=message.id, batch_id=message.batch_id, i=message.i, m=message.m, r=message.r, verified=message.verified)
        for message in messages]
    return data


def get_batch_messages(batch_id):
    data = Messages.query.filter(Messages.batch_id == batch_id, Messages.verified == "True").all()
    messages = [
        dict(id=message.id, batch_id=message.batch_id, i=message.i, m=message.m, r=message.r, verified=message.verified)
        for message in data]
    return messages

def get_unverified_messages(batch_id):
    data = Messages.query.filter(Messages.batch_id == batch_id, Messages.verified == "False").all()
    messages = [
        dict(id=message.id, batch_id=message.batch_id, i=message.i, m=message.m, r=message.r, verified=message.verified)
        for message in data]
    return messages

def approve_messages(batch_id):
    messages = Messages.query.filter(Messages.batch_id == batch_id, Messages.verified == "False").all()
    for message in messages:
        message.verified = "True"
    db.session.commit()

def insert_batch(batch):
    if batch:
        perm = Perm(batch_id=batch["batch_id"], commit_s=batch["commit_s"], perm=batch["perm"],
                    challenge=batch["challenge"], challenge_id=batch["challenge_id"], batch_len=batch["batch_len"],
                    peers=batch["peers"])
    else:
        raise AttributeError
    db.session.add(perm)
    db.session.commit()


def get_batch_info(batch_id):
    data = Perm.query.filter(Perm.batch_id == batch_id).first()
    if not data:
        return None
    res = dict(batch_id=data.batch_id, commit_s=data.commit_s, perm=data.perm, challenge=data.challenge,
               challenge_id=data.challenge_id, batch_len=data.batch_len, peers=data.peers)
    return res


def insert_messages(msg_list):
    for msg in msg_list:
        message = Messages(batch_id=msg["batch_id"], i=msg["i"], m=msg["m"], r=msg["r"],
                           verified=msg["verified"])
        db.session.add(message)
    db.session.commit()
