from app.model import Voter
from app import db


def get_all():
    voters = Voter.query.all()
    if not voters:
        return None
    else:
        data = [dict(l=voter.l, x=voter.x, y=voter.y) for voter in voters]
    return data


def get_id(id):
    vote = Voter.query.filter(Voter.l == id).first()
    if not vote:
        return None
    else:
        data = dict(l=vote.l, x=vote.x, y=vote.y)
    return data


def insert(data):
    if data:
        # post = Post(m=data['m'], T=data['T'], W=data['W'], H=data['H'], SW=data['SW'], SB=data['SB'])
        vote = Voter(x=data["x"], y=data["y"])
    else:
        raise AttributeError
    db.session.add(vote)
    db.session.commit()
    db.session.refresh(vote)
    return vote.l
