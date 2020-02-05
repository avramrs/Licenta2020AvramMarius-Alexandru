from app import db
from flask_table import Table,Col


class ItemTable(Table):
    id = Col('ID')
    m = Col('Message')
    T = Col('Time')
    W = Col('Author')
    H = Col('Hash')
    SW = Col('AuthorSig')
    SB = Col('BoardSig')


class Post(db.Model):
    __tablename__ = "bb"
    id = db.Column(db.Integer, primary_key=True)
    m = db.Column('m',db.Text)
    T = db.Column('T',db.Text)
    W = db.Column('W',db.Text)
    H = db.Column('H',db.Text)
    SW = db.Column('SW',db.Text)
    SB = db.Column('SB',db.Text)

    def __repr__(self):
        return '<Message {}>'.format(self.m)