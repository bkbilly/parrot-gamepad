from inputs import get_gamepad
import math
import threading
import time
import olympe
from olympe.messages import gimbal
from olympe.messages.skyctrl.CoPiloting import setPilotingSource
from olympe.messages.ardrone3.Piloting import TakeOff, Landing
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged
from olympe.messages.camera import zoom_info, zoom_level, set_zoom_target


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


class DroneConnect():

    def __init__(self, ip):
        self.ip = ip
        olympe.log.update_config({"loggers": {"olympe": {"level": "CRITICAL"}}})
        self.connected = False
        self.drone = olympe.Drone(self.ip)
        self.version = 1
        if hasattr(self.drone, 'connected'):
            self.version = 7
        connect_thread = threading.Thread(target=self._connect)
        connect_thread.setDaemon(True)
        connect_thread.start()

    def _controler_status(self):
        if self.version == 7:
            return self.drone.connected
        elif self.version == 1:
            return self.drone.connection().OK

    def _drone_status(self):
        if self.version == 7:
            return self.drone.connection_state()
        elif self.version == 1:
            return self.drone.connection_state().OK

    def _connect(self):
        while True:
            while not self._controler_status():
                time.sleep(1)
                self.drone.connect()
                if self._controler_status():
                    print("[o] CONTROLLER: Connected successfully!")
                else:
                    print("[!] CONTROLLER ERROR: Controller reconnection in progress...")

            drone_connected = self._drone_status()
            while not drone_connected and self._controler_status():
                time.sleep(1)
                drone_connected = self._drone_status()
                if not drone_connected:
                    print("[!] DRONE ERROR: Waiting for drone to connect...")
                    self.connected = False
            if not self.connected and drone_connected:
                print("[o] DRONE: Connected successfully!")
                self.connected = True

            time.sleep(10)


class ParrotAnafi():

    def __init__(self, drone):
        self.joy = XboxController()
        self.drone = drone
        self.dt = 0.1
        self.start()

    def start(self):
        self.drone(setPilotingSource(source="Controller")).wait()
        self.drone.start_piloting()
        self.start_control()

    def start_control(self):
        while True:
            try:
                if self.joy.Back:
                    flyingstate = self.drone.get_state(FlyingStateChanged)['state']
                    if flyingstate.name == 'landed':
                        print("TakeOff")
                        self.drone(TakeOff())
                    else:
                        print("Land")
                        self.drone(Landing())
                    while self.joy.Back:
                        time.sleep(0.1)
                elif self.joy.UpDPad or self.joy.DownDPad:
                    print("Gimbal position")
                    gimbal_pos = self.drone.get_state(gimbal.attitude)[0]['pitch_absolute']
                    if self.joy.UpDPad:
                        gimbal_pos += 5
                    else:
                        gimbal_pos -= 5
                    print(gimbal_pos)
                    self.drone(
                        gimbal.set_target(
                            gimbal_id=0,
                            control_mode="position",
                            yaw_frame_of_reference="none",
                            yaw=0.0,
                            pitch_frame_of_reference="absolute",
                            pitch=gimbal_pos,
                            roll_frame_of_reference="none",
                            roll=0.0,
                        )
                        >> gimbal.attitude(pitch_absolute=gimbal_pos)
                    ).wait().success()
                    time.sleep(self.dt)
                elif self.joy.LeftDPad or self.joy.RightDPad:
                    print("Set zoom level")
                    max_zoom = self.drone.get_state(zoom_info)[0]['maximum_level']
                    cur_zoom = self.drone.get_state(zoom_level)[0]['level']
                    set_zoom = cur_zoom - 0.5
                    if self.joy.RightDPad:
                        set_zoom = cur_zoom + 0.5
                    if set_zoom > max_zoom:
                        set_zoom = max_zoom
                    elif set_zoom < 1:
                        set_zoom = 1
                    self.drone(set_zoom_target(0, "level", set_zoom)).wait()
                    time.sleep(0.5)
                elif any([self.joy.RightJoystickX, self.joy.RightJoystickY, self.joy.LeftJoystickX, self.joy.LeftJoystickY]):
                    print("piloting_pcmd")
                    self.drone.piloting_pcmd(
                        roll=self.joy.RightJoystickX,
                        pitch=-self.joy.RightJoystickY,
                        yaw=self.joy.LeftJoystickX,
                        gaz=-self.joy.LeftJoystickY,
                        piloting_time=self.dt)
                    time.sleep(self.dt)
            except Exception as e:
                print(e)


if __name__ == '__main__':
    drone_obj = DroneConnect('10.202.0.1')
    ParrotAnafi(drone_obj.drone)
