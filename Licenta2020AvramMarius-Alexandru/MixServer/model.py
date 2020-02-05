from config import db


class Perm(db.Model):
    __tablename__ = "Permutari"
    batch_id = db.Column("BATCH_ID", db.Text, primary_key=True)
    commit_s = db.Column('COMMIT_S', db.Text)
    perm = db.Column('PERM', db.Text)
    challenge = db.Column('CHALLENGE', db.Text)
    challenge_id = db.Column('CHALLENGE_ID', db.Text)
    batch_len = db.Column('BATCH_LEN', db.Integer)
    peers = db.Column('PEERS', db.Text)


class Messages(db.Model):
    __tablename__ = "Messages"
    id = db.Column("ID", db.Integer, primary_key=True)
    batch_id = db.Column("BATCH_ID", db.Text)
    i = db.Column("IDX", db.Integer)
    m = db.Column("M", db.Text)
    r = db.Column("R", db.Text)
    verified = db.Column("VERIFIED", db.Text)
