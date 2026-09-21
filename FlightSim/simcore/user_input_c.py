# USER INPUT FILE FOR CONTROLLER ONLY. 
# If trying to use keyboard, name the other file user_input and rename this one something else

import pygame
from threading import Thread
from simcore.shared_state import controls, controls_lock


class UserInput:

    ROLL_MIN  = -20.0 / 57.2958
    ROLL_MAX  =  20.0 / 57.2958
    PITCH_MIN = -20.0 / 57.2958
    PITCH_MAX =  20.0 / 57.2958
    YAW_RATE_MIN = -1.0
    YAW_RATE_MAX = 1.0
    HEAVE_MIN = 0.0
    HEAVE_MAX = 1.0

    def start_listener(self):
        """
        Keeps same name, but now starts a controller polling loop
        """
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            raise RuntimeError("No controller detected")

        self.throttle = pygame.joystick.Joystick(0)
        self.throttle.init()

        self.stick = None
        if pygame.joystick.get_count() > 1:
            self.stick = pygame.joystick.Joystick(1)
            self.stick.init()

        # Run controller polling in background thread
        self.thread = Thread(target=self.controller_loop, daemon=True)
        self.thread.start()

    def controller_loop(self):
        """
        Continuous polling loop (replaces pynput listener)
        """
        clock = pygame.time.Clock()

        while True:
            pygame.event.pump()

            with controls_lock:

                # =========================
                # ROLL & PITCH
                # =========================
                if self.stick:
                    roll = self.stick.get_axis(0)
                    pitch = self.stick.get_axis(1)

                    controls["roll_cmd"] = max(
                        min(roll * self.ROLL_MAX, self.ROLL_MAX),
                        self.ROLL_MIN
                    )

                    controls["pitch_cmd"] = max(
                        min(pitch * self.PITCH_MAX, self.PITCH_MAX),
                        self.PITCH_MIN
                    )

                    # =========================
                    # YAW
                    # =========================
                    rudder = self.stick.get_axis(4)

                    controls["yaw_rate_cmd"] = max(
                        min(rudder, self.YAW_RATE_MAX),
                        self.YAW_RATE_MIN
                    )

                # =========================
                # THROTTLE → HEAVE
                # =========================
                axis = 1 if self.throttle.get_numaxes() > 1 else 0
                throttle = self.throttle.get_axis(axis)

                throttle_norm = (throttle + 1) / 2
                throttle_norm = 1 - throttle_norm

                controls["heave_cmd"] = max(
                    min(throttle_norm, self.HEAVE_MAX),
                    self.HEAVE_MIN
                )

            clock.tick(60)  # 60 Hz update