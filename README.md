# Cyphra_Autonomy_Parse

A Python tool for parsing `.BIN` flight logs from ArduPilot/PX4 systems, calculating key flight metrics like total distance, duration, and flight mode times.

Created by Arnav Gorantla

---

## Features

- Upload a .BIN file, it will prompt you while running
- Parses all the data from the log into csv (XKF1.csv, MODE.csv, etc.)
- Calculates:
  - Total distance traveled
  - Total flight duration
  - Time spent in MANUAL, GUIDED, and FOLLOW flight modes

---

## Requirements (Install dependencies if needed)

- Python 3.x
- `pymavlink` for reading `.BIN` log files
  - pip install pymavlink
- `tkinter` (included with Python standard library)

