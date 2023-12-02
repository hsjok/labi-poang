from flask_sqlalchemy import SQLAlchemy
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# A simple model that represents a User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=0)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    password_hash = db.Column(db.String(256))

    def __repr__(self):
        return '<User %r>' % self.username

    def add_points(self, points, description=""):
        old_balance = self.balance
        self.balance += points
        new_balance = self.balance
        transaction = Transaction(user_id=self.id, old_balance=old_balance, change=points, new_balance=new_balance, description=description)
        db.session.add(transaction)

    def subtract_points(self, points, description=""):
        if self.balance >= points:
            old_balance = self.balance
            self.balance -= points
            new_balance = self.balance
            transaction = Transaction(user_id=self.id, old_balance=old_balance, change=-points, new_balance=new_balance, description=description)
            db.session.add(transaction)
            return True
        return False

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    old_balance = db.Column(db.Integer, nullable=False)
    change = db.Column(db.Integer, nullable=False)
    new_balance = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transaction {self.id} by User {self.user_id}>"