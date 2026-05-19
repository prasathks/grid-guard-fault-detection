import serial
import tensorflow as tf
import numpy as np
from datetime import datetime
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# ======== SETTINGS ========
PORT = 'COM7'           # ESP32 COM port
BAUD = 115200
MODEL_PATH = 'dc_fault_model_v3.tflite'
SEQ_LEN = 50
THRESHOLD = 0.5
CURRENT_DEADBAND = 0.060      # <---- Ignore currents below 0.10 A
STABLE_NORMAL_SEC = 3        # Wait 3 seconds of continuous normal before restoring relay
RELAY_RESTORE_DELAY = 3      # Extra delay before turning relay back ON

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DEFAULT_LOCATION = "10.7954° N, 77.7081° E"
FAULT_TYPES = {
    0: "Normal",
    1: "Open Circuit / Line Fault",
    2: "Short Circuit",
    3: "Line-to-Ground Fault"
}
# ============================

interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

print("Model loaded. Listening to serial...")

buffer = []
state = "NORMAL"
current_fault_class = None
normal_start_time = None
relay_is_off = False  # Track relay state

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.get(url, params={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram send failed:", e)

def set_relay(state_cmd):
    """Send a single character command to ESP32 to control the relay."""
    global relay_is_off
    try:
        if state_cmd == "OFF":
            ser.write(b'R0\n')
            relay_is_off = True
            print(">> Relay turned OFF (Isolation)")
        elif state_cmd == "ON":
            ser.write(b'R1\n')
            relay_is_off = False
            print(">> Relay turned ON (Restored)")
    except Exception as e:
        print("Relay control failed:", e)

try:
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            continue

        # Ignore control feedback lines from ESP32
        if line.startswith("ACK"):
            continue

        try:
            current = float(line)
        except ValueError:
            continue

        # ---- Deadband filter ----
        if abs(current) < CURRENT_DEADBAND:
            current = 0.0

        # If relay is OFF, force current to 0 to avoid false positives
        if relay_is_off:
            current = 0.0

        buffer.append(current)
        if len(buffer) < SEQ_LEN:
            continue
        if len(buffer) > SEQ_LEN:
            buffer.pop(0)

        data = np.array(buffer, dtype=np.float32).reshape(1, SEQ_LEN, 1)
        interpreter.set_tensor(input_details[0]['index'], data)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])[0]

        pred_class = np.argmax(output)
        pred_prob = output[pred_class] * 100

        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] Current: {current:.3f} A | Predicted: {pred_class} | Prob: {pred_prob:.2f}%")

        if state == "NORMAL":
            # Trigger only if relay is ON and a real fault occurs
            if not relay_is_off and pred_class != 0 and pred_prob > THRESHOLD * 100:
                set_relay("OFF")  # Isolate load first
                current_fault_class = pred_class
                message = (
                    f"⚠️ FAULT DETECTED!\n"
                    f"Type: {FAULT_TYPES[pred_class]}\n"
                    f"Probability: {pred_prob:.2f}%\n"
                    f"Location: {DEFAULT_LOCATION}\n"
                    f"Google Maps: https://www.google.com/maps/search/?api=1&query={DEFAULT_LOCATION.replace('°','%C2%B0')}"
                )
                send_telegram_alert(message)
                state = "FAULT"
                normal_start_time = None

        elif state == "FAULT":
            # Accept normal only if current stays normal for required time
            if pred_class == 0 and pred_prob > THRESHOLD * 100:
                if normal_start_time is None:
                    normal_start_time = time.time()
                elif time.time() - normal_start_time >= STABLE_NORMAL_SEC:
                    message = f"✅ FAULT CLEARED. Line back to NORMAL at {DEFAULT_LOCATION}"
                    send_telegram_alert(message)

                    print(f"Waiting {RELAY_RESTORE_DELAY} sec before restoring relay...")
                    time.sleep(RELAY_RESTORE_DELAY)
                    set_relay("ON")

                    state = "NORMAL"
                    current_fault_class = None
                    normal_start_time = None
            else:
                normal_start_time = None

except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    ser.close()
