# main.py — ESP32 MicroPython
import time
import network                         # Delays and timing
from machine import Pin, ADC, PWM   # Hardware control classes
from config import (
    WIFI_SSID, WIFI_PASS,
    PIN_WATER_LEVEL, PIN_SOIL, PIN_BUZZER
    )
from supabase_client import post_reading, get_readings, get_threshold

# ── Hardware setup ────────────────────────────────────────────────────────────
water_level_adc = ADC(Pin(PIN_WATER_LEVEL))
soil_adc        = ADC(Pin(PIN_SOIL))

# ATTN_11DB = read voltages up to 3.6V (full ESP32 ADC range)
for adc in (water_level_adc, soil_adc):
    adc.atten(ADC.ATTN_11DB)

# Initialize the buzzer using Pulse Width Modulation (PWM) to control frequency
buzzer = PWM(Pin(PIN_BUZZER, Pin.OUT))
buzzer_status = False

# Default threshold if database retrieval fails
# Threshold Check: If the value drops below 400 it means 
# water is bridging the sensor traces and lowering resistance.
DEFAULT_WATER_THRESHOLD = 400

#buzzer_off()
def buzzer_off():
    buzzer.duty_u16(0)

def buzzer_on(freq=100):
    buzzer.freq(freq)# Lower frequency = lower pitch
    buzzer.duty_u16(32768)# 50% of 65535 duty cycle (sound)

# Ensure buzzer is silent at startup
buzzer_off()
    
    # ── Wi-Fi ─────────────────────────────────────────────────────────────────────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    print("Connecting to Wi-Fi", end="")
    timeout = 0
    while not wlan.isconnected() and timeout < 15:
        print(".", end="")
        time.sleep(1)
        timeout += 1
    if wlan.isconnected():
        print("\nConnected! IP:", wlan.ifconfig()[0])
    else:
        print("\nFailed to connect — check SSID/password in config.py")

# ── Sensor readers ────────────────────────────────────────────────────────────
def read_soil():
    """Returns averaged ADC value. Higher = drier soil."""
    total = 0
    for _ in range(5):
        total += soil_adc.read()
        time.sleep_ms(10)
    return total // 5

def read_water_level():
    """Returns averaged ADC value. Higher = more water detected."""
    total = 0
    for _ in range(5):
        total += water_level_adc.read()
        time.sleep_ms(10)
    return total // 5

# Connect to Wi-Fi before entering the main loop
connect_wifi()

# ── Main loop ─────────────────────────────────────────────────────────────────
# Wait for the pines to go HIGH (pulse start)
while True:
# Note: High values = Dry, Low values = Wet
# Step 1 — Read sensors
    soil_val        = read_soil()
    water_level_val = read_water_level()

# Print a summary of all current sensor values to the console
    print("\n--- Sensor Readings ---")
    print("Soil moisture : {} / 4095  (higher = drier)".format(soil_val))
    print("Water level   : {} / 4095  (higher = wetter)".format(water_level_val))
    
#Step 2 - Get threshold from Supabase
    threshold = DEFAULT_WATER_THRESHOLD
    try:
        supabase_data = get_readings()
        threshold = supabase_data["water_threshold"]

        if threshold is None:
            print(
                "No threshold found. Using default:",
                DEFAULT_WATER_THRESHOLD
            )
    except Exception as e:
        print(e)

    print("Current threshold:", threshold)

# Determine buzzer status Buzzer logic BEFORE POST (need buzzer_status)
    if water_level_val < threshold:

# Step 3 Determine buzzer status 
# Set volume/power (duty cycle) to a audible level      
        buzzer_on()# Low-pitched alarm
        buzzer_status = True
        print("LOW WATER  - Buzzer ON")
    else:
        buzzer_off()
        buzzer_status = False

        print("Water level OK - Buzzer OFF")

# Step 4: single POST call with all four arguments
    print("\n[POST] Sending data to Supabase...")
    post_reading(
        soil_val,
        water_level_val,
        buzzer_status
    )

    # Step 3 — GET last 5 readings from Supabase (display only)
    print("\n[GET] Fetching last 5 readings...")
    records = get_readings(limit=5)

    if records:
        print("Last {} readings:".format(len(records)))
        for i, row in enumerate(records, start=1):
            print("  {}. soil={} | water_level={} | time={}".format(
                i,
                row.get("soil_adc",        "N/A"),  # Must match column names
                row.get("water_level_adc", "N/A"),
                row.get("buzzer_status", "N/A"),
                row.get("created_at",      "N/A")
            )
        )
    else:
        print("\nNext reading in 10 seconds...")

# sleep always runs, not just in the else branch
    print("\nNext reading in 10 seconds...")
    time.sleep(10)
    