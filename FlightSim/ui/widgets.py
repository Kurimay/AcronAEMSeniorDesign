from __future__ import annotations
import math, time
from collections import deque
from turtle import heading

# PyQt6 core + GUI classes
from PyQt6.QtCore import Qt, QPointF, QRectF, QPoint, QLine, QLineF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF, QShortcut, QKeySequence, QBrush
import math
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox


# All the widgets used are built here (except the map and synthetic vision)


def format_val(val):    # this function is to fix Nan errors related to controller input, 
                        # it was a last minute fix before the showcase, i dont know if its necessary still

    #Returns an integer string or '--' if value is NaN.
    try:
        if math.isnan(val):
            return "--"
        return str(int(val))
    except (ValueError, TypeError):
        return "--"

class AttitudeBackground(QWidget):   # AttitudeBackground, AttitudeOverlay, and Attitude indicator used to be all one widget, 
                                     # But they were separated to make the synthetic vision work (even though its a little bit useless right now)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.roll = 0.0
        self.pitch = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_state(self, roll, pitch):
        self.roll, self.pitch = roll, pitch
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        
        p.translate(cx, cy)
        p.rotate(-self.roll)
        
        pitch_px_per_deg = h / 80
        y = self.pitch * pitch_px_per_deg
        
        # Draw Sky and Ground
        p.fillRect(QRectF(-w*2, -h*2 + y, w*4, h*2), QColor(118, 161, 207)) 
        p.fillRect(QRectF(-w*2, y, w*4, h*2), QColor(153, 90, 42))
        
        # Horizon Line
        p.setPen(QPen(Qt.GlobalColor.white, 3))
        p.drawLine(QPointF(-w*2, y), QPointF(w*2, y))

class AttitudeOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.roll = 0.0
        self.pitch = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_state(self, roll, pitch):
        self.roll, self.pitch = roll, pitch
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        pitch_px_per_deg = h / 80.0
        radius = h / 2

        # ROTATING ELEMENTS (Pitch Ladder & Roll Triangle)
        p.save()
        p.translate(cx, cy)
        p.rotate(-self.roll)
        y_offset = self.pitch * pitch_px_per_deg
        
        # Rolling Triangle (Top of the rotating ball)
        p.setBrush(QBrush(Qt.GlobalColor.white))
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        # Positioned relative to the arc
        movingtris = (QPointF(0, -radius * 0.8), 
                      QPointF(8, -radius * 0.8 + 20), 
                      QPointF(-8, -radius * 0.8 + 20))
        p.drawPolygon(QPolygonF(movingtris))

        # Pitch Ladder
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.setFont(QFont("Consolas", 14))
        for deg in range(-20, 21, 10):  # from -20 to 20 degrees
            yy = y_offset - deg * pitch_px_per_deg
            # Main degree line
            p.drawLine(QPointF(-70, yy), QPointF(70, yy))

            # 5-degree intermediate dashes
            if deg < 20:
                p.drawLine(QPointF(-35, yy - (pitch_px_per_deg * 5)), 
                           QPointF(35, yy - (pitch_px_per_deg * 5)))
            
            # Draw numbers on right and left of all lines except horizon line
            if deg != 0:
                p.drawText(QRectF(-105, yy - 12, 30, 20), Qt.AlignmentFlag.AlignRight, f"{abs(deg)}")
                p.drawText(QRectF(75, yy - 12, 30, 20), Qt.AlignmentFlag.AlignLeft, f"{abs(deg)}")
        p.restore()

    # FIXED ELEMENTS (Roll Scale & Aircraft Symbol)  
        # Roll Indicator arc and dashes
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        for ang in range(-45, 46, 15):
            a = math.radians(ang)
            # Lines pointing inward from the edge
            x1 = cx + math.sin(a) * radius * 0.8
            y1 = cy - math.cos(a) * radius * 0.8
            x2 = cx + math.sin(a) * radius * 0.85
            y2 = cy - math.cos(a) * radius * 0.85
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Static Top Triangle (0-degree roll reference)
        p.setBrush(QBrush(Qt.GlobalColor.white))
        static_tris = (QPointF(cx, cy - radius * 0.8), 
                       QPointF(cx + 8, cy - radius * 0.8 - 20), 
                       QPointF(cx - 8, cy - radius * 0.8 - 20))
        p.drawPolygon(QPolygonF(static_tris))

        # Connecting arc for roll scale
        p.setBrush(Qt.BrushStyle.NoBrush)
        arcrect = QRectF(cx - radius*0.8, cy - radius*0.8, radius*0.8 * 2, radius*0.8 * 2)
        p.drawArc(arcrect, 45 * 16, 90 * 16)

    # Yellow shape
        yellow_pen = QPen(QColor(241, 194, 50), 7)
        p.setPen(yellow_pen)
        p.setBrush(QColor(241, 194, 50))
        
        # Horizontal "Wings"
        p.drawLine(QPointF(cx - 190, cy), QPointF(cx - 100, cy))
        p.drawLine(QPointF(cx + 190, cy), QPointF(cx + 100, cy))
        
        # Center Reference Polygon
        thickness = 7
        points = [
            QPoint(int(cx), int(cy + thickness/2)), 
            QPoint(int(cx - 60), int(cy + 30)), 
            QPoint(int(cx), int(cy + 10)), 
            QPoint(int(cx + 60), int(cy + 30))
        ]
        p.drawPolygon(QPolygonF([QPointF(pt) for pt in points]))

class AttitudeIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg = AttitudeBackground(self)
        self.overlay = AttitudeOverlay(self)

    def resizeEvent(self, event):
        self.bg.setGeometry(0, 0, self.width(), self.height())
        self.overlay.setGeometry(0, 0, self.width(), self.height())

    def set_state(self, roll, pitch):
        self.bg.set_state(roll, pitch)
        self.overlay.set_state(roll, pitch)

# ==================== GENERIC TAPE (SPEED / ALTITUDE) ====================
class TapeWidget(QWidget):
    def __init__(self, label: str, fmt: str, color=QColor(255, 255, 255), parent=None):
        super().__init__(parent)

        # --- Display configuration ---
        self.label = label      # Display label ("TAS", "ALT", etc.)
        self.value = 0.0        # Current numeric value (e.g., knots, feet)
        self.fmt = fmt          # Format string for numeric display (e.g. "{:.0f}") ?????
        self.color = color      # Accent color for tick marks and text

        # Minimum visible size (prevents layout from collapsing)
        self.setMinimumSize(70, 280)

    def set_value(self, v: float):
        self.value = float(v)
        self.update()  # Triggers paintEvent()

    # Paint routine (responsible for all drawing)
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)  # Smooth edges

        R = self.rect()
        clipping_box = QRectF(R.left(), R.top()+5, R.width(), R.height()-11)
         # Apply clipping region so numbers arent drawn outside of box
        p.setClipRect(clipping_box)

        # Inset drawing area (6 px padding on each side)
        R = self.rect().adjusted(6, 6, -6, -6)

        # Draw a dark gray background with a thin white border
        p.fillRect(R, QColor(0, 0, 0, 100))               # background fill
        p.setPen(QPen(Qt.GlobalColor.white, 1))         # border outline
        p.drawRect(R)

        cy = R.center().y()                             # vertical center (origin for tick offsets)

        # --- Style for tick marks and text ---
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.setFont(QFont("Consolas", 13))

        # --- Tick marks and labels ---
        if self.label =="TAS":                          # Speed tape
            ticks = range(0, 201, 10)
            scale = 4
        else:                                           # Altitude tape
            ticks = range(0 , 5000, 100)                # this is the maximum and minimum numbers displayed, so 
            scale = 0.4                                 # right now, altitude wont show above 5000
            
        # Draw ticks every x units in a range
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        for tickvalue in ticks:
            y = cy + (self.value - tickvalue) * scale - 2           # vertical position per tick
            if self.label == "TAS":                                 # Speed tape
                p.drawLine(QPointF(R.right() - 2, y), QPointF(R.right() - 18, y))  # tick line
                p.drawText(
                    QRectF(R.right() - 55, y - 8, 35, 16),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    f"{abs(tickvalue)}"                             # number label
                )
            else:                                                    # Altitude tape
                p.drawLine(QPointF(R.left() + 2, y), QPointF(R.left() + 18, y))  # tick line
                p.drawText(
                    QRectF(R.left() + 20, y - 8, 45, 16),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    f"{abs(tickvalue)}"                             # number label
                )

        # Important number box (polygon with exact number for altitude/airspeed)
        p.setBrush(Qt.GlobalColor.black)

        if self.label == "TAS":  # Pointing right
            importantnumberpoints = [QPointF(R.right() - 6, cy), QPointF(R.right() - 12, cy + 6), QPointF(R.right() - 12, cy + 14), QPointF(R.left(), cy + 14), QPointF(R.left(), cy - 14), QPointF(R.right() - 12, cy - 14), QPointF(QPointF(R.right() - 12, cy - 6))]
        else:                    # Pointing left
            importantnumberpoints = [QPointF(R.left() + 6, cy), QPointF(R.left() + 12, cy + 6), QPointF(R.left() + 12, cy + 14), QPointF(R.right(), cy + 14), QPointF(R.right(), cy - 14), QPointF(R.left() + 12, cy - 14), QPointF(QPointF(R.left() + 12, cy - 6))]

        # Draw and fill the polygon
        tapepoly = QPolygonF(importantnumberpoints)
        p.drawPolygon(tapepoly)

        text_rect = tapepoly.boundingRect()
        p.setPen(Qt.GlobalColor.white)
        p.setFont(QFont("Consolas", 15, QFont.Weight.Bold))

        if math.isnan(self.value): # nan protection (not sure if still needed)
            display_value = 0
        else:
            display_value = int(self.value)

        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, f"{display_value}")    # exact value of altitude/airspeed

    # Bottom Box (label TAS or ALT)
        # Subtract 20 from the bottom so it sits inside the frame
        box_y = R.bottom() - 20 

        # Draw the Box
        p.setBrush(QColor("black"))
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        p.drawRect(R.left(), box_y, R.width(), 20)

        # Draw the Text centered in that new box
        p.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        label_text = "TAS" if self.label == "TAS" else "ALT"

        p.drawText(R.left(), box_y, R.width(), 20, 
                Qt.AlignmentFlag.AlignCenter, label_text)


