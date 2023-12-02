from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from os import environ
from dotenv import load_dotenv
from extensions import db

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
db.init_app(app)
migrate = Migrate(app, db)

# Import models after db is defined
from models import User, Transaction


def add_user(username, balance):
    #check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return 'User already exists!'

    new_user = User(username=username, balance=balance)
    db.session.add(new_user)
    db.session.commit()

# Set up the index route
@app.route('/')
def index():
    # Create a new user and add them to the database
    add_user('testuser', 0)

    # Query all users
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/add_points', methods=['POST'])
def add_points():
    data = request.json
    username = data['username']
    points = data['points']
    description = data['description']
    
    user = User.query.filter_by(username=username).first()
    if user:
        user.add_points(points, description)
        db.session.commit()
        return jsonify({'status': 'success', 'new_balance': user.balance}), 200
    else:
        return jsonify({'status': 'user not found'}), 404

@app.route('/subtract_points', methods=['POST'])
def subtract_points():
    data = request.json
    username = data['username']
    points = data['points']
    
    user = User.query.filter_by(username=username).first()
    if user:
        if user.subtract_points(points, description):
            db.session.commit()
            return jsonify({'status': 'success', 'new_balance': user.balance}), 200
        else:
            return jsonify({'status': 'insufficient balance'}), 400
    else:
        return jsonify({'status': 'user not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)


