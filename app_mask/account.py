from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from flask_login import UserMixin


USERS = [
    {
        "id": 1,
        "name": 'xchkoo',
        "mail": "Xchkoo@foxmail.com",
        "sex": "male",
        "position": "Hangzhou",
        "status": "Admin",
        "password": generate_password_hash('123')
    },
    {
        "id": 2,
        "name": 'weijianan3',
        "mail": "18667189667@qq.com",
        "sex": "male",
        "position": "Hangzhou",
        "status": "Admin",
        "password": generate_password_hash('20041221')
    }
]


def create_user(user_name, password):
    """创建一个用户"""
    user = {
        "name": user_name,
        "password": generate_password_hash(password),
        "id": uuid.uuid4(),
        "mail": "unknown",
        "sex": "unknown",
        "position": "unknown",
        "status": "Admin",
    }
    USERS.append(user)


def get_user(user_name):
    """根据用户名获得用户记录"""
    for user in USERS:
        if user.get("name") == user_name:
            return user
    return None


class User(UserMixin):
    """用户类"""
    def __init__(self, user):
        self.username = user.get("name")
        self.password_hash = user.get("password")
        self.id = user.get("id")
        self.mail = user.get("mail")
        self.sex = user.get("sex")
        self.position = user.get("position")
        self.status = user.get("status")

    def verify_password(self, password):
        """密码验证"""
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """获取用户ID"""
        return self.id

    @staticmethod
    def get(user_id):
        """根据用户ID获取用户实体，为 login_user 方法提供支持"""
        if not user_id:
            return None
        for user in USERS:
            if user.get('id') == user_id: # user["id"]
                return User(user)
        return None
