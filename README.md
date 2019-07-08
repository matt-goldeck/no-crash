# no-crash
*Nestio Orbital Commercial Real-estate Administration and Sales Headquarters*

A quick and kludgy API built on Flask and MySQL as an exercise. A constantly running python script (check_satellite.py) monitorss the `nestio.space/api/satellite/data` endpoint for altitude information, processes it, and stores it in the database. Two endpoints query and surface this data on a just-in-time basis.

This project can be downloaded and run locally, or accessed at http://goldeckm1.pythonanywhere.com.


## Usage
### File Structure
```bash
.
├── app
│   ├── __init__.py
│   ├── app.py - Main code empowering Flask
│   ├── secrets.py - Plaintext credentials file
│   └── utils.py - Various functions used by app.py and check_satellite.py
├── check_satellite.py - Constantly running script that polls the nestio API and stores the retrieved data. 
├── requirements.txt - Python Dependencies
├── sql
│   ├── nocrash.sql - 'Production' Database
│   └── test_nocrash.sql - Test Database
└── tests
    ├── __init__.py
    └── test_health.py - /health endpoint unit tests
```

### Initialize Virtual Envrionment 
NO-CRASH is built using Flask, MySQL, and a great deal of small supporting libraries. To best manage these dependencies, a virtual envrionment is recommended.

After cloning the github code, using Python 2.7.15, create a virtualenv with `python -m virtualenv venv` and activate it with `source venv/bin/activate`. Once activated, install the dependencies with `pip install -r requirements.txt`.

### Set Up MySQL
Two databases have been created: nocrash and test_nocrash, the former for 'production' and the later for unit testing. Each has only one table, `satellite_position`. Exports of the databases are available in the sql folder, but given the lightweight nature of the project it may be easier to simply create each one and its table by hand.

**Creation Statements**

```
create database nocrash;
USE nocrash;

CREATE TABLE satellite_position (kp INT AUTO_INCREMENT, altitude DECIMAL(18,14), last_updated TIMESTAMP NULL DEFAULT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (kp)) ENGINE=INNODB;

create database test_nocrash;
use test_nocrash;

CREATE TABLE satellite_position (kp INT AUTO_INCREMENT, altitude DECIMAL(18,14), last_updated TIMESTAMP NULL DEFAULT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (kp)) ENGINE=INNODB;
```
**satellite_position**

Column | Type | Description
-------|------|------------
kp| Integer | Auto-incrementing primary key
altitude| Decimal | Decimal value with 14 points of precision to the right; measured directly from endpoint.
last_updated| Timestamp | When this measurement was updated on the Nestio endpoint.
created_at | Timestamp | When this measurement was stored in the database.

### Extracting Data
The script check_satellite.py is intended to be constantly run. Every 10 seconds it polls the Nestio endpoint and extracts the data. Originally this was intended to be a cron job run on 10 minute intervals, but my hosting service only allows for hourly tasks so I had to adapt. This can optionally be run manually.

It should be noted that the application only extracts data from the previous five minutes such that the data provided by the endpoint will rapidly go stale and eventually completely dry up if this script is not running. 

### Using Flask
Flask is a barebones Python micro web framework that is very near and dear to my heart. A development server can be run by navigating to the containing directory and performing `python app.py`. A 'production' web server can be accessed at http://goldeckm1.pythonanywhere.com/.

### Performing Unit Tests
Unit tests have been written for the /health endpoint. Instead of using a strong professional framework, I've opted to throw together a kludgy pytest test-class in test_health.py. Each test wipes the test database clean, writes dummy data to the table, and performs a hit on the endpoint with parameter `?debug=true` to signal to the application logic that the test database is to be used.

To run these tests, perform the command `pytest` anywhere in the project directory.

## Endpoints

### /stats
Returns the minimum, maximum, and average altitude of the past five minutes in a nicely formatted JSON. 

Value | Type | Description
-------|---------|---------------------------------------------------------
alt_min| Decimal | Minimum altitude observed in the last five minutes.
alt_max| Decimal | Maximum altitude observed in the last five minutes.
alt_avg| Decimal | Average of the last five minutes of altitude.

### /health
Returns an informative message pertaining to the status of the satellite over the past two minutes. If the satellite 

Message | Meaning
-------|------------------
WARNING: RAPID ORBITAL DECAY IMMINENT | The average altitude (of the last five minutes) has been below 160 for at least 60 seconds. Satellite currently in a dangerous state.
Sustained Low Earth Orbit Resumed | The satellite was previously in a dangerous state, but the average has since risen above 160 in the past 60 seconds.
Altitude is A-OK | The satellite has not entered a dangerous state for at least two minutes.

### Parameters
Parameter| Options | Function
---------|---------|---------
?debug   | true/false| Determines whether or not the test database should be used. Used by unit tests.

