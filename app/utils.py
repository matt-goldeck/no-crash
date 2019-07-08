# utils.py
# Simple utilities used by application
import secrets
from decimal import *
import datetime, MySQLdb

class DatabaseConnection:
    # DatabaseConnection()
    # A quick and dirty wrapper class to abstract database communication

    database = cursor = host = username = password = db = None

    def __init__(self, debug=False):
        # Default to nocrash; otherwise use test_nocrash
        if debug:
            credentials = secrets.test_nocrash
        else:
            credentials = secrets.nocrash

        self.database = credentials['database']
        self.password = credentials['password']
        self.host = credentials['host']
        self.username = credentials['username']

    def perform(self, sql, params):
        self.connect()

        if sql[-1] is not ';':
            sql = "{0};".format(sql)

        self.cursor.execute(sql, params)
        result = self.cursor.fetchall()

        self.terminate()

        return result;

    def connect(self):
        try:
            self.db = MySQLdb.connect(
            host=self.host,
            user=self.username,
            passwd=self.password,
            db=self.database,
            use_unicode=True)

            self.cursor = self.db.cursor()
        except Exception as e:
            raise Exception("Failed to make connection ".e)

    def terminate(self):
        try:
            self.db.commit()

            self.cursor.close()
            self.db.close()
        except:
            raise Exception("Failed to terminate connection!")

def get_last_minutes_data(minutes_since, start_time, debug=False):
    # get_stats()
    # Returns list of dicts w/ alt and time data for the last x minutes

    target_time = start_time - datetime.timedelta(minutes=minutes_since)

    # = SQL Logic =
    # Note: Order by desc st highest altitude at beginning, lowest at end
    # Using created_at col to avoid timezone conversion
    sql = "SELECT altitude, last_updated FROM satellite_position WHERE created_at > %s AND created_at <= %s ORDER BY altitude desc;"

    conn = DatabaseConnection(debug)
    results = conn.perform(sql, [target_time, start_time])

    # = Format Data =
    formatted_data = [{'altitude':x[0], 'last_updated':x[1]} for x in results]

    return formatted_data

def get_stats(minutes_since=5, start_time=None, debug=False):
    # get_stats()
    # Calculates and returns dict object w/ stats for the last x minutes
    # Note: defaults to 5 from now

    # = Get satellite data =
    if not start_time:
        start_time = datetime.datetime.now()

    sat_data = get_last_minutes_data(minutes_since, start_time, debug)
    return_data = {}

    if sat_data:
        # = Min/max =
        # Note: get_last_five_data() orders by altitude desc
        return_data['alt_min'] = sat_data[-1]['altitude']
        return_data['alt_max'] = sat_data[0]['altitude']

        # = Average =
        alt_sum = sum([x['altitude'] for x in sat_data])
        return_data['alt_avg'] = alt_sum / len(sat_data)
    else:
        pass

    return return_data

def get_health(debug=False):
    # get_health()
    # Examines average over the last 120 seconds to determine satellite health
    # First examines past 60 for imminent danger, then again for recovery message

    # = Build time interval list =
    c = datetime.datetime.now()
    times = [c - datetime.timedelta(seconds=x) for x in [y*10 for y in range(13)]]

    # = Get average of last 5 minutes for each point in the past 2 minutes =
    interval_data = []
    for time in times:
        run_data = get_stats(start_time=time, debug=debug)
        if not run_data:
            pass
        else:
            interval_data.append(run_data['alt_avg'])

    # == Examine average of each point in past minute for danger state ==
    # = Cond 0: No data exists =
    if not interval_data:
        return "No data was found!";
    # = Cond 1: Currently in danger state ==
    if is_dangerous_interval(interval_data[0:7]):
        return "WARNING: RAPID ORBITAL DECAY IMMINENT"
    # = Cond 2: Danger existed in past 50 seconds =
    else:
        for x in range(6):
            if is_dangerous_interval(interval_data[x:x+6]):
                return "Sustained Low Earth Orbit Resumed"
            else:
                pass

    # = Cond 3: No danger has existed in past minute =
    return "Altitude is A-OK"

def is_dangerous_interval(interval):
    # is_dangerous_interval()
    # Interval is a list of measurements of avg alts over a given frame of time
    # Returns true if dangerous (average was <160km throughout), false otherwise

    # = If avg alt dips above 160, not dangerous =
    for avg_alt in interval:
        if avg_alt >= 160:
            return False

    return True
