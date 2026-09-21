from PyQt6.QtCore import QThread, pyqtSignal
from time import sleep

from simcore.shared_state import controls, controls_lock, latest_state, state_lock
from simcore.user_input import UserInput
from simcore.physics_engine import PhysicsEngine
from simcore.state_json import state_json

class SimulationCore(QThread):
    # signal to send to the UI
    stateUpdated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = True
        self.input = UserInput()
        self.input.start_listener()
        self.physics = PhysicsEngine()

    def run(self):
        while self.running:
            # 1. feed controls into physics (directly from shared state)
            self.physics.apply_controls()

            # 2. step physics
            self.physics.step()

            # 3. snapshot UI state
            sj = state_json(self.physics.fdm)

            ui_state = sj.to_ui_dict()

            # (optional) add controls if UI needs them
            with controls_lock:
                ui_state["controls"] = controls.copy()

            # 4. publish FLAT UI STATE ONLY
            with state_lock:
                latest_state.clear()
                latest_state.update(ui_state)

            sleep(self.physics.dt)
