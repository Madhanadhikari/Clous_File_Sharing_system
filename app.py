from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'upload'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'mp3', 'wav', 'pdf'}

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class FileDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uploaderID = db.Column(db.String(100), nullable=False)
    receiverID = db.Column(db.String(100), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'userID' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        userID = request.form['userID']
        password = request.form['password']
        user = User.query.filter_by(userID=userID).first()
        if user and user.password == password:
            session['userID'] = userID
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        userID = request.form['userID']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(userID=userID).first()
        if existing_user:
            flash('User already exists. Please log in.')
            return redirect(url_for('login'))
        new_user = User(userID=userID, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'userID' not in session:
        return redirect(url_for('login'))

    userID = session['userID']

    if request.method == 'POST':
        receiverID = request.form['receiverID']
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Store in DB
            new_file = FileDetails(
                uploaderID=userID,
                receiverID=receiverID,
                file_name=filename
            )
            db.session.add(new_file)
            db.session.commit()
            flash('File uploaded and shared successfully!')
        else:
            flash('Invalid file type. Only images, audio, and video allowed.')

    return render_template('home.html', userID=userID)

@app.route('/transfer', methods=['GET'])
def transfer():
    if 'userID' not in session:
        return redirect(url_for('login'))

    userID = session['userID']
    query = request.args.get('query')
    if query:
        files = FileDetails.query.filter(FileDetails.receiverID == userID, FileDetails.file_name.contains(query)).all()
    else:
        files = FileDetails.query.filter_by(receiverID=userID).all()
    
    return render_template('transfer.html', files=files)

@app.route('/logout')
def logout():
    session.pop('userID', None)
    return redirect(url_for('login'))

@app.route('/upload/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
