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
from flask_mail import Mail, Message
from functools import wraps
from os import environ
from dotenv import load_dotenv
from extensions import db
from datetime import datetime
from dateutil.relativedelta import relativedelta
from models import Transaction


# Define configuration class
class Config:
    SCHEDULER_API_ENABLED = True
    MONTHLY_POINTS = 2500
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

app.config["MAIL_SERVER"] = "smtp.mailgun.org"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = environ.get(
    "EMAIL_USERNAME"
)  # Your Mailgun SMTP Username
app.config["MAIL_PASSWORD"] = environ.get(
    "EMAIL_PASSWORD"
)  # Your Mailgun SMTP Password
app.config[
    "MAIL_DEFAULT_SENDER"
] = "LabisPoints@labilito.com"  # Your default "from" address

# Create an SQLAlchemy object named `db` and bind it to your app
db.init_app(app)
migrate = Migrate(app, db)

# Import models after db is defined
from models import User

# Initialize and start the scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Initialize the mail extension
mail = Mail(app)


# Function to add points
def allocate_monthly_points():
    with app.app_context():
        users = User.query.all()
        for user in users:
            user.add_points(Config.MONTHLY_POINTS, "Monthly allocation")
        db.session.commit()
        print(f"Allocated points on {datetime.now()}")


# Schedule tasks
@scheduler.task("cron", id="monthly_points", month="*", day=1, hour=0, minute=0)
def scheduled_task():
    allocate_monthly_points()


@scheduler.task("cron", id="send_report", month="*", day=1, hour=0, minute=5)
def send_report_task():
    with app.app_context():
        send_monthly_report_email()


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


@app.template_filter()
def format_points(value):
    try:
        # Format with , thousands separators
        return f"{value:,}"
    except ValueError:
        # If value can't be formatted, return it as is
        return value


# Add the filter to Jinja environment
app.jinja_env.filters["format_int"] = format_points


@app.route("/get_transactions/<int:user_id>", methods=["GET"])
def get_transactions(user_id):
    months = request.args.get("months", default=1, type=int)  # Default to last 1 month
    end_date = datetime.now()
    start_date = end_date - relativedelta(months=months)

    # Query using SQLAlchemy ORM
    transactions = (
        Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.created_at.between(start_date, end_date),
        )
        .order_by(Transaction.created_at.desc())
        .all()
    )

    # Format transactions into a list of dictionaries
    transactions_data = [
        {
            "description": trans.description,
            "change": trans.change,
            "new_balance": trans.new_balance,
            "created_at": trans.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for trans in transactions
    ]

    return jsonify(transactions_data)


def generate_monthly_report_data():
    # Calculate the date range for the last month
    end_date = datetime.now()
    start_date = end_date - relativedelta(months=1)

    users_data = []
    users = User.query.all()

    for user in users:
        # Calculate net points spent for the last month for this user
        transactions_last_month = Transaction.query.filter(
            Transaction.user_id == user.id,
            Transaction.created_at >= start_date,
            Transaction.created_at < end_date,
        ).all()

        net_spent_last_month = sum(
            t.change for t in transactions_last_month if t.change < 0
        )  # Assuming negative change for spending

        # Assuming User model has a method or attribute to get the current balance
        current_balance = (
            user.balance
        )  # Or user.get_current_balance(), depending on your User model

        users_data.append(
            {
                "username": user.username,
                "net_spent_last_month": abs(
                    net_spent_last_month
                ),  # Make the spent amount positive for readability
                "current_balance": current_balance,
            }
        )

    return users_data


def send_monthly_report_email():
    report_data = generate_monthly_report_data()
    email_body = "Dear Labis,\n\nHere is your monthly points summary:\n\n"

    # Accumulate report data for both users
    for user_data in report_data:
        email_body += (
            f"User: {user_data['username']}\n"
            f"Net Points Spent Last Month: {user_data['net_spent_last_month']}\n"
            f"Current Balance: {user_data['current_balance']}\n\n"
        )

    email_body += "Puss"

    recipients = ["henriksjokvist94@gmail.com", "sofiawiklund.95@gmail.com"]

    # Send the email
    with app.app_context():
        msg = Message(
            "Your Monthly Points Summary", recipients=recipients, body=email_body
        )
        mail.send(msg)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
