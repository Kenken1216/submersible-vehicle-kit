# Import necessary modules
import pygame    # For Xbox controller input handling
import serial    # For serial communication with the XRP board
import time      # For sleep and timing functions
from dashboard import telemetry, run_dashboard, send_command_callback   # Dashboard functions and shared telemetry data
from threading import Thread     # To run dashboard GUI in a separate thread

# Change COM port if needed
ser = serial.Serial('COM16', 115200, timeout=1)

# Function to send raw serial data to the XRP board
def send_serial_command(data):  # <-- ADDED
    ser.write(data)

# Register this function as a callback for dashboard button commands
send_command_callback = send_serial_command

# Initialize pygame and the Xbox controller
pygame.init()
pygame.joystick.init()
controller = pygame.joystick.Joystick(0)
controller.init()

# Clamp function ensures value stays within min and max limits
def clamp(value, min_value=-1.0, max_value=1.0):
    return max(min_value, min(value, max_value))

# Applies a deadzone to ignore small joystick noise
def apply_deadzone(value, threshold=0.1):
    return 0.0 if abs(value) < threshold else value

# Normalizes raw joystick values with clamping and deadzone
def normalize_axis(raw_value):
    return apply_deadzone(clamp(raw_value))

# Maps a -1 to 1 effort value to a PWM range used by the motors
def map_effort_to_pwm(effort):
    mid = 4915
    range_ = 1638
    return max(3277, min(6553, int(mid + effort * range_)))

# Launch the dashboard in a separate thread
dashboard_thread = Thread(target=run_dashboard, daemon=True)
dashboard_thread.start()

# Initialize dictionary to store IMU telemetry data
imu_data = {"ax": 0, "ay": 0, "az": 0, "gx": 0, "gy": 0, "gz": 0, "pitch": 0, "roll": 0, "yaw": 0}

# Initialize depth hold mode state and variables
depth_hold_enabled = False
target_depth = 0
last_a = last_y = last_b = False  # Add last_b

while True:
    pygame.event.pump() # Process internal Pygame events


    forward = normalize_axis(controller.get_axis(1))
    yaw     = normalize_axis(controller.get_axis(0))
    roll    = normalize_axis(controller.get_axis(2))
    pitch   = normalize_axis(-controller.get_axis(3))

    a_pressed = controller.get_button(0)
    y_pressed = controller.get_button(3)
    b_pressed = controller.get_button(1)

     # Toggle depth hold mode on A button press (only on new press)
    if a_pressed and not last_a:
        depth_hold_enabled = not depth_hold_enabled
        print(f"[DEPTH HOLD] {'ENABLED' if depth_hold_enabled else 'DISABLED'}")
    last_a = a_pressed

    # Set target depth to current relative depth when Y button is newly pressed
    if y_pressed and not last_y and "relative_depth_cm" in telemetry["pressure"]:
        target_depth = telemetry["pressure"]["relative_depth_cm"]
        print(f"[DEPTH HOLD] Set Target Relative Depth: {target_depth:.2f} cm")

    # Send zeroing command when B button is pressed to reset relative depth
    if b_pressed and not last_b:
        ser.write(b"ZERO_DEPTH\n")
        print("[RELATIVE DEPTH] Zeroed at current position")
    last_b = b_pressed

     # If joystick is centered, set all PWM to neutral
    if all(val == 0.0 for val in [forward, yaw, pitch, roll]):
        pwm1 = pwm2 = pwm3 = pwm4 = 4915
    else:
        left_thrust  = clamp(forward + yaw)
        right_thrust = clamp(forward - yaw)
        right_vthrust = clamp(pitch - roll)
        left_vthrust  = clamp(pitch + roll)
        pwm1 = map_effort_to_pwm(left_thrust)
        pwm2 = map_effort_to_pwm(right_thrust)
        pwm3 = map_effort_to_pwm(right_vthrust)
        pwm4 = map_effort_to_pwm(left_vthrust)

    cmd = f"{pwm1},{pwm2},{pwm3},{pwm4},{int(depth_hold_enabled)},{target_depth:.2f}\n"
    ser.write(cmd.encode())

    # Handle incoming serial data from the XRP board
    if ser.in_waiting:
        response = ser.readline().decode().strip()
        print("RAW RESPONSE:", response)  # DEBUG LINE
        if response.startswith("TELEMETRY:"):
            try:
                # Parse data into sections
                parts = response.split(":")[1].replace("[", "").replace("]", "").split(",")
                print("PARTS COUNT:", len(parts))  # DEBUG LINE
                print("PARTS:", parts)             # DEBUG LINE

                # Decode and store telemetry values
                pwm_vals = list(map(int, parts[:4]))
                imu_vals = list(map(float, parts[4:10]))
                imu_data = dict(zip(["ax", "ay", "az", "gx", "gy", "gz"], imu_vals))
                if len(parts) >= 13:
                    imu_data["pitch"] = float(parts[10])
                    imu_data["roll"] = float(parts[11])
                    imu_data["yaw"] = float(parts[12])
                if len(parts) >= 21:
                    telemetry["pressure"] = {
                        "pressure": float(parts[13]),
                        "external_temp_c": float(parts[14]),
                        "external_temp_f": float(parts[15]),
                        "depth_cm": float(parts[16]),
                        "depth_ft": float(parts[16]) * 0.0328084
                    }
                    telemetry["depth_hold"] = {
                        "enabled": bool(int(parts[17])),
                        "target": float(parts[18])
                    }
                    telemetry["internal_temp"] = {
                        "temp_c": float(parts[19]),
                        "temp_f": float(parts[20])
                    }
                if len(parts) >= 22:
                    telemetry["pressure"]["relative_depth_cm"] = float(parts[21])
                    telemetry["pressure"]["relative_depth_ft"] = float(parts[21]) * 0.0328084
                
                # Add to telemetry["pwm_pid"]
                if len(parts) >= 25:
                    telemetry["pwm_pid"] = {
                        "m3": int(parts[22]),
                        "m4": int(parts[23])
                    }
                
                if len(parts) >= 28:  # --- Battery Monitor: updated index and length check
                    telemetry["battery"] = {
                        "voltage": float(parts[24]),
                        "percent": int(parts[25]),
                         "status": parts[26].strip()
                    }
                telemetry["pid_debug"] = {
                    "error": float(parts[27]),
                    "effort": float(parts[28])
                }
            except Exception as e:
                print("Bad telemetry:", response, "| Error:", e)

    telemetry["joystick"] = {
        "F": round(forward, 2),
        "Y": round(yaw, 2),
        "P": round(pitch, 2),
        "R": round(roll, 2)
    }
    telemetry["pwm"] = [pwm1, pwm2, pwm3, pwm4]
    telemetry["imu"] = imu_data

    time.sleep(0.01)







