import os

basedir = os.path.abspath(os.path.dirname(__file__))
basedbdir = os.path.abspath(os.path.dirname(__file__)).strip(r"\app") + r'\db'


class Config(object):
    DATABASE = os.environ.get("DATABASE")
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedbdir, DATABASE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PASS = os.environ["PASS"]
    with open(basedir + "\\question.txt", 'r') as f:
        TEXT = list(map(str.strip, f.readlines()))
    VOTING = True
    RESULTS = None
