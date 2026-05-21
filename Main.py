import os
from flask import Flask, render_template, request, redirect, url_for
from api_helpers import get_coordinates, get_weather_data # Import your new functions

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html.jinja')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html.jinja'), 404

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        return redirect(url_for('home'))
        
    location_info = get_coordinates(query)
    
    if not location_info:
        return "Location not found", 404
        
    weather_info = get_weather_data(location_info['latitude'], location_info['longitude'])
    
    return render_template(
        'weather.html.jinja',
        location_name=location_info['address'],
        current=weather_info['current'],
        hourly_data=weather_info['hourly'],
        daily_data=weather_info['daily']
    )