# ====================== VERTICAL RATE =========================

class RateWidget(QWidget):   # a little broken when its maxed out, maybe change the size in main_window.py to fix the clipping
    def __init__(self, parent = None):
        super().__init__(parent)
        self.value = 0.0

    def set_value(self, v: float):
        self.value = float(v) * 60
        self.update()  # Triggers paintEvent()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        R = self.rect()#.adjusted(8, 8, -8, -8)

        # Transparent background
        p.setBrush(QColor(0, 0, 0, 100))   # translucent gray

        # Limit of vertical speed
        limit = 2500

        # p.drawRect(R)
        cx = R.center().x()
        cy = R.center().y()
        rightoffset = 20

        # Box outline
        ratepoints = [QPointF(R.left(), R.top()),QPointF(R.right() - rightoffset, R.top()),QPointF(R.right() - rightoffset, cy - (30-rightoffset)),QPointF(R.left(), cy),QPointF(R.right() - rightoffset, cy + (30-rightoffset)),QPointF(R.right() - rightoffset, R.bottom()),QPointF(R.left(), R.bottom()),]
        ratepoly = QPolygonF(ratepoints)
        p.drawPolygon(ratepoly)

        # Ticks and tick numbers
        for percent in range(0, 100, 10):
            if percent == 50:
                continue  # don't draw middle tick
            y = int(percent/100 * R.height())
            p.drawLine(R.left(), y, R.left() + 5, y)

        ticks = [10, 30, 70, 90]
            # mapping from tick to label
        labels = {10: "2", 30: "1", 70: "1", 90: "2",}  # 1000 ft/m, 2000ft/m

        # draw 2, 1, 1, 2 at correct locations
        p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        for percent in ticks:
            y = percent / 100 * R.height()
            p.drawText(
                QRectF(R.right() - 29, y - 7, 18, 14),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                labels[percent]
            )
                

        # Pointer
        heightoffset = -self.value * R.height() / 2 / limit
        p.setBrush(Qt.GlobalColor.black)
        ratepointerpoints = [QPointF(cx + 19, cy - (30-rightoffset) + heightoffset), QPointF(R.right() - rightoffset, cy - (30-rightoffset) + heightoffset),QPointF(R.left(), cy + heightoffset),QPointF(R.right() - rightoffset, cy + (30-rightoffset) + heightoffset), QPointF(cx + 19, cy + (30-rightoffset) + heightoffset)]
        ratepointer = QPolygonF(ratepointerpoints)
        p.drawPolygon(ratepointer)

        # Exact vertical rate in pointer
        text_rect = ratepointer.boundingRect().translated(-2,3)
        p.setPen(Qt.GlobalColor.white)
        p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))

        if math.isnan(self.value): # Nan Prtecion
            heightoffset = 0
        else:
            heightoffset = -self.value * R.height() / 2 / limit

        display_text = format_val(self.value)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignRight, display_text)

