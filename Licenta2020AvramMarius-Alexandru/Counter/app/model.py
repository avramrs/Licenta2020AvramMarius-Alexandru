from app import db


class Voter(db.Model):
    __tablename__ = "voters"
    l = db.Column("l", db.Integer, primary_key=True)
    x = db.Column("x", db.Text)
    y = db.Column("y", db.Text)
