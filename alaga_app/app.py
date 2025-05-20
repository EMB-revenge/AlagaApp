from flask import Flask, render_template, url_for, redirect, request, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from flask_migrate import Migrate
from wtforms.validators import InputRequired, Length, ValidationError
import os
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import traceback
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'database.db')
app.config['SECRET_KEY'] = 'ubedelechesecretkey'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads/profile_pics')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_default_profile_pic():
    default_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], 'default.jpg')
    
    # Only create if it doesn't exist
    if not os.path.exists(default_pic_path):
        # Create a blank image with a purple background (to match your theme)
        img = Image.new('RGB', (200, 200), color=(188, 111, 183))  # #BC6FB7
        d = ImageDraw.Draw(img)
        
        # Draw a simple avatar placeholder
        d.ellipse((50, 50, 150, 150), fill=(255, 255, 255))
        d.ellipse((85, 85, 115, 115), fill=(188, 111, 183))
        d.arc((70, 120, 130, 160), start=0, end=180, fill=(188, 111, 183), width=5)
        
        # Save the image
        img.save(default_pic_path)
        app.logger.info("Default profile picture created")


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~MODELS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    profile_pic = db.Column(db.String(100), nullable=False, default='default.jpg')

    # User medications
    medications = db.relationship('Medication', backref='user_profile', lazy=True, cascade="all, delete-orphan")
    # User todos
    todos = db.relationship('Todo', backref='user', lazy=True, cascade="all, delete-orphan")
    # User health records
    health_records = db.relationship('HealthRecord', backref='user', lazy=True, cascade="all, delete-orphan")

class RegisterForm(FlaskForm):
    fullname = StringField('Fullname', validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={'placeholder': 'Fullname'}) 
    username = StringField('Username', validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={'placeholder': 'Username'})  
    
    password = PasswordField('Password', validators=[InputRequired(), Length(\
        min=8, max=20)], render_kw={'placeholder': 'Password'})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()

        # Check if the username already exists in the database, if so,
        if existing_user:
            raise ValidationError(
                "Username already exists. Please choose a different one.") 

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={'placeholder': 'Username'})  
    
    password = PasswordField('Password', validators=[InputRequired(), Length(\
        min=8, max=20)], render_kw={'placeholder': 'Password'})

    submit = SubmitField('Login') 
        
class CareProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    care_recipient = db.Column(db.String(50), nullable=False)  # who you care for
    relationship = db.Column(db.String(50), nullable=False)    # relationship to them
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Add relationship to medications
    medications = db.relationship('Medication', backref='care_profile', lazy=True, cascade="all, delete-orphan")
    # Add relationship to todos
    todos = db.relationship('Todo', backref='care_profile', lazy=True, cascade="all, delete-orphan")
    # Add relationship to health records
    health_records = db.relationship('HealthRecord', backref='care_profile', lazy=True, cascade="all, delete-orphan")

# New Medication model
class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(100))
    instructions = db.Column(db.String(200))
    dosage_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=False)  # Store as HH:MM
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('care_profile.id'), nullable=False)
    
    # Relationship to medication history
    history = db.relationship('MedicationHistory', backref='medication', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'dosage': self.dosage,
            'instructions': self.instructions,
            'dosageType': self.dosage_type,
            'startDate': self.start_date.isoformat(),
            'endDate': self.end_date.isoformat(),
            'time': self.time,
            'profile_id': self.profile_id
        }

# New MedicationHistory model
class MedicationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'taken' or 'skipped'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def to_dict(self):
        medication = Medication.query.get(self.medication_id)
        return {
            'id': self.id,
            'medicationId': self.medication_id,
            'name': medication.name,
            'dosage': medication.dosage,
            'date': self.date.isoformat(),
            'time': self.time,
            'status': self.status,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }

# Todo model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('care_profile.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'date': self.date.isoformat(),
            'completed': self.completed
        }

