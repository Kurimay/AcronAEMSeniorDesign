from PyQt6.QtWidgets import QApplication
from ui.main_window import *
from simcore.simulation_core import SimulationCore
# json stuff from ui.ui_update_loop import update_ui

app = QApplication(sys.argv)

sim = SimulationCore()
ui = CockpitWindow()

# PASS UI INPUT TO SIM CORE
ui.parent_sim = sim

# PASS SIM CORE STATE TO UI
# json stuff commtend out for now. sim.stateUpdated.connect(update_ui)

sim.start()
ui.show()

app.exec()
