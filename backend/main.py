from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx


# =========================================================
# CREATE FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="WeatherGPT API",
    description="Backend API for WeatherGPT",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://weather-gpt-blush-alpha.vercel.app"
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# CHAT REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):
    message: str
    city: str


# =========================================================
# WEATHER CODE → DESCRIPTION
# =========================================================

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


# =========================================================
# GET CITY COORDINATES
# =========================================================

async def get_coordinates(city: str):

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    async with httpx.AsyncClient(timeout=15) as client:

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


# =========================================================
# GET WEATHER DATA FROM OPEN-METEO
# =========================================================

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

    async with httpx.AsyncClient(timeout=15) as client:

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


# =========================================================
# PROCESS WEATHER DATA
# =========================================================

def process_weather(weather_data):

    current = weather_data["current"]

    # -----------------------------------------------------
    # CURRENT WEATHER
    # -----------------------------------------------------

    current_weather = {

        "temperature": current.get(
            "temperature_2m",
            0
        ),

        "feels_like": current.get(
            "apparent_temperature",
            0
        ),

        "humidity": current.get(
            "relative_humidity_2m",
            0
        ),

        "precipitation": current.get(
            "precipitation",
            0
        ),

        "wind_speed": current.get(
            "wind_speed_10m",
            0
        ),

        "weather": get_weather_description(
            current.get(
                "weather_code",
                0
            )
        )
    }


    # -----------------------------------------------------
    # 7 DAY FORECAST
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # BASIC VALUES
    # -----------------------------------------------------

    temperature = current.get(
        "temperature_2m",
        0
    )

    rain_probability = forecast[0].get(
        "rain_probability",
        0
    )

    wind_speed = current.get(
        "wind_speed_10m",
        0
    )

    weather_code = current.get(
        "weather_code",
        0
    )


    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

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


    # =====================================================
    # WEATHER ALERTS
    # =====================================================

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


    # =====================================================
    # TRAVEL SCORE
    # =====================================================

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


    # Keep between 0 and 100

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


    # =====================================================
    # FINAL WEATHER DATA
    # =====================================================

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


# =========================================================
# HOME ENDPOINT
# =========================================================

@app.get("/")
async def home():

    return {

        "message":
            "Welcome to WeatherGPT API",

        "status":
            "running"
    }


# =========================================================
# WEATHER BY CITY
# =========================================================

@app.get("/weather")
async def weather(city: str):

    try:

        # Get coordinates

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

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to get weather: {str(e)}"
        )


# =========================================================
# WEATHER USING GPS LOCATION
# =========================================================

@app.get("/weather/location")
async def weather_by_location(
    latitude: float,
    longitude: float
):

    try:

        # Get weather

        weather_data = await get_weather(
            latitude,
            longitude
        )


        # Process weather

        processed = process_weather(
            weather_data
        )


        # -------------------------------------------------
        # REVERSE GEOCODING
        # -------------------------------------------------

        async with httpx.AsyncClient(timeout=15) as client:

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


        # -------------------------------------------------
        # FIND CITY
        # -------------------------------------------------

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


        # -------------------------------------------------
        # RETURN DATA
        # -------------------------------------------------

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


    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=
                f"Unable to get location weather: {str(e)}"
        )


# =========================================================
# WEATHERGPT LOCAL CHATBOT
# =========================================================

