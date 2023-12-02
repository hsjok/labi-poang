from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from os import environ
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Construct the database URI
db_user = environ.get('POSTGRES_USER')
db_password = environ.get('POSTGRES_PASSWORD')
db_name = environ.get('POSTGRES_DB')
db_host = 'db'  # Hostname used in docker-compose for the database service

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create an SQLAlchemy object named `db` and bind it to your app
db = SQLAlchemy(app)

# A simple model that represents a User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<User %r>' % self.username

# Set up the index route
@app.route('/')
def index():
    # Create a new user and add them to the database
    new_user = User(username="testuser")
    db.session.add(new_user)
    db.session.commit()

    # Query all users
    users = User.query.all()
    return render_template('index.html', users=users)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)