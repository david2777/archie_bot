import os

basedir = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DB = 'sqlite:///' + os.path.join(basedir, 'app.db')


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or "El0O1J0mgOCfu79u6axtwfCROdgKku0r"
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or DEFAULT_DB
    SQLALCHEMY_TRACK_MODIFICATIONS = False
