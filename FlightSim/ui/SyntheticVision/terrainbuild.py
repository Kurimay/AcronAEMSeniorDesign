import json
import sys
import os
import math
from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, QUrl, Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQuick import QQuickView

# This file cannot run on its own
# The main point of it is to build the terrain from bigterrain.qml, put in the runways, and match the camera attitude to the vehicle attitude.
# One big issue that isnt fixable as far as I know is that the terrain color is just mostly a flat green so its hard to tell how fast you're moving
# If at all.  I tried to add a noise texture but I dont think its possible.  
# The height measurement is not perfect because the JSBsim terrain is just flat, so when on "the ground" in JSBsim you might seem to be in the sky with these visuals.

# --- NAVIGATION DATA BRIDGE ---
class Navigator(QObject):
    dataChanged = pyqtSignal()
    def __init__(self):
        super().__init__()
        # Added self._r for roll
        self._p, self._h, self._r, self._x, self._y, self._z = 0, 0, 0, 0, 186, 0
        self.refLat, self.refLon = 45.0, -93.0
        self.mPerLat, self.mPerLon = 111120.0, 80000.0

    @pyqtProperty(float, notify=dataChanged)
    def pitch(self): return self._p

    @pyqtProperty(float, notify=dataChanged)
    def hdg(self): return self._h

    # New property for Roll
    @pyqtProperty(float, notify=dataChanged)
    def roll(self): return self._r

    @pyqtProperty(float, notify=dataChanged)
    def posX(self): return self._x * 100.0

    @pyqtProperty(float, notify=dataChanged)
    def posY(self): return self._y

    @pyqtProperty(float, notify=dataChanged)
    def posZ(self): return self._z * 100.0

    # Added roll_deg to the arguments
    def update_state(self, lat, lon, alt_ft, pitch, hdg, roll_deg):
        self._x = (lon - self.refLon) * self.mPerLon
        self._z = -(lat - self.refLat) * self.mPerLat
        self._y = (alt_ft * 0.3048) #+ 100000
        self._p, self._h, self._r = pitch, hdg, roll_deg
        self.dataChanged.emit()

class TerrainApp(QQuickView):
    def __init__(self, nav_obj):
        super().__init__()
        self.nav = nav_obj
        
        # 1. Load the runway data
        runway_data = []
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(base_dir, "runways.json")
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    runway_data = json.load(f)
        except Exception as e:
            print(f"Error loading runways.json: {e}")

        # 2. Inject context properties
        self.rootContext().setContextProperty("nav", self.nav)
        self.rootContext().setContextProperty("runwayModel", runway_data)
        
        # 3. Load QML
        qml_path = os.path.join(os.path.dirname(__file__), "bigterrain.qml")
        self.setSource(QUrl.fromLocalFile(qml_path))

if __name__ == "__main__":
    # Standard standalone test runner
    app = QGuiApplication(sys.argv)
    
    nav_bridge = Navigator()
    win = TerrainApp(nav_bridge)
    win.setTitle("Synthetic Vision Debugger")
    win.resize(1280, 720)
    win.show()
    
    # Dummy update for testing standalone (Stationary at MSP)
    # update_state(lat, lon, alt_ft, pitch, hdg)
    nav_bridge.update_state(44.88, -93.22, 1200, 0, 0)
    
    sys.exit(app.exec())