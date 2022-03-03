from inputs import get_gamepad
import math
import threading
import time
import requests


class XboxController():
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):
        self.deadzone = 10

        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.Mode = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()


    def read(self): # return the buttons/triggers that you care about in this methode
        return [self.LeftJoystickY, self.LeftJoystickX, self.RightJoystickY, self.RightJoystickX, self.LeftTrigger, self.RightTrigger]


    def _monitor_controller(self):
        while True:
            events = get_gamepad()
            for event in events:
                if event.code == 'ABS_Y':
                    self.LeftJoystickY = int(round((event.state / XboxController.MAX_JOY_VAL * 100), 0)) # normalize between -1 and 1
                    if abs(self.LeftJoystickY) < self.deadzone:
                        self.LeftJoystickY = 0
                elif event.code == 'ABS_X':
                    self.LeftJoystickX = int(round((event.state / XboxController.MAX_JOY_VAL * 100), 0)) # normalize between -1 and 1
                    if abs(self.LeftJoystickX) < self.deadzone:
                        self.LeftJoystickX = 0
                elif event.code == 'ABS_RY':
                    self.RightJoystickY = int(round((event.state / XboxController.MAX_JOY_VAL * 100), 0)) # normalize between -1 and 1
                    if abs(self.RightJoystickY) < self.deadzone:
                        self.RightJoystickY = 0
                elif event.code == 'ABS_RX':
                    self.RightJoystickX = int(round((event.state / XboxController.MAX_JOY_VAL * 100), 0)) # normalize between -1 and 1
                    if abs(self.RightJoystickX) < self.deadzone:
                        self.RightJoystickX = 0
                elif event.code == 'ABS_Z':
                    self.LeftTrigger = int(round((event.state / XboxController.MAX_TRIG_VAL / 4 * 100), 0)) # normalize between 0 and 1
                elif event.code == 'ABS_RZ':
                    self.RightTrigger = int(round((event.state / XboxController.MAX_TRIG_VAL / 4 * 100), 0)) # normalize between 0 and 1
                elif event.code == 'BTN_TL':
                    self.LeftBumper = event.state
                elif event.code == 'BTN_TR':
                    self.RightBumper = event.state
                elif event.code == 'BTN_SOUTH':
                    self.A = event.state
                elif event.code == 'BTN_NORTH':
                    self.X = event.state
                elif event.code == 'BTN_WEST':
                    self.Y = event.state
                elif event.code == 'BTN_EAST':
                    self.B = event.state
                elif event.code == 'BTN_THUMBL':
                    self.LeftThumb = event.state
                elif event.code == 'BTN_THUMBR':
                    self.RightThumb = event.state
                elif event.code == 'BTN_SELECT':
                    self.Back = event.state
                elif event.code == 'BTN_START':
                    self.Start = event.state
                elif event.code == 'BTN_MODE':
                    self.Mode = event.state
                elif event.code == 'ABS_HAT0X':
                    self.LeftDPad = 0
                    self.RightDPad = 0
                    if event.state == 1:
                        self.RightDPad = 1
                    elif event.state == -1:
                        self.LeftDPad = 1
                elif event.code == 'ABS_HAT0Y':
                    self.UpDPad = 0
                    self.DownDPad = 0
                    if event.state == 1:
                        self.DownDPad = 1
                    elif event.state == -1:
                        self.UpDPad = 1


class ParrotAnafi():

    def __init__(self, url):
        self.url = url
        self.dt = 0.1
        self.joy = XboxController()
        self.start_control()


    def start_control(self):
        while True:
            try:
                if self.joy.RightBumper:
                    if self.joy.A:
                        print("Start Piloting")
                        requests.get(f"{self.url}/start_piloting")
                    if self.joy.B:
                        print("Stop Piloting")
                        requests.get(f"{self.url}/start_piloting")
                    elif self.joy.Back:
                        flyingstate = requests.get(f"{self.url}/flyingstate").text
                        print(flyingstate)
                        if flyingstate == 'landed':
                            print("TakeOff")
                            requests.get(f"{self.url}/takeoff")
                        else:
                            print("Land")
                            requests.get(f"{self.url}/land")
                        while self.joy.Back:
                            time.sleep(self.dt)
                    elif self.joy.UpDPad or self.joy.DownDPad:
                        print("Gimbal position")
                        gimbal_pos = float(requests.get(f"{self.url}/get_gimbal").text)
                        if self.joy.UpDPad:
                            gimbal_pos += 5
                        else:
                            gimbal_pos -= 5
                        print(gimbal_pos)
                        requests.get(f"{self.url}/set_gimbal/{gimbal_pos}")
                        time.sleep(self.dt)
                    elif self.joy.LeftDPad or self.joy.RightDPad:
                        print("Set zoom level")
                        max_zoom = float(requests.get(f"{self.url}/get_maxzoom").text)
                        cur_zoom = float(requests.get(f"{self.url}/get_zoom").text)
                        set_zoom = cur_zoom - 0.5
                        if self.joy.RightDPad:
                            set_zoom = cur_zoom + 0.5
                        if set_zoom > max_zoom:
                            set_zoom = max_zoom
                        elif set_zoom < 1:
                            set_zoom = 1
                        requests.get(f"{self.url}/set_zoom/{set_zoom}")
                        time.sleep(0.5)
                    elif any([self.joy.RightJoystickX, self.joy.RightJoystickY, self.joy.LeftJoystickX, self.joy.LeftJoystickY]):
                        print("piloting_pcmd")
                        roll = self.joy.RightJoystickX
                        pitch = -self.joy.RightJoystickY
                        yaw = self.joy.LeftJoystickX
                        gaz = -self.joy.LeftJoystickY
                        requests.get(f"{self.url}/set_pcmd/{roll}/{pitch}/{yaw}/{gaz}/{self.dt}")
                        time.sleep(self.dt)
            except Exception as e:
                print(e)



if __name__ == '__main__':
    url = 'http://127.0.0.1:5000'
    ParrotAnafi(url)
