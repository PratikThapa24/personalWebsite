from flask import Flask, render_template, request
import requests
from post import Post
import smtplib
import os

app = Flask(__name__)


url_blog_post = f"https://api.npoint.io/c790b4d5cab58020d391"
response = requests.get(url_blog_post)
json_response = response.json()
email = "prajwaljungthapa@gmail.com"
password = os.environ.get("PASS")


post_object = []
for post in json_response:
    # Create a post object and append to the post_object list 
    post = Post(post.get('id'), post.get('title'), post.get('subtitle'), post.get('body'))
    post_object.append(post)
    
@app.route('/')
def home():
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
            connection.login(email, password)
            connection.sendmail(email, email, email_message)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")


@app.route('/about')
def about():
    return render_template("about.html")

@app.route("/post_read/<int:index>")
def read_body(index):
    description = None
    for post in post_object:
        if post.id == index:
            description = post
            
    return render_template("post.html", read = description)

if __name__ == "__main__":
    app.run(debug=True)
