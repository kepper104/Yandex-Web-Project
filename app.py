import os

import mysql.connector
from PIL import Image
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, StopValidation
from mysql.connector import connect
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


class UniqueLogin:
    def __init__(self, message=None):
        self.message = message
        self.field_flags = {"required": True}

    def __call__(self, form, field):
        print("Validating")
        if does_user_exist(field.data):
            message = field.gettext("User with this login already exists")
        else:
            message = self.message

        print("Case 4")
        field.errors[:] = []
        raise StopValidation(message)


class User(flask_login.UserMixin):
    pass


class LoginForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired(), UniqueLogin(), Length(min=4, max=100)])
    name = StringField('Name', validators=[DataRequired(), Length(min=4, max=100)])
    password_1 = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
    password_2 = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=4), EqualTo("password_1", message="Passwords don't match!")])
    submit = SubmitField('Sign Up')


@login_manager.user_loader
def user_loader(login):
    res = get_user_id(login)

    if res == -1:
        return

    user = User()
    user.id = login
    return user


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
    print("User login is", user_login)
    user_id = get_user_id(user_login)
    if user_id == -1:
        return "Error, login or password didn't match"

    hashed_password = get_hashed_user_password(user_id)
    cur_password = form.password.data

    if not check_password_hash(hashed_password, cur_password):
        return "Error, login or password didn't match"

    user = User()
    user.id = user_login
    flask_login.login_user(user)
    print("Logged in as", user_login, "with id", user_id)
    return redirect(url_for("index"))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if not form.validate_on_submit():
        return render_template('signup.html', form=form)
    print("Login:", form.login.data, ". Password:", form.password_1.data)
    hashed_password = generate_password_hash(form.password_1.data)
    res = register_user(form.login.data, form.name.data, hashed_password)
    if not res:
        return "DataBase Error"
    return redirect(url_for("signin"))


@app.route('/post/<post_id>', methods=['GET', 'POST'])
def post(post_id):
    if request.method == "GET":
        post_data = get_post_data(post_id)
        return render_template("post.html", **post_data)
    comment_text = request.form['comment']

    return redirect(f"/post/{post_id}")


@app.route('/make_post', methods=['GET', 'POST'])
@flask_login.login_required
def make_post():
    if request.method == "GET":
        return render_template("make_post.html")
    print(request.form)
    print("FUCK")
    post_id = commit_post(request.form)
    print("REDIRECTING")
    # return redirect(url_for("index"))
    screenshots_n = request.form["screenshots_number"]
    if screenshots_n == 0 or screenshots_n == "" or screenshots_n == " " or screenshots_n == "0":
        create_dummy_screenshot(post_id)
        return redirect(url_for("index"))
    return redirect(url_for("make_post_screenshots", screenshots_number=request.form["screenshots_number"], post_id=post_id))


@app.route('/make_post_screenshots', methods=['GET', 'POST'])
@flask_login.login_required
def make_post_screenshots():
    if request.method == "GET":
        screenshots_n = request.args.get("screenshots_number")
        iterat = list(range(int(screenshots_n)))
        return render_template("make_post_screenshots.html", iterat=iterat)
    print(request.form)
    data = request.files
    print("Data:", data)
    post_id = request.args.get("post_id")
    print("Saving screenshots:")
    print(request.args.get("screenshots_number"))
    for i in range(int(request.args.get("screenshots_number"))):
        print(f"Saving {i}...")
        screen = data[f'screenshot_{i}']
        print("Got screenshot_data")
        commit_screenshot(screen, post_id)
        print(f"Saved {i}")
        # print(screen.read())
    return redirect(url_for("index"))

@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    print("Logged out!")
    return redirect(url_for("index"))


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized', 401


def get_post_data(post_id):
    cur.execute(f"SELECT * FROM posts WHERE post_id = {post_id};")
    post = cur.fetchall()[0]

    params = dict()
    params["title"] = post[1]

    cur.execute(f"SELECT name FROM users WHERE user_id = {post[2]};")
    params["author_name"] = cur.fetchone()[0]

    params["creation_date"] = post[7]
    params["description"] = post[3]
    params["text_tutorial"] = post[5]
    params["video_tutorial"] = post[6]
    cur.execute(f"SELECT picture_id FROM pictures WHERE parent_post_id = {post_id}")
    screenshots = list()
    screenshots_numbers = list()
    for index, i in enumerate(cur):
        if index == 0:
            first_screenshot = f"image_{i[0]}.png"
        else:
            screenshots_numbers.append(i[0])
            screenshots.append(f"image_{i[0]}.png")
    params["first_screenshot"] = first_screenshot
    params["screenshots"] = screenshots
    params["screenshots_numbers"] = screenshots_numbers

    cur.execute(f"""SELECT * FROM comments WHERE parent_post_id = {post_id}""")
    comments = list()
    for index, i in enumerate(cur):
        comment = dict()
        author_id = i[2]
        comment_text = i[3]
        post_date = i[4]
        cur.execute(f"SELECT name FROM users WHERE user_id = {author_id};")
        comment["author_name"] = cur.fetchone()[0]
        comment["comment_text"] = comment_text
        comment["post_date"] = post_date
        comments.append(comment)
    params["comments"] = comments

    return params


