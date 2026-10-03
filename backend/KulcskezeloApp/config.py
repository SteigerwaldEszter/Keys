import os

basedir = os.path.abspath(os.path.dirname(__file__))


def load_private_key():
    path = os.path.abspath(os.path.dirname(__file__))

    key_path = os.path.join(path, ".ssh", "private_key.pem")

    with open(key_path, "rb") as f:
        #return f.read()
        key_data = f.read()
        
        # Remove BOM if present
        if key_data.startswith(b'\xef\xbb\xbf'):
            key_data = key_data[3:]
        key_data = key_data.replace(b'\r\n', b'\n')
        key_data = key_data.strip()
        
        return key_data
        


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "egy-nagyon-titkos-kulcs-a-kulcsokhoz"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PRIVATE_KEY = load_private_key()
