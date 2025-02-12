
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()
apikey = os.getenv("API_KEY")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

def fetch_last_24_hours_weather(city):
    try:
        base_url = "https://api.weatherapi.com/v1/history.json"
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        params = {"key": apikey, "q": city, "dt": yesterday}
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()
            weather_data = [
                {
                    "dt": hour["time"],
                    "temp": hour["temp_c"],
                    "pressure": hour["pressure_mb"],
                    "humidity": hour["humidity"],
                    "clouds": hour["cloud"],
                    "wind_speed": hour["wind_kph"],
                    "wind_deg": hour["wind_degree"],
                }
                for hour in data["forecast"]["forecastday"][0]["hour"]
            ]
            return {"status": "success", "data": weather_data}

        return {"status": "error", "message": f"Failed to fetch data. Status code: {response.status_code}"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

def fetch_weather_data(years, latitude, longitude):
    base_url = "https://archive-api.open-meteo.com/v1/archive"
    today = datetime.today().date()
    all_data = []

    try:
        for year in range(today.year - years, today.year):
            start_date = datetime(year, today.month, today.day) - timedelta(days=15)
            end_date = datetime(year, today.month, today.day) + timedelta(days=15)

            print(f"Fetching data from {start_date.date()} to {end_date.date()} for year {year}")

            current_date = start_date
            while current_date <= end_date:
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_date": current_date.strftime("%Y-%m-%d"),
                    "end_date": current_date.strftime("%Y-%m-%d"),
                    "hourly": "temperature_2m,surface_pressure,relative_humidity_2m,cloud_cover,wind_speed_10m,wind_direction_10m",
                    "timezone": "auto",
                }
                response = requests.get(base_url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    for i in range(len(data["hourly"]["time"])):
                        all_data.append([
                            data["hourly"]["time"][i],
                            data["hourly"]["temperature_2m"][i],
                            data["hourly"]["surface_pressure"][i],
                            data["hourly"]["relative_humidity_2m"][i],
                            data["hourly"]["cloud_cover"][i],
                            data["hourly"]["wind_speed_10m"][i],
                            data["hourly"]["wind_direction_10m"][i],
                        ])
                else:
                    print(f"Failed to fetch data for {current_date.strftime('%Y-%m-%d')}")

                current_date += timedelta(days=1)

        print("Weather data fetching complete!")
        return all_data
    except Exception as e:
        print(f"Error fetching weather data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {str(e)}")

    
def geocode_city(city):
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    response = requests.get(geocode_url)
    if response.status_code == 200:
        geocode_response = response.json()
        if geocode_response.get("results"):
            latitude = geocode_response["results"][0]["latitude"]
            longitude = geocode_response["results"][0]["longitude"]
            return latitude, longitude
        else:
            raise ValueError("Invalid city name!")
    else:
        raise ConnectionError("Failed to fetch geocoding data.")

@app.get("/get_data/{city}/{years}")
def predict_weather(city: str, years: int):
    try:
        latitude, longitude = geocode_city(city=city)
        all_data = list(fetch_weather_data(years, latitude, longitude))

        return {"status": "success", "predictions": all_data}

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    


@app.get("/yesterday_data/{city}")
def predict_weather(city: str):
    try:
            
        weather_data = fetch_last_24_hours_weather(city)

        return {"status": "success", "predictions": weather_data}

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

