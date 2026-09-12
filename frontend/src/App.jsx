import { useState } from "react";
import "./App.css";

// =========================
// DEPLOYED BACKEND URL
// =========================
const API_BASE_URL = "https://weathergpt-backend-kid2.onrender.com";

function App() {
  const [city, setCity] = useState("Kanpur");
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [chatMessage, setChatMessage] = useState("");
  const [chatResponse, setChatResponse] = useState("");

  // =========================
  // SEARCH WEATHER BY CITY
  // =========================
  const searchWeather = async () => {
    if (!city.trim()) {
      setError("Please enter a city name.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/weather?city=${encodeURIComponent(city)}`
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Unable to get weather");
      }

      const data = await response.json();

      setWeather(data);
      setChatResponse("");
    } catch (err) {
      setError(err.message);
      setWeather(null);
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // WEATHER EMOJI
  // =========================
  const getWeatherEmoji = (weatherText) => {
    if (!weatherText) return "🌤️";

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

  // =========================
  // FORMAT DATE
  // =========================
  const formatDate = (dateString) => {
    const date = new Date(dateString);

    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  };

  // =========================
  // WEATHERGPT CHATBOT
  // =========================
  const askWeatherGPT = async () => {
    if (!chatMessage.trim()) return;

    if (!weather) {
      setChatResponse("Please search for a city first.");
      return;
    }

    console.log("Sending chat request...");
    console.log("Message:", chatMessage);
    console.log("City:", weather.city);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: chatMessage,
          city: weather.city,
        }),
      });

      console.log("Response status:", response.status);

      const data = await response.json();

      console.log("Backend response:", data);

      if (!response.ok) {
        throw new Error(data.detail || "Backend returned an error");
      }

      setChatResponse(data.response);
      setChatMessage("");
    } catch (error) {
      console.error("CHAT ERROR:", error);

      setChatResponse(`❌ Error: ${error.message}`);
    }
  };

  // =========================
  // MY LOCATION
  // =========================
  const getMyLocationWeather = () => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser.");
      return;
    }

    setLoading(true);
    setError("");

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        try {
          const response = await fetch(
            `${API_BASE_URL}/weather/location?latitude=${latitude}&longitude=${longitude}`
          );

          if (!response.ok) {
            throw new Error(
              "Unable to get your location weather."
            );
          }

          const data = await response.json();

          setWeather(data);
          setCity(data.city);
          setChatResponse("");
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

        setLoading(false);
      }
    );
  };

  // =========================
  // UI
  // =========================
  return (
    <div className="app">

      {/* ================= HEADER ================= */}

      <header className="top-header">
        <h1>🌦️ WeatherGPT</h1>

        <p>Your AI-powered weather companion</p>
      </header>

      {/* ================= SEARCH ================= */}

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
          onClick={getMyLocationWeather}
        >
          📍 My Location
        </button>

      </section>

      {/* ================= LOADING ================= */}

      {loading && (
        <div className="message">
          🌍 Getting latest weather data...
        </div>
      )}

      {/* ================= ERROR ================= */}

      {error && (
        <div className="error">
          ⚠️ {error}
        </div>
      )}

      {/* ================= WEATHER ================= */}

      {weather && !loading && (
        <>
          {/* ================= CURRENT WEATHER ================= */}

          <section className="current-card">

            <div className="main-weather">

              <div className="weather-icon">
                {getWeatherEmoji(
                  weather.current.weather
                )}
              </div>

              <div>

                <div className="temperature">
                  {Math.round(
                    weather.current.temperature
                  )}
                  °C
                </div>

                <div className="condition">
                  {weather.current.weather}
                </div>

                <div className="feels">
                  Feels like{" "}
                  {Math.round(
                    weather.current.feels_like
                  )}
                  °C
                </div>

              </div>

            </div>

            {/* ================= WEATHER DETAILS ================= */}

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

          {/* ================= WEATHER ALERTS ================= */}

          {weather.alerts &&
            weather.alerts.length > 0 && (
              <section className="alert-section">

                <h2>⚠️ Weather Alerts</h2>

                <div className="alert-container">

                  {weather.alerts.map(
                    (alert, index) => (

                      <div
                        className="alert-card"
                        key={index}
                      >

                        <strong>
                          {alert.type}
                        </strong>

                        <p>
                          {alert.message}
                        </p>

                      </div>

                    )
                  )}

                </div>

              </section>
            )}

          {/* ================= TRAVEL DECISION ================= */}

          <section className="travel-section">

            <div className="travel-header">

              <div>

                <h2>🧳 Travel Decision</h2>

                <p>
                  Weather-based travel recommendation
                </p>

              </div>

              <div className="travel-score">

                {weather.travel_score}

                <span>/100</span>

              </div>

            </div>

            <div className="travel-status">

              {weather.travel_score >= 75
                ? "🟢 Good for travel"
                : weather.travel_score >= 50
                ? "🟡 Travel with caution"
                : "🔴 Not recommended"}

            </div>

            <div className="travel-factors">

              <div className="travel-factor">

                <span>🌧️</span>

                <div>

                  <strong>
                    Rain Probability
                  </strong>

                  <p>
                    {weather.forecast[0].rain_probability}%
                  </p>

                </div>

              </div>

              <div className="travel-factor">

                <span>🌡️</span>

                <div>

                  <strong>
                    Temperature
                  </strong>

                  <p>
                    {Math.round(
                      weather.current.temperature
                    )}
                    °C
                  </p>

                </div>

              </div>

              <div className="travel-factor">

                <span>💨</span>

                <div>

                  <strong>
                    Wind Speed
                  </strong>

                  <p>
                    {weather.current.wind_speed} km/h
                  </p>

                </div>

              </div>

            </div>

          </section>

          {/* ================= RECOMMENDATIONS ================= */}

          <section className="recommendation-section">

            <h2>
              🎯 WeatherGPT Recommendations
            </h2>

            <div className="recommendation-container">

              {weather.recommendations.map(
                (recommendation, index) => (

                  <div
                    className="recommendation-card"
                    key={index}
                  >
                    💡 {recommendation}
                  </div>

                )
              )}

            </div>

          </section>

          {/* ================= 7 DAY FORECAST ================= */}

          <section className="forecast-section">

            <h2>📅 7-Day Forecast</h2>

            <div className="forecast-container">

              {weather.forecast.map(
                (day, index) => (

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
                      {getWeatherEmoji(
                        day.weather
                      )}
                    </div>

                    <p className="forecast-condition">
                      {day.weather}
                    </p>

                    <div className="temperatures">

                      <strong>
                        {Math.round(
                          day.max_temperature
                        )}
                        °
                      </strong>

                      <span>
                        {Math.round(
                          day.min_temperature
                        )}
                        °
                      </span>

                    </div>

                    <div className="rain">
                      🌧️ {day.rain_probability}%
                    </div>

                  </div>

                )
              )}

            </div>

          </section>

          {/* ================= WEATHERGPT CHATBOT ================= */}

          <section className="chat-section">

            <div className="chat-header">

              <div className="ai-icon">
                🤖
              </div>

              <div>

                <h2>
                  Ask WeatherGPT
                </h2>

                <p>
                  Your conversational weather assistant
                </p>

              </div>

            </div>

            <div className="chat-box">

              <div className="bot-message">

                🤖 Hi! Ask me about the weather in{" "}
                {weather.city}.

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
                onChange={(e) =>
                  setChatMessage(e.target.value)
                }
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

      {/* ================= WELCOME ================= */}

      {!weather && !loading && !error && (

        <div className="welcome">

          <div className="welcome-icon">
            🌍
          </div>

          <h2>
            Welcome to WeatherGPT
          </h2>

          <p>
            Enter a city to get real-time weather
            information.
          </p>

        </div>

      )}

    </div>
  );
}

export default App;