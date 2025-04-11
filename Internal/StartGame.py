import sys, functools
from PyQt5 import uic
from PyQt5.QtCore import QProcess, QTimer

import Internal.Client as Client
import Internal.GameOptions as GameOptions
from Internal.Util import *
from Internal.PlayerTableWidget import PlayerTableWidget
from Internal.ServerSettings import ServerSettingsWidget
from Internal.ClientConnector import ClientConnector
from Internal.RunGame import runLocally, runHosting, disconnect


localPlayerWidget = None
serverSettingsWidget = None
mainWidget = None
youSuffix = ' (You)'


def gObj():
    return Client.gameObject


def handleLocalPlayerCountChanged():
    mainWidget.button_addPlayer.setVisible(localPlayerWidget.rowCount() < gObj().maxPlayerCount)


def handleLocalPlayerAdded():
    i = localPlayerWidget.rowCount() + 1
    players = localPlayerWidget.getPlayers()
    while 'player ' + str(i) in players:
        i += 1
    localPlayerWidget.appendPlayer('player ' + str(i))


def handleConnected():
    Client.connector.host(type(gObj().hostGame) == int)
    serverPlayerWidget.setOverlayLabel(None)
    serverPlayerWidget.appendPlayer(Client.serverSettings.name + youSuffix)
    mainWidget.label_error.show()
    Client.connector.playerJoined.connect(handlePlayerJoined)
    Client.connector.playerDisjoined.connect(handlePlayerDisjoined)
    if type(gObj().hostGame) == int:
        Client.connector.sessionIdReceived.connect(startJoiningClients)


def handlePlayerJoined(player):
    serverPlayerWidget.appendPlayer(player)
    if serverPlayerWidget.rowCount() >= gObj().minPlayerCount:
        mainWidget.label_error.hide()
        mainWidget.button_start.setEnabled(True)


def handlePlayerDisjoined(player):
    serverPlayerWidget.removePlayer(player)
    if serverPlayerWidget.rowCount() < gObj().minPlayerCount:
        mainWidget.label_error.show()
        mainWidget.button_start.setEnabled(False)


def handleHostButtonToggled(host):
    mainWidget.stackedWidget.setCurrentIndex(1 if host else 0)
    if host:
        if Client.connector is None:
            serverSettingsWidget.lock()
            Client.connector = ClientConnector()
            Client.connector.connected.connect(handleConnected)
            mainWidget.button_start.setEnabled(False)
    else:
        mainWidget.button_start.setEnabled(True)


def handleStartButtonClicked():
    if not GameOptions.checkOptions():
        return
    ptw = serverPlayerWidget if mainWidget.button_host.isChecked() else localPlayerWidget
    gObj().players = list(map(lambda x: x[:-len(youSuffix)] if x.endswith(youSuffix) else x, ptw.getPlayers()))
    if gObj().playerTitles is not None:
        gObj().playerTitles = ptw.getTitles()
    gObj().hostGame = mainWidget.button_host.isChecked()
    if not gObj().hostGame:
        if Client.connector is not None:
            Client.connector.disconnect()
            Client.connector = None
        runLocally()
    else:
        mainWidget.setDisabled(True)
        runHosting()


childProcesses = []
serverProcess = None


def cleanUpChildProcesses():
    disconnect(waitForDisconnected=True)
    for childProcess in childProcesses:
        childProcess.waitForFinished()
    serverProcess.kill()
    if not serverProcess.waitForFinished(500):
        serverProcess.terminate()
        serverProcess.waitForFinished(500)


def startLocalServer():
    global serverProcess
    serverProcess = QProcess()
    serverProcess.setProcessChannelMode(QProcess.ForwardedChannels)
    serverProcess.start(sys.executable, ['GameSessionServer.py'])
    childProcesses.append(serverProcess)
    QApplication.instance().aboutToQuit.connect(cleanUpChildProcesses)


def startJoiningClients(sessionId):
    count = gObj().hostGame - 1
    def startChildProcess(player):
        process = QProcess()
        process.setProcessChannelMode(QProcess.ForwardedChannels)
        process.start(sys.executable, ['GamePlayer.py', '--join-id=' + str(sessionId),
                                       '--server-address=localhost', '--hosting-name=' + player])
        childProcesses.append(process)
    for i in range(count):
        QTimer.singleShot(i * 100, functools.partial(startChildProcess, gObj().players[i+1]))


def startGame():
    global mainWidget, localPlayerWidget, serverPlayerWidget, serverSettingsWidget
    mainWidget = QWidget()
    Client.setMainWidget(mainWidget)
    uic.loadUi('Internal/FormStartGame.ui', mainWidget)
    serverSettingsWidget = ServerSettingsWidget()
    fillGroupBox(mainWidget.groupBox_serverSettings, serverSettingsWidget)
    if GameOptions.empty():
        mainWidget.groupBox_gameSettings.hide()
    else:
        fillGroupBox(mainWidget.groupBox_gameSettings, GameOptions.Widget())
    localPlayerWidget = PlayerTableWidget(
        players=gObj().players,
        titles=gObj().playerTitles,
        minPlayerCount=gObj().minPlayerCount,
        playersAreMovable=True,
        playersAreEditable=True,
        playersAreRemovable=True,
        titlesAreChoosable=gObj().titlesAreChoosable,
    )
    mainWidget.page_local.layout().insertWidget(0, localPlayerWidget)
    localPlayerWidget.rowCountChanged.connect(handleLocalPlayerCountChanged)
    handleLocalPlayerCountChanged()
    mainWidget.button_addPlayer.clicked.connect(handleLocalPlayerAdded)

    serverPlayerWidget = PlayerTableWidget(
        players=[],
        titles=gObj().playerTitles,
        minPlayerCount=gObj().minPlayerCount,
        playersAreMovable=True,
        playersAreRemovable=True,
        titlesAreChoosable=gObj().titlesAreChoosable,
    )
    serverPlayerWidget.setOverlayLabel('Connecting ...')
    mainWidget.label_error.hide()
    mainWidget.label_error.setText('Minimum player count of {} not yet reached!'.format(gObj().minPlayerCount))

    mainWidget.button_host.toggled.connect(handleHostButtonToggled)
    mainWidget.page_server.layout().insertWidget(0, serverPlayerWidget)
    mainWidget.button_start.clicked.connect(handleStartButtonClicked)
    if gObj().autoStart:
        handleStartButtonClicked()
    elif gObj().hostGame:
        if gObj().hostGame is True:
            mainWidget.button_host.setChecked(True)
        elif type(gObj().hostGame) == int:
            gObj().getSessionId = True
            player = gObj().players[0]
            Client.serverSettings.name = player
            serverSettingsWidget.lineEdit_name.setText(player)
            host = 'localhost'
            Client.serverSettings.address = host
            serverSettingsWidget.lineEdit_address.setText(host)
            startLocalServer()
            def doWhenServerStarted():
                mainWidget.button_host.setChecked(True)
            QTimer.singleShot(500, doWhenServerStarted)
        mainWidget.show()
    else:
        mainWidget.show()
