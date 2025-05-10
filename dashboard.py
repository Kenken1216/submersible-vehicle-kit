import tkinter as tk     # GUI framework
from threading import Thread    # To run update functions in parallel
import cv2   # For camera feed handling
from PIL import Image, ImageTk  # For image conversion (OpenCV to Tkinter-compatible)
import time
import os    # For file naming

# Shared telemetry dictionary used across modules
telemetry = {
    "joystick": {"F": 0, "Y": 0, "P": 0, "R": 0},
    "pwm": [4915, 4915, 4915, 4915],
    "pwm_pid": {"m3": 4915, "m4": 4915},
    "imu": {"ax": 0, "ay": 0, "az": 0, "gx": 0, "gy": 0, "gz": 0, "pitch": 0, "roll": 0, "yaw": 0},
    "pressure": {"pressure": 0, "external_temp_c": 0, "external_temp_f": 0, "depth_cm": 0, "depth_ft": 0},
    "internal_temp": {"temp_c": 0, "temp_f": 0},
    "depth_hold": {"enabled": False, "target": 0},
    "pid_debug": {"error": 0.0, "effort": 0.0},
    "battery": {"voltage": 0, "percent": 0, "status": "Unknown"}
}

# Callback function placeholder to send commands from dashboard
send_command_callback = None

# Video recording state flags
recording = False
video_writer = None

# Updates all telemetry labels in the GUI
def update_loop(labels):
    while True:
        try:
            labels["joystick"].config(text=f"Joystick: {telemetry['joystick']}")
            labels["pwm"].config(text=f"Thrusters: {telemetry['pwm']}")
            labels["pwm_pid"].config(  
                text=f"PID Thrusters: m3={telemetry['pwm_pid'].get('m3', 0)} m4={telemetry['pwm_pid'].get('m4', 0)}"
            )
            labels["pid_debug"].config(text=                           # <-- ADDED
                f"PID Debug: error={telemetry['pid_debug']['error']:.2f}, "
                f"effort={telemetry['pid_debug']['effort']:.2f}"
            )
            labels["imu"].config(text=(
                f"IMU: ax={telemetry['imu']['ax']} ay={telemetry['imu']['ay']} az={telemetry['imu']['az']}\n"
                f"     gx={telemetry['imu']['gx']} gy={telemetry['imu']['gy']} gz={telemetry['imu']['gz']}\n"
                f"     pitch={telemetry['imu']['pitch']} roll={telemetry['imu']['roll']} yaw={telemetry['imu']['yaw']}"
            ))
            labels["pressure"].config(text=(
                f"Pressure: {telemetry['pressure']['pressure']} hPa\n"
                f"External Temp: {telemetry['pressure']['external_temp_c']} °C / {telemetry['pressure']['external_temp_f']} °F\n"
                f"Internal Temp: {telemetry['internal_temp']['temp_c']} °C / {telemetry['internal_temp']['temp_f']} °F\n"
                f"Depth: {telemetry['pressure']['depth_cm']} cm | {telemetry['pressure']['depth_ft']:.2f} ft\n"
                f"Relative Depth: {telemetry['pressure'].get('relative_depth_cm', 0):.2f} cm | "
                f"{telemetry['pressure'].get('relative_depth_ft', 0):.2f} ft\n"
            ))
            status = telemetry['depth_hold']
            labels["depth_hold"].config(
                text=(
                    f"Depth Hold: {'ON' if status['enabled'] else 'OFF'} | "
                    f"Target: {status['target']:.2f} cm | {status['target'] * 0.0328084:.2f} ft"
                ),
                fg="green" if status["enabled"] else "red"
            )
            labels["pwm_pid"].config(
                text=f"PID Thrusters: m3={telemetry['pwm_pid'].get('m3', 0)} m4={telemetry['pwm_pid'].get('m4', 0)}"
            )
              # --- Battery Monitor: START
            battery = telemetry.get("battery", {"voltage": 0, "percent": 0, "status": "Unknown"})
            voltage = battery["voltage"]
            percent = battery["percent"]
            bstatus = battery["status"]

            color = "green"
            if bstatus == "Moderate":
                color = "orange"
            elif bstatus == "Low":
                color = "orange red"
            elif bstatus == "Critical":
                color = "red"

            labels["battery"].config(
                text=f"Battery: {voltage:.2f}V | {percent}% | {bstatus}",
                fg=color
            )
            # --- Battery Monitor: END

        except:
            pass
        time.sleep(0.1)

