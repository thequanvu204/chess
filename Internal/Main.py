import sys
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

import Internal.Client as Client
from Internal.Util import *
from Internal.GameObject import GameObject
from Internal.ServerSettings import *
from Internal.StartGame import startGame
from Internal.RunGame import showMessageLater
from Internal.RunGame import addToNoSyncList
import Internal.SelectGame as SelectGame
from Internal.GameOptions import add as addOption
from Internal.GameOptions import showDialog as showOptionsDialog
from Internal.GameOptions import setChecker as setOptionsChecker
from Internal.ClientConnector import registerFile
from Internal.GameWidget import GameMainWindow


app = QApplication(sys.argv)


# def registerFile(filepath):
#     return Main.registerFile(filepath)
#
#
# def addToNoSyncList(*args):
#     Main.addToNoSyncList(*args)


def getGameObject():
    if Client.gameObject is None:
        raise Exception('You cannot call this function because the game has not yet started!')
    return Client.gameObject


def loadGame(gameFile, hostGame=None):
    try:
        Client.gameObject = GameObject(GameObject.LoadSelected, moduleFile=gameFile)
        Client.gameObject.execModule()
        if hostGame is not None:
            Client.gameObject.hostGame = hostGame
        return
    except Exception as e:
        QMessageBox.critical(Client.mainWidget, 'Error', 'The following error occurred:\n\n' + str(e))
    except:
        QMessageBox.critical(Client.mainWidget, 'Unknown Error', 'An unknown error occurred when loading the game.')
    Client.gameObject = None


def selectGame():
    settings = loadSettings()
    settings.update(parseArgs())
    if Client.serverSettings is None:
        Client.serverSettings = ServerSettings(
            name=settings.get('hostingName'),
            secret=settings.get('sessionSecret'),
            address=settings.get('serverAddress')
        )
    SelectGame.selectGame(loadGame)
    exec()


def exec():
    sys.exit(app.exec())


def run(settings):
    settings.update(loadSettings())
    settings.update(parseArgs())
    hostingName = settings.pop('hostingName')
    sessionSecret = settings.pop('sessionSecret')
    serverAddress = settings.pop('serverAddress', None)
    if hostingName is not None and type(hostingName) != str:
        raise Exception('hostingName parameter for GamePlayer.run must be None or a string!')
    if sessionSecret is not None and type(sessionSecret) != str:
        raise Exception('sessionSecret parameter for GamePlayer.run must be None or a string!')
    if Client.serverSettings is None:
        Client.serverSettings = ServerSettings(name=hostingName, secret=sessionSecret, address=serverAddress)
    if Client.gameObject is not None:
        Client.gameObject.addAndCheckSettings(settings)
    else:
        try:
            Client.gameObject = GameObject(GameObject.StartFromModule, settings=settings)
        except Exception as e:
            QMessageBox.critical(None, 'Error', 'The following error occurred:\n\n' + str(e))
            return
    if Client.gameObject.loadType != GameObject.LoadAsClient:
        QTimer.singleShot(0, startGame)
        if Client.gameObject.loadType == GameObject.StartFromModule:
            exec()


paintGameTimer = None


def startPaintGameTimer(milliSeconds, singleShot):
    global paintGameTimer
    if paintGameTimer is None:
        if type(Client.mainWidget) != GameMainWindow:
            raise Exception('startPaintTimer must not be called before the game has started!')
        paintGameTimer = QTimer(QApplication.instance())
        QApplication.instance().aboutToQuit.connect(paintGameTimer.stop)
        paintGameTimer.timeout.connect(Client.mainWidget.gameWidget.update)
    paintGameTimer.setSingleShot(singleShot)
    paintGameTimer.start(milliSeconds)


def stopPaintGameTimer():
    if paintGameTimer is not None:
        paintGameTimer.stop()


def paintGameTimerIsActive():
    return paintGameTimer is not None and paintGameTimer.isActive()
