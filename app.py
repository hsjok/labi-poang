from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    session,
    flash,
)
from flask_apscheduler import APScheduler
from flask_migrate import Migrate
from functools import wraps
from os import environ
from dotenv import load_dotenv
from extensions import db
from datetime import datetime


# Define configuration class
class Config:
    SCHEDULER_API_ENABLED = True
    MONTHLY_POINTS = 5000
    # Other configurations


load_dotenv()

app = Flask(__name__)
app.secret_key = environ.get("FLASK_SECRET_KEY")

# Construct the database URI
db_user = environ.get("POSTGRES_USER")
db_password = environ.get("POSTGRES_PASSWORD")
db_name = environ.get("POSTGRES_DB")
db_host = "db"  # Hostname used in docker-compose for the database service

# Configure the SQLAlchemy part of the app instance
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Create an SQLAlchemy object named `db` and bind it to your app
db.init_app(app)
migrate = Migrate(app, db)

# Import models after db is defined
from models import User

# Initialize and start the scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


# Function to add points
def allocate_monthly_points():
    with app.app_context():
        users = User.query.all()
        for user in users:
            user.add_points(Config.MONTHLY_POINTS, "Monthly allocation")
        db.session.commit()
        print(f"Allocated points on {datetime.now()}")


# Schedule the task
@scheduler.task("cron", id="monthly_points", month="*", day=1, hour=0, minute=0)
def scheduled_task():
    allocate_monthly_points()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if (
            "user_id" not in session
        ):  # Assuming 'user_id' is stored in session upon login
            # Redirect to login page, don't forget to return it!
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def add_user(username, balance):
    # check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return "User already exists!"

    new_user = User(username=username, balance=balance)
    db.session.add(new_user)
    db.session.commit()


# Set up the index route
@app.route("/")
@login_required
def index():
    # Query all users
    username = session.get("username", "default-username")
    users = User.query.all()
    return render_template("index.html", users=users, username=username)


### User management routes ###


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]

        user = User.query.get(
            session["user_id"]
        )  # Assuming user_id is stored in session

        if user and user.check_password(old_password):
            user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully")
            return redirect(url_for("index"))
        else:
            flash("Incorrect old password")

    return render_template("change_password.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = username
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password")

    return render_template("login.html")


### User interaction routes ###


@app.route("/add_points", methods=["POST"])
@login_required
def add_points():
    data = request.json
    username = data["username"]
    points = data["points"]
    description = data["description"]

    user = User.query.filter_by(username=username).first()
    if user:
        user.add_points(points, description)
        db.session.commit()
        return jsonify({"status": "success", "new_balance": user.balance}), 200
    else:
        return jsonify({"status": "user not found"}), 404


@app.route("/subtract_points", methods=["POST"])
def subtract_points():
    data = request.json
    username = data["username"]
    points = data["points"]
    description = data["description"]

    user = User.query.filter_by(username=username).first()
    if user:
        if user.subtract_points(points, description):
            db.session.commit()
            return jsonify({"status": "success", "new_balance": user.balance}), 200
        else:
            return jsonify({"status": "insufficient balance"}), 400
    else:
        return jsonify({"status": "user not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
