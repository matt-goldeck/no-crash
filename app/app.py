#!flask/bin/python
from flask import Flask, jsonify, request
from utils import get_stats, get_health

app = Flask(__name__)

@app.route('/')
def index():
    return "I'm operational!"

@app.route('/stats')
def stats():
    stats_obj = get_stats()
    for stat in stats_obj:
        stats_obj[stat] = str(stats_obj[stat])
    return jsonify(stats_obj)

@app.route('/health')
def health():
    debug = request.args.get('debug')
    if isinstance(debug, basestring) and debug.lower() == 'true':
        debug = True
    else:
        debug = False
    health_obj = get_health(debug)
    return jsonify(health_obj)

if __name__ == "__main__":
    app.run(debug=True)
