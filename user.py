from flask_login import UserMixin


class User(UserMixin):
    id = 0
    name = ""
    is_teacher = False

