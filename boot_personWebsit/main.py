from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Column
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_ckeditor import CKEditor, CKEditorField
from datetime import datetime
import requests
from post import Post
import smtplib
import os
from forms import RegisterForm, CreatePostForm, LoginForm
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

##Intializer
current_date = datetime.now()
login_manager = LoginManager()

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
ckeditor = CKEditor(app)
login_manager.init_app(app)

#Create database 
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class = Base)
db.init_app(app)

## Class or configure table for blog post 
class BlogPost(db.Model):
    id = Column(Integer, primary_key = True)
    title = Column(String(250), unique = True, nullable = False)
    subtitle = Column(String(250), nullable = False)
    date = Column(String(250), nullable = False)
    body = Column(Text, nullable=False)
    author = Column(String(250), nullable = False)
    img_url = Column(String(250), nullable = False)

# CREATE TABLE IN DB
class User(UserMixin, db.Model):
    ''' User database that holds values like id, email, password, name '''
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

url_blog_post = f"https://api.npoint.io/c790b4d5cab58020d391"
response = requests.get(url_blog_post)
json_response = response.json()
email = "prajwaljungthapa@gmail.com"
password = os.environ.get("PASS")

def create_post_from_db():
    ''' Creates the post list from the item in the database '''
    post_object = []
    all_post = db.session.execute(db.select(BlogPost).order_by(BlogPost.id)).scalars().all()
    for i in range(len(all_post)):
        post = Post(all_post[i].id, all_post[i].title, all_post[i].subtitle, all_post[i].body)
        post_object.append(post)
    return post_object

@app.route('/')
def home():
    post_object = create_post_from_db()    
    return render_template("index.html", json = post_object, logged_in = current_user.is_authenticated)

@app.route('/contact', methods=["POST", "GET"])
def contact():
    if request.method == "POST":
        data = request.form
        send_email(data["name"], data["email"], data["phone"], data["message"])
        return render_template("contact.html", msg_sent = True)
    return render_template("contact.html", msg_sent = False, logged_in = current_user.is_authenticated)
    
def send_email(name , email, phone, message):
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
    try:
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=email, password=password)
            connection.sendmail(email, email, email_message)
        print("Password", password)
        print("Email sent successfully.")
    except Exception as e:
        print("Password", password)
        print(f"Error sending email: {e}")

@app.route('/about')
def about():
    return render_template("about.html", logged_in = current_user.is_authenticated)

@app.route("/post_read/<int:index>")
def read_body(index):
    description = None
    request_post = db.get_or_404(BlogPost, index)
    return render_template("post.html", read = request_post, logged_in = current_user.is_authenticated)

@app.route("/new-post", methods = ["POST", "GET"])
def make_new_post():
    ''' Used to create a new post and add it to the database '''
    
    form = CreatePostForm()
    if request.method == "POST":
        new_blog = BlogPost(title = request.form['title'], subtitle = request.form['subtitle'], 
                            date = current_date.strftime("%B %d %Y"), body = request.form['body'], author = request.form['name'], img_url = request.form['url'])
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("make-post.html", form = form, edit = False , logged_in = current_user.is_authenticated)

@app.route("/edit-post/<post_id>", methods=["POST", "GET"])
def edit_post(post_id):
    ''' Method used to edit the post in the database '''
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title = post.title,
        subtitle = post.subtitle,
        url = post.img_url, 
        name = post.author, 
        body = post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.url.data
        post.author = edit_form.name.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("read_body", index = post.id))
    return render_template("make-post.htmlString", edit = True, form = edit_form, logged_in = current_user.is_authenticated)

@app.route("/delete/<int:post_id>", methods=["POST", "GET"])
def delete_post(post_id):
    post = BlogPost.query.get(post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
    return redirect(url_for('home'), logged_in = current_user.is_authenticated)

@app.route("/register", methods=["POST", "GET"])
def register_user():
    ''' Used to register new user by hashing and salting the user password '''
    form = RegisterForm()
    if form.validate_on_submit():
        email = request.form["email"]
        ## Check if the email is already in use
        email_found = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if email_found:
            flash("You've already signed up with that email, log in instead", 'error')
            return redirect(url_for('login'))
        
        hashed_pass = generate_password_hash(
            password = request.form['password'], 
            method = 'pbkdf2:sha256',
            salt_length = 8) ## Hashes the pass with salt len 8
        new_user = User(
            email = email,
            password = hashed_pass,
            name = request.form['name'])
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('home'))    
    return render_template("register.html", form = form, logged_in = current_user.is_authenticated)

@app.route('/login', methods = ['POST', 'GET'])
def login():
    loginform = LoginForm()
    if request.method == 'POST':
        ## Get the user from the database
        email = request.form['email']
        password = request.form['password']
        
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        
        if user:
            ## Check the password 
            if check_password_hash(user.password, password):
                login_user(user)
                flash('Successfully logged in' ,'error')
                return redirect(url_for('home')) 
            else:
                flash('Password incorrect', 'error')
        else:
            flash("The email does not exist, please try again later", 'error')
            
    return render_template("login.html", form = loginform, logged_in = current_user.is_authenticated)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
