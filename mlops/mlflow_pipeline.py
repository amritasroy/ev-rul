import subprocess
from src.drift import check_drift
import pandas as pd

reference_data = pd.read_csv('data/Battery_RUL.csv')  # initial reference
data = pd.read_csv('data/Battery_RUL.csv')  # Replace with new uploaded data in production

# Place engineered features logic here
# ...

if check_drift(reference_data, data):
    print("Drift detected, triggering retraining...")
    subprocess.run(["python", "src/train.py"])
else:
    print("No significant drift. Pipeline sleeping.")