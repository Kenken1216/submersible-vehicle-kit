# Underwater ROV Control System

This repository contains the software modules used for operating and monitoring a custom-built tethered underwater ROV (Remotely Operated Vehicle). The system is built around the XRP Beta board and integrates thruster control, sensor telemetry, and a live graphical dashboard for human interaction.

---

## 📁 Repository Contents

- `acce_test.py`  
  Python script (runs on the laptop) responsible for interfacing with the Xbox controller, transmitting joystick commands to the XRP, and receiving/parsing telemetry data from the board.

- `dashboard.py`  
  A live telemetry dashboard built with `tkinter`, displaying joystick input, motor PWM values, IMU readings, pressure-based depth information, PID outputs, and camera feed.

- `main.txt` *(Rename to `main.py` before uploading to XRP)*  
  MicroPython script that runs on the XRP Beta board. It handles motor PWM control, reads sensor data (IMU, pressure, temperature), and sends telemetry back via serial.

- `imu.txt` *(Rename to `imu.py`)*  
  MicroPython driver for the LSM6DSO IMU sensor, used to gather accelerometer and gyroscope data.

- `imu_defs.txt` *(Rename to `imu_defs.py`)*  
  Constant and register definitions required by the IMU driver.

- `lps33.txt` *(Rename to `lps33.py`)*  
  MicroPython driver for the LPS33 pressure sensor. This script reads pressure and calculates depth in both centimeters and feet.

---

## 🔧 Setup Instructions

### Hardware Required
- XRP Beta board with MicroPython support
- Raspberry Pi 4 (or laptop with USB serial connection)
- LSM6DSO IMU (connected via I2C)
- LPS33 pressure sensor (connected via Qwiic/I2C)
- Xbox controller (wired USB)
- External USB camera
- 4 thrusters connected to PWM pins (mL, mR, m3, m4)

### Installation

1. **On the XRP Beta Board (via Thonny IDE):**
   - Upload `main.txt` → rename as `main.py`
   - Upload `imu.txt` → rename as `imu.py`
   - Upload `imu_defs.txt` → rename as `imu_defs.py`
   - Upload `lps33.txt` → rename as `lps33.py`

2. **On the Laptop (VS Code or similar):**
   - Ensure Python 3.x is installed
   - Install dependencies:
     ```bash
     pip install opencv-python pillow pygame
     ```
   - Run `acce_test.py` in one terminal to start control and telemetry
   - Run `dashboard.py` in another terminal to view telemetry and video

---

## ▶️ Operation Guide

1. Connect all components and power on the XRP board.
2. Launch `main.py` on the XRP board via Thonny.
3. Connect the Xbox controller to your laptop via USB.
4. Launch `acce_test.py` to start joystick control and serial telemetry.
5. Launch `dashboard.py` to monitor all telemetry data in real-time.

### Controls
- Left/Right joystick: Thruster movement (surge/sway/heave)
- A button: Toggle depth hold
- Y button: Set current depth as target for depth hold
- B button: Reset relative depth to 0
- Dashboard button: Start/Stop video recording
- PID settings can be updated live from the dashboard

---

## 📊 Telemetry Includes:
- Joystick inputs
- PWM outputs for 4 motors
- PID PWM values for vertical thrusters
- IMU data (acceleration, gyroscope, pitch, roll, yaw)
- Pressure sensor readings (depth, temperature)
- Internal temperature from XRP
- Depth-hold mode status and target depth
- Live camera feed
- Debugging console

---

## 🛠️ Troubleshooting

- Ensure correct COM port is selected when using serial communication
- If dashboard freezes, check for controller connection or sensor data parsing
- Use print/debug statements in `acce_test.py` and `main.py` for error tracing
- Sensor readings return 0? Double-check I2C wiring and sensor addresses
- PID not stabilizing? Tune Kp, Ki, Kd values from the dashboard

---

## 👤 Author

Kenny Le  
B.S. in Computer Engineering, Florida State University  
Submersible ROV Project - Software Development Lead  
2024–2025

---

## 📜 License

MIT License. You are free to modify and use this code with attribution for non-commercial educational or research purposes.

