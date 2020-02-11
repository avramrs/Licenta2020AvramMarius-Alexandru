from app import db


class Voter(db.Model):
    __tablename__ = "voters"
    voter_id = db.Column('voter_id', db.Text, primary_key=True)
    e = db.Column('e', db.Text)
    s = db.Column('s', db.Text)
    key = db.Column('key', db.Text)
    voted = db.Column('voted', db.Text)
