# 🛰️ Presence Detection System with Arduino + Ultrasonic Sensor + Discord Notifications

A presence monitoring system based on **Arduino** and an **HC-SR04 ultrasonic sensor**, with automatic **Discord notifications** and movement logging via a Python backend.

The project detects when a room is occupied or becomes free and records events over time.

---

## 🎯 Features

- Presence detection using ultrasonic sensor
- Real-time Discord notifications
- Movement logging in JSON format
- Local web server for monitoring data
- Authentication system for protected access
- Tracking of room occupancy duration

---

## 🧩 Components

- Arduino
- HC-SR04 Ultrasonic Sensor
- Computer with Python
- Discord Webhook

---

## 🔌 Hardware Connections

| HC-SR04 Sensor | Arduino |
|---------------|--------|
| VCC           | 5V     |
| GND           | GND    |
| TRIG          | Pin 2  |
| ECHO          | Pin 3  |

---

## ⚙️ How It Works

- The sensor continuously measures distance
- An initial distance is defined (empty room)
- If distance decreases beyond a threshold → presence detected
- If distance returns to normal → room is free
- Data is sent via serial to the Python program
- Python handles notifications, logging, and web API

---

## 🔔 Discord Notifications

The system sends automatic notifications when:

- 🚨 Presence is detected
- ✅ The room becomes free again

---

## 🗂️ Logging

All movements are saved in a JSON file including:

- Occupancy start timestamp
- Occupancy end timestamp
- Duration in seconds
- Time period (morning, afternoon, evening, night)

---

## 🌐 Web Server

The Python backend runs a local server to monitor data.

Available endpoints:

- `/` → main page  
- `/login` → authentication  
- `/distances` → current and recent distance values  
- `/movements` → room status and movement history  
- `/logout` → logout  

---

## 🔐 Authentication

Access to the API is protected using a token.

---

## ⚙️ Configuration

Before running the project, you must:

- Configure the correct serial port
- Set the Discord webhook as an environment variable
- Define the log file path
- Set an authentication token

---

## 🚀 Getting Started

1. Upload the code to Arduino  
2. Connect Arduino to the computer via USB  
3. Set the correct serial port in the backend  
4. Configure the Discord webhook  
5. Start the Python server  

---

## 📁 Project Structure

---

## 📊 Possible Improvements

- Graphical dashboard
- Database integration
- Standalone version using ESP32
- Telegram / Email notifications
- Advanced usage statistics

---

## 📌 Notes

- The system is designed for local use
- Accuracy depends on sensor placement
- Avoid fixed obstacles in the detection area

---

## 👨‍💻 Author

Project developed for room presence monitoring using Arduino with Python backend and Discord integration.
