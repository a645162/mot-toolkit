import sys

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QPen, QBrush
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QPinchGesture, QSwipeGesture


class View(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.grabGesture(Qt.PinchGesture)
        self.grabGesture(Qt.SwipeGesture)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.scene.addRect(0, 0, 100, 100, QPen(Qt.NoPen), QBrush(Qt.green))

        self.setScene(self.scene)

    def event(self, event):
        if event.type() == QEvent.Gesture:
            self.gestureEvent(event)
            return True
        return super().event(event)

    def gestureEvent(self, event):
        pinch_gesture = event.gesture(Qt.PinchGesture)
        swipe_gesture = event.gesture(Qt.SwipeGesture)

        if pinch_gesture:
            print("Pinch gesture")
            self.pinchTriggered(pinch_gesture)

        if swipe_gesture:
            print("Swipe gesture")
            self.swipeTriggered(swipe_gesture)

        print()

    def pinchTriggered(self, gesture):
        if gesture.changeFlags() & QPinchGesture.ChangeFlag.ScaleFactorChanged:
            print(
                "Scale factor changed",
                gesture.scaleFactor(),
                gesture.totalScaleFactor(),
                gesture.lastScaleFactor()
            )

            factor_delta = gesture.totalScaleFactor() - gesture.scaleFactor()

            factor_delta = round(factor_delta, 6)
            print("factor_delta", factor_delta)
        if gesture.changeFlags() & QPinchGesture.ChangeFlag.RotationAngleChanged:
            print(
                "Rotation angle changed",
                gesture.rotationAngle(),
                gesture.totalRotationAngle(),
                gesture.lastRotationAngle()
            )
        if gesture.changeFlags() & QPinchGesture.ChangeFlag.CenterPointChanged:
            print(
                "Center point changed",
                gesture.center,
                gesture.lastCenterPoint()
            )

    def swipeTriggered(self, gesture):
        if gesture.verticalDirection() == QSwipeGesture.Direction.Up:
            print("Swipe up")
        elif gesture.verticalDirection() == QSwipeGesture.Direction.Down:
            print("Swipe down")
        if gesture.horizontalDirection() == QSwipeGesture.Direction.Left:
            print("Swipe left")
        elif gesture.horizontalDirection() == QSwipeGesture.Direction.Right:
            print("Swipe right")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    view = View()
    view.show()

    sys.exit(app.exec())