@app.post("/chat")
async def chat(request: ChatRequest):

    try:

        # =================================================
        # 1. CLEAN USER MESSAGE
        # =================================================

        original_message = request.message.strip()

        message = original_message.lower()

        # Remove common punctuation

        for symbol in [
            "?",
            "!",
            ",",
            ".",
            ":",
            ";"
        ]:

            message = message.replace(
                symbol,
                " "
            )

        message = " ".join(
            message.split()
        )


        # =================================================
        # 2. GET CITY COORDINATES
        # =================================================

        location = await get_coordinates(
            request.city
        )


        # =================================================
        # 3. GET LIVE WEATHER
        # =================================================

        weather_data = await get_weather(

            location["latitude"],
            location["longitude"]
        )


        # =================================================
        # 4. PROCESS WEATHER
        # =================================================

        processed = process_weather(
            weather_data
        )


        current = processed["current"]

        forecast = processed["forecast"]

        travel_score = processed["travel_score"]

        travel_status = processed["travel_status"]


        # =================================================
        # 5. CURRENT WEATHER VALUES
        # =================================================

        temperature = current.get(
            "temperature",
            0
        )

        feels_like = current.get(
            "feels_like",
            0
        )

        humidity = current.get(
            "humidity",
            0
        )

        wind_speed = current.get(
            "wind_speed",
            0
        )

        precipitation = current.get(
            "precipitation",
            0
        )

        weather_description = current.get(
            "weather",
            "Unknown weather"
        )


        # =================================================
        # 6. FORECAST VALUES
        # =================================================

        today = (
            forecast[0]
            if len(forecast) > 0
            else {}
        )

        tomorrow = (
            forecast[1]
            if len(forecast) > 1
            else today
        )


        today_rain = today.get(
            "rain_probability",
            0
        )

        tomorrow_rain = tomorrow.get(
            "rain_probability",
            0
        )

        tomorrow_max = tomorrow.get(
            "max_temperature",
            0
        )

        tomorrow_min = tomorrow.get(
            "min_temperature",
            0
        )

        tomorrow_weather = tomorrow.get(
            "weather",
            "Unknown"
        )


        # =================================================
        # 7. LANGUAGE DETECTION
        # =================================================

        hindi_words = [

            "क्या",
            "कैसे",
            "कैसा",
            "कब",
            "है",
            "होगा",
            "होगी",
            "बारिश",
            "मौसम",
            "गर्मी",
            "ठंड",
            "तापमान",
            "छतरी",
            "जाना",
            "चाहिए",
            "आज",
            "कल",
            "बाहर",
            "यात्रा"
        ]


        hinglish_words = [

            "kya",
            "kaise",
            "kaisa",
            "kab",
            "hai",
            "hoga",
            "hogi",
            "baarish",
            "barish",
            "mausam",
            "garmi",
            "thand",
            "temperature",
            "temp",
            "chhatri",
            "jana",
            "jaana",
            "chahiye",
            "aaj",
            "kal",
            "bahar",
            "bahar",
            "travel",
            "ghoom",
            "ghumna",
            "safe",
            "sakta",
            "sakti",
            "kar",
            "karna",
            "raha",
            "rahi",
            "hoga"
        ]


        has_hindi = any(

            word in original_message

            for word in hindi_words
        )


        hinglish_count = sum(

            word in message

            for word in hinglish_words
        )


        if has_hindi:

            language = "hindi"

        elif hinglish_count >= 1:

            language = "hinglish"

        else:

            language = "english"


        # =================================================
        # 8. INTENT DETECTION
        # =================================================

        # -------------------------------------------------
        # RAIN INTENT
        # -------------------------------------------------

        rain_words = [

            "rain",
            "raining",
            "baarish",
            "barish",
            "बारिश",
            "umbrella",
            "chhatri",
            "छतरी"
        ]


        is_rain_question = any(

            word in message
            or word in original_message

            for word in rain_words
        )


        # -------------------------------------------------
        # TEMPERATURE INTENT
        # -------------------------------------------------

        temperature_words = [

            "temperature",
            "temp",
            "degree",
            "degrees",
            "तापमान",
            "गर्मी",
            "ठंड",
            "kitna garam",
            "kitni garmi"
        ]


        is_temperature_question = any(

            word in message
            or word in original_message

            for word in temperature_words
        )


        # -------------------------------------------------
        # TRAVEL INTENT
        # -------------------------------------------------

        travel_words = [

            "travel",
            "trip",
            "journey",
            "bahar jana",
            "bahar ja",
            "ghoom",
            "ghumna",
            "jana chahiye",
            "go outside",
            "outside",
            "यात्रा",
            "बाहर जाना",
            "बाहर",
            "घूमना"
        ]


        is_travel_question = any(

            word in message
            or word in original_message

            for word in travel_words
        )


        # -------------------------------------------------
        # FORECAST INTENT
        # -------------------------------------------------

        forecast_words = [

            "forecast",
            "tomorrow",
            "today",
            "next",
            "kal",
            "aaj",
            "कल",
            "आज",
            "week",
            "weekly",
            "7 day",
            "7-day",
            "hoga",
            "hogi"
        ]


        is_forecast_question = any(

            word in message
            or word in original_message

            for word in forecast_words
        )


        # -------------------------------------------------
        # WEATHER INTENT
        # -------------------------------------------------

        weather_words = [

            "weather",
            "mausam",
            "mausam kaisa",
            "mausam kaise",
            "weather kaisa",
            "weather kaise",
            "कैसा मौसम",
            "मौसम",
            "मौसम कैसा",
            "मौसम कैसा है"
        ]


        is_weather_question = any(

            word in message
            or word in original_message

            for word in weather_words
        )


        # =================================================
        # 9. RESPONSE GENERATION
        # =================================================

        response_text = ""


        # =================================================
        # WEATHER RESPONSE
        # =================================================

        if is_weather_question:

            if language == "hindi":

                response_text = (
                    f"{location['name']} में अभी मौसम "
                    f"{weather_description} है। "
                    f"तापमान {temperature}°C है और "
                    f"महसूस होने वाला तापमान {feels_like}°C है। "
                    f"नमी {humidity}% और हवा की गति "
                    f"{wind_speed} km/h है।"
                )


            elif language == "hinglish":

                response_text = (
                    f"{location['name']} mein abhi "
                    f"{weather_description} hai. "
                    f"Temperature {temperature}°C hai aur "
                    f"feels-like temperature {feels_like}°C hai. "
                    f"Humidity {humidity}% hai aur "
                    f"wind speed {wind_speed} km/h hai."
                )


            else:

                response_text = (
                    f"The current weather in "
                    f"{location['name']} is "
                    f"{weather_description}. "
                    f"The temperature is {temperature}°C "
                    f"and it feels like {feels_like}°C. "
                    f"Humidity is {humidity}% and "
                    f"wind speed is {wind_speed} km/h."
                )


        # =================================================
        # RAIN RESPONSE
        # =================================================

        elif is_rain_question:

            if (
                "tomorrow" in message
                or "kal" in message
                or "कल" in original_message
            ):

                rain_value = tomorrow_rain

                if language == "hindi":

                    response_text = (
                        f"कल {location['name']} में बारिश "
                        f"की संभावना {rain_value}% है। "
                        f"कल का मौसम {tomorrow_weather} रहने "
                        f"की संभावना है।"
                    )


                elif language == "hinglish":

                    response_text = (
                        f"Kal {location['name']} mein "
                        f"baarish ki probability "
                        f"{rain_value}% hai. "
                        f"Kal weather {tomorrow_weather} "
                        f"rehne ka chance hai."
                    )


                else:

                    response_text = (
                        f"There is a {rain_value}% chance "
                        f"of rain in {location['name']} tomorrow. "
                        f"The expected weather is "
                        f"{tomorrow_weather}."
                    )


            else:

                rain_value = today_rain

                if language == "hindi":

                    response_text = (
                        f"आज {location['name']} में बारिश "
                        f"की संभावना {rain_value}% है।"
                    )


                elif language == "hinglish":

                    response_text = (
                        f"Aaj {location['name']} mein "
                        f"baarish ki probability "
                        f"{rain_value}% hai."
                    )


                else:

                    response_text = (
                        f"The chance of rain in "
                        f"{location['name']} today is "
                        f"{rain_value}%."
                    )


        # =================================================
        # TEMPERATURE RESPONSE
        # =================================================

        elif is_temperature_question:

            if language == "hindi":

                response_text = (
                    f"{location['name']} में अभी तापमान "
                    f"{temperature}°C है और महसूस होने वाला "
                    f"तापमान {feels_like}°C है।"
                )


            elif language == "hinglish":

                response_text = (
                    f"{location['name']} mein abhi "
                    f"temperature {temperature}°C hai. "
                    f"Feels-like temperature {feels_like}°C hai."
                )


            else:

                response_text = (
                    f"The current temperature in "
                    f"{location['name']} is {temperature}°C, "
                    f"with a feels-like temperature of "
                    f"{feels_like}°C."
                )


        # =================================================
        # TRAVEL RESPONSE
        # =================================================

        elif is_travel_question:

            if language == "hindi":

                response_text = (
                    f"{location['name']} के लिए Travel Score "
                    f"{travel_score}/100 है। "
                    f"स्थिति: {travel_status}। "
                    f"आज का मौसम {weather_description} है "
                    f"और बारिश की संभावना {today_rain}% है।"
                )


            elif language == "hinglish":

                response_text = (
                    f"{location['name']} ka Travel Score "
                    f"{travel_score}/100 hai. "
                    f"Status: {travel_status}. "
                    f"Aaj weather {weather_description} hai "
                    f"aur baarish ki probability "
                    f"{today_rain}% hai."
                )


            else:

                response_text = (
                    f"The Travel Score for "
                    f"{location['name']} is "
                    f"{travel_score}/100. "
                    f"Status: {travel_status}. "
                    f"Today's weather is "
                    f"{weather_description} with a "
                    f"{today_rain}% chance of rain."
                )


        # =================================================
        # FORECAST RESPONSE
        # =================================================

        elif is_forecast_question:

            if language == "hindi":

                response_text = (
                    f"कल {location['name']} में मौसम "
                    f"{tomorrow_weather} रहने की संभावना है। "
                    f"तापमान लगभग {tomorrow_min}°C से "
                    f"{tomorrow_max}°C के बीच रहेगा और "
                    f"बारिश की संभावना {tomorrow_rain}% है।"
                )


            elif language == "hinglish":

                response_text = (
                    f"Kal {location['name']} mein weather "
                    f"{tomorrow_weather} rehne ka chance hai. "
                    f"Temperature around {tomorrow_min}°C se "
                    f"{tomorrow_max}°C ke beech rahega aur "
                    f"baarish ki probability {tomorrow_rain}% hai."
                )


            else:

                response_text = (
                    f"Tomorrow in {location['name']}, "
                    f"the expected weather is "
                    f"{tomorrow_weather}. "
                    f"Temperature may range from "
                    f"{tomorrow_min}°C to {tomorrow_max}°C, "
                    f"with a {tomorrow_rain}% chance of rain."
                )


        # =================================================
        # GENERAL WEATHER RESPONSE
        # =================================================

        else:

            if language == "hindi":

                response_text = (
                    f"{location['name']} में अभी "
                    f"{weather_description} है और "
                    f"तापमान {temperature}°C है। "
                    f"बारिश की संभावना {today_rain}% है। "
                    f"Travel Score {travel_score}/100 है।"
                )


            elif language == "hinglish":

                response_text = (
                    f"{location['name']} mein abhi "
                    f"{weather_description} hai aur "
                    f"temperature {temperature}°C hai. "
                    f"Baarish ki probability "
                    f"{today_rain}% hai. "
                    f"Travel Score {travel_score}/100 hai."
                )


            else:

                response_text = (
                    f"In {location['name']}, the current "
                    f"weather is {weather_description} "
                    f"with a temperature of {temperature}°C. "
                    f"The chance of rain is {today_rain}% "
                    f"and the Travel Score is "
                    f"{travel_score}/100."
                )


        # =================================================
        # FINAL CHAT RESPONSE
        # =================================================

        return {

            "city":
                location["name"],

            "message":
                original_message,

            "response":
                response_text
        }


    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=
                f"Unable to process chat request: {str(e)}"
        )