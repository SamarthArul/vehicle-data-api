from flask import Flask, jsonify, request, abort
import sqlite3
import os
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)


app = Flask(__name__)
DATABASE = None

@app.before_request # Logs requests to command line
def log_request_info():
    """Log request method and endpoint before handling it."""
    print(f"Received {request.method} request for {request.path}")

@app.after_request
def log_response_info(response):
    """Log response status code after handling the request."""
    print(f"Returned {response.status} for {request.method} {request.path}")
    print('')
    return response



def get_db_connection():
    global DATABASE
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows dictionary-like access to rows
    return conn

def initialize_database(database_path):
    """Create and initialize the database schema if it doesn't exist."""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Create the Vehicle table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Vehicle (
        VIN TEXT UNIQUE NOT NULL,
        manufacturer_name TEXT NOT NULL,
        description TEXT,
        horse_power INTEGER,
        model_name TEXT NOT NULL,
        model_year INTEGER NOT NULL,
        purchase_price REAL,
        fuel_type TEXT NOT NULL
    );
    """)

    # Populate with basic entries
    default_vehicles = [
        ("1", "Honda", "Reliable Sedan", 150, "Accord", 2023, 25000.00, "Gasoline"),
        ("2", "Toyota", "Compact Hybrid", 200, "Prius", 2022, 27000.45, "Hybrid"),
        ("3", "Tesla", "Electric Sedan", 450, "Model S", 2024, 79999.99, "Electric"),
    ]

    try:
        cursor.executemany("""
        INSERT INTO Vehicle (VIN, manufacturer_name, description, horse_power, model_name, model_year, purchase_price, fuel_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, default_vehicles)
    except sqlite3.IntegrityError:
        # Skip if default vehicles already exist (useful for repeated initialization)
        pass

    conn.commit()
    conn.close()


@app.route('/vehicle', methods=['GET'])
def get_all_vehicles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vehicle")
    vehicles = cursor.fetchall()
    conn.close()

    result = [dict(row) for row in vehicles]
    return jsonify(result), 200

@app.route('/vehicle/<string:vin>', methods=['GET'])
def get_vehicle(vin):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vehicle WHERE VIN = ?", (vin,))
    vehicle = cursor.fetchone()
    conn.close()

    if vehicle:
        return jsonify(dict(vehicle)), 200
    else:
        abort(404, description="Vehicle not found")

@app.route('/vehicle', methods=['POST'])
def create_vehicle():
    if not request.is_json:
        abort(400, description="Invalid JSON payload")
    data = request.json
    required_fields = ['VIN', 'manufacturer_name', 'description', 'horse_power', 'model_name', 'model_year', 'purchase_price', 'fuel_type']

    if not all(field in data for field in required_fields):
        abort(422, description="Missing required fields")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO Vehicle (VIN, manufacturer_name, description, horse_power, model_name, model_year, purchase_price, fuel_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (data['VIN'], data['manufacturer_name'], data['description'], data['horse_power'], data['model_name'], data['model_year'], data['purchase_price'], data['fuel_type']))
        conn.commit()
    except sqlite3.IntegrityError:
        abort(422, description="VIN already exists")
    finally:
        conn.close()

    return jsonify(data), 201

@app.route('/vehicle/<string:vin>', methods=['PUT'])
def update_vehicle(vin):
    if not request.is_json:
        abort(400, description="Invalid JSON payload")
    data = request.json
    required_fields = ['manufacturer_name', 'description', 'horse_power', 'model_name', 'model_year', 'purchase_price', 'fuel_type']

    if not all(field in data for field in required_fields):
        abort(400, description="Missing fields in request")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Vehicle WHERE VIN = ?", (vin,))
    existing_vehicle = cursor.fetchone()

    if not existing_vehicle:
        abort(404, description="Vehicle not found")

    cursor.execute("""
    UPDATE Vehicle
    SET manufacturer_name = ?, description = ?, horse_power = ?, model_name = ?, model_year = ?, purchase_price = ?, fuel_type = ?
    WHERE VIN = ?
    """, (data['manufacturer_name'], data['description'], data['horse_power'], data['model_name'], data['model_year'], data['purchase_price'], data['fuel_type'], vin))
    conn.commit()
    conn.close()

    return jsonify(data), 200

@app.route('/vehicle/<string:vin>', methods=['DELETE'])
def delete_vehicle(vin):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Vehicle WHERE VIN = ?", (vin,))
    vehicle = cursor.fetchone()

    if not vehicle:
        conn.close()
        abort(404, description="Vehicle not found")

    cursor.execute("DELETE FROM Vehicle WHERE VIN = ?", (vin,))
    conn.commit()
    conn.close()

    return '', 204

if __name__ == '__main__':
    while True:
        db_name = input("Enter the name of the database to use (e.g. 'vehicles.db') or create a new one: ").strip()
        
        # Check if the user wants to exit
        if db_name.lower() == 'exit':
            print("Exiting the program. Goodbye!")
            exit(0)

        # Ensure the database name is valid
        if db_name:
            # Ensure the database name ends with ".db"
            if not db_name.endswith('.db'):
                db_name += '.db'
            break
        else:
            print("Error: Database name cannot be empty. Please try again or type 'exit' to exit:")

    DATABASE = os.path.join("database", db_name)
    if not os.path.exists(DATABASE):
        print(f"Creating '{DATABASE}'...")
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        initialize_database(DATABASE)
    else:
        print(f"Using existing database: {DATABASE}")

    print("Up and running on http://127.0.0.1:5000 (localhost)")
    print("Press CTRL+C to stop the server.")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