# ==================== COMPASS ====================
class CompassWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.heading = 0.0
        self.setMinimumSize(230, 230)

    def set_heading(self, deg: float):
        self.heading = float(deg) % 360.0
        self.update()

    def paintEvent(self, e):
        # Draw compass circle and labels
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        R = self.rect().adjusted(8, 8, -8, -8)
        cx, cy = R.center().x(), R.center().y()
        r = min(R.width(), R.height()) * 0.42

        # Transparent background + circle
        p.setBrush(QColor(0, 0, 0, 100))   # translucent gray
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Heading ticks
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        radius = r
        for ang in range(0, 360, 30):
            a = math.radians(ang - self.heading)
            x1 = cx + math.sin(a) * radius * 0.93
            y1 = cy - math.cos(a) * radius * 0.93
            x2 = cx + math.sin(a) * radius
            y2 = cy - math.cos(a) * radius 
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        p.setBrush(Qt.GlobalColor.white)
        p.setPen(QPen(Qt.GlobalColor.white, 1))        

        # Draw N, E, S, W
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        for i, direction in enumerate(["N","E","S","W"]):
            ang = math.radians(i*90.0 - self.heading)
            x = cx + math.sin(ang) * (r - 14)
            y = cy - math.cos(ang) * (r - 14)
            p.drawText(QRectF(x-10, y-10, 20, 20),
                       Qt.AlignmentFlag.AlignCenter, direction)

    # Numeric heading display
        p.setFont(QFont("Consolas", 12))

        # Box rectangle
        box_rect = QRectF(cx - 20, R.top() - 5, 40, 20)

        # Semi-transparent fill (black with alpha)
        p.setBrush(QColor(0, 0, 0))   
        p.setPen(QPen(QColor(255, 255, 255, 220), 1.5))  # white border

        # Draw the transparent box
        p.drawRect(box_rect)

        # Draw heading text centered inside
        p.setPen(QColor(255, 255, 255))  # solid white text

        if math.isnan(self.heading): # nan protection
            display_heading = 0
        else:
            display_heading = int(round(self.heading))

        p.drawText(
            box_rect,
            Qt.AlignmentFlag.AlignCenter,
            f"{display_heading}"
        )


class VMap(QWidget): # This is unused and broken right now, supposed to be a vertial situation indicator
    def __init__(self):
        super().__init__()
        self.setMinimumSize(360, 160)

        self.pitch = 0.0          # degrees
        self.altitude = 0.0       # meters
        self.scale = 10          # meters per pixel? also altitude isnt in meters

    def set_state(self, pitch: float, altitude: float):
        self.pitch = float(pitch)
        self.altitude = float(altitude)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        R = self.rect()
        cx, cy = R.center().x(), R.center().y()

        # Background
        p.fillRect(R, QColor(20, 20, 20))
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.drawRect(R)

        # Vertical offset from altitude
        y_offset = -self.altitude / self.scale

        # Draw airplane
        p.save()
        p.translate(cx, cy + y_offset)
        p.rotate(-self.pitch)

        plane = QPolygonF([
            QPointF(0, 0),
            QPointF(0, -12),
            QPointF(22, 0)
        ])

        p.setBrush(QColor(0, 0, 0))
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.drawPolygon(plane)

        p.restore()

        # Grid logic
        grid_spacing_px = 500 / self.scale # pixels per box
        # # x_offset = (self.x / self.scale) % grid_spacing_px
        # y_offset = (self.altitude / self.scale) % grid_spacing_px

        pen = QPen(QColor(80, 80, 80), 1, Qt.PenStyle.DashLine)
        p.setPen(pen)

        # Draw a grid
        grid_range = int(R.width())
        lines = []
        # for x in range(-grid_range, grid_range, int(grid_spacing_px)):
        #     lines.append(QLineF(x - x_offset, -grid_range, x - x_offset, grid_range))
        for y in range(-grid_range, grid_range, int(grid_spacing_px)):
            lines.append(QLineF(-grid_range, y, grid_range, y))
        
        p.drawLines(lines)


