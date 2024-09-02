from flask import Flask, render_template, redirect, url_for, request, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os
import threading
import subprocess

app = Flask(__name__)
app.config['SECRET_KEY'] = '7b5f6d0a2b9c1f74c8d5e1a3f4b7c6e9a2d5c4f3e6b7a9c0f1d3e4f5a6b8c7d'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DIRECTORY_TO_SERVE = './monitored'  # Directory containing files to serve

# Function to run the monitoring script
def run_monitor():
    subprocess.run(["python", "monitor.py"])

# Start monitoring in a separate thread
monitoring_thread = threading.Thread(target=run_monitor)
monitoring_thread.start()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    files = os.listdir(DIRECTORY_TO_SERVE)
    return render_template('index.html', files=files, current_user=current_user)

@app.route('/files/<filename>')
@login_required
def serve_file(filename):
    return send_from_directory(DIRECTORY_TO_SERVE, filename)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        file.save(os.path.join(DIRECTORY_TO_SERVE, file.filename))
        return redirect(url_for('index'))

@app.route('/monitored')
@login_required
def monitored():
    # Replace this with your actual monitoring data
    monitoring_data = [
        {'filename': 'file1.txt', 'status': 'OK'},
        {'filename': 'file2.txt', 'status': 'Error'},
        {'filename': 'file3.txt', 'status': 'OK'}
    ]
    return render_template('monitored.html', monitoring_data=monitoring_data)

# Monitoring route to handle unauthorized access
@app.route('/monitor')
def monitor():
    unauthorized_users = ["unauthorized_user1", "unauthorized_user2"]
    user = current_user.username
    if user in unauthorized_users:
        return "Unauthorized access detected!", 401
    return "Authorized access", 200

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(host='0.0.0.0', port=5000)