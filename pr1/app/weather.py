import math
import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

class WeatherError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status

def request_json(url, params):
    try:
        response = requests.get(url, params=params, timeout=(5, 15))
        if response.status_code >= 500:
            raise WeatherError("Сервіс погоди тимчасово недоступний", 503)
        if response.status_code >= 400:
            raise WeatherError("Сервіс відхилив запит", 502)
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError()
        return data
    except requests.Timeout as exc:
        raise WeatherError("Перевищено час очікування", 504) from exc
    except ValueError as exc:
        raise WeatherError("Некоректна відповідь сервісу") from exc
    except requests.RequestException as exc:
        raise WeatherError("Немає зв'язку із сервісом", 503) from exc

def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise WeatherError("У відповіді відсутні числові дані")
    return value

def find_city(name):
    name = name.strip()
    if not name or len(name) > 150:
        raise WeatherError("Введіть назву міста (до 150 символів)", 422)
    data = request_json(GEOCODING_URL, {"name": name, "count": 1, "language": "uk"})
    results = data.get("results", [])
    if not isinstance(results, list):
        raise WeatherError("Некоректний список міст")
    if not results:
        raise WeatherError("Місто не знайдено", 404)
    try:
        city = results[0]
        number(city['latitude']); number(city['longitude'])
        if not isinstance(city['name'], str): raise ValueError()
        return city
    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherError("Некоректні дані міста") from exc

def get_current_weather(city):
    place = find_city(city)
    data = request_json(FORECAST_URL, {
        "latitude": place['latitude'], "longitude": place['longitude'],
        "current": "temperature_2m,wind_speed_10m", "timezone": "auto"})
    try:
        current = data['current']
        return {"city": place['name'], "country": place.get('country', ''),
                "temperature": number(current['temperature_2m']), "temperature_unit": "°C",
                "wind_speed": number(current['wind_speed_10m']), "wind_unit": "km/h",
                "time": current['time']}
    except (KeyError, TypeError) as exc:
        raise WeatherError("Неповні дані погоди") from exc
