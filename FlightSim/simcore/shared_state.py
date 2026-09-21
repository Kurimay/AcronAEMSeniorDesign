"""
This is the shared state of the sim. Used to pass between files. 

"""

from threading import Lock

# user controls going INTO physics
controls = {
    "roll_cmd": 0.0,            #rad
    "pitch_cmd": 0.0,           #rad
    "yaw_rate_cmd": 0.0,
    "heave_cmd": 0.001  
}
controls_lock = Lock()

# physics state coming OUT to the UI
latest_state = {}
state_lock = Lock()
