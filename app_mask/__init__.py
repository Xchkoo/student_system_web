from flask import Flask
from flask_login import LoginManager
from app_mask import config,account
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['UPLOAD_FOLDER'] = 'app_mask/UPLOAD/'
app.config['JSON_AS_ASCII'] = False
if sys.platform == 'win32':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + config.APP_PATH + \
                                           '/database/user_database.db3'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + config.APP_PATH + \
                                           '/database/user_database.db3'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_ECHO'] = True

#flask-login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return account.find_user_by_id(user_id)


from app_mask import views


