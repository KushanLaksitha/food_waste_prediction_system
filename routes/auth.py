from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, UserPreference
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('prediction.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        
        if not email or '@' not in email:
            errors.append('Please provide a valid email address.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html')
        
        # Create new user
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            # Create default preferences
            preferences = UserPreference(user_id=new_user.id)
            db.session.add(preferences)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            print(f"Registration error: {e}")
    
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('prediction.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'
        
        if not username or not password:
            flash('Please provide both username and password.', 'warning')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('prediction.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
    return render_template('profile.html', preferences=preferences)


@auth_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    email = request.form.get('email', '').strip().lower()
    
    if not email or '@' not in email:
        flash('Please provide a valid email address.', 'warning')
        return redirect(url_for('auth.profile'))
    
    # Check if email is already taken by another user
    existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
    if existing_user:
        flash('Email address is already in use.', 'danger')
        return redirect(url_for('auth.profile'))
    
    try:
        current_user.email = email
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating your profile.', 'danger')
        print(f"Profile update error: {e}")
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('auth.profile'))
    
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'warning')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'warning')
        return redirect(url_for('auth.profile'))
    
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while changing your password.', 'danger')
        print(f"Password change error: {e}")
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/update_preferences', methods=['POST'])
@login_required
def update_preferences():
    alert_frequency = request.form.get('alert_frequency', 'Daily')
    email_notifications = request.form.get('email_notifications') == 'on'
    waste_threshold = request.form.get('waste_threshold', 50.0)
    
    try:
        waste_threshold = float(waste_threshold)
        if waste_threshold < 0 or waste_threshold > 100:
            raise ValueError("Threshold must be between 0 and 100")
    except ValueError:
        flash('Invalid waste threshold value.', 'warning')
        return redirect(url_for('auth.profile'))
    
    preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
    
    if not preferences:
        preferences = UserPreference(user_id=current_user.id)
        db.session.add(preferences)
    
    try:
        preferences.alert_frequency = alert_frequency
        preferences.email_notifications = email_notifications
        preferences.waste_threshold = waste_threshold
        db.session.commit()
        flash('Preferences updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating preferences.', 'danger')
        print(f"Preferences update error: {e}")
    
    return redirect(url_for('auth.profile'))