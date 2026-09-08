from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx


# Create FastAPI application
app = FastAPI(
    title="WeatherGPT API",
    description="Backend API for WeatherGPT",
    version="1.0.0"
)


# Allow React frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Convert weather codes into readable descriptions
def get_weather_description(weather_code: int) -> str:

    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Heavy rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail"
    }

    return weather_codes.get(weather_code, "Unknown weather")


# Find latitude and longitude of a city
async def get_coordinates(city: str):

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    async with httpx.AsyncClient() as client:

        response = await client.get(url, params=params)

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Unable to connect to location service"
            )

        data = response.json()

    if "results" not in data or not data["results"]:
        raise HTTPException(
            status_code=404,
            detail=f"City '{city}' was not found"
        )

    location = data["results"][0]

    return {
        "name": location["name"],
        "country": location.get("country", ""),
        "latitude": location["latitude"],
        "longitude": location["longitude"]
    }


# Get raw weather information
async def get_weather(latitude: float, longitude: float):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),

        "hourly": (
            "temperature_2m,"
            "precipitation_probability,"
            "precipitation,"
            "weather_code"
        ),

        "daily": (
            "weather_code,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_probability_max,"
            "precipitation_sum"
        ),

        "timezone": "auto",
        "forecast_days": 7
    }

    async with httpx.AsyncClient() as client:

        response = await client.get(url, params=params)

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Unable to retrieve weather data"
            )

        return response.json()


# Process raw weather data into WeatherGPT format
def process_weather(weather_data):

    current = weather_data["current"]

    # Current weather
    current_weather = {
        "temperature": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "humidity": current["relative_humidity_2m"],
        "precipitation": current["precipitation"],
        "wind_speed": current["wind_speed_10m"],
        "weather": get_weather_description(
            current["weather_code"]
        )
    }

    # 7-day forecast
    daily = weather_data["daily"]

    forecast = []

    for i in range(len(daily["time"])):

        day = {
            "date": daily["time"][i],

            "weather": get_weather_description(
                daily["weather_code"][i]
            ),

            "max_temperature":
                daily["temperature_2m_max"][i],

            "min_temperature":
                daily["temperature_2m_min"][i],

            "rain_probability":
                daily["precipitation_probability_max"][i],

            "precipitation":
                daily["precipitation_sum"][i]
        }

        forecast.append(day)

    # Recommendations
    recommendations = []

    temperature = current["temperature_2m"]

    rain_probability = forecast[0]["rain_probability"]

    if rain_probability >= 70:

        recommendations.append(
            "High chance of rain. Carry an umbrella."
        )

    elif rain_probability >= 40:

        recommendations.append(
            "There is a moderate chance of rain. "
            "Keep an umbrella nearby."
        )

    else:

        recommendations.append(
            "Low chance of rain today."
        )

    if temperature >= 35:

        recommendations.append(
            "It is very hot. Stay hydrated and avoid "
            "unnecessary outdoor activity."
        )

    elif temperature <= 15:

        recommendations.append(
            "It is cold. Consider wearing warm clothing."
        )

    if current["weather_code"] >= 95:

        recommendations.append(
            "Thunderstorm conditions detected. "
            "Avoid exposed outdoor areas."
        )

    # Weather alerts
    alerts = []

    if rain_probability >= 70:

        alerts.append({
            "type": "Rain Alert",
            "message": "High chance of rain. Carry an umbrella."
        })

    if temperature >= 40:

        alerts.append({
            "type": "Extreme Heat",
            "message": "Extreme heat detected. Stay hydrated and avoid prolonged outdoor activity."
        })

    if temperature <= 10:

        alerts.append({
            "type": "Cold Alert",
            "message": "Very low temperature detected. Wear warm clothing."
        })

    if current["weather_code"] >= 95:

        alerts.append({
            "type": "Thunderstorm Alert",
            "message": "Thunderstorm conditions detected. Avoid exposed outdoor areas."
        })

    return {
        "current": current_weather,
        "forecast": forecast,
        "recommendations": recommendations,
        "alerts": alerts
    }


# Home endpoint
@app.get("/")
async def home():

    return {
        "message": "Welcome to WeatherGPT API",
        "status": "running"
    }


# Search weather by city
@app.get("/weather")
async def weather(city: str):

    # Find city coordinates
    location = await get_coordinates(city)

    # Get weather
    weather_data = await get_weather(
        location["latitude"],
        location["longitude"]
    )

    # Process weather
    processed = process_weather(weather_data)

    return {
        "city": location["name"],
        "country": location["country"],
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": processed["current"],
        "forecast": processed["forecast"],
        "recommendations": processed["recommendations"],
        "alerts": processed["alerts"]
    }


# Search weather using GPS coordinates
@app.get("/weather/location")
async def weather_by_location(
    latitude: float,
    longitude: float
):

    try:

        # Get weather using coordinates
        weather_data = await get_weather(
            latitude,
            longitude
        )

        # Process weather
        processed = process_weather(weather_data)

        # Reverse geocoding
        async with httpx.AsyncClient() as client:

            response = await client.get(
                "https://geocoding-api.open-meteo.com/v1/reverse",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "count": 1,
                    "language": "en",
                    "format": "json"
                }
            )

            location_data = response.json()

        # Find city
        if (
            "results" in location_data
            and location_data["results"]
        ):

            location = location_data["results"][0]

            city = (
                location.get("name")
                or location.get("admin1")
                or "Your Location"
            )

            country = location.get("country", "")

        else:

            city = "Your Location"
            country = ""

        return {
            "city": city,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "current": processed["current"],
            "forecast": processed["forecast"],
            "recommendations": processed["recommendations"],
            "alerts": processed["alerts"]
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to get location weather: {str(e)}"
        )