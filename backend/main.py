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

    return weather_codes.get(
        weather_code,
        "Unknown weather"
    )


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

    # =====================================================
    # CURRENT WEATHER
    # =====================================================

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


    # =====================================================
    # 7 DAY FORECAST
    # =====================================================

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


    # =====================================================
    # BASIC VALUES
    # =====================================================

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


    if weather_code >= 95:

        recommendations.append(
            "Thunderstorm conditions detected. "
            "Avoid exposed outdoor areas."
        )


    # =====================================================
    # WEATHER ALERTS
    # =====================================================

    alerts = []


    if rain_probability >= 70:

        alerts.append({
            "type": "Rain Alert",
            "message":
                "High chance of rain. Carry an umbrella."
        })


    if temperature >= 40:

        alerts.append({
            "type": "Extreme Heat",
            "message":
                "Extreme heat detected. Stay hydrated "
                "and avoid prolonged outdoor activity."
        })


    if temperature <= 10:

        alerts.append({
            "type": "Cold Alert",
            "message":
                "Very low temperature detected. "
                "Wear warm clothing."
        })


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


    if rain_probability >= 80:

        travel_score -= 35

    elif rain_probability >= 60:

        travel_score -= 25

    elif rain_probability >= 40:

        travel_score -= 15

    elif rain_probability >= 20:

        travel_score -= 5


    if temperature >= 40:

        travel_score -= 25

    elif temperature >= 35:

        travel_score -= 15

    elif temperature <= 10:

        travel_score -= 15


    if weather_code >= 95:

        travel_score -= 30


    if wind_speed >= 50:

        travel_score -= 20

    elif wind_speed >= 35:

        travel_score -= 10


    travel_score = max(
        0,
        min(100, travel_score)
    )


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

        location = await get_coordinates(city)

        weather_data = await get_weather(
            location["latitude"],
            location["longitude"]
        )

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

        weather_data = await get_weather(
            latitude,
            longitude
        )

        processed = process_weather(
            weather_data
        )


        # =================================================
        # REVERSE GEOCODING
        # =================================================

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


        # =================================================
        # FIND CITY
        # =================================================

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


        # =================================================
        # RETURN DATA
        # =================================================

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
# WEATHERGPT CHATBOT
# =========================================================

