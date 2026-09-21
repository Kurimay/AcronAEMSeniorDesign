# USER INPUT FILE FOR KEYBOARD ONLY.  
# If trying to use controller, name the other file user_input and rename this one something else


from threading import Lock
from pynput import keyboard
from simcore.shared_state import controls, controls_lock

class UserInput:


    ROLL_MIN  = -20.0 / 57.2958     #Radians
    ROLL_MAX  =  20.0 / 57.2958     #Radians
    PITCH_MIN = -20.0 / 57.2958     #Radians
    PITCH_MAX =  20.0 / 57.2958     #Radians
    YAW_RATE_MIN = -1.0
    YAW_RATE_MAX = 1.0
    HEAVE_MIN = 0.0
    HEAVE_MAX = 1.0

    ANGLE_STEP = 1 / 57.2958    #Radians
    RATE_STEP  = 0.02

    def start_listener(self):
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        try:
            self.apply_user_input(key.char)
        except AttributeError:
            pass

    def apply_user_input(self, key: str):

        with controls_lock:
            if key == 'd':
                controls["roll_cmd"] = max(controls["roll_cmd"] - self.ANGLE_STEP, self.ROLL_MIN)
            elif key == 'a':
                controls["roll_cmd"] = min(controls["roll_cmd"] + self.ANGLE_STEP, self.ROLL_MAX)
            elif key == 's':
                controls["pitch_cmd"] = min(controls["pitch_cmd"] + self.ANGLE_STEP, self.PITCH_MAX)
            elif key == 'w':
                controls["pitch_cmd"] = max(controls["pitch_cmd"] - self.ANGLE_STEP, self.PITCH_MIN)
            elif key == 'l':
                controls["yaw_rate_cmd"] = max(controls["yaw_rate_cmd"] - self.RATE_STEP, self.YAW_RATE_MIN)
            elif key == 'j':
                controls["yaw_rate_cmd"] = min(controls["yaw_rate_cmd"] + self.RATE_STEP, self.YAW_RATE_MAX)
            elif key == 'i':
                controls["heave_cmd"] = min(controls["heave_cmd"] + self.RATE_STEP, self.HEAVE_MAX)
            elif key == 'k':
                controls["heave_cmd"] = max(controls["heave_cmd"] - self.RATE_STEP, self.HEAVE_MIN)
