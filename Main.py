from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/hello')
def hello():
    return 'Hello, World'

@app.route('/home')
def home():
    return render_template('home.html.jinja')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html.jinja'), 404