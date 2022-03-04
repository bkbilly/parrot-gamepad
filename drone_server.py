import threading
import time
import os
import cv2
import olympe
from olympe.messages import gimbal
from olympe.messages.skyctrl.CoPiloting import setPilotingSource
from olympe.messages.ardrone3.Piloting import TakeOff, Landing
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged
from olympe.messages.camera import zoom_info, zoom_level, set_zoom_target
from flask import Flask, render_template


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


class Stream():
    def __init__(self, drone_obj):
        os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'
        self.rtsp_stream = f"rtsp://{drone_obj.ip}:554/live"

        self._monitor_thread = threading.Thread(target=self.show_stream)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def show_stream(self):
        cam = cv2.VideoCapture(self.rtsp_stream)
        while True:
            if drone_obj.connected:
                try:
                    success, frame = cam.read()
                    if success:
                        cv2.imshow('VIDEO', frame)
                        cv2.waitKey(1)
                    else:
                        cv2.destroyAllWindows()
                        time.sleep(1)
                        cam.open(self.rtsp_stream)
                except:
                    cv2.destroyAllWindows()
                    time.sleep(1)
                    cam.open(self.rtsp_stream)
            else:
                cv2.destroyAllWindows()
                time.sleep(1)
                cam.release()


app = Flask(__name__)

drone_obj = DroneConnect('10.202.0.1')
Stream(drone_obj)


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/start_piloting")
def start_piloting():
    drone_obj.drone(setPilotingSource(source="Controller")).wait()
    drone_obj.drone.start_piloting()
    return 'ok'


@app.route("/stop_piloting")
def stop_piloting():
    drone_obj.drone.stop_piloting()
    drone_obj.drone(setPilotingSource(source="SkyController")).wait()
    return 'ok'


@app.route("/flyingstate")
def flyingstate():
    return drone_obj.drone.get_state(FlyingStateChanged)['state'].name


@app.route("/takeoff")
def takeoff():
    drone_obj.drone(TakeOff())
    return 'ok'


@app.route("/land")
def land():
    drone_obj.drone(Landing())
    return 'ok'


@app.route("/get_gimbal")
def get_gimbal():
    return str(drone_obj.drone.get_state(gimbal.attitude)[0]['pitch_absolute'])


@app.route("/set_gimbalup")
def set_gimbalup():
    gimbal_pos = drone_obj.drone.get_state(gimbal.attitude)[0]['pitch_absolute']
    gimbal_pos += 5
    set_gimbal(gimbal_pos)
    return 'ok'


@app.route("/set_gimbaldown")
def set_gimbaldown():
    gimbal_pos = drone_obj.drone.get_state(gimbal.attitude)[0]['pitch_absolute']
    gimbal_pos -= 5
    set_gimbal(gimbal_pos)
    return 'ok'


@app.route("/get_zoom")
def get_zoom():
    return str(drone_obj.drone.get_state(zoom_level)[0]['level'])


@app.route("/get_maxzoom")
def get_zoominfo():
    return str(drone_obj.drone.get_state(zoom_info)[0]['maximum_level'])


@app.route("/set_zoom/<zoom_set>")
def set_zoom(zoom_set):
    drone_obj.drone(set_zoom_target(0, "level", float(zoom_set))).wait()
    return 'ok'


@app.route("/set_zoomin")
def set_zoomin():
    current_zoom = drone_obj.drone.get_state(zoom_level)[0]['level']
    max_zoom = drone_obj.drone.get_state(zoom_info)[0]['maximum_level']
    zoom_set = current_zoom + 0.5
    if zoom_set > max_zoom:
        zoom_set = max_zoom
    drone_obj.drone(set_zoom_target(0, "level", float(zoom_set))).wait()
    return 'ok'


@app.route("/set_zoomout")
def set_zoomout():
    current_zoom = drone_obj.drone.get_state(zoom_level)[0]['level']
    zoom_set = current_zoom - 0.5
    if zoom_set < 1:
        zoom_set = 1
    drone_obj.drone(set_zoom_target(0, "level", float(zoom_set))).wait()
    return 'ok'


@app.route("/set_gimbal/<gimbal_set>")
def set_gimbal(gimbal_set):
    drone_obj.drone(
        gimbal.set_target(
            gimbal_id=0,
            control_mode="position",
            yaw_frame_of_reference="none",
            yaw=0.0,
            pitch_frame_of_reference="absolute",
            pitch=float(gimbal_set),
            roll_frame_of_reference="none",
            roll=0.0,
        )
        >> gimbal.attitude(pitch_absolute=float(gimbal_set))
    ).wait().success()
    return 'ok'


@app.route("/set_pcmd/<roll>/<pitch>/<yaw>/<gaz>/<dt>")
def set_pcmd(roll, pitch, yaw, gaz, dt):
    drone_obj.drone.piloting_pcmd(
        roll=int(roll),
        pitch=int(pitch),
        yaw=int(yaw),
        gaz=int(gaz),
        piloting_time=float(dt))
    return 'ok'


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
