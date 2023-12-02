from flask_sqlalchemy import SQLAlchemy
from extensions import db

# A simple model that represents a User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=0)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

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


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    old_balance = db.Column(db.Integer, nullable=False)
    change = db.Column(db.Integer, nullable=False)
    new_balance = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Transaction {self.id} by User {self.user_id}>"