# Health Record model
class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # vital-signs, biometrics, medical-notes
    type = db.Column(db.String(50), nullable=True)       # specific type within category
    value = db.Column(db.String(100), nullable=True)     # value for measurements
    systolic = db.Column(db.Integer, nullable=True)      # for blood pressure
    diastolic = db.Column(db.Integer, nullable=True)     # for blood pressure
    subject = db.Column(db.String(200), nullable=True)   # for medical notes
    body = db.Column(db.Text, nullable=True)             # for medical notes
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=False)      # Store as HH:MM
    timestamp = db.Column(db.BigInteger, nullable=False) # For sorting
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('care_profile.id'), nullable=True)
    
    def to_dict(self):
        result = {
            'id': self.id,
            'category': self.category,
            'date': self.date.isoformat(),
            'time': self.time,
            'timestamp': self.timestamp
        }
        
        if self.category in ['vital-signs', 'biometrics']:
            result['type'] = self.type
            result['value'] = self.value
            if self.type == 'blood-pressure':
                result['systolic'] = self.systolic
                result['diastolic'] = self.diastolic
        elif self.category == 'medical-notes':
            result['subject'] = self.subject
            result['body'] = self.body
            
        return result

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ROUTES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#route for about us page 
@app.route('/about') 
def about_us():
    return render_template('about_us.html')

#app route for home
@app.route('/')
def home():
    return render_template('start.html')

# route for the start page
@app.route('/start', methods=['GET', 'POST'])
def start():
    return render_template('start.html')

# route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        # checked if the user exists in the database and if the password is correct
        # if so, log the user in and redirect to the home page
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', form=form, error='Invalid username or password')
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if form.errors:
        return render_template('login.html', form=form, error=form.errors)
    return render_template('login.html', form=form)

# route for the logout page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# route for the registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(
            fullname=form.fullname.data, 
            username=form.username.data,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# route for the upgrade to premium page
@app.route('/upgrade_premium', methods=['GET', 'POST']) 
@login_required
def upgrade_premium():
    # Your existing todo route code
    profiles = CareProfile.query.filter_by(user_id=current_user.id).all()
    
    profile_id = session.get('active_profile_id')
    active_profile = None
    
    if profile_id:
        active_profile = CareProfile.query.get(profile_id)
    
    fullname = current_user.fullname
    initials = get_initials(fullname)
    return render_template('upgrade_premium.html', fullname=fullname, initials=initials, profiles=profiles, active_profile=active_profile)

# route for the profile page
@app.route('/view_profile', methods=['GET', 'POST'])
@login_required
def view_profile():
    profiles = CareProfile.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        new_fullname = request.form.get('name')
        new_username = request.form.get('username')
        new_password = request.form.get('password')

        # Update the current user's fullname and username
        current_user.fullname = new_fullname
        current_user.username = new_username

        # Only update password if a new password was entered
        if new_password:
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            current_user.password = hashed_password
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('view_profile'))

    fullname = current_user.fullname
    username = current_user.username
    initials = get_initials(fullname)
    return render_template('view_profile.html', fullname=fullname, username=username, initials=initials, profiles=profiles)

@app.route('/upload_profile_pic', methods=['POST'])
@login_required
def upload_profile_pic():
    if 'profile_pic' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('view_profile'))
    
    file = request.files['profile_pic']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('view_profile'))
    
    if file and allowed_file(file.filename):
        # Create a unique filename
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"user_{current_user.id}_{secrets.token_hex(8)}.{ext}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        
        # Save and resize the image
        img = Image.open(file)
        
        # Maintain aspect ratio but ensure it's not too large
        max_size = (500, 500)
        img.thumbnail(max_size)
        
        # Create a square image by cropping from center
        width, height = img.size
        if width != height:
            # Determine the shorter side
            min_side = min(width, height)
            # Calculate cropping points
            left = (width - min_side) // 2
            top = (height - min_side) // 2
            right = left + min_side
            bottom = top + min_side
            # Crop the image
            img = img.crop((left, top, right, bottom))
        
        # Resize to final size
        img = img.resize((200, 200))
        
        # Save the image
        img.save(filepath)
        
        # Delete old profile pic if it's not the default
        if current_user.profile_pic != 'default.jpg':
            try:
                old_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_pic)
                if os.path.exists(old_pic_path):
                    os.remove(old_pic_path)
            except Exception as e:
                app.logger.error(f"Error deleting old profile pic: {str(e)}")
        
        # Update user profile pic in database
        current_user.profile_pic = new_filename
        db.session.commit()
        
        flash('Profile picture updated successfully', 'success')
        return redirect(url_for('view_profile'))
    
    flash('Invalid file type. Allowed types: png, jpg, jpeg, gif', 'error')
    return redirect(url_for('view_profile'))


