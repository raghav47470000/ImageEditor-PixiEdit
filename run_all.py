import subprocess
import os
import time

# Start Flask API
print("Starting Flask API...")
flask_proc = subprocess.Popen(["python", "app.py"], cwd="flask_api")

# Wait a moment for Flask to start
time.sleep(2)

# Start Django
print("Starting Django server...")
try:
    subprocess.call(["python", "manage.py", "runserver"])
finally:
    print("Stopping Flask API...")
    flask_proc.terminate()
