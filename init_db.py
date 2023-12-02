from app import app, db
from models import User  # Import your model classes here

# Push an application context
with app.app_context():
    # Create the database tables
    db.create_all()