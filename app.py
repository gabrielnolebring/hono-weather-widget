from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

def fetch_weather():
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            page = browser.new_page()
            page.goto("https://www.nordicweather.se/")
            page.wait_for_load_state("networkidle")

            # Acceptera cookies
            try:
                page.click("text=Godkänn alla cookies", timeout=5000)
            except:
                print("🍪 Ingen cookie-popup")

            # Sök Hönö och tryck Enter
            page.wait_for_selector('#locationDesktop', timeout=10000)
            page.fill('#locationDesktop', "Hönö")
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(5000)  # Vänta extra för säkerhets skull

            # 💾 Spara debug.html
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(page.content())

            # 👉 Hämta väder just nu
            try:
                temp = page.locator(".forecast-row .temperature").first.inner_text().strip()
            except:
                print("❌ Kunde inte hitta temperatur")
                temp = None

            try:
                wind = page.locator(".forecast-row .wind-cell span").first.inner_text().strip()
            except:
                print("❌ Kunde inte hitta vind")
                wind = None

            try:
                rain_chance_now = page.locator(".forecast-row .percentage").first.inner_text().strip()
            except:
                print("❌ Kunde inte hitta regnchans")
                rain_chance_now = None

            try:
                sunset = page.locator(".sunset .value").first.inner_text().strip()
            except:
                sunset = "okänt"

            try:
                humidity = page.locator(".current-weather .humidity .value").first.inner_text().strip()
            except:
                humidity = None

            # 👉 Prognos för kommande dagar
            forecast = []
            print("🔍 Försöker hämta forecast från .day-section...")

            day_sections = page.locator("div.day-section")
            count = day_sections.count()
            print(f"📅 Hittade {count} dagar i forecast...")

            for i in range(count):
                day = day_sections.nth(i)
                try:
                    day_name = day.locator(".day-name").inner_text().strip()
                    day_temp = day.locator(".day-temp").inner_text().strip()
                    day_wind = day.locator(".day-wind span").inner_text().strip()
                    day_pop = day.locator(".day-certainty .percentage").inner_text().strip()
                    day_icon = day.locator(".day-weather-icon img").get_attribute("src")

                    forecast.append({
                        "day": day_name,
                        "temp": day_temp,
                        "wind": day_wind,
                        "pop": day_pop,
                        "icon": day_icon,
                    })
                except Exception as e:
                    print(f"⚠️ Kunde inte läsa dag {i}: {e}")

            input("👉 Tryck ENTER för att fortsätta och stänga browsern...")
            browser.close()

            return {
                "temp": temp,
                "wind": wind,
                "rain_chance_now": rain_chance_now,
                "sunset": sunset,
                "humidity": humidity,
                "forecast": forecast
            }

    except Exception as e:
        print(f"❌ Fel vid väderhämtning: {e}")
        return {
            "temp": None,
            "wind": None,
            "rain_chance_now": None,
            "sunset": None,
            "humidity": None,
            "forecast": []
        }

# Första hämtning
weather_cache = fetch_weather()

# Uppdatera varje timme
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: globals().update(weather_cache=fetch_weather()), 'interval', minutes=60)
scheduler.start()

# API endpoints
@app.route('/data')
def data():
    return jsonify(weather_cache)

@app.route('/')
def home():
    return jsonify({"message": "Weather widget is running"})

if __name__ == '__main__':
    app.run(debug=True)