# route for care profiles page
@app.route('/care_profiles', methods=['GET', 'POST'])
@login_required
def care_profiles():
    # Get existing profiles
    profiles = CareProfile.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        # Check if user has reached the profile limit (3)
        if len(profiles) >= 3:
            flash('You have reached the maximum number of care profiles (3). Please upgrade your subscription to add more profiles.', 'warning')
            return redirect(url_for('care_profiles'))
        
            
        care_recipient = request.form['care_recipient']
        relationship = request.form['relationship']

        new_profile = CareProfile(
            care_recipient=care_recipient,
            relationship=relationship,
            user_id=current_user.id
        )

        db.session.add(new_profile)
        db.session.commit()
        
        # Automatically set this as the active profile
        session['active_profile_id'] = new_profile.id
        return redirect(url_for('dashboard'))

    fullname = current_user.fullname
    initials = get_initials(fullname)
    return render_template('care_profiles.html', profiles=profiles, fullname=fullname, initials=initials)

# route for the profile edit page
@app.route('/edit_profile/<int:profile_id>', methods=['GET', 'POST'])
@login_required
def edit_profile(profile_id):
    # Get the profile to edit
    profile = CareProfile.query.filter_by(id=profile_id, user_id=current_user.id).first_or_404()
    
    # Get all profiles for the sidebar
    profiles = CareProfile.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        # Update the profile with new data
        profile.care_recipient = request.form.get('care_recipient')
        profile.relationship = request.form.get('relationship')
        
        db.session.commit()
        return redirect(url_for('care_profiles'))
    
    # For GET requests, show the edit form
    fullname = current_user.fullname
    initials = get_initials(fullname)
    return render_template('edit_profile.html', profile=profile, profiles=profiles, fullname=fullname, initials=initials)

