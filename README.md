# Alexa-ventra-bus-tracker
# 🚌 Alexa-Integrated Real-Time Bus Tracker

A voice-powered **Amazon Alexa Skill** that helps users check how far a CTA (Chicago Transit Authority) bus is from their current location using real-time data. Built with **Flask**, **ASK SDK**, and the **CTA Bus Tracker API**, this project demonstrates smart city integration with voice-first technology.

---

## 🎯 Features

- 🗣️ **Alexa Skill Integration**: Users can ask Alexa “how far is bus 22 heading north?” and get real-time ETA.
- 📍 **User Location Handling**: Users set their latitude and longitude via voice input for personalized results.
- 🔁 **Live CTA Bus Tracking**: Pulls real-time vehicle data from CTA’s public API using XML parsing.
- 📡 **Direction Matching**: Estimates direction (North, South, etc.) based on bus heading.
- ⚙️ **Local Development Setup**: Connected via **Ngrok** to enable Alexa to interact with locally hosted Flask app.

---

## 🧰 Tech Stack

- **Python**
- **Flask**
- **Amazon Alexa ASK SDK**
- **Ngrok**
- **CTA Bus Tracker API**
- **Visual Studio Code**
- **dotenv**
- **XML Parsing**
- **Geolocation APIs**

---

## 🚀 How It Works

1. Users launch the Alexa Skill and set their location.
2. The skill receives a bus route number and optional direction.
3. Flask queries the CTA Bus Tracker API and parses vehicle locations.
4. It calculates distance & ETA using Haversine formula.
5. Alexa responds with real-time bus arrival information.

---

## 📦 Project Structure

alexa-bus-tracker/
├── app.py # Main Flask app with intent handlers
├── .env # API keys (not committed)
├── requirements.txt # Python dependencies
├── README.md # Project documentation
