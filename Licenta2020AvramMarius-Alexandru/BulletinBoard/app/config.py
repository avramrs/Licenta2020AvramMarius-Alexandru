import os
basedir = os.path.abspath(os.path.dirname(__file__)).strip(r'\app') + r'\db'

class Config(object):
    DATABASE = os.environ.get("DATABASE")
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, DATABASE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
