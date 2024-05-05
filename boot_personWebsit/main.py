from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Column
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from datetime import datetime
import requests
from post import Post
import smtplib
import os

##Intializing the datetime 
current_date = datetime.now()

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
ckeditor = CKEditor(app)

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

with app.app_context():
    db.create_all()

class Form(FlaskForm):
    ''' Form that will be used in make-post html to get user input '''
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    name = StringField("Your Name", validators=[DataRequired()])
    url = StringField("Blog image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content")
    submit = SubmitField("Submit Post")
    

url_blog_post = f"https://api.npoint.io/c790b4d5cab58020d391"
response = requests.get(url_blog_post)
json_response = response.json()
email = "prajwaljungthapa@gmail.com"
password = os.environ.get("PASS")


# post_object = []
# for post in json_response:
#     # Create a post object and append to the post_object list 
#     post = Post(post.get('id'), post.get('title'), post.get('subtitle'), post.get('body'))
#     post_object.append(post)

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
    return render_template("index.html", json = post_object)

@app.route('/contact', methods=["POST", "GET"])
def contact():
    if request.method == "POST":
        data = request.form
        send_email(data["name"], data["email"], data["phone"], data["message"])
        return render_template("contact.html", msg_sent = True)
    return render_template("contact.html", msg_sent = False)
    
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
    return render_template("about.html")

@app.route("/post_read/<int:index>")
def read_body(index):
    description = None
    request_post = db.get_or_404(BlogPost, index)
    return render_template("post.html", read = request_post)

@app.route("/new-post", methods = ["POST", "GET"])
def make_new_post():
    ''' Used to create a new post and add it to the database '''
    
    form = Form()
    if request.method == "POST":
        new_blog = BlogPost(title = request.form['title'], subtitle = request.form['subtitle'], 
                            date = current_date.strftime("%B %d %Y"), body = request.form['body'], author = request.form['name'], img_url = request.form['url'])
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("make-post.html", form = form, edit = False )

@app.route("/edit-post/<post_id>", methods=["POST", "GET"])
def edit_post(post_id):
    ''' Method used to edit the post in the database '''
    post = BlogPost.query.get(post_id)
    edit_form = Form(
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
    return render_template("make-post.html", edit = True, form = edit_form)

@app.route("/delete/<int:post_id>", methods=["POST", "GET"])
def delete_post(post_id):
    post = BlogPost.query.get(post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
