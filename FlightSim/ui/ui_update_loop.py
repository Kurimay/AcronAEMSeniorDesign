from PyQt6.QtCore import QTimer
from simcore.shared_state import latest_state, state_lock

class UIUpdateLoop:
    def __init__(self, ui):
        self.ui = ui
        self.timer = QTimer(self.ui)   # <-- parented timer (important)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(16)  # ~60 FPS

    def update_ui(self):
        with state_lock:
            if not latest_state:
                return
            state_json = latest_state.copy()

        self.ui.handleUpdate(state_json)