class SemicircleIndicator(QWidget):     # Used for RPM
    def __init__(
        self,
        parent=None,
        value= 0,
        label="PROP1",
        unit="RPM",
        valuerange = (0, 1250), # Actual numbers
        greenrange = (9, 98), # Percent its reversed though sorry
        yellowrange = (5, 10), # percent its reversed though sorry
        redrange = (2,5) # percent its reversed though sorry
    ):
        super().__init__(parent)

        self.value = value
        self.valuepercent = (value - valuerange[0]) / (valuerange[1] - valuerange[0])
        self.label = label
        self.unit = unit
        self.valuerange = valuerange
        self.greenrange = greenrange
        self.yellowrange = yellowrange
        self.redrange = redrange

    def set_value(self, v: float):
        self.value = float(v)

        # clamp to range
        vmin, vmax = self.valuerange
        self.value = max(vmin, min(self.value, vmax))

        # recompute percent
        self.valuepercent = (self.value - vmin) / (vmax - vmin)

        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # bounding box
        R = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        #p.drawRect(R) # draw outline

        percentSize = 0.9

        # new R is Smaller bounding box
        R = QRectF(int((1-percentSize) * R.height() / 2), int((1-percentSize) * R.height() / 2), int(R.height() * 0.9), int(R.height() * 0.9))
        W = R.width()
        H = R.height()
        #p.drawRect(R) # draw outline

        # white arc
        pen = QPen(QColor(255, 255, 255), 2)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        start_deg = 15
        span_deg = 180 #180 - start_deg
        p.drawArc(R, int((start_deg)* 16 - 10), int(span_deg * 16) + 20)      

        cx, cy = R.center().x(), R.center().y()
        radius = int(R.width() / 2)
        offset = 0

        # green ring
        pen = QPen(QColor(115, 200, 70), 6)
        p.setPen(pen)

        gstartdeg = (span_deg * self.greenrange[0] / 100) + start_deg
        gspandeg = (span_deg * (self.greenrange[1] - self.greenrange[0]) / 100)
        p.drawArc(R.adjusted(5,5,-5,-5), int((gstartdeg)* 16 - 10), int(gspandeg * 16) + 20)

        # yellow ring
        pen = QPen(QColor(255, 255, 0), 6)
        p.setPen(pen)

        ystartdeg = (span_deg * self.yellowrange[0] / 100) + start_deg
        yspandeg = (span_deg * (self.yellowrange[1] - self.yellowrange[0]) / 100)

        p.drawArc(R.adjusted(5,5,-5,-5), int((ystartdeg)* 16 - 10), int(yspandeg * 16) + 20)

        # red ring
        pen = QPen(QColor(255, 0, 0), 6)
        p.setPen(pen)

        rstartdeg = (span_deg * self.redrange[0] / 100) + start_deg
        rspandeg = (span_deg * (self.redrange[1] - self.redrange[0]) / 100)

        p.drawArc(R.adjusted(5,5,-5,-5), int((rstartdeg)* 16 - 10), int(rspandeg * 16) + 20)


        # ticks
        tickmultiplier = 1   # 0 = 2 ticks, 1 = 5 ticks, 2 = 9 ticks, 3 = 17 ticks, 4 = 33 ticks, 
        ticknum = pow(2,tickmultiplier+1)+1

        pen = QPen(QColor(255, 255, 255), 2)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        step = span_deg / (ticknum - 1)

        # draw ticks
        for i in range(ticknum):
            ang = start_deg + i * step
            a = math.radians(ang)
            x1 = cx + math.cos(a) * radius * 1
            y1 = cy - math.sin(a) * radius * 1 + offset
            x2 = cx + math.cos(a) * radius * 0.85
            y2 = cy - math.sin(a) * radius * 0.85 + offset
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    # pointer
        p.setBrush(Qt.GlobalColor.white)
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        pt1 = QPointF(cx, cy - radius)
        pt2 = QPointF(cx + 6, cy -  radius + 15)
        pt3 = QPointF(cx - 6, cy -  radius + 15)
        #self.valuepercent
        
        if math.isnan(self.valuepercent): # nan Protection
            angle = start_deg - 90 
        else:
            angle = (span_deg * self.valuepercent) + start_deg - 90 - start_deg * 2

        theta = math.radians(angle)

        def rotate_point(x, y, cx, cy, theta): # rotate points (x,y) of pointer around center (cx,cy) given angle theta
            dx = x - cx
            dy = y - cy
            xr = cx + dx * math.cos(theta) - dy * math.sin(theta)
            yr = cy + dx * math.sin(theta) + dy * math.cos(theta)
            return QPointF(xr, yr)

        pt1adjusted = rotate_point(pt1.x(), pt1.y(), cx, cy, theta)
        pt2adjusted = rotate_point(pt2.x(), pt2.y(), cx, cy, theta)
        pt3adjusted = rotate_point(pt3.x(), pt3.y(), cx, cy, theta)

        # draw rotated pointer
        tris = (pt1adjusted, pt2adjusted, pt3adjusted)
        p.drawPolygon(tris)


    # number
        textbox = QRectF(R.width() * 0.85, int(R.height()/2)+5, float(R.width()*0.3), float(R.height()*0.15))
        if (self.value > (100 - self.redrange[1]-3)/100 * self.valuerange[1]): # if in red range, make text box red
            p.setPen(Qt.PenStyle.NoPen)                     
            p.setBrush(QColor(255, 0, 0)) # red             
            p.drawRect(textbox)
            p.setPen(QPen(QColor(255, 255, 255))) # white      
        else:
            p.setPen(QPen(QColor(115, 200, 70))) # green         

        p.setFont(QFont("Consolas", 12))
        p.drawText(textbox, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, format_val(self.value))

        # label (PROP # in this case)  
        p.setPen(QPen(Qt.GlobalColor.white))
        p.setFont(QFont("Consolas", 12))

        p.drawText(QRectF(5, int(R.height()*0.35), float(R.width()), float(R.height()*0.2)),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self.label)
                
        # unit (RPM in this case)
        p.setPen(QPen(Qt.GlobalColor.white))
        p.setFont(QFont("Consolas", 12))

        p.drawText(QRectF(5, int(R.height()*0.5), float(R.width()), float(R.height()*0.2)),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self.unit)


