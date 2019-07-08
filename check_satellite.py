# check_satellite.py
# Script run by a cron-job every minute to retreieve the latest satellite data
# Validates and stores data, else writes error to log file

from app.utils import DatabaseConnection # Bespoke db connection wrapper
from decimal import *
import requests, time, dateutil.parser

def get_satellite_data():
    response = requests.get("http://nestio.space/api/satellite/data")
    data = response.json()

    return data

def validate_satellite_data(data):
    # validate_satellite_data()
    # Accept raw data from satellite endpoint
    # Check if data exists + is in proper form
    # Returns validated data; throws exception otherwise

    validated_data = {}

    # == altitude ==
    if (data['altitude']):
        try:
            validated_data['altitude'] = Decimal(data['altitude'])
        except:
            raise Exception("Altitude not valid!")
    else:
        raise Exception("Altitude not found!");

    # == last_updated ==
    if (data['last_updated']):
        try:
            validated_data['last_updated'] = dateutil.parser.parse(data['last_updated'])
        except:
            raise Exception("Last updated time not valid!")
    else:
        raise Exception("Last updated time not found!")

    return validated_data

def store_satellite_data(data):
    conn = DatabaseConnection()
    sql = "INSERT INTO satellite_position (altitude, last_updated) VALUES (%s, %s);"

    conn.perform(sql, [data['altitude'], data['last_updated']])

def process_satellite():
    # satellite_driver()
    # Called every 10 seconds in a 6-call routine
    try:
        raw_data = get_satellite_data()
        valid_data = validate_satellite_data(raw_data)
        store_satellite_data(valid_data)
    except Exception as e:
        # TODO: Logging goes here
        print "It crashed, dude"
        print e

# == Driver Code ==
# Run every 10 seconds for 50 seconds 60 times - accommodate PythonAnywhere
for y in range(60):
    for i in range(6):
        process_satellite()
        time.sleep(10)
