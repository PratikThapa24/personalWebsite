from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
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
from forms import RegisterForm, CreatePostForm, LoginForm, CommentForm
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from typing import List
from flask_gravatar import Gravatar

##Intializer
current_date = datetime.now()
login_manager = LoginManager()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("APP_SECRET_KEY")
Bootstrap5(app)
ckeditor = CKEditor(app)
login_manager.init_app(app)

#Create database 
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "SQL")
db = SQLAlchemy(model_class = Base)
db.init_app(app)

# For adding user pictures
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# CREATE TABLE IN DB
class User(UserMixin, db.Model):
    ''' User database that holds values like id, email, password, name '''
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
        
    #The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")

    #Each user has one to many relationship with the comments
    comments = relationship("Comment", back_populates="comment_author")


## Configure table for blog post 
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
        
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")
    
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    ## One to many relationship with child Comment --> Creating a list where we can store Comment object 
    comments = relationship("Comment", back_populates = "parent_post")

## Configure table for Comment
class Comment(db.Model):
    ''' Table for comment contains entries like id and text '''
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key = True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id")) ## "User.id" refers to the user of the table
    comment_author = relationship("User", back_populates = "comments")
    
    text: Mapped[str] = mapped_column(Text, nullable = False)
    
    ## One to many relationship with the parent BlogPost -> Think like creating a list that holds comments
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id")) ## "blog_posts.id" refers to the blog in the table
    parent_post = relationship("BlogPost", back_populates = "comments")
    

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

email = os.environ.get("EMAIL")
password = os.environ.get("PASS")


def admin_only(f):
    ''' Decorative function used to verify is the user is admin '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ## if the id is not admin return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def check_login(f):
    ''' Decorative function used to verify is the user is logged in '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Call the original function
        if request.method == "POST":
            ## Check if the current user is logged in
            if not current_user.is_authenticated:
                flash("You are not Logged in", 'error')
                return redirect(url_for('login'))
            # ## Check if the current user is not registered
            # if not current_user.registered:
            #     flash("You are not Registered", 'error')
            #     return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function

def only_commenter(function):
    @wraps(function)
    def check(*args, **kwargs):
        user = db.session.execute(db.select(Comment).where(Comment.author_id ==  current_user.id)).scalar()
        if not current_user.is_authenticated or current_user.id != user.author_id:
            return abort(403)
        return function(*args, **kwargs)
    return check 

@app.route('/')
def home():  
    post_object = db.session.execute(db.select(BlogPost).order_by(BlogPost.id)).scalars().all()
    return render_template("index.html", json = post_object, current_user = current_user)


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
    return render_template("about.html", current_user = current_user)



@app.route("/post_read/<int:index>", methods = ["POST", "GET"])
def read_body(index):
    comment_form = CommentForm()
    requested_post = db.get_or_404(BlogPost, index)
    if request.method == "POST":
        ## Check if the user is valid 
        if not current_user.is_authenticated:
            flash("Need to login or register to comment")
            return redirect(url_for("login"))
        
        new_comment = Comment(
            text = comment_form.comment_text.data, 
            comment_author = current_user,
            parent_post = requested_post
            )
        
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post = requested_post, current_user = current_user, form = comment_form)



@app.route("/new-post", methods = ["POST", "GET"])
@admin_only
def make_new_post():
    ''' Used to create a new post and add it to the database '''
    form = CreatePostForm()
    if request.method == "POST":
        new_blog = BlogPost(title = request.form['title'], subtitle = request.form['subtitle'], 
                            date = current_date.strftime("%B %d %Y"), body = request.form['body'], author = current_user, img_url = request.form['url'])
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("make-post.html", form = form, edit = False , current_user = current_user)



@app.route("/edit-post/<post_id>", methods=["POST", "GET"])
@admin_only
def edit_post(post_id):
    ''' Method used to edit the post in the database '''
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title = post.title,
        subtitle = post.subtitle,
        url = post.img_url, 
        body = post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("read_body", index = post.id))
    return render_template("make-post.html", edit = True, form = edit_form, current_user = current_user)



@app.route("/delete/<int:post_id>", methods=["POST", "GET"])
@admin_only
def delete_post(post_id):
    post = BlogPost.query.get(post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
    return redirect(url_for('home'))



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
        login_user(new_user) ## Logins in after registration
        return redirect(url_for('home'))    
    return render_template("register.html", form = form, current_user = current_user)




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
            
    return render_template("login.html", form = loginform, current_user = current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/delete/comment/<int:comment_id>/<int:post_id>")
@only_commenter
def delete_comment(post_id, comment_id):
    post_to_delete = db.get_or_404(Comment, comment_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('read_body', index = post_id))
    

if __name__ == "__main__":
    app.run(debug=False)
