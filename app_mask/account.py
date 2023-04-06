from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 创建引擎，连接到数据库
engine = create_engine('sqlite:///app_mask/user.db?check_same_thread=False', echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


# 创建用户表
class User(UserMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

    def __init__(self, username, password):

        self.username = username
        self.password = generate_password_hash(password)

    def verify_password(self, userpasswd):
        if self.password == userpasswd:
            return True
        else:
            return False

    def check_password(self, password):
        # return check_password_hash(self.password, password)
        if self.password == password:
            return True


Base.metadata.create_all(engine)


# 创建用户
def create_user(username, password):
    new_user = User(username=username, password=password)
    session.add(new_user)
    session.commit()
    session.close()


# 查询用户
def find_user(username):
    user = session.query(User).filter_by(username=username).first()
    return user


def find_user_by_id(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    return user
