from flask import Flask
from sqlalchemy.exc import SQLAlchemyError
from userClass import db, User
from datetime import datetime

# Create a Flask application and configure it
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Siteforge1@35.243.209.101/siteforge_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def test_db_connection():
    with app.app_context():
        try:
            # Drop all tables and recreate them
            db.drop_all()
            db.create_all()
            print("Tables dropped and recreated")

            # Create a new user
            new_user = User(username='testuser', email='testuser@example.com', password='testpassword', created_at=datetime.utcnow())
            db.session.add(new_user)
            db.session.commit()
            print("User added successfully")

            # Query the user
            user = User.query.filter_by(username='testuser').first()
            if user:
                print(f"User found: {user.username}, {user.email}")

            # Update the user
            user.email = 'newemail@example.com'
            db.session.commit()
            print("User updated successfully")

            # Delete the user
            db.session.delete(user)
            db.session.commit()
            print("User deleted successfully")

        except SQLAlchemyError as e:
            print(f"Database error: {e}")

if __name__ == '__main__':
    test_db_connection()