class VerticalIndicator(QWidget): # Used for Power / Batter indicators
    def __init__(
        self,
        parent=None,
        value= 0,
        label="POWER",
        unit="KW",
        valuerange = (0, 2200), # Actual numbers
        greenrange = (2, 89), # Percent
        yellowrange = (90, 98), # Percent
        redrange = (179,180) # Percent  (I have crazy high number here just because I want no red range for power.)
    ):
        super().__init__(parent)

        self.value = value
        self.valuepercent = (value - valuerange[0]) / (valuerange[1] - valuerange[0])
        self.label = label
        self.unit = unit
        self.valuerange = valuerange
        self.greenrange = greenrange
        self.yellowrange = yellowrange
        self.redrange = redrange

    def set_value(self, v: float):
        self.value = float(v)

        # clamp to range
        vmin, vmax = self.valuerange
        self.value = max(vmin, min(self.value, vmax))

        # recompute percent
        self.valuepercent = (self.value - vmin) / (vmax - vmin)

        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # bounding box
        R = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        # p.drawRect(R) # show outline

        percentSize = 0.7

        dx = R.width() * (1 - percentSize) / 2
        dy = R.height() * (1 - percentSize) / 2

        # adjusted bounding box
        R = QRectF(
            R.x() + dx,
            R.y() + dy,
            R.width() * percentSize,
            R.height() * percentSize
        )

        right = R.x() + R.width()
        bottom = R.y() + R.height()
        left = R.x()
        top = R.y()

        # red line      draw first because otherwise the red text box doesnt align with the red line
        pen = QPen(QColor(255, 0, 0), 6)
        p.setPen(pen)

        p.drawLine(QLine(int(right-5), int(bottom - R.height() * self.redrange[0] / 100), int(right-5), int(bottom - R.height() * self.redrange[1] / 100)))

        # green line
        pen = QPen(QColor(115, 200, 70), 6)
        p.setPen(pen)

        p.drawLine(QLine(int(right-5), int(bottom - R.height() * self.greenrange[0] / 100), int(right-5), int(bottom - R.height() * self.greenrange[1] / 100)))

        # yellow line
        pen = QPen(QColor(255, 255, 0), 6)
        p.setPen(pen)
        p.drawLine(QLine(int(right-5), int(bottom - R.height() * self.yellowrange[0] / 100), int(right-5), int(bottom - R.height() * self.yellowrange[1] / 100)))

        # white outline
        pen = QPen(QColor(255, 255, 255), 3)
        pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        p.setPen(pen)

        outlinewidth = 40

        # thick white line outlines
        lines = [
            QLine(int(right - outlinewidth), int(top),
                int(right), int(top)),

            QLine(int(right), int(top),
                int(right), int(bottom)),

            QLine(int(right), int(bottom),
                int(right - outlinewidth), int(bottom))
        ]

        p.drawLines(lines)


    # pointer
        p.setBrush(Qt.GlobalColor.white)
        p.setPen(QPen(Qt.GlobalColor.white, 1))


        if math.isnan(self.valuepercent): # NAN protection
            pointer_y = bottom
        else:
            pointer_y = bottom - (R.height() * self.valuepercent) # convert percent into Y position

        # pointer size
        pointer_width = 15
        pointer_height = 12

        # position it slightly right of the bar
        px = right - 5

        pt1 = QPointF(px, pointer_y)  # tip
        pt2 = QPointF(px - pointer_width, pointer_y - pointer_height / 2)
        pt3 = QPointF(px - pointer_width, pointer_y + pointer_height / 2)

        tris = (pt1, pt2, pt3)
        p.drawPolygon(tris)

    # number
        textbox = QRectF(R.width() * 0.5, R.height() + 35, float(R.width() * 0.75), float(R.height()*0.12)) # below indicator

        if (self.redrange[0] <= self.valuepercent * 100 <= self.redrange[1]): # draw red if in red range, else green.
            p.setPen(Qt.PenStyle.NoPen)                     
            p.setBrush(QColor(255, 0, 0)) # red background             
            p.drawRect(textbox)
            p.setPen(QPen(QColor(255, 255, 255))) # white text    
        else:
            p.setPen(QPen(QColor(115, 200, 70))) # green       
        p.setFont(QFont("Consolas", 12))
        p.drawText(textbox, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, format_val(self.value))        
        
    # label (example: Power) positioned above indicator
        p.setPen(QPen(Qt.GlobalColor.white))
        p.setFont(QFont("Consolas", 10))

        p.drawText(QRectF(0, -7, float(R.width() + 20), float(R.height()*0.2)),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self.label)
                
    # unit (example: KW) positioned above indicator
        p.setPen(QPen(Qt.GlobalColor.white))
        p.setFont(QFont("Consolas", 8))

        p.drawText(QRectF(int(R.width() / 4), 5, float(R.width()), float(R.height()*0.2)),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self.unit)

