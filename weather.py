from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver
import os
import requests

load_dotenv()  # Load environment variables from .env file

def get_weather(city: str):
   """get weather for a givem city. 
   return temperature_farenheit value in farenheit lable for locaations such as USA, bahamas, Belize, Cayman Islands, Palau, Puerto Rico, US Virgin Islands, Guam, Northern Mariana Islands, American Samoa, and the Federated States of Micronesia.
   """
   api_key = os.getenv("OPEN_WEATHER_API_KEY")
   base_url = "https://api.openweathermap.org/data/2.5/weather"
   params = {
         "q": city,
            "appid": api_key,
            "units": "metric"
   }
   response = requests.get(base_url, params=params)
   data= response.json()
   temperature = data["main"]["temp"]
   temperature_farenheit = (temperature * 9/5) + 32
   return data, {'temperature_celsius': temperature, 'temperature_farenheit': temperature_farenheit}

def get_location(city: str):
   """get user's current location. when user asks for weather without specifying a city,
     this tool will be used to get the user's current location"""
   from flask import session
   location = session.get('user_location')
   if not isinstance(location, dict) or location.get('lat') is None or location.get('lon') is None:
      raise ValueError("Current location is unavailable. Allow location access or enter a city.")

   try:
      user_lat = float(location['lat'])
      user_lon = float(location['lon'])
   except (TypeError, ValueError) as exc:
      raise ValueError("Current location coordinates are invalid.") from exc

   if not -90 <= user_lat <= 90 or not -180 <= user_lon <= 180:
      raise ValueError("Current location coordinates are outside valid ranges.")

   response = requests.get(
      "https://nominatim.openstreetmap.org/reverse",
      params={"format": "jsonv2", "lat": user_lat, "lon": user_lon},
      headers={"User-Agent": "WeatherAPP/1.0"},
      timeout=10,
   )
   response.raise_for_status()
   try:
      data = response.json()
   except requests.exceptions.JSONDecodeError as exc:
      raise ValueError("The location service returned an invalid response.") from exc

   address = data.get('address')
   if not isinstance(address, dict):
      raise ValueError("The location service did not return an address.")

   city_name = address.get('city') or address.get('town') or address.get('village') or 'Unknown'
   country = address.get('country')
   if not country:
      raise ValueError("The location service response did not include a country.")
   return f"{city_name}, {country}"

#initialize the Google Generative AI chat model
llm = ChatOpenAI(
    model="google/gemini-3.8-flash",
    api_key=os.getenv("KODEKEY_API_KEY"),
    base_url="https://api.ai.kodekloud.com/v1",
    temperature=0.7
)

system_prompt = """You are a helpful assistant that can provide weather information for a given city.
YOUR WORKFLOW:
1. if the user ask about the weaher without specifying a location, you must follow:
- first call the get_location tool to get the user's current location
- then call the get_weather(city) tool to get the weather for that location
2. if user provide a city, you must call the get_weather(city) directly to get the weather for that city.
3.  use your knowlege  to determine which temprature unit is standard for the given location.
"""

connection = SqliteSaver.from_conn_string("checkpoints.db")
checkpointer = connection.__enter__()
agent = create_agent(model=llm, 
                        tools=[get_weather,get_location],
                        system_prompt=system_prompt,
                        checkpointer=checkpointer)

  