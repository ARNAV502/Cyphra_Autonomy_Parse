import os
import math
import csv
from tkinter import Tk, filedialog
from pymavlink import mavutil

# --- Ask user to select a .BIN file ---
print("Select your .BIN log file")
root = Tk()
root.withdraw()
bin_file_path = filedialog.askopenfilename(filetypes=[("BIN files", "*.BIN")])
root.destroy()

if not bin_file_path:
    print("No file selected. Exiting.")
    exit()

print("Selected:", bin_file_path)

# --- Prepare output folder ---
output_folder = "output_csv"
os.makedirs(output_folder, exist_ok=True)

# --- Parse the .BIN file using pymavlink ---
mav = mavutil.mavlink_connection(bin_file_path)
messages_by_type = {}

while True:
    msg = mav.recv_match(blocking=False)
    if msg is None:
        break
    if msg.get_type() == "BAD_DATA":
        continue
    msg_type = msg.get_type()
    messages_by_type.setdefault(msg_type, []).append(msg.to_dict())

# --- Save each message type as its own CSV file ---
csv_paths = {}

for msg_type, messages in messages_by_type.items():
    csv_path = os.path.join(output_folder, f"{msg_type}.csv")
    csv_paths[msg_type] = csv_path

    with open(csv_path, "w", newline="") as f:
        if messages:
            # Collect all unique fieldnames across all messages of this type
            keys = sorted({key for msg in messages for key in msg})
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in messages:
                writer.writerow(row)

    print(f"Saved: {csv_path}")

# --- Distance Calculation using XKF1 ---
xkf1_csv_path = csv_paths.get("XKF1")
if xkf1_csv_path and os.path.exists(xkf1_csv_path):
    total_distance = 0.0
    previous_point = None

    with open(xkf1_csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                pe = float(row['PE'])
                pn = float(row['PN'])

                if previous_point:
                    dx = pe - previous_point[0]
                    dy = pn - previous_point[1]
                    delta = math.sqrt(dx**2 + dy**2)
                    total_distance += delta

                previous_point = (pe, pn)
            except (ValueError, KeyError):
                continue

    print("\nTotal distance traveled:", round(total_distance, 2), "meters")

    # --- Duration Calculation from XKF1 ---
    start_time = None
    end_time = None

    with open(xkf1_csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                time_us = int(row['TimeUS'])
                time_sec = time_us / 1_000_000

                if start_time is None:
                    start_time = time_sec
                end_time = time_sec
            except (ValueError, KeyError):
                continue

    if start_time is not None and end_time is not None:
        duration_minutes = (end_time - start_time) / 60
        print("Flight duration:", round(duration_minutes, 2), "minutes")
    else:
        print("Could not determine duration.")
else:
    print("\nXKF1.csv not found. Distance/duration not computed.")

# --- Mode Durations from MODE.csv ---
mode_csv_path = csv_paths.get("MODE")
if mode_csv_path and os.path.exists(mode_csv_path):
    mode_names = {
        "0": "MANUAL",
        "15": "GUIDED",
        "6": "FOLLOW"
    }

    durations = {name: 0 for name in mode_names.values()}
    last_mode = None
    last_time = None

    with open(mode_csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            mode = row.get("Mode")
            time_us = row.get("TimeUS")
            if not mode or not time_us:
                continue
            try:
                time_us = int(time_us)
            except ValueError:
                continue

            if mode != last_mode:
                if last_mode in mode_names and last_time is not None:
                    delta = time_us - last_time
                    durations[mode_names[last_mode]] += delta
                last_mode = mode
                last_time = time_us

    if last_mode in mode_names and last_time is not None:
        durations[mode_names[last_mode]] += time_us - last_time

    print("\nMode durations:")
    for mode in ["MANUAL", "GUIDED", "FOLLOW"]:
        seconds = durations[mode] / 1_000_000
        print(f"{mode} for {round(seconds, 3)} sec")
else:
    print("\nMODE.csv not found. Mode durations not computed.")
