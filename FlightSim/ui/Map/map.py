import sys
import sqlite3
import http.server
import socketserver
import threading
import math
from pathlib import Path
from urllib.parse import unquote

from PyQt6.QtCore import QRect, QUrl, Qt, QPointF, QTimer, QRect
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QPainter, QPolygonF, QColor, QPen, QFont


# =====================
# CONFIGURATION
# =====================
BASE_DIR = Path(__file__).parent.resolve()
MBTILES_FILE = "msp.mbtiles"
STYLE_FILE = "style.json"
TILE_PORT = 8000

MBTILES_PATH = BASE_DIR / MBTILES_FILE
STYLE_PATH = BASE_DIR / STYLE_FILE
HTML_FILE = BASE_DIR / "map.html"
JS_FILE = BASE_DIR / "maplibre-gl.js"
CSS_FILE = BASE_DIR / "maplibre-gl.css"

center_lon, center_lat, zoom_default = -93.278, 44.943, 12.0

# =====================
# MBTiles HTTP SERVER
# =====================
class MBTilesHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args): return 
    def do_GET(self):
        path = unquote(self.path)
        if path.startswith("/tiles/") and path.endswith(".pbf"):
            parts = path.strip("/").split("/")
            try:
                z, x = int(parts[1]), int(parts[2])
                y = int(parts[3].replace(".pbf",""))
                y_tms = (1 << z) - 1 - y 
                conn = sqlite3.connect(MBTILES_PATH)
                cur = conn.cursor()
                cur.execute("SELECT tile_data FROM map WHERE zoom_level=? AND tile_column=? AND tile_row=?", (z, x, y_tms))
                row = cur.fetchone()
                if row:
                    self.send_response(200)
                    self.send_header("Content-type", "application/x-protobuf")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(row[0])
                else:
                    self.send_error(404)
                conn.close()
            except Exception:
                self.send_error(500)
        else:
            super().do_GET()

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    return socketserver.TCPServer(("", TILE_PORT), MBTilesHandler)

