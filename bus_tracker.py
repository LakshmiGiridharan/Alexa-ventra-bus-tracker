from flask import Flask, request
from flask_ask_sdk.skill_adapter import SkillAdapter
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
import requests
from math import radians, sin, cos, sqrt, atan2
from word2number import w2n
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import os

load_dotenv()  # Load from .env


app = Flask(__name__)
skill_builder = SkillBuilder()

user_location = {"latitude": None, "longitude": None}

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def calculate_travel_time(distance_km, speed_kmh=32):
    return (distance_km / speed_kmh) * 60

def get_direction(heading):
    if 315 <= heading or heading < 45:
        return "North"
    elif 45 <= heading < 135:
        return "East"
    elif 135 <= heading < 225:
        return "South"
    else:
        return "West"

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Welcome to the Bus Tracker. Ask me how far the bus is from you.").response

class SetLocationIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("SetLocationIntent")(handler_input)

    def handle(self, handler_input):
        print("Inside SetLocationIntentHandler.handle()") 
        print("SetLocationIntent triggered!") 
        
        slots = handler_input.request_envelope.request.intent.slots
        print(f"Slots received: {slots}") 

        lat_sign = slots["latSign"].value if "latSign" in slots else None
        lat_value = slots["lat"].value if "lat" in slots else None
        long_sign = slots["longSign"].value if "longSign" in slots else None
        long_value = slots["long"].value if "long" in slots else None

        if not lat_value or not long_value:
            return handler_input.response_builder.speak("Please provide valid latitude and longitude values.").response

        try:
            print(lat_value)
            print(long_value)
            lat_num = float(lat_value)
            long_num = float(long_value)
            print(f"Converted lat/lon: {lat_num}, {long_num}")

            if lat_sign and lat_sign.lower() in ["negative", "minus"]:
                lat_num *= -1
            if long_sign and long_sign.lower() in ["negative", "minus"]:
                long_num *= -1
            if lat_sign and lat_sign.lower() in ["positive", "plus"]:
                lat_num *= +1
            if long_sign and long_sign.lower() in ["positive", "plus"]:
                long_num *= +1

        except ValueError:
            return handler_input.response_builder.speak("I didn't understand the location. Please try again using numbers.").response

        user_location["latitude"] = lat_num
        user_location["longitude"] = long_num
        print(f"Location set: {user_location}") 

        return handler_input.response_builder.speak(
            f"Your location is set to latitude {lat_num} and longitude {long_num}."
        ).response

class GetMyLocationIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("GetMyLocationIntent")(handler_input)

    def handle(self, handler_input):
        lat = user_location.get("latitude")
        lon = user_location.get("longitude")

        if lat is None or lon is None:
            speech_text = "I don't have your location. Please set it first."
        else:
            speech_text = f"Your current latitude is {lat} and longitude is {lon}."

        return handler_input.response_builder.speak(speech_text).response

class GetBusTimeIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("GetBusTimeIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        route_number = slots["routeNumber"].value if "routeNumber" in slots else None
        requested_direction = slots["direction"].value.lower() if "direction" in slots and slots["direction"].value else None

        if not route_number:
            return handler_input.response_builder.speak("Please specify a bus route number.").response

        if not user_location["latitude"] or not user_location["longitude"]:
            return handler_input.response_builder.speak("I don't have your location. Please set it first.").response

        my_lat, my_lon = user_location["latitude"], user_location["longitude"]
        cta_api_key = os.getenv("CTA_API_KEY") 
        cta_url = f"http://www.ctabustracker.com/bustime/api/v2/getvehicles?key={cta_api_key}&rt={route_number}&tmres=m&format=xml"

        try:
            response = requests.get(cta_url)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            vehicles = root.findall(".//vehicle")
        except requests.RequestException:
            return handler_input.response_builder.speak("I couldn't fetch bus data. Try again later.").response
        except ET.ParseError:
            return handler_input.response_builder.speak("There was an error processing the bus data. Please try again.").response

        if not vehicles:
            return handler_input.response_builder.speak(f"No buses found for route {route_number}.").response

        threshold = 1.0 

        nearby_buses = []
        for vehicle in vehicles:
            bus_lat = float(vehicle.find("lat").text)
            bus_lon = float(vehicle.find("lon").text)
            bus_hdg = float(vehicle.find("hdg").text)
            bus_direction = get_direction(bus_hdg).lower()

            if requested_direction and bus_direction != requested_direction:
                continue

            distance = calculate_distance(my_lat, my_lon, bus_lat, bus_lon)
            
            if distance > threshold:
                continue

            travel_time = calculate_travel_time(distance)
            nearby_buses.append({
                "vid": vehicle.find("vid").text,
                "time": travel_time,
                "direction": bus_direction
            })

        if nearby_buses:
            nearby_buses.sort(key=lambda x: x["time"])
            nearest_bus = nearby_buses[0]
            direction_text = f"heading {nearest_bus['direction']}" if not requested_direction else f"going {requested_direction}"
            return handler_input.response_builder.speak(
                f"Bus {nearest_bus['vid']} on route {route_number} is approximately {nearest_bus['time']:.2f} minutes away, {direction_text}."
            ).response
        else:
            direction_text = f"going {requested_direction}" if requested_direction else ""
            return handler_input.response_builder.speak(
                f"No buses {direction_text} on route {route_number} are near you right now."
            ).response


skill_builder.add_request_handler(LaunchRequestHandler())
skill_builder.add_request_handler(SetLocationIntentHandler())
skill_builder.add_request_handler(GetBusTimeIntentHandler())
skill_builder.add_request_handler(GetMyLocationIntentHandler())

skill_adapter = SkillAdapter(
    skill=skill_builder.create(),
    skill_id="amzn1.ask.skill.fb6dd91e-009e-4f44-ab99-441b4dcdfbd7",  # ✅ use your actual Skill ID
    app=app
)

@app.route("/alexa", methods=["POST"])
def alexa_webhook():
    print("✅ Alexa webhook triggered")
    print("Raw request data:", request.get_data(as_text=True))
    return skill_adapter.dispatch_request()


@app.route("/", methods=["GET"])
def home():
   if request.method == "GET":
        return "Welcome to the Bus Tracker App! Use the Alexa interface to interact."
   #if request.method == "POST":
        #print("POST request received at root endpoint")
        #print(request.get_json()) 
        #return skill_adapter.dispatch_request()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
