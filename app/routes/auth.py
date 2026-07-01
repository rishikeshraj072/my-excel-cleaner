from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            AuthService.register(username, email, password)
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), "danger")
            
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        
        user = AuthService.authenticate(username_or_email, password)
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('main.dashboard'))
        else:
            flash("Invalid username/email or password.", "danger")
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))
