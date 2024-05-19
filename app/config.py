from os import environ

ALGORITHM = "HS256"
SECRET_KEY = environ['SECRET_KEY']
SQLALCHEMY_DATABASE_URL = environ['SQLALCHEMY_DATABASE_URL']
ACCESS_TOKEN_EXPIRE_MINUTES = int(environ['ACCESS_TOKEN_EXPIRE_MINUTES'])
SAVE_DIRECTORY = environ['SAVE_DIRECTORY']