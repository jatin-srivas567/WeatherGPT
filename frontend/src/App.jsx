  import { useState } from "react";
import "./App.css";

function App() {
  const [city, setCity] = useState("Kanpur");
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const searchWeather = async () => {
    if (!city.trim()) {
      setError("Please enter a city name.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/weather?city=${encodeURIComponent(city)}`
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Unable to get weather");
      }

      const data = await response.json();

      setWeather(data);
    } catch (err) {
      setError(err.message);
      setWeather(null);
    } finally {
      setLoading(false);
    }
  };

  const getWeatherEmoji = (weatherText) => {
    const text = weatherText.toLowerCase();

    if (text.includes("thunderstorm")) return "⛈️";
    if (text.includes("rain")) return "🌧️";
    if (text.includes("drizzle")) return "🌦️";
    if (text.includes("snow")) return "❄️";
    if (text.includes("fog")) return "🌫️";
    if (text.includes("cloud")) return "☁️";
    if (text.includes("clear")) return "☀️";

    return "🌤️";
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);

    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  };

  const [chatMessage, setChatMessage] = useState("");
const [chatResponse, setChatResponse] = useState("");

const askWeatherGPT = () => {
  if (!chatMessage.trim()) return;

  const question = chatMessage.toLowerCase().trim();

  const tomorrow = weather.forecast[1];
  const temperature = weather.current.temperature;
  const rainProbability = tomorrow.rain_probability;

  // 🌧️ RAIN QUESTIONS
  if (
    question.includes("rain") ||
    question.includes("barish") ||
    question.includes("baarish") ||
    question.includes("बारिश") ||
    question.includes("बरसात") ||
    question.includes("paani padega") ||
    question.includes("pani padega") ||
    question.includes("chhata") ||
    question.includes("छाता")
  ) {
    if (rainProbability >= 70) {
      setChatResponse(
        `🌧️ Haan, kal baarish ki high possibility hai. Rain probability ${rainProbability}% hai. Chhata zaroor le jaiye.`
      );
    } else if (rainProbability >= 40) {
      setChatResponse(
        `🌦️ Kal baarish ki moderate possibility hai. Rain probability ${rainProbability}% hai. Chhata saath rakhna better rahega.`
      );
    } else {
      setChatResponse(
        `☀️ Kal baarish ki possibility kam hai. Rain probability sirf ${rainProbability}% hai.`
      );
    }
  }

  // ✈️ TRAVEL QUESTIONS
  else if (
    question.includes("travel") ||
    question.includes("trip") ||
    question.includes("go tomorrow") ||
    question.includes("ghoomne") ||
    question.includes("ghumna") ||
    question.includes("bahar") ||
    question.includes("बाहर") ||
    question.includes("yatra") ||
    question.includes("यात्रा") ||
    question.includes("safar") ||
    question.includes("सफर") ||
    question.includes("ja sakta") ||
    question.includes("jaa sakta") ||
    question.includes("jaun") ||
    question.includes("जाऊं") ||
    question.includes("kal travel") ||
    question.includes("kal bahar")
  ) {
    if (rainProbability >= 70) {
      setChatResponse(
        `🚫 Kal travel karna difficult ho sakta hai. Baarish ki probability ${rainProbability}% hai. Agar possible ho to trip postpone karein ya rain protection lekar niklein.`
      );
    } else if (rainProbability >= 40) {
      setChatResponse(
        `⚠️ Kal travel kar sakte hain, lekin baarish ka chance ${rainProbability}% hai. Chhata/raincoat saath rakhna better rahega.`
      );
    } else {
      setChatResponse(
        `✅ Kal travel ke liye weather generally suitable lag raha hai. Baarish ki probability sirf ${rainProbability}% hai.`
      );
    }
  }
   // 👕 CLOTHING QUESTIONS
  else if (
    question.includes("wear") ||
    question.includes("clothes") ||
    question.includes("dress") ||
    question.includes("kapde") ||
    question.includes("कपड़े") ||
    question.includes("kya pehnu") ||
    question.includes("kya pahnu") ||
    question.includes("क्या पहनूं") ||
    question.includes("garmi me kya pehnu") ||
  question.includes("garmi mein kya pehnu") ||
  question.includes("garmi me kya pahnu") ||
  question.includes("garmi mein kya pahnu") ||
  question.includes("गर्मी में क्या पहनूं")||
    question.includes("pehnu") ||
    question.includes("pahnu") ||
    question.includes("pehenna") ||
    question.includes("kya pehen") ||
    question.includes("kya pahen")
  )
   {
    if (temperature >= 35) {
      setChatResponse(
        `👕 Aaj ${Math.round(
          temperature
        )}°C temperature hai. Light, loose aur cotton clothes pehniye. Bahar ja rahe hain to paani bhi saath rakhein.`
      );
    } else if (temperature >= 25) {
      setChatResponse(
        `👕 Aaj ${Math.round(
          temperature
        )}°C hai. Light cotton clothes comfortable rahenge.`
      );
    } else if (temperature >= 15) {
      setChatResponse(
        `🧥 Aaj ${Math.round(
          temperature
        )}°C hai. Full-sleeve clothes ya light jacket suitable rahegi.`
      );
    } else {
      setChatResponse(
        `🧥 Aaj ${Math.round(
          temperature
        )}°C hai. Warm clothes aur extra layer pehenna better rahega.`
      );
    }
  }

  // 🌡️ TEMPERATURE QUESTIONS
  else if (
    question.includes("temperature") ||
    question.includes("temp") ||
    question.includes("taapman") ||
    question.includes("तापमान") ||
    question.includes("garmi") ||
    question.includes("गर्मी") ||
    question.includes("hot") ||
    question.includes("garam") ||
    question.includes("ठंड") ||
    question.includes("thand") ||
    question.includes("cold")
  ) {
    if (temperature >= 35) {
      setChatResponse(
        `🌡️ Aaj temperature ${Math.round(
          temperature
        )}°C hai. Kaafi garmi hai. Hydrated rahein aur unnecessary outdoor activity avoid karein.`
      );
    } else if (temperature >= 25) {
      setChatResponse(
        `🌡️ Aaj temperature ${Math.round(
          temperature
        )}°C hai. Weather relatively warm hai.`
      );
    } else if (temperature >= 15) {
      setChatResponse(
        `🌡️ Aaj temperature ${Math.round(
          temperature
        )}°C hai. Weather comfortable hai.`
      );
    } else {
      setChatResponse(
        `🌡️ Aaj temperature ${Math.round(
          temperature
        )}°C hai. Kaafi thand hai, warm clothes pehenna better rahega.`
      );
    }
  }

 

  // ❓ DEFAULT RESPONSE
  else {
    setChatResponse(
      "🤖 Main rain, travel, temperature aur clothing ke baare mein answer kar sakta hoon. Example: 'Kal baarish hogi?', 'Kya main kal travel kar sakta hoon?', ya 'Aaj kya pehnu?'"
    );
  }

  setChatMessage("");
};

  return (
    <div className="app">
      {/* HEADER */}
      <header className="top-header">
      <h1 color="Black">🌦️ WeatherGPT</h1>
      <p>Your AI-powered weather companion</p>

  {weather && (
    <div className="location">
      📍 {weather.city}, {weather.country}
    </div>
  )}
</header>


      {/* SEARCH */}
      <section className="search-section">

  <input
    type="text"
    placeholder="Enter city name..."
    value={city}
    onChange={(e) => setCity(e.target.value)}
    onKeyDown={(e) => {
      if (e.key === "Enter") {
        searchWeather();
      }
    }}
  />

  <button onClick={searchWeather}>
    🔍 Search
  </button>

  <button
    className="location-button"
    onClick={() => {
      if (!navigator.geolocation) {
        setError("Geolocation is not supported by your browser.");
        return;
      }

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const latitude = position.coords.latitude;
          const longitude = position.coords.longitude;

          try {
            setLoading(true);
            setError("");

            const response = await fetch(
              `http://127.0.0.1:8000/weather/location?latitude=${latitude}&longitude=${longitude}`
            );

            if (!response.ok) {
              throw new Error("Unable to get your location weather.");
            }

            const data = await response.json();

            setWeather(data);
            setCity(data.city);
          } catch (err) {
            setError(err.message);
            setWeather(null);
          } finally {
            setLoading(false);
          }
        },
        () => {
          setError(
            "Location permission denied. Please allow location access."
          );
        }
      );
    }}
  >
    📍 My Location
  </button>

