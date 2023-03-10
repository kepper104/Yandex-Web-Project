from flask import Flask, render_template, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'example_key'

class LoginForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')

class RegisterForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired()])
    password_1 = PasswordField('Password', validators=[DataRequired()])
    password_2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Log in')


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    if form.validate_on_submit():
        return "Nice!"
        # return redirect('/success')
    return render_template('signin.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        return "Nice!"
        # return redirect('/success')
    return render_template('signup.html', form=form)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')