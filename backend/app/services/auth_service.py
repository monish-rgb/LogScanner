from app.extensions import db, bcrypt
from app.models.user import User


def register_user(username, email, password):
    if User.query.filter_by(username=username).first():
        raise ValueError("Username already exists")
    if User.query.filter_by(email=email).first():
        raise ValueError("Email already registered")

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, email=email, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return None
    return user
