from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from models import connect_db, db, User, Feedback
from forms import UserForm, LoginForm, FeedbackForm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///feedback_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'abc123'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)

@app.route('/')
def root_route():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """Allow users to register"""
    form = UserForm()
    if form.validate_on_submit():
        new_user = User.register(
            username=form.username.data,
            pwd=form.password.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
        )
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already in use.', 'danger')
            return redirect('/register')
        session['current_user'] = new_user.username
        return redirect(f'/users/{new_user.username}')
    else:
        return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """Allows registered users to log in"""
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if User.authenticate(username=username, pwd=password):
            flash(f'Welcome back, {username}!', 'success')
            session['current_user'] = username
            return redirect(f'/users/{username}')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout_user():
    """Logs user out and redirects home"""
    session.pop('current_user')
    return redirect('/login')

@app.route('/users/<username>')
def show_user_details(username):
    if 'current_user' in session:
        user = User.query.get(username)
        if username != session['current_user']:
            flash('You cannot access this page.', 'danger')
            return redirect(f'/users/{user.username}')
        else:
            return render_template('user_details.html', user=user)
    else:
        flash('You must log in to view this page.', 'danger')
        return redirect('/login')

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """allows users to delete their account"""
    if 'current_user' not in session:
        flash('You must log in first to perform this action.', 'danger')
        return redirect('/login')
    elif session['current_user'] != username:
        flash('You are not allowed to delete someone else''s account')
        return redirect(f"/users/{session['current_user']}")
    else:
        user = User.query.get(username)
        db.session.delete(user)
        db.session.commit()
        flash('Successfully deleted your account.', 'success')
        return redirect('/login')

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    """Allows validated user to create new feedback"""
    form = FeedbackForm()
    if form.validate_on_submit():
        if 'current_user' not in session:
            flash('You must log in to perform this action.', 'danger')
            return redirect('/login')
        elif session['current_user'] != username:
            flash('You cannot perform this action.', 'danger')
            return redirect(f'/users/{username}')
        else:
            title = form.title.data
            content = form.content.data
            new_feedback = Feedback(title=title, content=content, username=session['current_user'])
            db.session.add(new_feedback)
            db.session.commit()
            flash('Thank you for your feedback!', 'success')
            return redirect(f'/users/{username}')
    else:
        return render_template('feedback.html', form=form)

@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def edit_feedback(feedback_id):
    """Allows validated user to edit their feedback"""
    feedback = Feedback.query.get_or_404(feedback_id)
    form = FeedbackForm(obj=feedback)
    if form.validate_on_submit():
        if 'current_user' not in session:
            flash('You must log in to perform this action.', 'danger')
            return redirect('/login')
        elif session['current_user'] != feedback.user.username:
            flash('You cannot perform this action.', 'danger')
            return redirect(f'/users/{feedback.user.username}')
        else:
            feedback.title = form.title.data
            feedback.content = form.content.data
            db.session.add(feedback)
            db.session.commit()
            flash('Feedback updated!', 'success')
            return redirect(f'/users/{feedback.user.username}')
    else:
        return render_template('feedback.html', form=form)

@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    """Allows validated user to delete their feedback"""
    feedback = Feedback.query.get_or_404(feedback_id)
    if 'current_user' not in session:
        flash('You must log in first to perform this action.', 'danger')
        return redirect('/login')
    elif session['current_user'] != feedback.user.username:
        flash('You are not allowed to delete someone else''s feedback')
        username = session['current_user']
        return redirect(f'/users/{username}')
    else:
        username = session['current_user']
        db.session.delete(feedback)
        db.session.commit()
        flash('Successfully deleted your feedback.', 'success')
        return redirect(f'/users/{username}')

@app.route('/secret')
def show_secret():
    """shows a secret to a validated user"""
    if 'current_user' in session:
        return render_template('secret.html')
    else:
        flash('You must log in to view this page.', 'danger')
        return redirect('/login')