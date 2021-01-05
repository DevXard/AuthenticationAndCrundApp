from flask import Flask, render_template, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from models import User, db, connect_db, Feedback
from forms import UserRegisterForm, UserLoginForm, NewFeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///feedback_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "dsafaw43f436y3"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)

toolbar = DebugToolbarExtension


@app.route('/')
def index():
    return redirect('/register')

@app.route('/secret')
def secret():
    if 'user_id' not in session:
        flash('You have to login/register first', 'warning')
        return redirect('/login')
    return render_template('secret.html')

@app.route('/register', methods=['POST', 'GET'])
def register_user():
    form = UserRegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        new_user = User.register(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.errors.append("User Alredy exsists")

        session['user_id'] = new_user.id
        flash('Wolcome! You have successfully registered', 'success')
        return redirect(f'/users/{new_user.username}')
    return render_template('register.html', form=form)
 
@app.route('/login', methods=['POST', "GET"])
def login_user():
    form = UserLoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash('Wlcome back', 'success')
            session['user_id'] = user.id
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Invalid Username or Password']
    return render_template('login.html', form=form)

@app.route('/users/<username>')
def profile(username):
    if 'user_id' not in session:
        flash('You have to login/register first', 'warning')
        return redirect('/login')
    user = User.query.filter_by(username=username).first()
    return render_template('profile.html', user=user)

@app.route('/logout')
def login():
    session.pop('user_id')
    flash('Goodby', 'success')
    return redirect('/login')

@app.route('/users/<int:id>/delete', methods=['POST'])
def delete(id):

    if 'user_id' not in session: 
        flash('You have to login/register first', 'warning')
        return redirect('/login')
    user = User.query.get_or_404(id)
    if user.id == session['user_id']:
        session.pop('user_id')
        feeds = Feedback.query.filter_by(username=user.username).delete()
        db.session.delete(user)
        db.session.commit()
        flash('Account deleated')
        return redirect('/')
    else:
        flash('You dont have Permision')
        return redirect('/register')

@app.route('/users/<username>/add', methods=['GET', 'POST'])
def add_new_feedback(username):
    if 'user_id' not in session:
        flash('You have to login/register first', 'warning')
        return redirect('/login')
    form = NewFeedbackForm()
    user = User.query.filter_by(username=username).first()
    
    if form.validate_on_submit():
        title = form.title.data
        feedback = form.feedback.data

        new_feedback = Feedback(title=title, content=feedback, username=username)
        db.session.add(new_feedback)
        db.session.commit()
        return redirect(f'/users/{user.username}')
    return render_template('create_feedback.html', form =form)


@app.route('/feedback/<int:id>/update', methods=['GET', 'POST'])
def update_feedback(id):
    if 'user_id' not in session:
        flash('You have to login/register first', 'warning')
        return redirect('/login')
    form = NewFeedbackForm()
    feedback = Feedback.query.get_or_404(id)
    if form.validate_on_submit():
        title = form.title.data
        content = form.feedback.data

        feedback.title = title
        feedback.content = content
        db.session.commit()
        return redirect(f'/users/{feedback.username}')
    return render_template('update_feedback.html', form = form)

@app.route('/feedback/<int:id>/delete', methods=['POST'])
def delete_feedback(id):
    if 'user_id' not in session:
        flash('You have to login/register first', 'warning')
        return redirect('/login')
    feedback = Feedback.query.get_or_404(id)
    username = feedback.username

    if feedback.user.id == session.get('user_id'):
        db.session.delete(feedback)
        db.session.commit()
        return redirect(f'/users/{username}')