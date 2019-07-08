# test_health.py
# Barebones and kludgy unit tests for the /health endpoint
from app.secrets import test_nocrash
import MySQLdb, requests, datetime
base_url = "http://127.0.0.1:5000"

class DebugConnection:
    # DebugConnection()
    # Awful kludgy barebones variant of DatabaseConnection for use with test database

    def __init__(self):
        self.creds = test_nocrash

    def open_connection(self):
        self.db = MySQLdb.connect(
            host=self.creds['host'],
            user=self.creds['username'],
            passwd=self.creds['password'],
            db=self.creds['database'],
            use_unicode=True)
        self.cursor = self.db.cursor()

    def close_connection(self):
        self.db.commit()
        self.cursor.close()

    def teardown_db(self):
        # teardown_db()
        # Quick and kludgy method to clean the test database

        sql = "DELETE FROM satellite_position;"

        self.open_connection()
        self.cursor.execute(sql)
        self.close_connection()

    def load_dummy_data(self, sql, values):
        # load_dummy_data()
        # Kludgy way to quickly load data into the test db
        self.teardown_db()
        self.open_connection()
        self.cursor.execute(sql, values)
        self.close_connection()

class Test_Health:
    def test_empty(self):
        # test_empty()
        # Test for a response when the database is wiped clean
        db = DebugConnection()

        db.teardown_db()
        db.close_connection()

        response = requests.get("{0}/health?debug=True".format(base_url))

        assert response.text == u'"No data was found!"\n'

    def test_imminent(self):
        # test_imminent()
        # Test for an imminent orbital decay message

        # == Generate dummy data ==
        altitude_list = [159 for x in range(31)]
        dummy_data = generate_dummy_sql(altitude_list)

        # = Insert values into db =
        conn = DebugConnection()
        conn.load_dummy_data(dummy_data['sql'], dummy_data['data'])

        # == Perform Test ==
        response = requests.get("{0}/health?debug=True".format(base_url))
        assert response.text == u'"WARNING: RAPID ORBITAL DECAY IMMINENT"\n'

    def test_sustained(self):
        # test_sustained()
        # Test for sustained orbit message

        # == Generate dummy data==
        danger_state = [159 for x in range(6)] # 1 minute dangerous timeframe
        safe_state = [160 for x in range(24)] # 4 minutes safe timeframe
        altitude_list = [180] + danger_state + safe_state # avg of last min is now 162.5 (safe)

        dummy_data = generate_dummy_sql(altitude_list)

        # = Insert values into db =
        conn = DebugConnection()
        conn.load_dummy_data(dummy_data['sql'], dummy_data['data'])

        # == Perform Test ==
        response = requests.get("{0}/health?debug=True".format(base_url))
        assert response.text == u'"Sustained Low Earth Orbit Resumed"\n'

    def test_ok(self):
        # test_ok()
        # Test for A-OK message

        # == Generate Dummy Data ==
        altitude_list = [160 for x in range(31)]
        dummy_data = generate_dummy_sql(altitude_list)

        # = Insert values into test db =
        conn = DebugConnection()
        conn.load_dummy_data(dummy_data['sql'], dummy_data['data'])

        # == Perform Test ==
        response = requests.get("{0}/health?debug=True".format(base_url))
        assert response.text == u'"Altitude is A-OK"\n'

def generate_dummy_sql(altitude_list):
    # generate_dummy_data()
    # Generates made-up time columns to simulate 5 minutes of data

    current_time = datetime.datetime.now()

    # = Entry for every 10 seconds in given range =
    created_at = [current_time-datetime.timedelta(seconds=x*10) for x in range(len(altitude_list))]
    # = Adjust slices for timezone difference in last_updated col (5 hours) =
    last_updated = [x+datetime.timedelta(hours=4) for x in created_at]

    # = Prep SQL statement =
    run_params = []
    run_values = []
    for alt, updated, created in zip(altitude_list, last_updated, created_at):
        run_params.append("(%s, %s, %s)")
        run_values.extend([alt, updated, created])

    sql = "INSERT INTO satellite_position (altitude, last_updated, created_at) VALUES {0};".format(", ".join(run_params))

    return {'sql':sql, 'data':run_values}
