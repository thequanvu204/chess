from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtGui import QTransform, QPicture, QPainter
from PyQt5.QtWidgets import QWidget, QMainWindow

import Internal.Client as Client
from Internal.Util import getModuleAttrDict


def getPlayerString(index):
    if Client.gameObject.playerTitles is None:
        return Client.gameObject.players[index]
    if Client.gameObject.players is None:
        return Client.gameObject.playerTitles[index]
    else:
        return '{} ({})'.format(Client.gameObject.players[index], Client.gameObject.playerTitles[index])


class GameMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        gObj = Client.gameObject
        windowTitle = gObj.gameName
        if gObj.hostGame:
            windowTitle += ' - ' + gObj.players[gObj.thisPlayerIndex]
        self.setWindowTitle(windowTitle)
        self.gameWidget = GameWidget()
        self.setCentralWidget(self.gameWidget)
        self.updateStatusBar()
        self.gameWidget.moveDone.connect(self.updateStatusBar)

    def updateStatusBar(self):
        gObj = Client.gameObject
        if gObj.currentPlayerIndex == -1:
            message = 'The game is over.'
        elif not gObj.hostGame or gObj.currentPlayerIndex != gObj.thisPlayerIndex:
            message = getPlayerString(gObj.currentPlayerIndex) + ' is to move.'
        elif gObj.playerTitles is None:
            message = 'You are to move.'
        else:
            message = 'You ({}) are to move'.format(gObj.playerTitles[gObj.thisPlayerIndex])
        self.statusBar().showMessage(message)

    def keyPressEvent(self, event):
        self.gameWidget.handleEvent(event)
        return super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.gameWidget.handleEvent(event)
        return super().keyReleaseEvent(event)


def openGameWindow():
    mainWidget = GameMainWindow()
    Client.setMainWidget(mainWidget)
    mainWidget.show()
    return mainWidget.gameWidget


class GameWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.invTrafo = QTransform()
        self.sizeHint_ = None

    def paintEvent(self, QPaintEvent):
        pic = QPicture()
        painter = QPainter(pic)
        nextUpdate = getModuleAttrDict(Client.gameObject.module)['paintGame'](painter)
        if nextUpdate is not None:
            if type(nextUpdate) != int or nextUpdate < 0:
                raise Exception('The return value of "paintGame" must be None or an integer >= 0')
            QTimer.singleShot(nextUpdate, self.update)
        painter.end()
        painter.begin(self)
        bRect = pic.boundingRect()
        self.sizeHint_ = bRect.size()
        painter.setWindow(bRect)
        painter.setViewTransformEnabled(True)
        width = self.width()
        height = self.height()
        if width * bRect.height() < height * bRect.width():
            pheight = int((width * bRect.height()) / bRect.width())
            painter.setViewport(0, int((height - pheight) / 2), width, pheight)
        else:
            pwidth = int((height * bRect.width()) / bRect.height())
            painter.setViewport(int((width - pwidth) / 2), 0, pwidth, height)
        self.invTrafo = painter.combinedTransform().inverted()[0]
        pic.play(painter)

    def sizeHint(self):
        if not self.sizeHint_:
            pic = QPicture()
            painter = QPainter(pic)
            getModuleAttrDict(Client.gameObject.module)['paintGame'](painter)
            painter.end()
            self.sizeHint_ = pic.boundingRect().size()
        return self.sizeHint_

    moveDone = pyqtSignal(int)

    def handleMouseEvent(self, event):
        if not Client.gameObject.isMoving:
            return
        oldPos = event.pos
        oldX = event.x
        oldY = event.y
        worldPos = self.invTrafo.map(event.pos()) * self.devicePixelRatio()

        class Returner:
            def __init__(self, returnVal):
                self.returnVal = returnVal

            def __call__(self):
                return self.returnVal

        event.pos = Returner(worldPos)
        event.x = Returner(worldPos.x())
        event.y = Returner(worldPos.y())
        self.handleEvent(event)
        event.pos = oldPos
        event.x = oldX
        event.y = oldY

    def handleEvent(self, event):
        if not Client.gameObject.isMoving():
            return
        next = getModuleAttrDict(Client.gameObject.module)['makeMove'](event)
        if next is not None:
            if type(next) != int:
                raise Exception('makeMove returned "{}" which is neither None nor an integer'.format(str(next)))
            if not (-1 <= next < Client.gameObject.getPlayerCount()):
                raise Exception('makeMove returned {} which is neither -1 nor a valid player index'.format(next))
            if next in Client.gameObject.leftPlayers:
                raise Exception('makeMove returned {} but this player already left the game.'.format(next))
            Client.gameObject.currentPlayerIndex = next
            self.moveDone.emit(next)
        self.update()

    def mousePressEvent(self, event):
        self.handleMouseEvent(event)
        return QWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        self.handleMouseEvent(event)
        return QWidget.mouseReleaseEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        self.handleMouseEvent(event)
        return QWidget.mouseDoubleClickEvent(self, event)

    def mouseMoveEvent(self, event):
        if Client.gameObject.mouseMoveEventsEnabled:
            self.handleMouseEvent(event)
        return QWidget.mouseMoveEvent(self, event)

    def wheelEvent(self, event):
        self.handleMouseEvent(event)
        return QWidget.wheelEvent(self, event)
