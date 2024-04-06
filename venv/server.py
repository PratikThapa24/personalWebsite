from flask import Flask, render_template
import requests
import os

app = Flask(__name__)


@app.route('/<name>')
def home(name):
    url_age = f"https://api.agify.io?name={name}"
    url_gender = f"https://api.genderize.io?name={name}"
    response_age = requests.get(url_age)
    response_gender = requests.get(url_gender)
    
    # For the age 
    if response_age.status_code == 200:
        data_age = response_age.json()
        
        predicted_age = data_age.get('age')
    else:
        predicted_age = None
        
    # For the gender 
    if response_gender.status_code == 200:
        data_gender = response_gender.json()
        
        predicted_gender = data_gender.get('gender')
    else:
        predicted_gender = None
        
    return render_template('index.html', name = name, age = predicted_age, gender = predicted_gender)

@app.route('/blog')
def blog():
    blog_url = "https://api.npoint.io/c790b4d5cab58020d391"
    response = requests.get(blog_url)
    all_posts = response.json()
    return render_template("blog.html", posts=all_posts)
    
if __name__ == "__main__":
    app.run(debug=True)
