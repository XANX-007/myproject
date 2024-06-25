from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from userClass import db, User
import os
import requests
from functools import wraps

app = Flask(__name__)

API_URL = 'https://pfzwi3wvcc.execute-api.eu-central-1.amazonaws.com/test/'
app.config['SECRET_KEY'] = 'test_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Siteforge1@35.243.209.101/siteforge_db'
db.init_app(app)
app.secret_key = 'supersecured'

def get_user_email():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if user:
            return user.email
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def create_tables():
    if not hasattr(app, 'tables_created'):
        db.create_all()
        app.tables_created = True

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken, please choose another one')
            return render_template('signup.html')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password, first_name=first_name, last_name=last_name)

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            flash('There was an issue adding your account: ' + str(e))
            return render_template('signup.html')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            session['user_id'] = user.id
            session['username'] = user.username
            print(f"User {user.username} logged in")
            return redirect(url_for('home'))

        print("Invalid username or password")
        flash('Invalid username or password')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/')
def home():
    return render_template('index.html')


@login_required
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('index.html', username=user.username)
    return redirect(url_for('login'))

@app.route('/launch')
@login_required
def launch_instance():
    return render_template('order-page.html')

@app.route('/launch', methods=['POST'])
@login_required
def launch():
    try:
        project_name = request.form.get('project_name')
        options = request.form.get('option')
        username = session.get('username')  # Get username from session

        response = requests.post(API_URL, json={
            'projectName': project_name,
            'options': options,
            'email': get_user_email(),
            'customerName': username
        }, headers={
            'Content-Type': 'application/json',
            'x-api-key': 'your-api-key'  # Add this line if your API requires an API key
        })

        print(f"API response status: {response.status_code}")
        print(f"API response body: {response.text}")

        if response.status_code != 200:
            flash('Failed to launch instance')
            return redirect(url_for('home'))

        return render_template('launch_instance.html', instance_id=response.json().get('executionArn'))

    except Exception as e:
        flash(f"Error launching instance: {str(e)}")
        return render_template('order-page.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