# =====================
# GENERATE HTML
# =====================
STYLE_URL = STYLE_PATH.as_uri()
JS_URL = JS_FILE.as_uri()
CSS_URL = CSS_FILE.as_uri()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <link href="{CSS_URL}" rel="stylesheet" />
    <script src="{JS_URL}"></script>
    <style>
        body {{ margin:0; padding:0; background: #507C3C; overflow: hidden; }}
        #map {{ position:absolute; top:0; bottom:0; width:100%; }}
    </style>
</head>
<body>
<div id="map"></div>
<script>
    var map;
    map = new maplibregl.Map({{
        container: 'map',
        style: '{STYLE_URL}',
        center: [{center_lon}, {center_lat}],
        zoom: {zoom_default},
        attributionControl: false
    }});

    window.updateMap = function(lat, lon, hdg, zoom) {{
        if (map) {{
            map.jumpTo({{ center: [lon, lat], bearing: hdg, zoom: zoom, animate: false }});
        }}
    }};
</script>
</body>
</html>
"""
with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(html_content)

# =====================
# MAP COMPONENTS
# =====================

class MapOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.heading = 0.0      
        self.map_bearing = 0.0  
        self.zoom = zoom_default
        self.lat = center_lat
        self.is_north_up = True
        
        # --- FIXED UI SETTINGS ---
        self.RING_RADIUS_PX = 200  # The circle will always be 200px on screen

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx, cy = self.width() / 2, self.height() / 2
        self.draw_fixed_range_circle(painter, cx, cy)
        self.draw_aircraft(painter, cx, cy)
        self.draw_north_arrow(painter)

    def draw_fixed_range_circle(self, painter, cx, cy):
        """Draws a circle that stays the same size on screen, but updates the NM label."""
        # 1. Calculate how many meters are currently represented by 1 pixel
        # Formula: meters_per_pixel = (EarthCircumference * cos(lat)) / 2^(zoom + 8)
        # Using the standard Web Mercator constant:

        correctionfactor = 0.5 # correction factor determined by guessing because the original number was incorrect
                                # maybe it was radius instead of diameter or something

        meters_per_pixel = (156543.03 * math.cos(math.radians(self.lat))) / (2 ** self.zoom) * correctionfactor
        
        # 2. Total meters covered by our fixed pixel radius
        total_meters = meters_per_pixel * self.RING_RADIUS_PX
        
        # 3. Convert meters to Nautical Miles (1 NM = 1852 meters)
        current_nm = total_meters / 1852.0

        painter.save()
        # Draw the ring
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
        painter.drawEllipse(QPointF(cx, cy), self.RING_RADIUS_PX, self.RING_RADIUS_PX)
        
        # Draw the dynamic label (rounded to 1 decimal)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        label = f"{current_nm:.1f} NM"
        # 1. Calculate the 45-degree point (Northeast)
        angle_rad = math.radians(45)
        # Point exactly on the line
        target_x = cx + (self.RING_RADIUS_PX * math.cos(angle_rad))
        target_y = cy - (self.RING_RADIUS_PX * math.sin(angle_rad))

        # 2. Setup Label and Font
        painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        label = f"{current_nm:.1f} NM"
        
        # 3. Get text dimensions and add padding
        metrics = painter.fontMetrics()
        raw_text_rect = metrics.boundingRect(label)
        padding_h = 4
        padding_v = 2
        
        # Calculate box size
        box_w = raw_text_rect.width() + (padding_h * 2)
        box_h = raw_text_rect.height() + (padding_v * 2)
        
        # 4. Center the box ON the line
        # Subtract half the width/height so the box center is on the circle edge
        final_box = QRect(
            int(target_x - (box_w / 2)), 
            int(target_y - (box_h / 2)), 
            box_w, 
            box_h
        )

        # 5. Draw Rounded Black Box with White Outline
        painter.setBrush(QColor(0, 0, 0))        
        painter.setPen(QPen(QColor(255, 255, 255), 1)) 
        # Draw with 5px corner radius
        painter.drawRoundedRect(final_box, 5, 5)

        # 6. Draw Text centered in that box
        painter.setPen(QColor(255, 255, 255)) 
        painter.drawText(final_box, Qt.AlignmentFlag.AlignCenter, label)
        painter.restore()

    def draw_aircraft(self, painter, cx, cy):
        painter.save()
        painter.translate(cx, cy)
        if self.is_north_up:
            painter.rotate(self.heading)
        
        pointer = QPolygonF([QPointF(-8, 12), QPointF(8, 12), QPointF(0, -12)])
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawPolygon(pointer)
        painter.restore()

    def draw_north_arrow(self, painter):
        painter.save()
        painter.translate(50, 60) 
        
        # 1. Rotate and draw the arrow
        painter.save() # Save state before arrow rotation
        painter.rotate(-self.map_bearing)
        
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setBrush(QColor(255, 255, 255))
        painter.drawPolygon(QPolygonF([
            QPointF(-20, 20),  # Left
            QPointF(0, 10),   # Bottom
            QPointF(20, 20),   # Right
            QPointF(0, -30)   # Top Tip
        ]))
        painter.restore() # Restore to "upright" state at (50, 60)

        # 2. Draw the "N" (Now it's upright because of the restore)
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        # Centered on the same pivot point, but ignoring map rotation
        text_rect = QRect(-20, -20, 40, 40) 
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "N")
        
        painter.restore()

class Map(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.north_up = True
        self.current_zoom = float(zoom_default)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = QWebEngineView()
        s = self.view.settings()
        s.setAttribute(s.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        s.setAttribute(s.WebAttribute.LocalContentCanAccessFileUrls, True)
        
        self.view.load(QUrl.fromLocalFile(str(HTML_FILE)))
        layout.addWidget(self.view)

        self.overlay = MapOverlay(self)
        self.setup_buttons()

    def setup_buttons(self):
        # Shared Style: Uniform sizing and removed right borders for a "joined" look 
        # (optional: if you want a gap, add 'margin-right: 2px;')
        btn_style = """
            QPushButton {
                background-color: black; 
                color: white; 
                border: 1px solid white;
                font-weight: bold; 
                font-family: Consolas, monospace;
            }
            QPushButton:pressed {
                background-color: #444;
            }
        """
        # All buttons same size: 100x35
        self.btn_w = 70
        self.btn_h = 35

        self.nubutton = QPushButton("North Up", self)       # toggle north up button
        self.nubutton.setFixedSize(self.btn_w, self.btn_h)
        self.nubutton.setStyleSheet(btn_style)
        self.nubutton.clicked.connect(self.toggle_north_up)

        self.plusbutton = QPushButton("Zoom +", self)       # zoom in button
        self.plusbutton.setFixedSize(self.btn_w, self.btn_h)
        self.plusbutton.setStyleSheet(btn_style)
        self.plusbutton.clicked.connect(self.zoom_in)

        self.minusbutton = QPushButton("Zoom -", self)      # zoom out button
        self.minusbutton.setFixedSize(self.btn_w, self.btn_h)
        self.minusbutton.setStyleSheet(btn_style)
        self.minusbutton.clicked.connect(self.zoom_out)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        
        # Bottom Left configuration
        margin = 0
        bottom_y = self.height() - self.btn_h - margin
        
        # Position buttons right next to each other (no extra padding)
        # Starting from the left margin
        self.nubutton.move(margin, bottom_y)
        self.plusbutton.move(margin + self.btn_w, bottom_y)
        self.minusbutton.move(margin + (self.btn_w * 2), bottom_y)

        # Ensure UI stays on top
        self.overlay.raise_()
        self.nubutton.raise_()
        self.plusbutton.raise_()
        self.minusbutton.raise_()
    

    def toggle_north_up(self):
        self.north_up = not self.north_up
        self.overlay.is_north_up = self.north_up
        self.nubutton.setText("North Up" if self.north_up else "Track Up")
        self.overlay.update()

    def zoom_in(self): 
        self.current_zoom = min(20, self.current_zoom + 0.5)
        self.overlay.update()

    def zoom_out(self): 
        self.current_zoom = max(1, self.current_zoom - 0.5)
        self.overlay.update()

    def set_state(self, lat, lon, hdg):
        # NaN protection
        if any(math.isnan(x) for x in [lat, lon, hdg]):
            return 

        self.overlay.heading = hdg
        self.overlay.zoom = self.current_zoom
        self.overlay.lat = lat
        
        map_hdg = 0 if self.north_up else hdg
        self.overlay.map_bearing = map_hdg
        
        # Use standard values to ensure JS doesn't break
        js_code = f"if(window.updateMap) {{ window.updateMap({lat}, {lon}, {map_hdg}, {self.current_zoom}); }}"
        self.view.page().runJavaScript(js_code)
        self.overlay.update()

if __name__ == "__main__": # starts the window or something I dont understand
    server = start_server()
    threading.Thread(target=server.serve_forever, daemon=True).start()

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.resize(1024, 768)
    
    map_widget = Map()
    window.setCentralWidget(map_widget)
    window.show()
    
    # Test simulation
    test_hdg = 0
    def sim_update():
        global test_hdg
        test_hdg = (test_hdg + 1) % 360
        map_widget.set_state(center_lat, center_lon, test_hdg)
    
    timer = QTimer()
    timer.timeout.connect(sim_update)
    timer.start(50) 
    
    try:
        sys.exit(app.exec())
    finally:
        server.shutdown()