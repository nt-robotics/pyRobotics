import sys

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.uic import loadUi


class MainWindow(QWidget):

    __GUI_PATH = "/home/user/Projects/pyCharm/pyRobotics/tests/pyQt5/gui.ui"

    def __init__(self):
        super().__init__()
        loadUi(self.__GUI_PATH, self)


class GuiTestController:

    def __init__(self, win):


        # window = MainWindow()

        # GuiTestController(window)

        win.pushButton.setEnabled(True)
        win.pushButton.clicked.connect(self.test_handler)





    def test_handler(self):
        print("TEST CLICK")


app = QApplication(sys.argv)

window = MainWindow()

window.show()
GuiTestController(window)
sys.exit(app.exec_())




