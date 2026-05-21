import os
import requests
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from dotenv import load_dotenv

load_dotenv()

def get_coordinates(location_name):
    """Fetches coordinates for a given location name."""
    api_key = os.getenv('LOCATION_API_KEY')
    url = f"https://geokeo.com/geocode/v1/search.php?q={location_name}&api={api_key}"
    
    try:
        resp = requests.get(url)
        data = resp.json()
        
        if data.get('status') == 'ok':
            result = data['results'][0]
            return {
                'address': result['formatted_address'],
                'latitude': result['geometry']['location']['lat'],
                'longitude': result['geometry']['location']['lng']
            }
    except Exception as e:
        print(f"Error fetching location: {e}")
    return None

def get_weather_data(lat, lon):
    """Fetches weather data for given coordinates."""
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    # Your exact parameters
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "sunrise", "sunset", "uv_index_max", "weather_code"],
        "hourly": ["temperature_2m", "apparent_temperature", "relative_humidity_2m", "precipitation_probability", "wind_speed_10m", "weather_code"],
        "current": ["temperature_2m", "weather_code"],
        "timezone": "GMT",
        "wind_speed_unit": "mph",
    }
    
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    
    # Process Current Data
    current = response.Current()
    current_data = {
        "temperature": round(current.Variables(0).Value()),
        "condition": get_condition_from_code(current.Variables(1).Value())
    }

    # Process Hourly Data
    hourly = response.Hourly()
    hourly_temp = hourly.Variables(0).ValuesAsNumpy()
    hourly_app_temp = hourly.Variables(1).ValuesAsNumpy()
    hourly_hum = hourly.Variables(2).ValuesAsNumpy()
    hourly_precip = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind = hourly.Variables(4).ValuesAsNumpy()
    hourly_code = hourly.Variables(5).ValuesAsNumpy()
    
    hourly_dates = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )
    
    hourly_data_list = []
    for i in range(24): 
        hourly_data_list.append({
            "time": hourly_dates[i].strftime("%H:00"), 
            "temperature": round(hourly_temp[i]),
            "feels_like": round(hourly_app_temp[i]),
            "humidity": round(hourly_hum[i]),
            "precip_prob": round(hourly_precip[i]),
            "wind_speed": round(hourly_wind[i]),
            "condition": get_condition_from_code(hourly_code[i])
        })

    # Process Daily Data
    daily = response.Daily()
    daily_temp_max = daily.Variables(0).ValuesAsNumpy()
    daily_temp_min = daily.Variables(1).ValuesAsNumpy()
    daily_sunrise = daily.Variables(2).ValuesInt64AsNumpy()
    daily_sunset = daily.Variables(3).ValuesInt64AsNumpy()
    daily_uv = daily.Variables(4).ValuesAsNumpy()
    daily_code = daily.Variables(5).ValuesAsNumpy()
    
    daily_dates = pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )
    
    daily_data_list = []
    for i in range(1, len(daily_dates)): 
        # Convert UNIX timestamps to readable H:M format
        sunrise_time = pd.to_datetime(daily_sunrise[i], unit="s").strftime("%H:%M")
        sunset_time = pd.to_datetime(daily_sunset[i], unit="s").strftime("%H:%M")
        
        daily_data_list.append({
            "date": daily_dates[i].strftime("%A"), 
            "max_temp": round(daily_temp_max[i]),
            "min_temp": round(daily_temp_min[i]),
            "sunrise": sunrise_time,
            "sunset": sunset_time,
            "uv_index": round(daily_uv[i], 1),
            "condition": get_condition_from_code(daily_code[i])
        })

    return {
        "current": current_data,
        "hourly": hourly_data_list,
        "daily": daily_data_list
    }

def get_condition_from_code(code):
    """Maps WMO weather codes to text descriptions."""
    weather_codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog", 51: "Drizzle: Light", 
        53: "Drizzle: Moderate", 55: "Drizzle: Dense intensity", 
        56: "Freezing Drizzle: Light", 57: "Freezing Drizzle: Dense intensity",
        61: "Rain: Slight", 63: "Rain: Moderate", 65: "Rain: Heavy intensity",
        66: "Freezing Rain: Light", 67: "Freezing Rain: Heavy intensity",
        71: "Snow fall: Slight", 73: "Snow fall: Moderate", 75: "Snow fall: Heavy intensity",
        77: "Snow grains", 80: "Rain showers: Slight", 81: "Rain showers: Moderate",
        82: "Rain showers: Violent", 85: "Snow showers: Slight", 86: "Snow showers: Heavy",
        95: "Thunderstorm: Slight or moderate", 96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(code, "Unknown")