# Parrot Anafi Gamepad

You can use an Xbox controller to control the Parrot Anafi drones.
Uses a client/server architecture which means that the controller can be connected to another computer.

## Controlls
 - **Right Bumper (5):** Keep pressing it to allow the other buttons to be pressed (Dead man's switch)
 - **A (0):** Activate Piloting (Disables Skycontroller and enables gamepad control)
 - **B (1):** Stop Piloting (Control using Skycontroller)
 - **Select/Back button (8):** Land
 - **Start button (9):** TakeOff
 - **Left Stick:**
   - **Up/Down:** Altitude
   - **Left/Right:** Yaw
 - **Right Stick:** Move left/right/forward/back
 - **DPad:**
   - **Up/Down:** Gimbal control
   - **Left/Right:** Zoom level


## How to run
You might want to edit the Drone IP from the `drone_server.py` file and the server IP on the `controller.py` file.
```
pip install -r requirements.txt
python drone_server.py
python controller.py
```
