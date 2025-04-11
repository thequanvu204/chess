import glob, sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QVBoxLayout

import Internal.Client as Client
from Internal.ClientConnector import ClientConnector
from Internal.Util import fillGroupBox, getParam
from Internal.ServerSettings import ServerSettingsWidget, ServerSettings
from Internal.SelectTableWidgets import *
from Internal.RunGame import runClient


sessionTableWidget = None
serverSettingsWidget = None
mainWidget = None
waitDialog = None


def handleConnectorError(error):
    sessionTableWidget.clearContents()
    sessionTableWidget.setError(error)
    mainWidget.button_reconnect.show()
    serverSettingsWidget.unlock()
    Client.connector = None


def handleConnected():
    sessionTableWidget.setConnected()
    sessionId = getParam('--join-id', int)
    if sessionId is None:
        Client.connector.getSessions()
    else:
        handleJoined(sessionId)


def handleJoined(sessionId):
    global waitDialog
    Client.connector.join(sessionId)
    waitDialog = QMessageBox(QMessageBox.Information, 'Waiting For Host',
                             'It is waited for the host to start the game.', QMessageBox.Cancel, Client.mainWidget)
    def handleDialogDone(res):
        if res == QMessageBox.Cancel:
            Client.connector.disjoin()
        waitDialog.deleteLater()
    waitDialog.finished.connect(handleDialogDone)
    waitDialog.show()


def handleCancel(error):
    waitDialog.accept()
    QMessageBox.critical(Client.mainWidget, 'Session Canceled', error)


def handleGameDataReceived(data, state):
    waitDialog.accept()
    Client.connector.errorOccurred.disconnect(handleConnectorError)
    runClient(data, state)


def connectToServer():
    sessionTableWidget.reset()
    mainWidget.button_reconnect.hide()
    serverSettingsWidget.lock()
    if Client.connector is None:
        Client.connector = ClientConnector()
    sessionTableWidget.setConnecting()
    Client.connector.connected.connect(handleConnected)
    Client.connector.sessionsAdded.connect(sessionTableWidget.addSessions)
    Client.connector.sessionRemoved.connect(sessionTableWidget.removeSession)
    Client.connector.errorOccurred.connect(handleConnectorError)
    Client.connector.sessionCanceled.connect(handleCancel)
    Client.connector.gameDataReceived.connect(handleGameDataReceived)
    sessionTableWidget.sessionJoined.connect(handleJoined)


def handleTabChanged(index):
    if index == 1 and Client.connector is None:
        connectToServer()


def selectGame(loadGame):
    global mainWidget, sessionTableWidget, serverSettingsWidget
    gameFiles = []
    for file in glob.glob('*.py'):
        with open(file, 'rb') as gameFile:
            for line in gameFile.readlines():
                if line.startswith(b'GamePlayer.run('):
                    gameFiles.append(file)
                    break

    if len(gameFiles) == 0:
        QMessageBox.critical(None, 'No Game Found', 'No game file has been found.')
        QApplication.instance().exit(1)
        return

    mainWidget = QWidget()
    Client.setMainWidget(mainWidget)
    uic.loadUi('Internal/FormSelectGame.ui', mainWidget)
    serverSettingsWidget = ServerSettingsWidget()

    fillGroupBox(mainWidget.groupBox_serverSettings, serverSettingsWidget)

    gameTableWidget = GameTableWidget(gameFiles)
    mainWidget.tab_local.setLayout(QVBoxLayout())
    mainWidget.tab_local.layout().addWidget(gameTableWidget)
    gameTableWidget.playLocally.connect(lambda game: loadGame(game, False))
    gameTableWidget.hostGame.connect(serverSettingsWidget.lock)
    gameTableWidget.hostGame.connect(lambda game: loadGame(game, True))

    sessionTableWidget = SessionTableWidget()
    mainWidget.tab_server.layout().insertWidget(0, sessionTableWidget)
    mainWidget.tabWidget.setCurrentIndex(0)
    mainWidget.button_reconnect.hide()
    mainWidget.button_reconnect.clicked.connect(connectToServer)

    mainWidget.tabWidget.currentChanged.connect(handleTabChanged)
    if any(map(lambda x: x.startswith('--join'), sys.argv)):
        mainWidget.tabWidget.setCurrentIndex(1)

    mainWidget.show()