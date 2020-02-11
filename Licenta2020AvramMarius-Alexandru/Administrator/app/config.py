from Crypto.PublicKey import RSA
import os

basedir = os.path.abspath(os.path.dirname(__file__)).strip(r"\app") + r'\db'


class Config(object):
    DATABASE = os.environ.get("DATABASE")
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, DATABASE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    with open("key.pem", "r") as key_f:
        SECRET_KEY = RSA.import_key(key_f.read(), os.environ.get('SECRET_PHRASE'))
    OPEN = True
    PASS = os.environ.get("PASS")
