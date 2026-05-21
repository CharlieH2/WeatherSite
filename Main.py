import os
from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html.jinja')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html.jinja'), 404

@app.route('/weather')
def weather():
    # Pass empty lists and dictionaries to satisfy the template
    return render_template(
        'weather.html.jinja',
        location_name='Preview City',
        current={},       # Empty dictionary for current weather
        hourly_data=[],   # Empty list for the hourly loop
        daily_data=[]     # Empty list for the daily loop
    )