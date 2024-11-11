import serial
import tkinter as tk
import requests
import time

# IFTTT Webhook URL 
IFTTT_WEBHOOK_URL = "https://maker.ifttt.com/trigger/Health_Alert/with/key/le9VQaMMdcEx3oL-1bM-idqoEJi3fOPLj7lccdoYn7L"

# Thingspeak API URL and Write Key
THINGSPEAK_API_URL = "https://api.thingspeak.com/update"
THINGSPEAK_WRITE_KEY = "ALWOA3PQ41ZBDG1Y"  

# Alert thresholds for abnormal readings
HIGH_HEART_RATE = 57  # bpm
LOW_SPO2_LEVEL = 85   # percentage

# Initialize Serial Connection
arduino_port = '/dev/ttyACM0'  
baud_rate = 9600
try:
    ser = serial.Serial(arduino_port, baud_rate)
    print("Connected to Arduino")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit()

# Setup GUI
root = tk.Tk()
root.title("Patient Health Monitoring")

# Labels for displaying data
timestamp_label = tk.Label(root, text="Timestamp: -- ms", font=("Arial", 14))
hr_label = tk.Label(root, text="Heart Rate: -- BPM", font=("Arial", 14))
spo2_label = tk.Label(root, text="SpO2 Level: -- %", font=("Arial", 14))
motion_label = tk.Label(root, text="Motion: --", font=("Arial", 14))
timestamp_label.pack()
hr_label.pack()
spo2_label.pack()
motion_label.pack()

# Function to send alert to IFTTT when abnormal data is detected
def send_ifttt_alert(heart_rate, spo2_level):
    payload = {"value1": heart_rate, "value2": spo2_level}
    try:
        response = requests.post(IFTTT_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            print("Alert sent successfully.")
        else:
            print(f"Failed to send alert: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error sending IFTTT request: {e}")

# Function to send data to Thingspeak
def send_to_thingspeak(heart_rate, spo2, motion):
    payload = {
        'api_key': THINGSPEAK_WRITE_KEY,
        'field1': heart_rate,
        'field2': spo2,
        'field3': motion
    }
    try:
        response = requests.post(THINGSPEAK_API_URL, params=payload)
        if response.status_code == 200:
            print("Data sent to Thingspeak successfully.")
        else:
            print(f"Failed to send data to Thingspeak: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error sending Thingspeak request: {e}")

# Update GUI with received data and check for abnormal readings
def update_data():
    try:
        line = ser.readline().decode('utf-8').strip()
        print(f"Received: {line}")  # For debugging
        
        if line:
            data = line.split(',')
            if len(data) == 4:
                timestamp, heart_rate, spo2, motion = data
                timestamp_label.config(text=f"Timestamp: {timestamp} ms")
                hr_label.config(text=f"Heart Rate: {heart_rate} BPM")
                spo2_label.config(text=f"SpO2 Level: {spo2} %")
                motion_label.config(text=f"Motion: {motion}")
                
                # Check if readings are abnormal and send alert
                heart_rate = int(heart_rate) if heart_rate.isdigit() else 0
                spo2 = float(spo2) if spo2.replace('.', '', 1).isdigit() else 100
                if heart_rate > HIGH_HEART_RATE or spo2 < LOW_SPO2_LEVEL:
                    print("Abnormal readings detected. Sending alert.")
                    send_ifttt_alert(heart_rate, spo2)
                
                # Send data to Thingspeak
                send_to_thingspeak(heart_rate, spo2, motion)
                
            else:
                print("Data format error")
        
    except (serial.SerialException, ValueError) as e:
        print(f"Error: {e}")
    
    root.after(1000, update_data)  # Update every second

update_data()  # Initial call to start updating
root.mainloop()

# Close serial connection on exit
ser.close()
