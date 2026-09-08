from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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
# ---------------------------------------------
# CHAT REQUEST MODEL
# ---------------------------------------------

class ChatRequest(BaseModel):
    message: str
    city: str


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

        response = await client.get(
            url,
            params=params
        )

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

        response = await client.get(
            url,
            params=params
        )

        if response.status_code != 200:

            raise HTTPException(
                status_code=500,
                detail="Unable to retrieve weather data"
            )

        return response.json()


# Process raw weather data
def process_weather(weather_data):

    current = weather_data["current"]


    # -----------------------------------------
    # CURRENT WEATHER
    # -----------------------------------------

    current_weather = {

        "temperature":
            current["temperature_2m"],

        "feels_like":
            current["apparent_temperature"],

        "humidity":
            current["relative_humidity_2m"],

        "precipitation":
            current["precipitation"],

        "wind_speed":
            current["wind_speed_10m"],

        "weather":
            get_weather_description(
                current["weather_code"]
            )
    }


    # -----------------------------------------
    # 7-DAY FORECAST
    # -----------------------------------------

    daily = weather_data["daily"]

    forecast = []

    for i in range(len(daily["time"])):

        day = {

            "date":
                daily["time"][i],

            "weather":
                get_weather_description(
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


    # -----------------------------------------
    # BASIC VALUES
    # -----------------------------------------

    temperature = current["temperature_2m"]

    rain_probability = forecast[0]["rain_probability"]

    wind_speed = current["wind_speed_10m"]

    weather_code = current["weather_code"]


    # -----------------------------------------
    # RECOMMENDATIONS
    # -----------------------------------------

    recommendations = []


    # Rain recommendation
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


    # Temperature recommendation
    if temperature >= 35:

        recommendations.append(
            "It is very hot. Stay hydrated and avoid "
            "unnecessary outdoor activity."
        )

    elif temperature <= 15:

        recommendations.append(
            "It is cold. Consider wearing warm clothing."
        )


    # Thunderstorm recommendation
    if weather_code >= 95:

        recommendations.append(
            "Thunderstorm conditions detected. "
            "Avoid exposed outdoor areas."
        )


    # -----------------------------------------
    # WEATHER ALERTS
    # -----------------------------------------

    alerts = []


    # Rain alert
    if rain_probability >= 70:

        alerts.append({

            "type": "Rain Alert",

            "message":
                "High chance of rain. Carry an umbrella."
        })


    # Extreme heat alert
    if temperature >= 40:

        alerts.append({

            "type": "Extreme Heat",

            "message":
                "Extreme heat detected. Stay hydrated "
                "and avoid prolonged outdoor activity."
        })


    # Cold alert
    if temperature <= 10:

        alerts.append({

            "type": "Cold Alert",

            "message":
                "Very low temperature detected. "
                "Wear warm clothing."
        })


    # Thunderstorm alert
    if weather_code >= 95:

        alerts.append({

            "type": "Thunderstorm Alert",

            "message":
                "Thunderstorm conditions detected. "
                "Avoid exposed outdoor areas."
        })


    # -----------------------------------------
    # TRAVEL DECISION SCORE
    # -----------------------------------------

    travel_score = 100


    # Rain penalty
    if rain_probability >= 80:

        travel_score -= 35

    elif rain_probability >= 60:

        travel_score -= 25

    elif rain_probability >= 40:

        travel_score -= 15

    elif rain_probability >= 20:

        travel_score -= 5


    # Temperature penalty
    if temperature >= 40:

        travel_score -= 25

    elif temperature >= 35:

        travel_score -= 15

    elif temperature <= 10:

        travel_score -= 15


    # Thunderstorm penalty
    if weather_code >= 95:

        travel_score -= 30


    # Wind penalty
    if wind_speed >= 50:

        travel_score -= 20

    elif wind_speed >= 35:

        travel_score -= 10


    # Keep score between 0 and 100
    travel_score = max(
        0,
        min(100, travel_score)
    )


    # Travel status
    if travel_score >= 75:

        travel_status = "Good for travel"

    elif travel_score >= 50:

        travel_status = "Travel with caution"

    else:

        travel_status = "Not recommended"


    # -----------------------------------------
    # FINAL PROCESSED DATA
    # -----------------------------------------

    return {

        "current":
            current_weather,

        "forecast":
            forecast,

        "recommendations":
            recommendations,

        "alerts":
            alerts,

        "travel_score":
            travel_score,

        "travel_status":
            travel_status
    }


# ---------------------------------------------
# HOME ENDPOINT
# ---------------------------------------------

@app.get("/")
async def home():

    return {

        "message":
            "Welcome to WeatherGPT API",

        "status":
            "running"
    }


# ---------------------------------------------
# SEARCH WEATHER BY CITY
# ---------------------------------------------

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
    processed = process_weather(
        weather_data
    )


    return {

        "city":
            location["name"],

        "country":
            location["country"],

        "latitude":
            location["latitude"],

        "longitude":
            location["longitude"],

        "current":
            processed["current"],

        "forecast":
            processed["forecast"],

        "recommendations":
            processed["recommendations"],

        "alerts":
            processed["alerts"],

        "travel_score":
            processed["travel_score"],

        "travel_status":
            processed["travel_status"]
    }


# ---------------------------------------------
# SEARCH WEATHER USING GPS LOCATION
# ---------------------------------------------

@app.get("/weather/location")
async def weather_by_location(
    latitude: float,
    longitude: float
):

    try:

        # Get weather using GPS coordinates
        weather_data = await get_weather(
            latitude,
            longitude
        )


        # Process weather
        processed = process_weather(
            weather_data
        )


        # -------------------------------------
        # REVERSE GEOCODING
        # -------------------------------------

        async with httpx.AsyncClient() as client:

            response = await client.get(

                "https://geocoding-api.open-meteo.com/v1/reverse",

                params={

                    "latitude":
                        latitude,

                    "longitude":
                        longitude,

                    "count":
                        1,

                    "language":
                        "en",

                    "format":
                        "json"
                }
            )

            location_data = response.json()


        # -------------------------------------
        # FIND CITY NAME
        # -------------------------------------

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

            country = location.get(
                "country",
                ""
            )

        else:

            city = "Your Location"

            country = ""


        # -------------------------------------
        # FINAL RESPONSE
        # -------------------------------------

        return {

            "city":
                city,

            "country":
                country,

            "latitude":
                latitude,

            "longitude":
                longitude,

            "current":
                processed["current"],

            "forecast":
                processed["forecast"],

            "recommendations":
                processed["recommendations"],

            "alerts":
                processed["alerts"],

            "travel_score":
                processed["travel_score"],

            "travel_status":
                processed["travel_status"]
        }


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=
                f"Unable to get location weather: {str(e)}"
        )
# ---------------------------------------------
# WEATHERGPT CHAT ENDPOINT
# ---------------------------------------------

@app.post("/chat")
async def chat(request: ChatRequest):

    try:

        # Get coordinates of the city
        location = await get_coordinates(request.city)

        # Get latest weather data
        weather_data = await get_weather(
            location["latitude"],
            location["longitude"]
        )

        # Process weather data
        processed = process_weather(weather_data)

        current = processed["current"]

        tomorrow = processed["forecast"][1]

        travel_score = processed["travel_score"]

        travel_status = processed["travel_status"]


        # -----------------------------------------
        # WEATHER CONTEXT
        # -----------------------------------------

        message = request.message.lower()


        # -----------------------------------------
        # RAIN QUESTIONS
        # -----------------------------------------

        if (
            "rain" in message
            or "barish" in message
            or "baarish" in message
            or "बारिश" in message
            or "umbrella" in message
            or "chhata" in message
        ):

            rain_probability = tomorrow["rain_probability"]

            if rain_probability >= 70:

                response = (
                    f"🌧️ Yes, there is a high chance of rain "
                    f"tomorrow in {request.city}. "
                    f"The rain probability is {rain_probability}%. "
                    f"Please carry an umbrella."
                )

            elif rain_probability >= 40:

                response = (
                    f"🌦️ There is a moderate chance of rain "
                    f"tomorrow in {request.city}. "
                    f"The rain probability is {rain_probability}%. "
                    f"Keeping an umbrella with you would be a good idea."
                )

            else:

                response = (
                    f"☀️ The chance of rain tomorrow in "
                    f"{request.city} is relatively low. "
                    f"The rain probability is {rain_probability}%."
                )


        # -----------------------------------------
        # TRAVEL QUESTIONS
        # -----------------------------------------

        elif (
            "travel" in message
            or "trip" in message
            or "go tomorrow" in message
            or "ghoom" in message
            or "ghumna" in message
            or "bahar" in message
            or "बाहर" in message
            or "yatra" in message
            or "यात्रा" in message
            or "safar" in message
            or "सफर" in message
        ):

            response = (
                f"🧳 Travel score for {request.city} is "
                f"{travel_score}/100 — {travel_status}. "
                f"Tomorrow's rain probability is "
                f"{tomorrow['rain_probability']}%. "
                f"The temperature is expected to be around "
                f"{tomorrow['max_temperature']}°C."
            )


        # -----------------------------------------
        # TEMPERATURE QUESTIONS
        # -----------------------------------------

        elif (
            "temperature" in message
            or "temp" in message
            or "taapman" in message
            or "तापमान" in message
            or "garmi" in message
            or "गर्मी" in message
            or "hot" in message
            or "garam" in message
            or "thand" in message
            or "ठंड" in message
            or "cold" in message
        ):

            response = (
                f"🌡️ The current temperature in "
                f"{request.city} is "
                f"{round(current['temperature'])}°C. "
                f"It feels like "
                f"{round(current['feels_like'])}°C."
            )


        # -----------------------------------------
        # CLOTHING QUESTIONS
        # -----------------------------------------

        elif (
            "wear" in message
            or "clothes" in message
            or "dress" in message
            or "kapde" in message
            or "कपड़े" in message
            or "pehnu" in message
            or "pahnu" in message
            or "pehen" in message
        ):

            temperature = current["temperature"]

            if temperature >= 35:

                response = (
                    f"👕 It is quite hot in {request.city}, "
                    f"with a temperature of "
                    f"{round(temperature)}°C. "
                    f"Light and breathable cotton clothes "
                    f"would be suitable."
                )

            elif temperature >= 25:

                response = (
                    f"👕 The temperature is around "
                    f"{round(temperature)}°C. "
                    f"Light cotton clothes should be comfortable."
                )

            elif temperature >= 15:

                response = (
                    f"🧥 The temperature is around "
                    f"{round(temperature)}°C. "
                    f"Full-sleeve clothes or a light jacket "
                    f"would be suitable."
                )

            else:

                response = (
                    f"🧥 It is quite cold in {request.city}. "
                    f"The temperature is around "
                    f"{round(temperature)}°C. "
                    f"Warm clothes are recommended."
                )


        # -----------------------------------------
        # GENERAL WEATHER QUESTION
        # -----------------------------------------

        elif (
            "weather" in message
            or "mausam" in message
            or "मौसम" in message
        ):

            response = (
                f"🌤️ The current weather in {request.city} "
                f"is {current['weather']}. "
                f"The temperature is "
                f"{round(current['temperature'])}°C, "
                f"humidity is {current['humidity']}%, "
                f"and wind speed is "
                f"{current['wind_speed']} km/h."
            )


        # -----------------------------------------
        # DEFAULT RESPONSE
        # -----------------------------------------

        else:

            response = (
                "🤖 I can help you with weather, rain, "
                "travel, temperature and clothing. "
                "Try asking: "
                "'Will it rain tomorrow?', "
                "'Can I travel tomorrow?', "
                "'What is the temperature?', "
                "or 'What should I wear?'"
            )


        return {
            "city": request.city,
            "message": request.message,
            "response": response
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to process chat request: {str(e)}"
        )