def get_post_tile_data():
    cur.execute("SELECT * FROM posts;")
    posts = list()
    for i in cur:
        print(i)
        posts.append(i)

    posts_dict = dict()
    posts_dict["posts"] = list()

    for i in posts:
        cur_dict = dict()
        cur_dict["post_id"] = i[0]
        cur_dict["title"] = i[1]
        cur_dict["author_id"] = i[2]
        cur.execute(f"SELECT name FROM users WHERE user_id = {i[2]};")
        cur_dict["author_name"] = cur.fetchone()[0]

        cur_dict["description"] = i[3]
        cur_dict["likes"] = i[4]
        cur_dict["text_tutorial"] = i[5]
        cur_dict["video_tutorial"] = i[6]
        cur.execute(f"SELECT picture_id FROM pictures WHERE parent_post_id = {i[0]}")
        res = list(cur.fetchall())
        try:
            cur_dict["thumbnail_image"] = "image_" + str(res[0][0]) + ".png"
        except:
            cur_dict["thumbnail_image"] = "image_" + str(res[0]) + ".png"

        print("Thumbnail image:", cur_dict['thumbnail_image'])
        posts_dict["posts"].append(cur_dict)

    return posts_dict


def get_user_id(user_login):
    print("Trying to find user login", user_login)
    cur.execute("SELECT login FROM users")
    logins = cur.fetchall()
    print("Logins are:", logins)

    for i in logins:
        if user_login in i:
            print("User found! Now searching their ID!")
            cur.execute(f"SELECT user_id FROM users WHERE login = '{user_login}';")
            user_id = cur.fetchall()[0][0]
            print(f"{user_login}'s id is", user_id)
            return user_id

    print("No user with such login located!")
    return -1


def get_hashed_user_password(user_id):
    cur.execute(f"SELECT password FROM users WHERE user_id = '{user_id}';")
    res = cur.fetchall()[0][0]
    print(res)
    return res


def register_user(login, name, password):
    try:
        cur.execute(f'INSERT INTO users (login, password, name) VALUES ("{login}", "{password}", "{name}")')
        connection.commit()
        return True
    except mysql.connector.Error as e:
        print(e)
        return False


def does_user_exist(login):
    id = get_user_id(login)
    if id == -1:
        return False
    return True


def commit_post(form_data):
    print("I AM GOING TO DIE")
    cont_name = form_data['contraption_name']
    cont_description = form_data['description']
    cont_category = form_data['category']
    cont_text_tutorial = form_data['text_tutorial']
    cont_video_tutorial = form_data['video_tutorial'].strip()
    cont_author_id = get_user_id(flask_login.current_user.id)

    print("User: ", cont_author_id)
    # print(cont_screenshot)
    # if cont_screenshot is not None:

    print(repr(cont_text_tutorial))

    cur.execute(f"""INSERT INTO posts (title, author_id, description, text_tutorial, video_tutorial, category)
                    VALUES ("{cont_name}", {cont_author_id}, "{cont_description}", "{cont_text_tutorial}", "{cont_video_tutorial}", "{cont_category}")""")

    connection.commit()
    print("Post posted!")
    print("Post's id:", cur.lastrowid)
    return cur.lastrowid


def commit_screenshot(screenshot, post_id):
    print("Executing...", post_id, screenshot)
    cur.execute(f"""INSERT INTO pictures (parent_post_id)
                    VALUES ({post_id})""")
    connection.commit()
    print("Committed")
    picture_id = cur.lastrowid
    print(f"Saving picture with id {picture_id}")
    screenshot.save(f"./static/pictures/image_{picture_id}.png")
    print(f"Saved image_{picture_id}.png")


def create_dummy_screenshot(post_id):
    print("Executing...", post_id)
    cur.execute(f"""INSERT INTO pictures (parent_post_id)
                        VALUES ({post_id})""")
    connection.commit()
    print("Committed")
    picture_id = cur.lastrowid
    print(f"Saving picture with id {picture_id}")
    f = Image.open("./static/pictures/default_image.jpeg")
    f.save(f"./static/pictures/image_{picture_id}.png")
    print(f"Saved image_{picture_id}.png")

def commit_comment(comment_text, post_id):
    author_id = get_user_id(flask_login.current_user.id)
    cur.execute(f"""INSERT INTO comments(parent_post_id, author_id, text)
                    VALUES ({post_id}, {author_id}, "{comment_text}")""")
    connection.commit()
    print("Comment posted!")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

