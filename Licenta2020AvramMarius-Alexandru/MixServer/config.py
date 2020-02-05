import os
import elgamal
import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__)) + r'\db'


class Config(object):
    DATABASE = os.environ.get("DATABASE")
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, DATABASE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    P = int(os.environ["p"])
    G = int(os.environ["g"])
    H = int(os.environ["h"])
    Q = (P - 1) // 2
    NET_X = int(os.environ["mixSecretKey"])
    NET_H = int(os.environ["mixPublicKey"])
    MIX_PRIV_KEY = elgamal.PrivateKey(P, G, NET_X)
    MIX_PUB_KEY = elgamal.PublicKey(P, G, NET_H)
    BBOARD = "http://127.0.0.1:5000/"
    MSGBOARD = "http://127.0.0.1:5001/"
    BBOARD_KEY = os.environ["bboard_key"]
    PEERS = json.loads(os.environ["peers"])
    IDENTITY = int(os.environ["identity"])
    ADDRESS = os.environ["address"]


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