# route for the delete profile page
@app.route('/delete_profile/<int:profile_id>', methods=['POST'])
@login_required
def delete_profile(profile_id):
    # Get the profile to delete
    profile = CareProfile.query.filter_by(id=profile_id, user_id=current_user.id).first_or_404()
    
    # If this is the active profile, clear the active profile from session
    if session.get('active_profile_id') == profile_id:
        session.pop('active_profile_id', None)
    
    # Delete the profile
    db.session.delete(profile)
    db.session.commit()
    
    return redirect(url_for('care_profiles'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    # Get all profiles for the sidebar
    profiles = CareProfile.query.filter_by(user_id=current_user.id).all()
    has_profiles = len(profiles) > 0
    
    # Get active profile if one is selected
    profile_id = session.get('active_profile_id')
    active_profile = None
    
    if profile_id:
        active_profile = CareProfile.query.get(profile_id)
    
    # Get today's date
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Fetch todos for today
    if active_profile:
        todos = Todo.query.filter_by(
            user_id=current_user.id,
            profile_id=active_profile.id,
            date=today
        ).limit(3).all()
    else:
        todos = Todo.query.filter_by(
            user_id=current_user.id,
            date=today
        ).limit(3).all()
    
    # Fetch medications for today
    if active_profile:
        medications = Medication.query.filter_by(
            user_id=current_user.id,
            profile_id=active_profile.id
        ).limit(3).all()
    else:
        medications = Medication.query.filter_by(
            user_id=current_user.id
        ).limit(3).all()
    
    # Filter medications that should be taken today
    today_medications = []
    for med in medications:
        start_date = med.start_date
        end_date = med.end_date
        if start_date <= today <= end_date:
            today_medications.append(med)
    
    # Fetch recent health records
    if active_profile:
        health_records = HealthRecord.query.filter_by(
            user_id=current_user.id,
            profile_id=active_profile.id
        ).order_by(HealthRecord.timestamp.desc()).limit(3).all()
    else:
        health_records = HealthRecord.query.filter_by(
            user_id=current_user.id
        ).order_by(HealthRecord.timestamp.desc()).limit(3).all()
    
    # Group health records by category
    vital_signs = [r for r in health_records if r.category == 'vital-signs']
    biometrics = [r for r in health_records if r.category == 'biometrics']
    medical_notes = [r for r in health_records if r.category == 'medical-notes']
    
    # Combine and limit to most recent 2
    combined_records = (vital_signs + biometrics)[:2]
    
    fullname = current_user.fullname
    initials = get_initials(fullname)
    image_file = url_for('static', filename='uploads/profile_pics/' + current_user.profile_pic)
    
    return render_template('dashboard.html', 
                          fullname=fullname, 
                          initials=initials, 
                          profiles=profiles, 
                          active_profile=active_profile,
                          todos=todos,
                          medications=today_medications,
                          health_records=combined_records,
                          today=today,
                          image_file=image_file,
                          has_profiles=has_profiles)

@app.route('/todo', methods=['GET', 'POST'])
@login_required
def todo():
    # Your existing todo route code
    profiles = CareProfile.query.filter_by(user_id=current_user.id).all()
    has_profiles = len(profiles) > 0
    
    profile_id = session.get('active_profile_id')
    active_profile = None
    
    if profile_id:
        active_profile = CareProfile.query.get(profile_id)
    
    fullname = current_user.fullname
    initials = get_initials(fullname)
    image_file = url_for('static', filename='uploads/profile_pics/' + current_user.profile_pic)
    return render_template('todo.html', 
                          fullname=fullname, 
                          initials=initials, 
                          profiles=profiles, 
                          active_profile=active_profile, 
                          image_file=image_file,
                          has_profiles=has_profiles)
#route for medications page
@app.route('/medications', methods=['GET'])
@login_required
def medications():
    # Get all profiles for the sidebar
    profiles = CareProfile.query.filter_by(user_id=current_user.id).all()
    has_profiles = len(profiles) > 0
    
    # Get active profile if one is selected
    profile_id = session.get('active_profile_id')
    active_profile = None
    
    if profile_id:
        active_profile = CareProfile.query.get(profile_id)
    
    fullname = current_user.fullname
    initials = get_initials(fullname)
    image_file = url_for('static', filename='uploads/profile_pics/' + current_user.profile_pic)
    return render_template('medications.html', 
                          fullname=fullname, 
                          initials=initials, 
                          profiles=profiles, 
                          active_profile=active_profile, 
                          image_file=image_file,
                          has_profiles=has_profiles)

#route for health records page
@app.route('/health_records', methods=['GET', 'POST'])
@login_required
def health_records():
    # Get all profiles for the sidebar
    profiles = CareProfile.query.filter_by(user_id=current_user.id).all()
    has_profiles = len(profiles) > 0
    
    # Get active profile if one is selected
    profile_id = session.get('active_profile_id')
    active_profile = None
    
    if profile_id:
        active_profile = CareProfile.query.get(profile_id)
    
    fullname = current_user.fullname
    initials = get_initials(fullname)
    image_file = url_for('static', filename='uploads/profile_pics/' + current_user.profile_pic)
    return render_template('health_records.html', 
                          fullname=fullname, 
                          initials=initials, 
                          profiles=profiles, 
                          active_profile=active_profile, 
                          image_file=image_file,
                          has_profiles=has_profiles)

@app.route('/switch_profile/<int:profile_id>', methods=['POST'])
@login_required
def switch_profile(profile_id):

    referrer = request.referrer
    
    selected_profile = CareProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
    if selected_profile:
        session['active_profile_id'] = profile_id
    
    if referrer:
        if 'todo' in referrer:
            return redirect(url_for('todo'))  
        elif 'medications' in referrer:
            return redirect(url_for('medications')) 
        elif 'view_profile' in referrer:
            return redirect(url_for('view_profile'))
        elif 'health_records' in referrer:
            return redirect(url_for('health_records'))
        
    return redirect(url_for('dashboard'))

# ----------------------------------------------------API Routes for Medications

# Get all medications for the current active profile
@app.route('/api/medications', methods=['GET'])
@login_required
def get_medications():

    profiles = CareProfile.query.filter_by(user_id=current_user.id).all()
    if not profiles:
        return jsonify({'error': 'Please create a care profile first to manage medications.'}), 400
    
    profile_id = session.get('active_profile_id')
    if not profile_id:
        return jsonify({'error': 'No active care profile selected. Data will be erased when refreshed.'}), 400
    
    # Verify the profile belongs to the current user
    profile = CareProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    medications = Medication.query.filter_by(profile_id=profile_id).all()
    return jsonify({
        'medications': [med.to_dict() for med in medications]
    })

# Add a new medication
@app.route('/api/medications', methods=['POST'])
@login_required
def add_medication():
    profile_id = session.get('active_profile_id')
    
    if not profile_id:
        return jsonify({'error': 'No active care profile selected. Data will be erased when refreshed.'}), 400
    
    # Verify the profile belongs to the current user
    profile = CareProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
    
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    # Check if user has reached the medication limit (3 for free users)
    medication_count = Medication.query.filter_by(profile_id=profile_id).count()
    if medication_count >= 3:
        return jsonify({'error': 'You have reached the maximum number of medications (3). Please upgrade to premium.'}), 403
    
    data = request.json
    
    try:
        # Convert string dates to datetime objects
        start_date = datetime.strptime(data['startDate'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['endDate'], '%Y-%m-%d').date()
        
        new_medication = Medication(
            name=data['name'],
            dosage=data.get('dosage', ''),
            instructions=data.get('instructions', ''),
            dosage_type=data['dosageType'],
            start_date=start_date,
            end_date=end_date,
            time=data['time'],
            user_id=current_user.id,
            profile_id=profile_id
        )
        
        db.session.add(new_medication)
        db.session.commit()
        
        return jsonify({
            'message': 'Medication added successfully',
            'medication': new_medication.to_dict()
        })
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400

# Update an existing medication
@app.route('/api/medications/<int:medication_id>', methods=['PUT'])
@login_required
def update_medication(medication_id):
    # Find the medication and verify it belongs to the current user
    medication = Medication.query.filter_by(id=medication_id, user_id=current_user.id).first()
    
    if not medication:
        return jsonify({'error': 'Medication not found'}), 404
    
    data = request.json
    
    try:
        # Update medication fields
        if 'name' in data:
            medication.name = data['name']
        if 'dosage' in data:
            medication.dosage = data['dosage']
        if 'instructions' in data:
            medication.instructions = data['instructions']
        if 'dosageType' in data:
            medication.dosage_type = data['dosageType']
        if 'startDate' in data:
            medication.start_date = datetime.strptime(data['startDate'], '%Y-%m-%d').date()
        if 'endDate' in data:
            medication.end_date = datetime.strptime(data['endDate'], '%Y-%m-%d').date()
        if 'time' in data:
            medication.time = data['time']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Medication updated successfully',
            'medication': medication.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400

# Delete a medication
@app.route('/api/medications/<int:medication_id>', methods=['DELETE'])
@login_required
def delete_medication(medication_id):
    # Find the medication and verify it belongs to the current user
    medication = Medication.query.filter_by(id=medication_id, user_id=current_user.id).first()
    
    if not medication:
        return jsonify({'error': 'Medication not found'}), 404
    
    db.session.delete(medication)
    db.session.commit()
    
    return jsonify({'message': 'Medication deleted successfully'})

# --------------------------------------------------API Routes for Medication History

# Get medication history for the current active profile
@app.route('/api/medication-history', methods=['GET'])
@login_required
def get_medication_history():
    profile_id = session.get('active_profile_id')
    
    if not profile_id:
        return jsonify({'error': 'No active profile selected'}), 400
    
    # Get all medications for this profile
    medications = Medication.query.filter_by(profile_id=profile_id, user_id=current_user.id).all()
    medication_ids = [med.id for med in medications]
    
    # Get history for these medications
    history = MedicationHistory.query.filter(
        MedicationHistory.medication_id.in_(medication_ids),
        MedicationHistory.user_id == current_user.id
    ).order_by(MedicationHistory.date.desc(), MedicationHistory.time).all()
    
    return jsonify({
        'history': [item.to_dict() for item in history]
    })

# Add or update medication history (mark as taken or skipped)
@app.route('/api/medication-history', methods=['POST'])
@login_required
def add_medication_history():
    data = request.json
    
    try:
        medication_id = data['medicationId']
        status = data['status']
        date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Verify the medication belongs to the current user
        medication = Medication.query.filter_by(id=medication_id, user_id=current_user.id).first()
        
        if not medication:
            return jsonify({'error': 'Medication not found'}), 404
        
        # Convert string date to datetime object
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Check if there's already a history entry for this medication on this date
        existing_history = MedicationHistory.query.filter_by(
            medication_id=medication_id,
            user_id=current_user.id,
            date=date
        ).first()
        
        if existing_history:
            # Update existing history
            existing_history.status = status
            existing_history.updated_at = datetime.utcnow()
        else:
            # Create new history entry
            new_history = MedicationHistory(
                medication_id=medication_id,
                user_id=current_user.id,
                date=date,
                time=medication.time,
                status=status
            )
            db.session.add(new_history)
        
        db.session.commit()
        
        return jsonify({'message': 'Medication history updated successfully'})
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400

# Delete medication history entry
@app.route('/api/medication-history/<int:history_id>', methods=['DELETE'])
@login_required
def delete_medication_history(history_id):
    # Find the history entry and verify it belongs to the current user
    history = MedicationHistory.query.filter_by(id=history_id, user_id=current_user.id).first()
    
    if not history:
        return jsonify({'error': 'History entry not found'}), 404
    
    db.session.delete(history)
    db.session.commit()
    
    return jsonify({'message': 'History entry deleted successfully'})

# -------------------------------------------------- API Routes for Todos

@app.route('/api/todos', methods=['GET'])
@login_required
def get_todos():
    try:
        # Check if an active profile is selected
        profiles = CareProfile.query.filter_by(user_id=current_user.id).all()
        if not profiles:
            return jsonify({'error': 'Please create a care profile first to manage todos.'}), 400
        
        profile_id = session.get('active_profile_id')
        if not profile_id:
            return jsonify({'error': 'No active care profile selected. Data will be erased when refreshed.'}), 400
            
        # Get current date
        today = datetime.now().date()
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        # Get todos for the current user and profile
        todos_query = Todo.query.filter_by(user_id=current_user.id, profile_id=profile_id)
        
        # Get all todos
        all_todos = todos_query.all()
        
        # Categorize todos
        today_todos = []
        tomorrow_todos = []
        upcoming_todos = []
        
        for todo in all_todos:
            if todo.date == today:
                today_todos.append(todo.to_dict())
            elif todo.date == tomorrow:
                tomorrow_todos.append(todo.to_dict())
            elif todo.date > tomorrow:
                upcoming_todos.append(todo.to_dict())
        
        return jsonify({
            'today': today_todos,
            'tomorrow': tomorrow_todos,
            'upcoming': upcoming_todos
        })
    except Exception as e:
        app.logger.error(f"Error in get_todos: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos', methods=['POST'])
@login_required
def add_todo():
    try:
        # Check if an active profile is selected
        profile_id = session.get('active_profile_id')
        if not profile_id:
            return jsonify({'error': 'No active care profile selected. Data will be erased when refreshed.'}), 400
            
        # Check if user has reached the todo limit (5 for free users)
        todo_count = Todo.query.filter_by(user_id=current_user.id, profile_id=profile_id).count()
        if todo_count >= 5:
            return jsonify({'error': 'You have reached the maximum number of todos (5). Please upgrade to premium.'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Convert string date to datetime object
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        new_todo = Todo(
            text=data['text'],
            date=date,
            completed=data.get('completed', False),
            user_id=current_user.id,
            profile_id=profile_id
        )
        
        db.session.add(new_todo)
        db.session.commit()
        
        return jsonify({
            'message': 'Todo added successfully',
            'todo': new_todo.to_dict()
        })
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Error in add_todo: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
@login_required
def update_todo(todo_id):
    try:
        # Find the todo and verify it belongs to the current user
        todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
        
        if not todo:
            return jsonify({'error': 'Todo not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        
        # Update todo fields
        if 'text' in data:
            todo.text = data['text']
        if 'date' in data:
            todo.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'completed' in data:
            todo.completed = data['completed']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Todo updated successfully',
            'todo': todo.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Error in update_todo: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
@login_required
def delete_todo(todo_id):
    try:
        # Find the todo and verify it belongs to the current user
        todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
        
        if not todo:
            return jsonify({'error': 'Todo not found'}), 404
        
        db.session.delete(todo)
        db.session.commit()
        
        return jsonify({'message': 'Todo deleted successfully'})
    except Exception as e:
        app.logger.error(f"Error in delete_todo: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# ----------------------------------------------------- API Routes for Health Records

@app.route('/api/health-records', methods=['GET'])
@login_required
def get_health_records():
    try:
        profiles = CareProfile.query.filter_by(user_id=current_user.id).all()
        if not profiles:
            return jsonify({'error': 'Please create a care profile first to manage medications.'}), 400
        # Check if an active profile is selected
        profile_id = session.get('active_profile_id')
        if not profile_id:
            return jsonify({'error': 'No active care profile selected. Data will be erased when refreshed.'}), 400
            
        # Get health records for the current user and profile
        records_query = HealthRecord.query.filter_by(user_id=current_user.id, profile_id=profile_id)
        
        # Get all records sorted by timestamp (newest first)
        all_records = records_query.order_by(HealthRecord.timestamp.desc()).all()
        
        return jsonify([record.to_dict() for record in all_records])
    
    except Exception as e:
        app.logger.error(f"Error in get_health_records: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/health-records', methods=['POST'])
@login_required
def add_health_record():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        profile_id = session.get('active_profile_id')
        
        # Check if an active profile is selected
        if not profile_id:
            return jsonify({'error': 'No active care profile selected. Data will be erased when refreshed.'}), 400
        
        # Check if user has reached the health record limit (3 for free users)
        # Count unique types for vital signs and biometrics for this profile
        unique_vital_signs = db.session.query(HealthRecord.type).filter(
            HealthRecord.user_id == current_user.id,
            HealthRecord.profile_id == profile_id,
            HealthRecord.category == 'vital-signs'
        ).distinct().count()
        
        unique_biometrics = db.session.query(HealthRecord.type).filter(
            HealthRecord.user_id == current_user.id,
            HealthRecord.profile_id == profile_id,
            HealthRecord.category == 'biometrics'
        ).distinct().count()
        
        medical_notes_count = HealthRecord.query.filter_by(
            user_id=current_user.id,
            profile_id=profile_id,
            category='medical-notes'
        ).count()
        
        total_record_types = unique_vital_signs + unique_biometrics + (1 if medical_notes_count > 0 else 0)
        if total_record_types >= 3:
            return jsonify({'error': 'You have reached the maximum number of health record types (3). Please upgrade to premium.'}), 403
        
        # Convert string date to datetime object
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        new_record = HealthRecord(
            category=data['category'],
            date=date,
            time=data['time'],
            timestamp=data['timestamp'],
            user_id=current_user.id,
            profile_id=profile_id
        )
        
        # Add category-specific fields
        if data['category'] in ['vital-signs', 'biometrics']:
            new_record.type = data['type']
            new_record.value = data['value']
            
            if data['type'] == 'blood-pressure':
                new_record.systolic = data['systolic']
                new_record.diastolic = data['diastolic']
                
        elif data['category'] == 'medical-notes':
            new_record.subject = data['subject']
            new_record.body = data.get('body', '')
        
        db.session.add(new_record)
        db.session.commit()
        
        return jsonify({
            'message': 'Health record added successfully',
            'id': new_record.id
        })
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Error in add_health_record: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/health-records/<int:record_id>', methods=['PUT'])
@login_required
def update_health_record(record_id):
    try:
        # Find the record and verify it belongs to the current user
        record = HealthRecord.query.filter_by(id=record_id, user_id=current_user.id).first()
        
        if not record:
            return jsonify({'error': 'Health record not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update common fields
        if 'date' in data:
            record.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'time' in data:
            record.time = data['time']
        if 'timestamp' in data:
            record.timestamp = data['timestamp']
        
        # Update category-specific fields
        if record.category in ['vital-signs', 'biometrics']:
            if 'value' in data:
                record.value = data['value']
            
            if record.type == 'blood-pressure':
                if 'systolic' in data:
                    record.systolic = data['systolic']
                if 'diastolic' in data:
                    record.diastolic = data['diastolic']
                
        elif record.category == 'medical-notes':
            if 'subject' in data:
                record.subject = data['subject']
            if 'body' in data:
                record.body = data['body']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Health record updated successfully',
            'record': record.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Error in update_health_record: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/health-records/<int:record_id>', methods=['DELETE'])
@login_required
def delete_health_record(record_id):
    try:
        # Find the record and verify it belongs to the current user
        record = HealthRecord.query.filter_by(id=record_id, user_id=current_user.id).first()
        
        if not record:
            return jsonify({'error': 'Health record not found'}), 404
        
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({'message': 'Health record deleted successfully'})
    except Exception as e:
        app.logger.error(f"Error in delete_health_record: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.context_processor
def utility_processor():
    return dict(get_initials=get_initials)


def get_initials(name):
    parts = name.strip().split()
    initials = ''.join([p[0].upper() for p in parts if p])
    return initials

# Add this at the bottom of your file, before if __name__ == '__main__'
def init_app():
    """Initialize application resources"""
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    create_default_profile_pic()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_app()
    app.run(debug=True)
