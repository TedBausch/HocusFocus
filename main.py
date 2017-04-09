__author__ = "Ted Bausch"

from PyQt5 import *
import sys
import os
import winsound
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QLCDNumber, QSlider, QVBoxLayout, QHBoxLayout, QApplication, QPushButton, QDesktopWidget, QPlainTextEdit, QDialog
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import pyqtSlot

print("Hello")

blockList = list()


class TimerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 400
        self.initUI()

    def initUI(self):
        # initialize LCD
        self.lcd = QLCDNumber(self)
        self.lcd.display(30)

        # initialize slider
        self.sld = QSlider(Qt.Horizontal, self)
        self.sld.setMinimum(30)
        self.sld.setMaximum(120)

        # initialize a timer
        self.time = 30
        self.tmr = QTimer()
        self.tmr.timeout.connect(self.timerTick)

        self.breaktmr = QTimer()
        self.breaktmr.timeout.connect(self.breakTick)

        # set up buttons
        self.startButton = QPushButton()
        self.startButton.setText("Start!")
        self.startButton.resize(self.startButton.sizeHint())

        self.editButton = QPushButton()
        self.editButton.setText("Edit")
        self.editButton.resize(self.editButton.sizeHint())

        self.breakbutton = QPushButton()
        self.breakbutton.setText("15 minute break")
        self.breakbutton.resize(self.breakbutton.sizeHint())

        # set up logo
        label = QLabel(self)
        pixmap = QPixmap('HocusFocusNew.png')
        label.setPixmap(pixmap)

        # set up layout
        vbox = QVBoxLayout()
        hbox1 = QHBoxLayout()
        finalbox = QVBoxLayout()

        vbox.addWidget(label)
        vbox.addWidget(self.lcd)
        vbox.addWidget(self.sld)
        finalbox.addLayout(vbox)
        hbox1.addWidget(self.startButton)
        hbox1.addWidget(self.editButton)
        hbox1.addWidget(self.breakbutton)
        finalbox.addLayout(hbox1)
        self.setLayout(finalbox)

        # when the slider is moved, update the display and the time variable
        self.sld.valueChanged.connect(self.lcd.display)
        self.sld.valueChanged.connect(self.setTime)

        # connect buttons to functions
        self.startButton.clicked.connect(self.startTimer)
        self.editButton.clicked.connect(self.startEdit)
        self.breakbutton.clicked.connect(self.startBreak)

        self.setGeometry(self.left, self.top, self.width, self.height)
        self.center()
        self.setWindowTitle("Hocus Focus")
        self.show()

    # called every minute for the main timer
    def timerTick(self):

        # when time runs out, stop the timer and stop blocking
        if self.time <= 0:
            self.tmr.stop()
            lockHosts.stopBlocking()
            # play applause
            winsound.PlaySound("SMALL_CROWD_APPLAUSE.wav", winsound.SND_ASYNC)
            return

        self.time = self.time - 1
        self.lcd.display(self.time)

    # called after 15 minutes when the break button is pushed
    def breakTick(self):

        self.breaktmr.stop()
        # resume blocking
        lockHosts.beginBlocking()
        # restart the main timer
        self.startTimer()
        # reset button text
        self.breakbutton.setText("15 minute break")

    def setTime(self, time):
        self.time = time

    def startTimer(self):
        # if the timer is active, stop it and reset text
        if self.tmr.isActive():
            self.tmr.stop()
            self.startButton.setText('Start!')

        else:
            lockHosts.beginBlocking()
            # one minute ticks
            self.tmr.start(1000)
            # pauses when pushed again
            self.startButton.setText('Pause')

    # open a simple plaintext editor
    def startEdit(self):
        blockList.show()

    # start the break
    def startBreak(self):
        # prevents extension of breaks
        if self.breaktmr.isActive():
            return
        if self.tmr.isActive():
            # pause the main timer
            self.tmr.stop()
            self.breakbutton.setText('Break happening...')
            # 15 minute break in ms
            self.breaktmr.start(5000)
            lockHosts.stopBlocking()

    # function to center the window
    def center(self):
        frame = self.frameGeometry()
        center = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                "Are you sure you want to quit?", QMessageBox.Yes |
                QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            lockHosts.stopBlocking()
            event.accept()
        else:
            event.ignore()

class LockHosts():

    # define the path for the hosts file
    def __init__(self):
        self.hostsFilePath = "C:\Windows\System32\drivers\etc\hosts"

    def beginBlocking(self):
        blockList.close()

        # open the host file
        file = open(self.hostsFilePath, mode='a')

        # write a line to mark the start of the blocked sites
        file.write("# This is the start of the blocked sites. \n")

        # redirect blocked sites to localhost
        # for site in list:
        sites = blockList.blockListView.toPlainText()
        sites = sites.split("\n")
        for site in sites:
            file.write("0.0.0.0 " + site + "\n")

        # write line to mark the end of the blocked sites
        file.write("# End of blocked sites.\n")

        # close the file
        file.close()

    # revert changes to the hosts file
    def stopBlocking(self):

        # read all the lines
        file = open(self.hostsFilePath, mode='r')
        lines = file.readlines()
        file.close()

        # go through lines, and skip everything
        # between the start mark and end mark, inclusive
        skipLine = False
        file = open(self.hostsFilePath, mode='w')
        for line in lines:
            print(line)
            if line == "# This is the start of the blocked sites. \n":
                print("Got inside this if!")
                skipLine = True

            if not skipLine:
                file.write(line)

            if line == "# End of blocked sites.\n":
                skipLine = False

        file.close()

class ListEditor(QDialog):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.blockListView = QPlainTextEdit()
        # path to the user's appdata/roaming directory
        self.datadir = os.getenv('APPDATA')

        # if a list of sites to block doesn't exist, make a new one
        if not os.path.isfile(self.datadir + "blocklist"):
            self.makeList()

        # load the list
        self.loadList()

        layout = QVBoxLayout()
        layout.addWidget(self.blockListView)
        self.saveB = QPushButton("Save")
        self.saveB.clicked.connect(self.closeEditor)
        layout.addWidget(self.saveB, 0, Qt.AlignCenter)

        self.setLayout(layout)
        # self.show()

    def loadList(self):
        file = open(self.datadir + "blocklist", mode='r')
        self.blockListView.appendPlainText(file.read())
        file.close()

    def makeList(self):
        file = open(self.datadir + "blocklist", mode='w')
        # tip for user at top of list
        file.write("# Add only one URL per line.")
        file.close()

    def updateList(self):
        file = open(self.datadir + "blocklist", mode='w+')
        file.write(blockList.blockListView.toPlainText())
        file.close()

    def closeEditor(self):
        self.updateList()
        blockList.hide()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    lockHosts = LockHosts()
    blockList = ListEditor()

    w = TimerWidget()

    sys.exit(app.exec_())