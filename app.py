import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_mysqldb import MySQL
from functools import wraps
from dotenv import load_dotenv
import time

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'automlp')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

mysql = MySQL(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_cursor():
    """Safely handles MySQL reconnections"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            cursor = mysql.connection.cursor()
            return cursor
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(retry_delay)
            mysql.connection.ping(reconnect=True)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        hashed_password = generate_password_hash(password)
        
        try:
            cursor = get_db_cursor()
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                         (username, email, hashed_password))
            mysql.connection.commit()
            cursor.close()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Email or username may already exist.', 'danger')
    
    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor = get_db_cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout/')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard/')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/process/', methods=['POST'])
@login_required
def process():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('dashboard'))
    
    file = request.files['file']
    prompt = request.form.get('prompt', '')
    model_type = request.form.get('model_type', 'xgboost')
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('dashboard'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # In a real app, we would process the file and generate the model here
        # For now, we'll just store the file info in the session
        session['last_processed'] = {
            'filename': filename,
            'prompt': prompt,
            'model_type': model_type
        }
        
        flash('File successfully uploaded and processing started!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Allowed file types are .csv only', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/download-model/')
@login_required
def download_model():
    if 'last_processed' not in session:
        flash('No model available for download', 'danger')
        return redirect(url_for('dashboard'))
    
    # Create a dummy model file if it doesn't exist
    dummy_model_path = os.path.join(app.config['UPLOAD_FOLDER'], 'dummy_model.pt')
    if not os.path.exists(dummy_model_path):
        with open(dummy_model_path, 'wb') as f:
            f.write(b'Dummy PyTorch model data')
    
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        'dummy_model.pt',
        as_attachment=True,
        download_name=f"{session['username']}_model.pt"
    )

if __name__ == '__main__':
    app.run(debug=True)