# Continuously capture and update camera feed in dashboard
def update_camera(cam_label, cap, root):
    global recording, video_writer
    ret, frame = cap.read()
    if ret:
        orientation = camera_orientation.get()
        if orientation == "Flip Horizontal":
            frame = cv2.flip(frame, 1)
        elif orientation == "Flip Vertical":
            frame = cv2.flip(frame, 0)
        elif orientation == "Rotate 90":
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif orientation == "Rotate 180":
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif orientation == "Rotate 270":
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Convert frame for Tkinter display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        cam_label.imgtk = imgtk
        cam_label.configure(image=imgtk)

         # Save video if recording
        if recording and video_writer:
            video_writer.write(frame)

    # Schedule next frame update
    root.after(15, update_camera, cam_label, cap, root)


# Toggle video recording on/off
def toggle_record():
    global recording, video_writer
    recording = not recording
    if recording:
        filename = f"recording_{int(time.time())}.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
        record_btn.config(text="Stop Recording", bg="red")
        print(f"[RECORDING] Started: {filename}")
    else:
        if video_writer:
            video_writer.release()
        record_btn.config(text="Start Recording", bg="green")
        print("[RECORDING] Stopped")

def run_dashboard():
    global record_btn
    global camera_orientation
    root = tk.Tk()
    root.title("ROV Telemetry Dashboard")
    camera_orientation = tk.StringVar(value="Normal")

    # Initialize all telemetry label elements
    labels = {
        "joystick": tk.Label(root, text="Joystick:"),
        "pwm": tk.Label(root, text="Thrusters:"),
        "pwm_pid": tk.Label(root, text="PID Thrusters:"),
        "pid_debug": tk.Label(root, text="PID Debug:"),
        "imu": tk.Label(root, text="IMU:"),
        "pressure": tk.Label(root, text="Pressure:"),
        "depth_hold": tk.Label(root, text="Depth Hold:"),
        "pwm_pid": tk.Label(root, text="PID Thrusters:"),
        "battery": tk.Label(root, text="Battery:")
    }

    # Display labels
    for lbl in labels.values():
        lbl.pack(pady=4)

    record_btn = tk.Button(root, text="Start Recording", command=toggle_record, bg="green", fg="white")
    record_btn.pack(pady=10)

    orientation_options = [
        "Normal", "Flip Horizontal", "Flip Vertical",
        "Rotate 90", "Rotate 180", "Rotate 270"
    ]

    tk.Label(root, text="Camera Orientation:").pack()
    tk.OptionMenu(root, camera_orientation, *orientation_options).pack(pady=5)

    pid_frame = tk.LabelFrame(root, text="PID Tuning", padx=10, pady=10)
    pid_frame.pack(pady=10)

    tk.Label(pid_frame, text="Kp:").grid(row=0, column=0)
    tk.Label(pid_frame, text="Ki:").grid(row=1, column=0)
    tk.Label(pid_frame, text="Kd:").grid(row=2, column=0)

    kp_entry = tk.Entry(pid_frame, width=6)
    ki_entry = tk.Entry(pid_frame, width=6)
    kd_entry = tk.Entry(pid_frame, width=6)
    kp_entry.grid(row=0, column=1)
    ki_entry.grid(row=1, column=1)
    kd_entry.grid(row=2, column=1)

    kp_entry.insert(0, "0.05")
    ki_entry.insert(0, "0.01")
    kd_entry.insert(0, "0.02")

    def update_pid():
        if send_command_callback:
            try:
                kp = float(kp_entry.get())
                ki = float(ki_entry.get())
                kd = float(kd_entry.get())
                cmd = f"PID:{kp:.4f},{ki:.4f},{kd:.4f}\n"
                send_command_callback(cmd.encode())
                print(f"[PID UPDATE] Sent: {cmd.strip()}")
            except ValueError:
                print("[PID UPDATE] Invalid input!")

    tk.Button(pid_frame, text="Update PID", command=update_pid, bg="blue", fg="white").grid(row=3, columnspan=2, pady=5)

    # Camera display element
    cam_label = tk.Label(root)
    cam_label.pack(pady=10)

    # Open video capture (index 2 for external camera)
    cap = cv2.VideoCapture(2)

    # Start camera update loop
    root.after(0, update_camera, cam_label, cap, root)

    # Start telemetry update loop in a background thread
    Thread(target=update_loop, args=(labels,), daemon=True).start()

    # Begin GUI main loop
    root.mainloop()