@app.post("/chat")
async def chat(request: ChatRequest):

    try:

        # =================================================
        # 1. CLEAN USER MESSAGE
        # =================================================

        original_message = request.message.strip()

        message = original_message.lower()


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
        # 2. GET LOCATION
        # =================================================

        location = await get_coordinates(
            request.city
        )


        # =================================================
        # 3. GET WEATHER
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


        # TODAY

        today_rain = today.get(
            "rain_probability",
            0
        )

        today_min = today.get(
            "min_temperature",
            temperature
        )

        today_max = today.get(
            "max_temperature",
            temperature
        )

        today_weather = today.get(
            "weather",
            weather_description
        )


        # TOMORROW

        tomorrow_rain = tomorrow.get(
            "rain_probability",
            0
        )

        tomorrow_min = tomorrow.get(
            "min_temperature",
            temperature
        )

        tomorrow_max = tomorrow.get(
            "max_temperature",
            temperature
        )

        tomorrow_weather = tomorrow.get(
            "weather",
            "Unknown weather"
        )


        # =================================================
        # 7. DATE DETECTION
        # =================================================

        asking_tomorrow = (

            "tomorrow" in message

            or "kal" in message

            or "कल" in original_message
        )


        asking_today = (

            "today" in message

            or "aaj" in message

            or "आज" in original_message
        )


        if asking_tomorrow:

            selected_day = "tomorrow"

        else:

            selected_day = "today"


        # =================================================
        # 8. LANGUAGE DETECTION
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
            "यात्रा",
            "कपड़े",
            "कपड़ा",
            "पहनना",
            "पहनूं",
            "पहनूँ"
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
            "kapde",
            "kapda",
            "pehnu",
            "pahnu",
            "pehne"
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
        # 9. INTENT DETECTION
        # =================================================


        # -------------------------------------------------
        # CLOTHING INTENT
        # -------------------------------------------------

        clothing_words = [

            "wear",
            "clothes",
            "clothing",
            "dress",
            "outfit",
            "what should i wear",
            "what to wear",

            "kapde",
            "kapda",
            "kya pehnu",
            "kya pahnu",
            "kya pehne",
            "pehnu",
            "pahnu",
            "pehne",

            "कपड़े",
            "कपड़ा",
            "क्या पहनूं",
            "क्या पहनूँ",
            "क्या पहनना चाहिए"
        ]


        is_clothing_question = any(

            word in message
            or word in original_message

            for word in clothing_words
        )


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
        # 10. RESPONSE GENERATION
        # =================================================

        response_text = ""


        # =================================================
        # CLOTHING RESPONSE
        # =================================================

        if is_clothing_question:

            if selected_day == "tomorrow":

                clothing_weather = tomorrow
                day_name = "tomorrow"

            else:

                clothing_weather = today
                day_name = "today"


            clothing_min = clothing_weather.get(
                "min_temperature",
                temperature
            )

            clothing_max = clothing_weather.get(
                "max_temperature",
                temperature
            )

            clothing_rain = clothing_weather.get(
                "rain_probability",
                0
            )

            clothing_weather_type = clothing_weather.get(
                "weather",
                "Unknown weather"
            )


            # =================================================
            # CLOTHING ADVICE
            # =================================================

            if clothing_rain >= 60:

                clothing_advice = (
                    "Carry an umbrella or raincoat. "
                    "Wear light, breathable clothes and "
                    "prefer waterproof footwear."
                )

            elif clothing_max >= 35:

                clothing_advice = (
                    "Wear light, loose and breathable "
                    "cotton clothes. Avoid heavy clothing "
                    "and stay hydrated."
                )

            elif clothing_max >= 30:

                clothing_advice = (
                    "Wear light and comfortable cotton clothes."
                )

            elif clothing_min <= 15:

                clothing_advice = (
                    "Wear warm clothes such as a sweater "
                    "or jacket."
                )

            else:

                clothing_advice = (
                    "Comfortable regular clothes should "
                    "be suitable for the weather."
                )


            # =================================================
            # ENGLISH CLOTHING RESPONSE
            # =================================================

            if language == "english":

                response_text = (

                    f"For {day_name} in "
                    f"{location['name']}, "

                    f"the expected weather is "
                    f"{clothing_weather_type}. "

                    f"Temperature may range from "
                    f"{clothing_min}°C to "
                    f"{clothing_max}°C, "

                    f"with a {clothing_rain}% "
                    f"chance of rain. "

                    f"{clothing_advice}"
                )


            # =================================================
            # HINGLISH CLOTHING RESPONSE
            # =================================================

            elif language == "hinglish":

                day_text = (

                    "Aaj"

                    if day_name == "today"

                    else "Kal"
                )


                if clothing_rain >= 60:

                    clothing_advice_hinglish = (

                        "Umbrella ya raincoat carry karo. "
                        "Light aur breathable clothes "
                        "pehno aur waterproof footwear "
                        "prefer karo."
                    )

                elif clothing_max >= 35:

                    clothing_advice_hinglish = (

                        "Light, loose aur breathable "
                        "cotton clothes pehno. "
                        "Heavy clothes avoid karo aur "
                        "hydrated raho."
                    )

                elif clothing_max >= 30:

                    clothing_advice_hinglish = (

                        "Light aur comfortable cotton "
                        "clothes pehno."
                    )

                elif clothing_min <= 15:

                    clothing_advice_hinglish = (

                        "Sweater ya jacket jaise warm "
                        "clothes pehno."
                    )

                else:

                    clothing_advice_hinglish = (

                        "Comfortable regular clothes "
                        "pehen sakte ho."
                    )


                response_text = (

                    f"{day_text} {location['name']} "
                    f"mein weather "
                    f"{clothing_weather_type} rehne ka "
                    f"chance hai. "

                    f"Temperature {clothing_min}°C se "
                    f"{clothing_max}°C ke beech rahega "
                    f"aur baarish ki probability "
                    f"{clothing_rain}% hai. "

                    f"{clothing_advice_hinglish}"
                )


            # =================================================
            # HINDI CLOTHING RESPONSE
            # =================================================

            else:

                hindi_day = (

                    "आज"

                    if day_name == "today"

                    else "कल"
                )


                if clothing_rain >= 60:

                    clothing_advice_hindi = (

                        "छतरी या रेनकोट साथ रखें। "
                        "हल्के और आरामदायक कपड़े पहनें "
                        "और वाटरप्रूफ जूते पहनना बेहतर रहेगा।"
                    )

                elif clothing_max >= 35:

                    clothing_advice_hindi = (

                        "हल्के, ढीले और सूती कपड़े पहनें। "
                        "भारी कपड़ों से बचें और पर्याप्त "
                        "पानी पिएं।"
                    )

                elif clothing_max >= 30:

                    clothing_advice_hindi = (

                        "हल्के और आरामदायक सूती कपड़े पहनें।"
                    )

                elif clothing_min <= 15:

                    clothing_advice_hindi = (

                        "स्वेटर या जैकेट जैसे गर्म कपड़े पहनें।"
                    )

                else:

                    clothing_advice_hindi = (

                        "आरामदायक सामान्य कपड़े पहन सकते हैं।"
                    )


                response_text = (

                    f"{hindi_day} {location['name']} में "
                    f"मौसम {clothing_weather_type} "
                    f"रहने की संभावना है। "

                    f"तापमान {clothing_min}°C से "
                    f"{clothing_max}°C के बीच रहेगा और "
                    f"बारिश की संभावना "
                    f"{clothing_rain}% है। "

                    f"{clothing_advice_hindi}"
                )


        # =================================================
        # WEATHER RESPONSE
        # =================================================

        elif is_weather_question:

            if language == "hindi":

                response_text = (

                    f"{location['name']} में अभी मौसम "
                    f"{weather_description} है। "

                    f"तापमान {temperature}°C है और "
                    f"महसूस होने वाला तापमान "
                    f"{feels_like}°C है। "

                    f"नमी {humidity}% और हवा की गति "
                    f"{wind_speed} km/h है।"
                )


            elif language == "hinglish":

                response_text = (

                    f"{location['name']} mein abhi "
                    f"{weather_description} hai. "

                    f"Temperature {temperature}°C hai aur "
                    f"feels-like temperature "
                    f"{feels_like}°C hai. "

                    f"Humidity {humidity}% hai aur "
                    f"wind speed {wind_speed} km/h hai."
                )


            else:

                response_text = (

                    f"The current weather in "
                    f"{location['name']} is "
                    f"{weather_description}. "

                    f"The temperature is "
                    f"{temperature}°C and it feels like "
                    f"{feels_like}°C. "

                    f"Humidity is {humidity}% and "
                    f"wind speed is "
                    f"{wind_speed} km/h."
                )


        # =================================================
        # RAIN RESPONSE
        # =================================================

        elif is_rain_question:

            if selected_day == "tomorrow":

                rain_value = tomorrow_rain

                selected_weather = tomorrow_weather

                day_text_hindi = "कल"

                day_text_hinglish = "Kal"

                day_text_english = "tomorrow"

            else:

                rain_value = today_rain

                selected_weather = today_weather

                day_text_hindi = "आज"

                day_text_hinglish = "Aaj"

                day_text_english = "today"


            if language == "hindi":

                response_text = (

                    f"{day_text_hindi} {location['name']} में "
                    f"बारिश की संभावना {rain_value}% है। "

                    f"मौसम {selected_weather} रहने की "
                    f"संभावना है।"
                )


            elif language == "hinglish":

                response_text = (

                    f"{day_text_hinglish} {location['name']} mein "
                    f"baarish ki probability "
                    f"{rain_value}% hai. "

                    f"Weather {selected_weather} rehne "
                    f"ka chance hai."
                )


            else:

                response_text = (

                    f"There is a {rain_value}% chance "
                    f"of rain in {location['name']} "
                    f"{day_text_english}. "

                    f"The expected weather is "
                    f"{selected_weather}."
                )


        # =================================================
        # TEMPERATURE RESPONSE
        # =================================================

        elif is_temperature_question:

            if selected_day == "tomorrow":

                temp_min = tomorrow_min
                temp_max = tomorrow_max

                day_text_hindi = "कल"
                day_text_hinglish = "Kal"
                day_text_english = "tomorrow"

            else:

                temp_min = today_min
                temp_max = today_max

                day_text_hindi = "आज"
                day_text_hinglish = "Aaj"
                day_text_english = "today"


            if language == "hindi":

                response_text = (

                    f"{day_text_hindi} {location['name']} में "
                    f"तापमान लगभग {temp_min}°C से "
                    f"{temp_max}°C के बीच रहेगा। "

                    f"अभी तापमान {temperature}°C है।"
                )


            elif language == "hinglish":

                response_text = (

                    f"{day_text_hinglish} {location['name']} mein "
                    f"temperature approximately "
                    f"{temp_min}°C se {temp_max}°C ke beech "
                    f"rahega. "

                    f"Abhi temperature {temperature}°C hai."
                )


            else:

                response_text = (

                    f"The temperature in "
                    f"{location['name']} "
                    f"{day_text_english} may range from "
                    f"{temp_min}°C to {temp_max}°C. "

                    f"The current temperature is "
                    f"{temperature}°C."
                )


        # =================================================
        # TRAVEL RESPONSE
        # =================================================

        elif is_travel_question:

            if selected_day == "tomorrow":

                selected_rain = tomorrow_rain

                selected_weather = tomorrow_weather

                selected_max = tomorrow_max

                selected_min = tomorrow_min

                selected_score = 100


                if selected_rain >= 80:

                    selected_score -= 35

                elif selected_rain >= 60:

                    selected_score -= 25

                elif selected_rain >= 40:

                    selected_score -= 15

                elif selected_rain >= 20:

                    selected_score -= 5


                if selected_max >= 40:

                    selected_score -= 25

                elif selected_max >= 35:

                    selected_score -= 15

                elif selected_min <= 10:

                    selected_score -= 15


                if "thunderstorm" in selected_weather.lower():

                    selected_score -= 30


                selected_score = max(
                    0,
                    min(100, selected_score)
                )


                if selected_score >= 75:

                    selected_status = "Good for travel"

                elif selected_score >= 50:

                    selected_status = "Travel with caution"

                else:

                    selected_status = "Not recommended"


                day_text_hindi = "कल"

                day_text_hinglish = "Kal"

                day_text_english = "tomorrow"


            else:

                selected_rain = today_rain

                selected_weather = today_weather

                selected_score = travel_score

                selected_status = travel_status

                day_text_hindi = "आज"

                day_text_hinglish = "Aaj"

                day_text_english = "today"


            if language == "hindi":

                response_text = (

                    f"{day_text_hindi} {location['name']} के लिए "
                    f"Travel Score {selected_score}/100 है। "

                    f"स्थिति: {selected_status}। "

                    f"मौसम {selected_weather} है और "
                    f"बारिश की संभावना "
                    f"{selected_rain}% है।"
                )


            elif language == "hinglish":

                response_text = (

                    f"{day_text_hinglish} {location['name']} ka "
                    f"Travel Score {selected_score}/100 hai. "

                    f"Status: {selected_status}. "

                    f"Weather {selected_weather} hai aur "
                    f"baarish ki probability "
                    f"{selected_rain}% hai."
                )


            else:

                response_text = (

                    f"The Travel Score for "
                    f"{location['name']} "
                    f"{day_text_english} is "
                    f"{selected_score}/100. "

                    f"Status: {selected_status}. "

                    f"The expected weather is "
                    f"{selected_weather} with a "
                    f"{selected_rain}% chance of rain."
                )


        # =================================================
        # FORECAST RESPONSE
        # =================================================

        elif is_forecast_question:

            if selected_day == "tomorrow":

                forecast_weather = tomorrow_weather

                forecast_min = tomorrow_min

                forecast_max = tomorrow_max

                forecast_rain = tomorrow_rain

                day_text_hindi = "कल"

                day_text_hinglish = "Kal"

                day_text_english = "tomorrow"

            else:

                forecast_weather = today_weather

                forecast_min = today_min

                forecast_max = today_max

                forecast_rain = today_rain

                day_text_hindi = "आज"

                day_text_hinglish = "Aaj"

                day_text_english = "today"


            if language == "hindi":

                response_text = (

                    f"{day_text_hindi} {location['name']} में "
                    f"मौसम {forecast_weather} रहने की "
                    f"संभावना है। "

                    f"तापमान लगभग {forecast_min}°C से "
                    f"{forecast_max}°C के बीच रहेगा और "

                    f"बारिश की संभावना "
                    f"{forecast_rain}% है।"
                )


            elif language == "hinglish":

                response_text = (

                    f"{day_text_hinglish} {location['name']} mein "
                    f"weather {forecast_weather} rehne ka "
                    f"chance hai. "

                    f"Temperature around {forecast_min}°C se "
                    f"{forecast_max}°C ke beech rahega aur "

                    f"baarish ki probability "
                    f"{forecast_rain}% hai."
                )


            else:

                response_text = (

                    f"{day_text_english.capitalize()} in "
                    f"{location['name']}, "

                    f"the expected weather is "
                    f"{forecast_weather}. "

                    f"Temperature may range from "
                    f"{forecast_min}°C to "
                    f"{forecast_max}°C, "

                    f"with a {forecast_rain}% chance "
                    f"of rain."
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

                    f"बारिश की संभावना "
                    f"{today_rain}% है। "

                    f"Travel Score "
                    f"{travel_score}/100 है।"
                )


            elif language == "hinglish":

                response_text = (

                    f"{location['name']} mein abhi "
                    f"{weather_description} hai aur "
                    f"temperature {temperature}°C hai. "

                    f"Baarish ki probability "
                    f"{today_rain}% hai. "

                    f"Travel Score "
                    f"{travel_score}/100 hai."
                )


            else:

                response_text = (

                    f"In {location['name']}, the current "
                    f"weather is {weather_description} "
                    f"with a temperature of "
                    f"{temperature}°C. "

                    f"The chance of rain is "
                    f"{today_rain}% and the Travel Score "
                    f"is {travel_score}/100."
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
