import subprocess
import time
import requests

# Provide the database name
db_name = "test_vehicles.db"

# Start the Flask server in a subprocess and provide the database name as input
server_process = subprocess.Popen(
    ["python3", "app.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Send the database name to the server's input
server_process.stdin.write(f"{db_name}\n".encode())
server_process.stdin.flush()

# Give the server time to start
time.sleep(1)

# Initialize test result counters
tests_passed = 0
tests_failed = 0

try:
    # Base URL of the server
    BASE_URL = "http://127.0.0.1:5000"

    # Test 1: Create a new vehicle (POST)
    try:
        new_vehicle = {
            "VIN": "4",
            "manufacturer_name": "Ford",
            "description": "Truck",
            "horse_power": 400,
            "model_name": "F-150",
            "model_year": 2022,
            "purchase_price": 55000.00,
            "fuel_type": "Gasoline"
        }
        response = requests.post(f"{BASE_URL}/vehicle", json=new_vehicle)
        assert response.status_code == 201, f"POST failed: {response.status_code}"
        print("POST /vehicle: Passed")
        tests_passed += 1
    except Exception as e:
        print(f"POST /vehicle: Failed ({e})")
        tests_failed += 1

    # Test 2: Retrieve all vehicles (GET)
    try:
        response = requests.get(f"{BASE_URL}/vehicle")
        assert response.status_code == 200, f"GET failed: {response.status_code}"
        assert any(vehicle["VIN"] == "4" for vehicle in response.json()), "GET /vehicle did not return the new vehicle"
        print("GET /vehicle: Passed")
        tests_passed += 1
    except Exception as e:
        print(f"GET /vehicle: Failed ({e})")
        tests_failed += 1

    # Test 3: Retrieve the new vehicle by VIN (GET)
    try:
        response = requests.get(f"{BASE_URL}/vehicle/4")
        assert response.status_code == 200, f"GET by VIN failed: {response.status_code}"
        assert response.json()["manufacturer_name"] == "Ford", "GET /vehicle/4 returned incorrect data"
        print("GET /vehicle/4: Passed")
        tests_passed += 1
    except Exception as e:
        print(f"GET /vehicle/4: Failed ({e})")
        tests_failed += 1

    # Test 4: Delete the vehicle (DELETE)
    try:
        response = requests.delete(f"{BASE_URL}/vehicle/4")
        assert response.status_code == 204, f"DELETE failed: {response.status_code}"
        print("DELETE /vehicle/4: Passed")
        tests_passed += 1
    except Exception as e:
        print(f"DELETE /vehicle/4: Failed ({e})")
        tests_failed += 1

    # Test 5: Ensure the deleted vehicle is gone (GET)
    try:
        response = requests.get(f"{BASE_URL}/vehicle/4")
        assert response.status_code == 404, f"GET for deleted vehicle failed: {response.status_code}"
        print("GET /vehicle/4 after DELETE: Passed")
        tests_passed += 1
    except Exception as e:
        print(f"GET /vehicle/4 after DELETE: Failed ({e})")
        tests_failed += 1

    # Test 6: POST /vehicle with invalid JSON
    try:
        response = requests.post(f"{BASE_URL}/vehicle", data="invalid_json")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("POST /vehicle with invalid JSON: Passed")
        tests_passed += 1
    except Exception as e:
        print(f"POST /vehicle with invalid JSON: Failed ({e})")
        tests_failed += 1

    # Test 7: POST /vehicle with missing required fields
    try:
        incomplete_vehicle = {
            "VIN": "5",
            "manufacturer_name": "Chevy"
            # Missing required fields
        }
        response = requests.post(f"{BASE_URL}/vehicle", json=incomplete_vehicle)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("POST /vehicle with missing fields: Passed")
        tests_passed += 1
    except Exception as e:
        print(f"POST /vehicle with missing fields: Failed ({e})")
        tests_failed += 1

    # Test 8: GET /vehicle/<VIN> with a non-existent VIN
    try:
        response = requests.get(f"{BASE_URL}/vehicle/nonexistent")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("GET /vehicle/<VIN> not found: Passed")
        tests_passed += 1
    except Exception as e:
        print(f"GET /vehicle/<VIN> not found: Failed ({e})")
        tests_failed += 1

    # Test 9: PUT /vehicle/<VIN> with non-existent VIN
    try:
        updated_vehicle = {
            "manufacturer_name": "Ford",
            "description": "Updated Truck",
            "horse_power": 450,
            "model_name": "F-150 Raptor",
            "model_year": 2023,
            "purchase_price": 65000.00,
            "fuel_type": "Gasoline"
        }
        response = requests.put(f"{BASE_URL}/vehicle/4", json=updated_vehicle)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PUT /vehicle/<VIN> for non-existent vehicle: Passed")
        tests_passed += 1
    except Exception as e:
        print(f"PUT /vehicle/<VIN> for non-existent vehicle: Failed ({e})")
        tests_failed += 1

    # Test 10: DELETE /vehicle/<VIN> with a non-existent VIN
    try:
        response = requests.delete(f"{BASE_URL}/vehicle/nonexistent")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("DELETE /vehicle/<VIN> not found: Passed")
        tests_passed += 1
    except Exception as e:
        print(f"DELETE /vehicle/<VIN> not found: Failed ({e})")
        tests_failed += 1

except Exception as e:
    print(f"Test failed: {e}")
finally:
    # Stop the Flask server and print logs
    server_process.terminate()
    stdout, stderr = server_process.communicate()
    server_process.wait()

    # Print test summary
    total_tests = tests_passed + tests_failed
    pass_percentage = (tests_passed / total_tests) * 100 if total_tests > 0 else 0
    print('')
    print(f"Summary: {tests_passed}/{total_tests} tests passed ({pass_percentage:.2f}%)")
    print("Testing concluded.")
