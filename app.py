import os

from flask import Flask, render_template, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from mysql.connector import connect, Error
from config import db_user, db_password

# from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'example_key'

connection = connect(host="localhost", user=db_user, password=db_password, database="minecraft_repository")
cur = connection.cursor()
print("Connected to DB!")
# cur.execute("SELECT * FROM users")
# print(cur)

class LoginForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
    submit = SubmitField('Log in')


class RegisterForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired(), Length(min=4, max=20)])
    password_1 = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
    password_2 = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=4), EqualTo("password_1", message="Passwords don't match!")])
    submit = SubmitField('Log in')


@app.route('/')
@app.route('/index')
def index():
    cur.execute("SELECT * FROM posts")
    posts = list()
    for i in cur:
        print(i)
        posts.append(i)
    # print(posts)
    # posts = [(2, 'Greatest contraption of all time!', 1, 'I spent 80 years on this', None, None, None)]
    posts_dict = dict()
    for i in posts:
        posts_dict[i[0]] = dict()
        posts_dict[i[0]]["post_id"] = i[0]
        posts_dict[i[0]]["title"] = i[1]
        posts_dict[i[0]]["author_id"] = i[2]
        cur.execute(f"SELECT name FROM users WHERE user_id = {i[2]}")
        posts_dict[i[0]]["author_name"] = cur.fetchone()

        posts_dict[i[0]]["description"] = i[3]
        posts_dict[i[0]]["likes"] = i[4]
        posts_dict[i[0]]["text_tutorial"] = i[5]
        posts_dict[i[0]]["video_tutorial"] = i[6]
    print(posts_dict)

    return render_template("index.html", posts=posts_dict)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    if form.validate_on_submit():
        return form.username.data + " " + form.password.data
        # return redirect('/success')
    return render_template('signin.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        return "<h1>" + form.username.data + " " + form.password_1.data + " " + form.password_2.data + "</h1>"
        # return redirect('/success')
    return render_template('signup.html', form=form)


@app.route('/post/<post_id>')
def post(post_id):
    return render_template('post.html')


@app.route('/make_post', methods=['GET', 'POST'])
def make_post():
    # if
    return render_template('makepost.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)