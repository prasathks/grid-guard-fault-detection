import serial
import csv
import time
from datetime import datetime

# --- CONFIGURATION ---
SERIAL_PORT = "COM7"    # Replace with your ESP32 COM port
BAUD_RATE = 115200
CSV_FILE = "current_dataset.csv"

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
        time.sleep(2)  # Wait for ESP32 to initialize
    except Exception as e:
        print("Error opening serial port:", e)
        return

    print("Recording data... Press Ctrl+C to stop.")

    # Open CSV file for appending
    with open(CSV_FILE, mode='a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # Write header if file is empty
        if csvfile.tell() == 0:
            csv_writer.writerow(["Timestamp", "Current_A", "Label"])

        try:
            while True:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                
                # Remove unwanted characters (like '->')
                line = line.replace("->", "").strip()
                
                # Split line by comma
                parts = line.split(',')
                if len(parts) != 3:
                    continue  # Ignore malformed lines
                
                timestamp_str, current_str, label_str = parts
                
                # Convert to float/int
                try:
                    current_val = float(current_str)
                    label_val = int(label_str)
                except:
                    continue  # Skip if conversion fails
                
                # Add datetime timestamp for CSV
                timestamp_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Write to CSV
                csv_writer.writerow([timestamp_now, current_val, label_val])
                csvfile.flush()  # Ensure immediate write
                
                # Print live data
                print(f"{timestamp_now} | Current: {current_val:.3f} A | Label: {label_val}")

        except KeyboardInterrupt:
            print("\nRecording stopped by user.")
        finally:
            ser.close()
            print(f"Data saved to {CSV_FILE}")

if __name__ == "__main__":
    main()
