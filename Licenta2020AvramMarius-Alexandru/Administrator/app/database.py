from app.model import Voter
from app import db


def get_by_voter_id(voter_id):
    voter = Voter.query.filter(Voter.voter_id == voter_id).first()
    if voter:
        return dict(voter_id=voter.voter_id, e=voter.e, s=voter.s, key=voter.key, voted=voter.voted)
    else:
        return None

def update_voter(voter_id,e,s):
    voter = Voter.query.filter(Voter.voter_id==voter_id).first()
    voter.e=e
    voter.s=s
    voter.voted="True"
    db.session.commit()

def get_voters():
    voters = Voter.query.filter(Voter.voted == "True").all()
    voter_list = []
    for voter in voters:
        voter_list.append(dict(voter_id=voter.voter_id, e=voter.e, s=voter.s, key=voter.key, voted=voter.voted))
    return voter_list