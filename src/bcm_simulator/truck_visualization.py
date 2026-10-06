"""Animated side-view truck instrument visualization."""

from __future__ import annotations

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from bcm_simulator.simulation import VehicleState


class TruckVisualization(QWidget):
    """Render vehicle state as a smoothly animated truck side profile."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.lamp_level = 0
        self.wiper_mode = "OFF"
        self.wiper_active = False
        self.motor_running = False
        self.door_open = False
        self.left_indicator = False
        self.right_indicator = False
        self.animation_enabled = True
        self.animation_speed = 1.0
        self._door_progress = 0.0
        self._last_frame = time.monotonic()
        self.setMinimumSize(560, 330)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def set_vehicle_state(self, state: VehicleState) -> None:
        self.lamp_level = state.interior_light_level
        self.wiper_mode = state.wiper_mode
        self.wiper_active = state.wiper_active
        self.motor_running = state.motor_running
        self.door_open = state.door_open
        self.left_indicator = state.left_indicator
        self.right_indicator = state.right_indicator
        self.update()

    def set_states(
        self,
        *,
        lamp_level: int,
        wiper_mode: str,
        wiper_active: bool,
        motor_running: bool,
        door_open: bool = False,
        left_indicator: bool = False,
        right_indicator: bool = False,
    ) -> None:
        """Keep the original widget API for existing consumers."""
        self.lamp_level = max(0, min(100, lamp_level))
        self.wiper_mode = wiper_mode
        self.wiper_active = wiper_active
        self.motor_running = motor_running
        self.door_open = door_open
        self.left_indicator = left_indicator
        self.right_indicator = right_indicator
        self.update()

    def set_animation(self, *, enabled: bool, speed: float | None = None) -> None:
        self.animation_enabled = enabled
        if speed is not None:
            self.animation_speed = max(0.25, min(2.0, speed))
        if not enabled:
            self._door_progress = 1.0 if self.door_open else 0.0
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale = min(self.width() / 1000, self.height() / 500)
        painter.translate((self.width() - 1000 * scale) / 2, (self.height() - 500 * scale) / 2)
        painter.scale(scale, scale)
        self._paint_background(painter)
        self._advance_door()
        self._paint_header(painter)
        self._paint_road(painter)
        self._paint_truck(painter)
        self._paint_footer(painter)

    def _advance_door(self) -> None:
        now = time.monotonic()
        elapsed = min(now - self._last_frame, 0.05)
        self._last_frame = now
        target = 1.0 if self.door_open else 0.0
        step = elapsed * 2.8 * self.animation_speed
        if self.animation_enabled:
            self._door_progress = (
                min(target, self._door_progress + step)
                if target
                else max(target, self._door_progress - step)
            )
        else:
            self._door_progress = target

    def _paint_background(self, painter: QPainter) -> None:
        gradient = QLinearGradient(0, 0, 0, 500)
        gradient.setColorAt(0, QColor("#18282b"))
        gradient.setColorAt(0.62, QColor("#24383a"))
        gradient.setColorAt(1, QColor("#10191b"))
        painter.fillRect(QRectF(0, 0, 1000, 500), gradient)
        painter.setPen(QPen(QColor(130, 166, 158, 17), 1))
        for x in range(24, 1000, 36):
            painter.drawLine(x, 0, x, 500)
        for y in range(18, 500, 36):
            painter.drawLine(0, y, 1000, y)

    def _paint_header(self, painter: QPainter) -> None:
        painter.setPen(QColor("#dce7e2"))
        painter.drawText(
            QRectF(36, 24, 500, 30), Qt.AlignmentFlag.AlignLeft, "VEHICLE BAY 01  /  BCM"
        )
        painter.setPen(QColor("#91a9a2"))
        painter.drawText(
            QRectF(36, 56, 500, 22), Qt.AlignmentFlag.AlignLeft, "HEAVY DUTY  |  SIDE ELEVATION"
        )
        running = self.motor_running
        self._status_lamp(painter, 934, 38, running, "RUNNING" if running else "STANDBY")

    def _paint_road(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#77908a"), 2))
        painter.drawLine(54, 408, 946, 408)
        painter.setPen(QPen(QColor(153, 177, 168, 55), 1, Qt.PenStyle.DashLine))
        painter.drawLine(54, 432, 946, 432)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 72))
        painter.drawEllipse(QRectF(110, 378, 760, 64))

    def _paint_truck(self, painter: QPainter) -> None:
        self._paint_trailer(painter)
        self._paint_chassis(painter)
        self._paint_cabin(painter)
        self._paint_wheels(painter)
        self._paint_lights(painter)
        self._paint_wiper(painter)
        self._paint_door(painter)

    def _paint_trailer(self, painter: QPainter) -> None:
        trailer = QPainterPath()
        trailer.moveTo(128, 143)
        trailer.lineTo(625, 143)
        trailer.lineTo(625, 350)
        trailer.lineTo(128, 350)
        trailer.closeSubpath()
        fill = QLinearGradient(128, 143, 128, 350)
        fill.setColorAt(0, QColor("#e1e5df"))
        fill.setColorAt(1, QColor("#abb8b1"))
        painter.setPen(QPen(QColor("#d2ddd6"), 3))
        painter.setBrush(fill)
        painter.drawPath(trailer)
        painter.setPen(QPen(QColor("#8b9d95"), 2))
        painter.drawLine(148, 169, 605, 169)
        painter.drawLine(148, 321, 605, 321)
        painter.setPen(QColor("#667971"))
        painter.drawText(
            QRectF(190, 210, 355, 48), Qt.AlignmentFlag.AlignCenter, "NORTHLINE  /  540"
        )
        painter.setPen(QPen(QColor("#7b8b84"), 2))
        for x in (170, 583):
            painter.drawLine(x, 175, x, 312)
        painter.setPen(QPen(QColor("#f3f5ee"), 4))
        painter.drawLine(148, 338, 606, 338)

    def _paint_chassis(self, painter: QPainter) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#52615e"))
        painter.drawRoundedRect(QRectF(112, 341, 714, 31), 7, 7)
        painter.setBrush(QColor("#93a39b"))
        painter.drawRoundedRect(QRectF(134, 369, 695, 13), 5, 5)
        painter.setPen(QPen(QColor("#334440"), 4))
        painter.drawLine(150, 357, 797, 357)

    def _paint_cabin(self, painter: QPainter) -> None:
        body = QPainterPath()
        body.moveTo(600, 350)
        body.lineTo(600, 194)
        body.quadTo(601, 164, 636, 151)
        body.lineTo(718, 125)
        body.quadTo(745, 116, 766, 143)
        body.lineTo(827, 226)
        body.lineTo(858, 246)
        body.lineTo(858, 350)
        body.closeSubpath()
        fill = QLinearGradient(610, 130, 852, 350)
        fill.setColorAt(0, QColor("#dce5df"))
        fill.setColorAt(0.5, QColor("#aabbb2"))
        fill.setColorAt(1, QColor("#748b83"))
        painter.setPen(QPen(QColor("#e0e8e2"), 3))
        painter.setBrush(fill)
        painter.drawPath(body)

        window = QPainterPath()
        window.moveTo(626, 190)
        window.lineTo(642, 159)
        window.lineTo(713, 137)
        window.quadTo(731, 133, 743, 150)
        window.lineTo(772, 195)
        window.closeSubpath()
        glass = QLinearGradient(645, 140, 740, 196)
        glass.setColorAt(0, QColor("#aec8c9"))
        glass.setColorAt(1, QColor("#547579"))
        painter.setPen(QPen(QColor("#58716f"), 3))
        painter.setBrush(glass)
        painter.drawPath(window)

        side_window = QPainterPath()
        side_window.moveTo(752, 152)
        side_window.lineTo(775, 152)
        side_window.lineTo(813, 207)
        side_window.lineTo(777, 207)
        side_window.closeSubpath()
        painter.setPen(QPen(QColor("#617975"), 3))
        painter.setBrush(QColor("#64858a"))
        painter.drawPath(side_window)

        if self.lamp_level:
            glow = QRadialGradient(QPointF(713, 226), 112)
            glow.setColorAt(0, QColor(255, 204, 99, min(125, 45 + self.lamp_level)))
            glow.setColorAt(1, QColor(255, 204, 99, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QRectF(620, 135, 190, 190))
        painter.setPen(QPen(QColor("#546761"), 2))
        painter.setBrush(QColor("#f0c56d" if self.lamp_level else "#596966"))
        painter.drawRoundedRect(QRectF(665, 218, 17, 7), 3, 3)
        painter.drawRoundedRect(QRectF(692, 218, 17, 7), 3, 3)
        painter.setPen(QPen(QColor("#576a64"), 2))
        painter.drawLine(608, 202, 608, 342)
        painter.drawLine(842, 246, 842, 342)
        painter.setPen(QPen(QColor("#4b5e59"), 4))
        painter.drawLine(601, 342, 852, 342)
        painter.setPen(QPen(QColor("#52635e"), 2))
        painter.drawLine(818, 226, 867, 230)
        painter.drawLine(816, 225, 808, 211)
        painter.setBrush(QColor("#455652"))
        painter.drawRoundedRect(QRectF(853, 229, 33, 14), 5, 5)

    def _paint_door(self, painter: QPainter) -> None:
        painter.save()
        painter.translate(604, 230)
        painter.rotate(-58 * self._door_progress)
        painter.setPen(QPen(QColor("#536963"), 3))
        door_gradient = QLinearGradient(0, 0, 0, 113)
        door_gradient.setColorAt(0, QColor("#c4d0c9"))
        door_gradient.setColorAt(1, QColor("#82978e"))
        painter.setBrush(door_gradient)
        painter.drawRoundedRect(QRectF(0, 0, 116, 112), 4, 4)
        painter.setPen(QPen(QColor("#475b55"), 2))
        painter.drawLine(12, 58, 102, 58)
        painter.setBrush(QColor("#52645e"))
        painter.drawRoundedRect(QRectF(87, 68, 15, 5), 2, 2)
        painter.restore()

    def _paint_wheels(self, painter: QPainter) -> None:
        angle = (
            (time.monotonic() * 210 * self.animation_speed) % 360
            if self.motor_running and self.animation_enabled
            else 0
        )
        for center_x in (306, 704, 816):
            center = QPointF(center_x, 365)
            painter.setPen(QPen(QColor("#111719"), 4))
            painter.setBrush(QColor("#222c2d"))
            painter.drawEllipse(QRectF(center_x - 49, 316, 98, 98))
            painter.save()
            painter.translate(center)
            painter.rotate(angle)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#78857e"))
            for _ in range(12):
                painter.drawRoundedRect(QRectF(-4, -46, 8, 9), 2, 2)
                painter.rotate(30)
            painter.restore()
            painter.setPen(QPen(QColor("#64716d"), 3))
            painter.setBrush(QColor("#9eaaa4"))
            painter.drawEllipse(QRectF(center_x - 30, 335, 60, 60))
            painter.setPen(QPen(QColor("#53625d"), 3))
            painter.setBrush(QColor("#d5dbd5"))
            painter.drawEllipse(QRectF(center_x - 9, 356, 18, 18))
            painter.save()
            painter.translate(center)
            painter.rotate(angle)
            painter.setPen(
                QPen(QColor("#596862"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            for _ in range(6):
                painter.drawLine(QPointF(0, -11), QPointF(0, -24))
                painter.rotate(60)
            painter.restore()

    def _paint_lights(self, painter: QPainter) -> None:
        blink_on = not self.animation_enabled or (int(time.monotonic() * 2.5) % 2 == 0)
        painter.setPen(QPen(QColor("#303e39"), 2))
        for x in (616, 849):
            active = blink_on and (
                (x == 616 and self.left_indicator) or (x == 849 and self.right_indicator)
            )
            painter.setBrush(QColor("#ffb33f" if active else "#6d654e"))
            painter.drawRoundedRect(QRectF(x, 281, 22, 12), 4, 4)
        painter.setBrush(QColor("#f4d27a"))
        painter.drawRoundedRect(QRectF(851, 254, 22, 14), 5, 5)
        painter.setBrush(QColor("#b5493f"))
        painter.drawRoundedRect(QRectF(115, 273, 12, 34), 3, 3)
        for x, active in ((116, self.left_indicator), (603, self.right_indicator)):
            painter.setBrush(QColor("#ffad38" if active and blink_on else "#826440"))
            painter.drawRoundedRect(QRectF(x, 278, 14, 15), 4, 4)

    def _paint_wiper(self, painter: QPainter) -> None:
        angle = (
            48 * math.sin(time.monotonic() * 5.8 * self.animation_speed)
            if self.wiper_active and self.animation_enabled
            else 0
        )
        for pivot_x, sweep in ((766, -28 + angle), (790, 25 - angle * 0.85)):
            painter.save()
            painter.translate(QPointF(pivot_x, 204))
            painter.rotate(sweep)
            painter.setPen(
                QPen(QColor("#1d3030"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            painter.drawLine(QPointF(0, 0), QPointF(0, -42))
            painter.setPen(
                QPen(QColor("#263c3c"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            painter.drawLine(QPointF(-8, -39), QPointF(8, -39))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#e1e9e2"))
            painter.drawEllipse(QPointF(0, 0), 4, 4)
            painter.restore()

    def _paint_footer(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#52706a"), 1))
        painter.drawLine(36, 455, 964, 455)
        signals = (
            ("DOOR", self.door_open),
            ("CABIN", self.lamp_level > 0),
            ("L IND", self.left_indicator),
            ("R IND", self.right_indicator),
            ("WIPER", self.wiper_active),
            ("MOTOR", self.motor_running),
        )
        x = 42
        for label, active in signals:
            self._status_lamp(painter, x + 5, 480, active, label)
            x += 153

    @staticmethod
    def _status_lamp(painter: QPainter, x: float, y: float, active: bool, label: str) -> None:
        color = QColor("#68d2a2") if active else QColor("#63736e")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(x, y), 5, 5)
        painter.setPen(QColor("#c8d5ce") if active else QColor("#91a29a"))
        painter.drawText(QRectF(x + 13, y - 12, 122, 24), Qt.AlignmentFlag.AlignVCenter, label)


LoadVisualization = TruckVisualization
