from __future__ import annotations
import sys
import json
import os
from PyQt6.QtCore import Qt, QPointF, QRectF, QObject, pyqtProperty, pyqtSignal, QUrl
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel, QGridLayout, QHBoxLayout, QVBoxLayout, QStackedLayout)
from PyQt6.QtQuickWidgets import QQuickWidget

from .widgets import *
from .Map.map import Map
from .ui_update_loop import UIUpdateLoop
from .SyntheticVision.terrainbuild import Navigator

import threading
import socketserver

if not QApplication.instance():
    app = QApplication(sys.argv if sys.argv else ["python"])

def start_tile_server():    # this is for the map
    from ui.Map.map import MBTilesHandler 
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", 8000), MBTilesHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd

# ==================== Main Window ====================
class CockpitWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1280, 720)

        # --- WINDOW SETUP ---
        self.setWindowTitle("eVTOL Glass – PyQt6")
        self.setStyleSheet("background:#000; color:#fff;")


        # =========================================================
        # LEFT PANEL (Attitude + 3D Terrain + Overlays)
        # =========================================================
        self.nav_bridge = Navigator()
        
        runway_data = []
        try:
            with open("ui/runways.json", 'r') as f:
                runway_data = json.load(f)
        except: pass

        left = QWidget()
        left.setStyleSheet("background: black;")

        # Create the Terrain View
        self.terrain_view = QQuickWidget(left)
            # Now self.nav_bridge exists, so this won't crash:
        self.terrain_view.rootContext().setContextProperty("nav", self.nav_bridge)
        self.terrain_view.rootContext().setContextProperty("runwayModel", runway_data)
        self.terrain_view.setSource(QUrl.fromLocalFile("ui/SyntheticVision/bigterrain.qml"))
        self.terrain_view.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

        # Create the Instruments
        self.ai = AttitudeIndicator(left)
        self.tas = TapeWidget("TAS", "{:.0f}", QColor(180, 220, 255))
        self.alt = TapeWidget("ALT", "{:.0f}", QColor(255, 220, 220))
        self.compass = CompassWidget()
        self.vrate = RateWidget()

        # Set parents for the manual overlays
        for w in [self.tas, self.alt, self.compass, self.vrate]:
            w.setParent(left)

        # Widget Placement
        def reposition_overlays():
            w, h = left.width(), left.height()
            
            # Bottom Layer
            self.terrain_view.setGeometry(0, 0, w, h)
            
            # Middle Layer (Instruments)
            self.ai.setGeometry(0, 0, w, h)
            
            # Top Layer (Tapes & Gauges) (x,y,width,height)
            self.tas.setGeometry(20, int(h * 0.25), 90, int(h * 0.5))
            self.alt.setGeometry(int(w - 120), int(h * 0.25), 90, int(h * 0.5))
            self.vrate.setGeometry(int(w - 30-6), int(h * 0.25) + int(h * 0.15/2), 30+6, int(h * 0.35))
            self.compass.setGeometry(int(w / 2 - 110), int(h * 0.7), 120, 120)

            # FORCE Z-ORDER
            self.terrain_view.lower()
            self.ai.raise_()
            self.tas.raise_()
            self.alt.raise_()
            self.compass.raise_()
            self.vrate.raise_()

        left.resizeEvent = lambda e: reposition_overlays()

        # Toggle terrain, press T to toggle terrain right now
        from PyQt6.QtGui import QShortcut, QKeySequence
        self.t_key = QShortcut(QKeySequence("T"), self)
        self.t_key.activated.connect(self.toggle_ai_bg)

        # =========================================================
        # RIGHT PANEL
        # =========================================================

        right = QWidget()
        right.setStyleSheet("background:black;")

        # Widgets
        self.map = Map() 
        self.vsi = VMap()
        self.RPM1 = SemicircleIndicator(label="PROP1")
        self.RPM2 = SemicircleIndicator(label="PROP2")
        self.RPM3 = SemicircleIndicator(label="PROP3")
        self.RPM4 = SemicircleIndicator(label="PROP4")
        self.POWER = VerticalIndicator()
        self.battery = VerticalIndicator(label = "BATTERY", unit="%", valuerange = (0,100), greenrange = (30,98), yellowrange = (10,29), redrange = (2,9))
        self.range = BasicText()
        self.endurance = BasicText(label = "ENDURANCE MIN", unit="MIN")
        self.checklist = PreflightChecklist()

        # Parent them all to right side
        self.map.setParent(right)  
        self.RPM1.setParent(right)
        self.RPM2.setParent(right)
        self.RPM3.setParent(right)
        self.RPM4.setParent(right)
        self.POWER.setParent(right)
        self.battery.setParent(right)
        self.range.setParent(right)
        self.endurance.setParent(right)
        self.checklist.setParent(right)

        # Widget placement
        def resize_right_layers():  
            W, H = right.width(), right.height()
            self.map.setGeometry(0, 0, int(W), int(H * 6/8) - 20)
            self.RPM1.setGeometry(0, int(H*3/4), int(W), int(H/5.5))
            self.RPM2.setGeometry(int(W*1/5)+5, int(H*3/4), int(W), int(H/5.5))
            self.RPM3.setGeometry(0, int(H*3/4) + int(H/8), int(W), int(H/5.5))
            self.RPM4.setGeometry(int(W*1/5)+5, int(H*3/4) + int(H/8), int(W), int(H/5.5))
            self.POWER.setGeometry(int(W*4/10)+5, int(H*3/4)-5, int(W/9), int(H/4)+15)
            self.battery.setGeometry(int(W*5/10), int(H*3/4)-5, int(W/9), int(H/4)+15)
            self.range.setGeometry(int(W*6.5/10), int(H*12/16), int(W/3), int(H/16))
            self.endurance.setGeometry(int(W*6.5/10), int(H*13/16)-2, int(W/3), int(H/16))
            self.checklist.setGeometry(int(W*6.5/10), int(H*12/16), W-int(W*6.5/10),H-int(H*12/16))

        right.resizeEvent = lambda e: resize_right_layers()

        # Put left panel on left and right panel on right
        central = QWidget() 
        grid = QGridLayout(central)
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setHorizontalSpacing(10)
        grid.addWidget(left, 0, 0)
        grid.addWidget(right, 0, 1)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 2)

        self.setCentralWidget(central)
        self.ui_loop = UIUpdateLoop(self)

    # Get state from JSBsim and set value of widget variables
    def handleUpdate(self, d: dict):
        self.ai.set_state(d["roll_deg"], d["pitch_deg"])
        self.tas.set_value(d["tas_kt"])
        self.alt.set_value(d["alt_ft"])
        self.compass.set_heading(d["hdg_deg"])
        self.vrate.set_value(d["vrate_fps"])

        # Update 3D Bridge
        self.nav_bridge.update_state(d["latitude_deg"], d["longitude_deg"], d["alt_ft"], d["pitch_deg"], d["hdg_deg"], d["roll_deg"])

        self.map.set_state(d["latitude_deg"], d["longitude_deg"], d["hdg_deg"])
        self.vsi.set_state(d["pitch_deg"], d["alt_ft"])
        self.RPM1.set_value(d["rotor_rpm"][0])
        self.RPM2.set_value(d["rotor_rpm"][2])
        self.RPM3.set_value(d["rotor_rpm"][3])
        self.RPM4.set_value(d["rotor_rpm"][1])
        self.POWER.set_value(sum(d["rotor_powers_kw"][0:4]))
        self.battery.set_value(d["hdg_deg"] / 3.6)
        self.range.set_value(d["range_nm"])
        self.endurance.set_value(d["endurance_min"])

    def toggle_ai_bg(self): # T to toggle terrain 
        if hasattr(self, 'ai'):
            is_visible = self.ai.bg.isVisible()
            self.ai.bg.setVisible(not is_visible)
            print(f"SVT Mode: {is_visible}") # If BG was visible, it's now SVT

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CockpitWindow()
    window.show()
    sys.exit(app.exec())