class BasicText(QWidget):  # Used for range and endurance, its just text with a number next to it
    def __init__(
        self,
        parent=None,
        value= 0,
        label="RANGE NM",
        unit="NM",
    ):
        super().__init__(parent)

        self.value = value
        self.label = label
        self.unit = unit

    def set_value(self, v: float):
        self.value = float(v)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        R = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        p.drawRect(R)

        # Value on right
        textbox = QRectF(int(R.width() * 3/4), 0, int(R.width() * 1/4), int(R.height()))
        p.setPen(QPen(QColor(255, 255, 255)))           
        p.setPen(QPen(QColor(115, 200, 70)))            
        p.setFont(QFont("Consolas", 12))
        p.drawText(textbox, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, format_val(self.value))

        # Label on left
        p.setPen(QPen(Qt.GlobalColor.white))
        p.setFont(QFont("Consolas", 12))

        labelbox = QRectF(0, 0, int(R.width() * 3/4), int(R.height()))

        p.drawText(labelbox,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self.label) 


class PreflightChecklist(QWidget):  # its quite ugly and dumb right now, and covers range and endurance, so it could be changed a lot
    def __init__(self):
        super().__init__()


        layout = QVBoxLayout()
        self.setLayout(layout)

        items = [
            "Flux capacitor stable",
            "Door closed",
            "Battery charged",
            "Seatbelt fastened",
            "Check weather",
        ]

        self.checkboxes = []

        for text in items:
            cb = QCheckBox(text)
            cb.stateChanged.connect(self.check_all)
            layout.addWidget(cb)
            self.checkboxes.append(cb)

    # hide item if its checked 
    def check_all(self):   
        if all(cb.isChecked() for cb in self.checkboxes):
            self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        R = self.rect()
        p.fillRect(R, QColor(0, 0, 0))
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.drawRect(R)

