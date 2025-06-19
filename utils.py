import csv
from datetime import datetime
import os

DATA_DIR = "data"
LOG_FILE = os.path.join(DATA_DIR, "game_log.csv")

def init_log():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOG_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "event", "x_pos", "y_pos", "score"])

def log_event(event, x_pos, y_pos, score):
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, event, x_pos, y_pos, score])
