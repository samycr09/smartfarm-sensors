# supabase_client.py
# Handles all communication with the Supabase REST API

import urequests
import ujson

from config import SUPABASE_KEY, SUPABASE_URL, SENSOR_TABLE

# ── Common headers ────────────────────────────────────────────────────────────

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": "Bearer " + SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# ── POST: Send sensor readings to Supabase ───────────────────────────────────

def post_reading(
    soil_adc,
    water_level_adc,
    buzzer_status
):
    url = "{}{}".format(
        SUPABASE_URL,
        SENSOR_TABLE
    )

    payload = {
        "soil_adc": soil_adc,
        "water_level_adc": water_level_adc,
        "buzzer_status": buzzer_status
    }

    try:
        response = urequests.post(
            url,
            headers=HEADERS,
            data=ujson.dumps(payload)
        )

        print("[POST] Status:", response.status_code)

        response.close()

    except Exception as e:
        print("[POST] Error:", e)

# ── GET: Fetch recent sensor readings ────────────────────────────────────────

def get_readings(limit=5):

    url = (
        "{}{}"
        "?select=*"
        "&order=created_at.desc"
        "&limit={}"
    ).format(
        SUPABASE_URL,
        SENSOR_TABLE,
        limit
    )

    try:
        response = urequests.get(
            url,
            headers=HEADERS
        )

        print("[GET] Status:", response.status_code)

        if response.status_code == 200:
            data = ujson.loads(response.text)

            response.close()

            return data

        print("[GET] Error body:", response.text)

        response.close()

        return []

    except Exception as e:
        print("[GET] Error:", e)

        return []

# ── GET: Fetch latest water threshold ────────────────────────────────────────

def get_threshold():

    url = (
        "{}/rest/v1/{}"
        "?select=water_threshold"
        "&order=created_at.desc"
        "&limit=1"
    ).format(
        SUPABASE_URL,
        SENSOR_TABLE
    )

    try:
        response = urequests.get(
            url,
            headers=HEADERS
        )

        print("[GET Threshold] Status:", response.status_code)

        if response.status_code == 200:

            data = ujson.loads(response.text)

            response.close()

            if len(data) > 0:
                return data[0].get("water_threshold")

            return None

        print("[GET Threshold] Error body:", response.text)

        response.close()

        return None

    except Exception as e:

        print("[GET Threshold] Error:", e)

        return None