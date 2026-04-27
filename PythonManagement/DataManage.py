import serial
import json
import os
import threading
import requests
from datetime import datetime
from flask import Flask, jsonify, request, make_response, redirect, abort

SERIAL_PORT = "COM4"
BAUDRATE = 9600
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL").strip()
if not DISCORD_WEBHOOK_URL:
    raise ValueError("Webhook Discord non configurato!")
else:
    print("webhook trovato!")
    print("Webhook letto:", DISCORD_WEBHOOK_URL)
FILE_LOG = r"C:\Users\Matteo\Desktop\componenti arduino\AccendeLuceStanza\PythonManagement\movements_log.json"
AUTH_TOKEN = "sjdkhAKJFDGASLDFKJskfjhsDALKFHGSDFLKJh238467239"

app = Flask(__name__)


class SensorPacket:
    def __init__(self, dist, state):
        self.dist = dist
        self.state = state

    @classmethod
    def from_string(cls, line):
        line = line.strip()

        if not line.startswith("<") or not line.endswith(">"):
            return None

        content = line[1:-1]

        try:
            dist_part, state_part = content.split(",")

            key1, value1 = dist_part.split(":", 1)
            key2, value2 = state_part.split(":", 1)

            key1 = key1.strip()
            value1 = value1.strip()
            key2 = key2.strip()
            value2 = value2.strip()

            if key1 != "DIST" or key2 != "STATE":
                return None

            dist = float(value1)
            state = value2

            if state not in ("RILEVATO", "LIBERA", "NONE"):
                return None

            return cls(dist, state)

        except ValueError:
            return None

def send_discord_message(message):
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json={
                "content": message,
                "username": "Sensore Stanza"
            },
            timeout=5
        )

        if response.status_code not in (200, 204):
            print(f"Errore invio Discord: {response.status_code} - {response.text}")

    except requests.RequestException as e:
        print(f"Errore richiesta Discord: {e}")

def get_period(dt):
    total_minutes = dt.hour * 60 + dt.minute

    if 6 * 60 <= total_minutes <= 11 * 60 + 59:
        return "mattina"
    elif 12 * 60 <= total_minutes <= 19 * 60 + 59:
        return "pomeriggio"
    elif 20 * 60 <= total_minutes <= 22 * 60 + 59:
        return "sera"
    else:
        return "notte"


def create_log_if_missing():
    folder = os.path.dirname(FILE_LOG)

    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    if not os.path.exists(FILE_LOG):
        with open(FILE_LOG, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)

    print("Percorso log:", FILE_LOG)
    print("Esiste?", os.path.exists(FILE_LOG))


def append_movement_log(start_time, end_time, occupied_seconds):
    entry = {
        "DetectedAt": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "Period": get_period(start_time),
        "FreedAt": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        "OccupiedSeconds": round(occupied_seconds, 2)
    }

    try:
        with open(FILE_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(entry)

    with open(FILE_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Nuovo log aggiunto:", entry)


def is_authorized(req):
    auth_header = req.headers.get("Authorization", "")
    expected = f"Bearer {AUTH_TOKEN}"

    if auth_header == expected:
        return True

    cookie_token = req.cookies.get("auth_token")
    if cookie_token == AUTH_TOKEN:
        return True

    return False


def require_auth():
    if not is_authorized(request):
        return redirect("/login")
    return None


class SerialManager:
    def __init__(self, port, baudrate):
        self.ser = serial.Serial(port, baudrate, timeout=1)

        self.current_dist = None
        self.distances = []

        self.last_movement = None
        self.occupancy_start = None

        self.lock = threading.Lock()

    def add_distance(self, dist):
        self.distances.append({
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Dist": dist
        })

        if len(self.distances) > 10:
            self.distances.pop(0)

    def get_current_occupied_seconds(self):
        if self.occupancy_start is None:
            return None

        return round((datetime.now() - self.occupancy_start).total_seconds(), 2)

    def get_movements_log(self):
        try:
            with open(FILE_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def run(self):
        while True:
            raw = self.ser.readline()
            if not raw:
                continue

            try:
                line = raw.decode("utf-8", errors="ignore").strip()
            except Exception:
                continue

            if not line:
                continue

            print("Ricevuto:", line)

            packet = SensorPacket.from_string(line)

            if packet is None:
                print("Pacchetto non valido")
                continue

            now = datetime.now()

            with self.lock:
                self.current_dist = packet.dist
                self.add_distance(packet.dist)

                if packet.state == "RILEVATO":
                    if self.occupancy_start is None:
                        self.occupancy_start = now
                        self.last_movement = now.strftime("%Y-%m-%d %H:%M:%S")
                        print("Occupazione iniziata")

                        send_discord_message(
                            f"🚨 Movimento rilevato!\n"
                            f"Ora: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"@everyone"
                        )
                elif packet.state == "LIBERA":
                    if self.occupancy_start is not None:
                        occupied_seconds = (now - self.occupancy_start).total_seconds()

                        append_movement_log(
                            start_time=self.occupancy_start,
                            end_time=now,
                            occupied_seconds=occupied_seconds
                        )

                        send_discord_message(
                            f"✅ Stanza di nuovo libera.\n"
                            f"Fine occupazione: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"Durata: {round(occupied_seconds, 2)} secondi"
                        )

                        self.occupancy_start = None
                        print("Occupazione terminata")

    def close(self):
        self.ser.close()


manager = None


@app.route("/")
def home():
    return """
    <html>
        <body style="font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto;">
            <h1>Server sensore</h1>
            <p><a href="/login">Login</a></p>
            <p><a href="/distances">/distances</a></p>
            <p><a href="/movements">/movements</a></p>
            <p><a href="/logout">Logout</a></p>
        </body>
    </html>
    """


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 40px auto;">
                <h1>Login</h1>
                <form method="POST">
                    <label for="token">Token:</label><br><br>
                    <input
                        type="password"
                        id="token"
                        name="token"
                        style="width: 100%; padding: 10px; font-size: 16px;"
                        required
                    ><br><br>
                    <button type="submit" style="padding: 10px 16px; font-size: 16px;">
                        Entra
                    </button>
                </form>
            </body>
        </html>
        """

    token = request.form.get("token", "")

    if token != AUTH_TOKEN:
        abort(401)

    resp = make_response(redirect("/movements"))
    resp.set_cookie(
        "auth_token",
        AUTH_TOKEN,
        httponly=True,
        samesite="Lax"
    )
    return resp


@app.route("/logout")
def logout():
    resp = make_response("""
    <html>
        <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 40px auto;">
            <h1>Logout eseguito</h1>
            <p><a href="/login">Torna al login</a></p>
        </body>
    </html>
    """)
    resp.set_cookie("auth_token", "", expires=0)
    return resp


@app.route("/distances")
def distances():
    auth_error = require_auth()
    if auth_error:
        return auth_error

    with manager.lock:
        return jsonify({
            "CurrentDist": manager.current_dist,
            "Distances": manager.distances
        })


@app.route("/movements")
def movements():
    auth_error = require_auth()
    if auth_error:
        return auth_error

    with manager.lock:
        return jsonify({
            "LastMovement": manager.last_movement,
            "IsOccupiedNow": manager.occupancy_start is not None,
            "CurrentOccupiedSeconds": manager.get_current_occupied_seconds(),
            "MovementsLog": manager.get_movements_log()
        })


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not Found"}), 404


def main():
    global manager

    create_log_if_missing()

    manager = SerialManager(SERIAL_PORT, BAUDRATE)

    serial_thread = threading.Thread(target=manager.run, daemon=True)
    serial_thread.start()

    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()