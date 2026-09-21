import os
basedir = os.path.abspath(os.path.dirname(__file__))

def load_private_key():

    path = os.path.abspath(os.path.dirname(__file__))

    key_path = os.path.join(path, ".ssh", "private_key.pem")

    with open(key_path, 'r') as f:

        return f.read()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'egy-nagyon-titkos-kulcs-a-raktarhoz'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')\
        or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