</section>


      {/* LOADING */}
      {loading && (
        <div className="message">
          🌍 Getting latest weather data...
        </div>
      )}


      {/* ERROR */}
      {error && (
        <div className="error">
          ⚠️ {error}
        </div>
      )}


      {/* WEATHER */}
      {weather && !loading && (
        <>

          {/* CURRENT WEATHER */}
          <section className="current-card">

            <div className="main-weather">

              <div className="weather-icon">
                {getWeatherEmoji(weather.current.weather)}
              </div>

              <div>

                <div className="temperature">
                  {Math.round(weather.current.temperature)}°C
                </div>

                <div className="condition">
                  {weather.current.weather}
                </div>

                <div className="feels">
                  Feels like{" "}
                  {Math.round(weather.current.feels_like)}°C
                </div>

              </div>

            </div>


            {/* WEATHER DETAILS */}
            <div className="weather-details">

              <div className="detail">
                <span>💧</span>

                <div>
                  <small>Humidity</small>
                  <strong>
                    {weather.current.humidity}%
                  </strong>
                </div>
              </div>


              <div className="detail">
                <span>💨</span>

                <div>
                  <small>Wind</small>
                  <strong>
                    {weather.current.wind_speed} km/h
                  </strong>
                </div>
              </div>


              <div className="detail">
                <span>🌧️</span>

                <div>
                  <small>Precipitation</small>
                  <strong>
                    {weather.current.precipitation} mm
                  </strong>
                </div>
              </div>

            </div>

          </section>

    {/* WEATHER ALERTS */}

{weather.alerts.length > 0 && (
  <section className="alert-section">

    <h2>⚠️ Weather Alerts</h2>

    <div className="alert-container">

      {weather.alerts.map((alert, index) => (

        <div
          className="alert-card"
          key={index}
        >

          <strong>{alert.type}</strong>

          <p>{alert.message}</p>

        </div>

      ))}

    </div>

  </section>
)}

          {/* WEATHER RECOMMENDATIONS */}

<section className="recommendation-section">

  <h2>🎯 WeatherGPT Recommendations</h2>

  <div className="recommendation-container">

    {weather.recommendations.map((recommendation, index) => (

      <div
        className="recommendation-card"
        key={index}
      >
        💡 {recommendation}
      </div>

    ))}

  </div>

</section>


          {/* 7 DAY FORECAST */}
          <section className="forecast-section">

            <h2>📅 7-Day Forecast</h2>

            <div className="forecast-container">

              {weather.forecast.map((day, index) => (

                <div
                  className="forecast-card"
                  key={day.date}
                >

                  <h3>
                    {index === 0
                      ? "Today"
                      : formatDate(day.date)}
                  </h3>

                  <div className="forecast-icon">
                    {getWeatherEmoji(day.weather)}
                  </div>

                  <p className="forecast-condition">
                    {day.weather}
                  </p>

                  <div className="temperatures">

                    <strong>
                      {Math.round(day.max_temperature)}°
                    </strong>

                    <span>
                      {Math.round(day.min_temperature)}°
                    </span>

                  </div>

                  <div className="rain">
                    🌧️ {day.rain_probability}%
                  </div>

                </div>

              ))}

            </div>

          </section>




         {/* WEATHERGPT CHATBOT */}

<section className="chat-section">

  <div className="chat-header">
    <div className="ai-icon">🤖</div>

    <div>
      <h2>Ask WeatherGPT</h2>
      <p>Your conversational weather assistant</p>
    </div>
  </div>

  <div className="chat-box">

    <div className="bot-message">
      🤖 Hi! Ask me about the weather in {weather.city}.
    </div>

    {chatResponse && (
      <div className="bot-message response">
        {chatResponse}
      </div>
    )}

  </div>

  <div className="chat-input">

    <input
      type="text"
      placeholder='Try "Will it rain tomorrow?"'
      value={chatMessage}
      onChange={(e) => setChatMessage(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          askWeatherGPT();
        }
      }}
    />

    <button onClick={askWeatherGPT}>
      Send
    </button>

  </div>

</section>

        </>
      )}


      {/* WELCOME */}
      {!weather && !loading && !error && (

        <div className="welcome">

          <div className="welcome-icon">
            🌍
          </div>

          <h2>
            Welcome to WeatherGPT
          </h2>

          <p>
            Enter a city to get real-time weather information.
          </p>

        </div>

      )}

    </div>
  );
}

export default App;