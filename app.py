import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Weather App", page_icon="🌦️", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #e0f2fe 0%, #fef9c3 50%, #fce7f3 100%); }
.banner {
    background: linear-gradient(90deg, #0ea5e9, #6366f1, #a855f7);
    color: white; padding: 26px 20px; border-radius: 18px;
    text-align: center; font-size: 2.1rem; font-weight: 700;
    box-shadow: 0 8px 20px rgba(14, 165, 233, 0.35); margin-bottom: 22px;
}
h3 { color: #4338ca !important; border-left: 6px solid #0ea5e9; padding-left: 12px !important; }
div[data-testid="stMetric"] {
    background: white; padding: 16px; border-radius: 16px;
    border-top: 6px solid #0ea5e9; box-shadow: 0 6px 16px rgba(0,0,0,0.10);
}
div[data-testid="stMetric"] * { color: #1f2937 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="banner">🌦️ Weather App</div>', unsafe_allow_html=True)

# ---------- Weather code -> description ----------
WEATHER_CODES = {
    0: "☀️ Clear sky", 1: "🌤️ Mainly clear", 2: "⛅ Partly cloudy", 3: "☁️ Overcast",
    45: "🌫️ Fog", 48: "🌫️ Fog", 51: "🌦️ Light drizzle", 53: "🌦️ Drizzle",
    55: "🌧️ Heavy drizzle", 61: "🌧️ Light rain", 63: "🌧️ Rain", 65: "🌧️ Heavy rain",
    71: "🌨️ Light snow", 73: "🌨️ Snow", 75: "❄️ Heavy snow", 80: "🌦️ Rain showers",
    81: "🌧️ Rain showers", 82: "⛈️ Violent showers", 95: "⛈️ Thunderstorm",
    96: "⛈️ Thunderstorm + hail", 99: "⛈️ Thunderstorm + hail",
}


def describe(code):
    return WEATHER_CODES.get(code, "🌡️ Unknown")


# ---------- API functions ----------
@st.cache_data(ttl=600)
def get_location(city):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    r = requests.get(url, params={"name": city, "count": 1}, timeout=10)
    r.raise_for_status()
    results = r.json().get("results")
    return results[0] if results else None


@st.cache_data(ttl=600)
def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code",
        "hourly": "temperature_2m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
        "timezone": "auto",
        "forecast_days": 7,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


# ---------- Search box ----------
city = st.text_input("🔍 City ka naam likhein", value="Delhi")

if city.strip():
    try:
        loc = get_location(city.strip())
    except requests.RequestException:
        st.error("Internet ya API ki problem hai. Thodi der baad try karein.")
        st.stop()

    if loc is None:
        st.warning("City nahi mili. Spelling check karein.")
        st.stop()

    try:
        data = get_weather(loc["latitude"], loc["longitude"])
    except requests.RequestException:
        st.error("Weather data nahi mil paya. Dobara try karein.")
        st.stop()

    place = f"{loc['name']}, {loc.get('admin1', '')}, {loc.get('country', '')}"
    cur = data["current"]

    # ---------- Current weather ----------
    st.subheader(f"📍 {place}")
    st.markdown(f"### {describe(cur['weather_code'])}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ Temperature", f"{cur['temperature_2m']} °C")
    c2.metric("🤒 Feels Like", f"{cur['apparent_temperature']} °C")
    c3.metric("💧 Humidity", f"{cur['relative_humidity_2m']} %")
    c4.metric("💨 Wind", f"{cur['wind_speed_10m']} km/h")

    # ---------- Next 24 hours ----------
    st.subheader("⏰ Agle 24 Ghante ka Temperature")
    hourly = pd.DataFrame({
        "time": pd.to_datetime(data["hourly"]["time"]),
        "temp": data["hourly"]["temperature_2m"],
    })
    now = pd.to_datetime(cur["time"])
    hourly = hourly[hourly["time"] >= now].head(24)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(hourly["time"].dt.strftime("%H:%M"), hourly["temp"],
            marker="o", color="#f97316", linewidth=2.5)
    ax.fill_between(range(len(hourly)), hourly["temp"], alpha=0.15, color="#f97316")
    ax.set_ylabel("Temperature (°C)")
    plt.xticks(rotation=60, fontsize=8)
    ax.grid(alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)

    # ---------- 7-day forecast ----------
    st.subheader("📅 7 Din ka Forecast")
    daily = pd.DataFrame({
        "Date": pd.to_datetime(data["daily"]["time"]).strftime("%a %d %b"),
        "Weather": [describe(c) for c in data["daily"]["weather_code"]],
        "Max °C": data["daily"]["temperature_2m_max"],
        "Min °C": data["daily"]["temperature_2m_min"],
        "Rain (mm)": data["daily"]["precipitation_sum"],
    })
    st.dataframe(daily, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌡️ Max / Min Temperature")
        fig, ax = plt.subplots()
        ax.plot(daily["Date"], daily["Max °C"], marker="o", color="#ef4444", label="Max")
        ax.plot(daily["Date"], daily["Min °C"], marker="o", color="#3b82f6", label="Min")
        ax.fill_between(daily["Date"], daily["Min °C"], daily["Max °C"], alpha=0.12, color="#a855f7")
        ax.legend()
        ax.grid(alpha=0.3)
        plt.xticks(rotation=45)
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        st.subheader("🌧️ Rain Forecast")
        fig, ax = plt.subplots()
        ax.bar(daily["Date"], daily["Rain (mm)"], color="#0ea5e9")
        ax.set_ylabel("Rain (mm)")
        plt.xticks(rotation=45)
        st.pyplot(fig)
        plt.close(fig)

st.caption("Data source: Open-Meteo.com (free, no API key needed)")