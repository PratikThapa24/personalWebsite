from flask import Flask, render_template
import requests
from post import Post

app = Flask(__name__)

url_blog_post = f"https://api.npoint.io/c790b4d5cab58020d391"
response = requests.get(url_blog_post)
json_response = response.json()

post_object = []
for post in json_response:
    # Create a post object and append to the post_object list 
    post = Post(post.get('id'), post.get('title'), post.get('subtitle'), post.get('body'))
    post_object.append(post)
    
@app.route('/')
def home():
    return render_template("index.html", json = post_object)

@app.route('/contact')
def contact():
    return render_template("contact.html")

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
