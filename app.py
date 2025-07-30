from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm, WorkoutForm
from models import db, User, Workout
import csv
import io
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).all()
    chart_data = [
        {"date": w.date.strftime('%Y-%m-%d'), "reps": w.reps, "weight": w.weight}
        for w in workouts
    ]
    return render_template('dashboard.html', workouts=workouts, chart_data=chart_data)

@app.route('/log', methods=['GET', 'POST'])
@login_required
def log_workout():
    form = WorkoutForm()
    if form.validate_on_submit():
        workout = Workout(
            user_id=current_user.id,
            exercise=form.exercise.data,
            reps=form.reps.data,
            weight=form.weight.data,
            date=form.date.data
        )
        db.session.add(workout)
        db.session.commit()
        flash('Workout logged!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('log_workout.html', form=form)

@app.route('/export')
@login_required
def export():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Exercise', 'Reps', 'Weight'])

    for w in Workout.query.filter_by(user_id=current_user.id).all():
        writer.writerow([w.date, w.exercise, w.reps, w.weight])

    output.seek(0)
    return send_file(io.BytesIO(output.read().encode()), mimetype='text/csv', as_attachment=True, download_name='workouts.csv')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
