import os

import flask
from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from mysql.connector import connect, Error
from config import db_user, db_password
import flask_login
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "amogus"
app.config['SECRET_KEY'] = 'example_key'

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

connection = connect(host="localhost", user=db_user, password=db_password, database="minecraft_repository")
cur = connection.cursor()
print("Connected to DB!")
# cur.execute("SELECT * FROM users")
# print(cur)


class User(flask_login.UserMixin):
    pass


class LoginForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
    submit = SubmitField('Log in')


class RegisterForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired(), Length(min=4, max=20)])
    password_1 = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
    password_2 = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=4), EqualTo("password_1", message="Passwords don't match!")])
    submit = SubmitField('Log in')


@login_manager.user_loader
def user_loader(login):
    res = get_user_id(login)

    if res == -1:
        return

    user = User()
    user.id = res
    return user


# @login_manager.request_loader
# def request_loader(request):
#
#     res = get_user_id(request.form.username.data)
#
#     if res == -1:  # no user found
#         return
#
#     user = User()
#     user.id = res
#     return user


@app.route('/')
@app.route('/index')
def index():
    posts_dict = get_post_tile_data()

    return render_template("index.html", posts=posts_dict)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    if not form.validate_on_submit():
        print("Showing sign in form")
        return render_template('signin.html', form=form)
    print("Trying to log in")
    user_login = form.username.data
    user_id = get_user_id(user_login)
    if user_id == -1:
        return "Bad login, no user found"
    if not check_password_hash(get_hashed_user_password(user_id), form.password.data):
        return "Bad login, password didn't match"
    user = User()
    user.id = user_id
    flask_login.login_user(user)
    return redirect(url_for("make_post"))
    # return redirect('/success')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        return "<h1>" + form.username.data + " " + form.password_1.data + " " + form.password_2.data + "</h1>"
        # return redirect('/success')
    return render_template('signup.html', form=form)


@app.route('/post/<post_id>')
def post(post_id):
    post_data = get_post_data(post_id)

    return render_template('post.html', **post_data)


@app.route('/make_post', methods=['GET', 'POST'])
@flask_login.login_required
def make_post():
    return render_template('makepost.html')


@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    print("Logged out!")
    redirect(url_for("index"))


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized', 401


def get_post_data(post_id):
    cur.execute(f"SELECT * FROM posts WHERE post_id = {post_id}")
    post = cur.fetchall()[0]

    params = dict()
    params["title"] = post[1]

    cur.execute(f"SELECT name FROM users WHERE user_id = {post[2]}")
    params["author_name"] = cur.fetchone()[0]

    params["creation_date"] = post[7]
    params["description"] = post[3]
    params["text_tutorial"] = post[5]
    params["video_tutorial"] = post[6]

    return params


def get_post_tile_data():
    cur.execute("SELECT * FROM posts")
    posts = list()
    for i in cur:
        print(i)
        posts.append(i)

    posts_dict = dict()
    posts_dict["news"] = list()

    for i in posts:
        cur_dict = dict()
        cur_dict["post_id"] = i[0]
        cur_dict["title"] = i[1]
        cur_dict["author_id"] = i[2]
        cur.execute(f"SELECT name FROM users WHERE user_id = {i[2]}")
        cur_dict["author_name"] = cur.fetchone()[0]

        cur_dict["description"] = i[3]
        cur_dict["likes"] = i[4]
        cur_dict["text_tutorial"] = i[5]
        cur_dict["video_tutorial"] = i[6]
        posts_dict["news"].append(cur_dict)

    return posts_dict


def get_user_id(user_login):
    print("Trying to find User Login!")
    cur.execute("SELECT login FROM users")
    logins = cur.fetchall()
    if user_login not in logins:
        print("No user with such login located!")
        return -1
    print("User found! Now searching their ID!")
    cur.execute(f"SELECT user_id FROM users WHERE login = {user_login}")
    user_id = cur.fetchall()[0]
    print(f"{user_login}'s  is", user_id)
    return user_id


def get_hashed_user_password(user_id):
    cur.execute(f"SELECT password FROM users WHERE user_id = {user_id}")
    return cur.fetchall()[0]


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

