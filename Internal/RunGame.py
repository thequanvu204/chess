import pickle, sys, inspect, os
from tempfile import TemporaryDirectory
from PyQt5.QtCore import QFileInfo, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

import Internal.Client as Client
from Internal.GameWidget import openGameWindow
from Internal.GameObject import GameObject
from Internal.Util import getModuleAttrDict, getModuleFilePath
import Internal.GameOptions as GameOptions
import GamePlayer


def initGame():
    initGameFunc = getModuleAttrDict(Client.gameObject.module).get('initGame')
    if initGameFunc:
        initGameFunc()


def runLocally():
    Client.gameObject.hostGame = False
    initGame()
    gameWindow = openGameWindow()
    def handleMoveDone():
        if Client.gameObject.currentPlayerIndex >= 0:
            Client.gameObject.thisPlayerIndex = Client.gameObject.currentPlayerIndex
    gameWindow.moveDone.connect(handleMoveDone)



def showMessageLater(title, text, showOnThisPC, sendToOthers):
    if sendToOthers and Client.connector:
        Client.connector.sendMessage(title, text)
    if showOnThisPC:
        QTimer.singleShot(0, lambda: handleMessageReceived(title, text))


messages = []
showingMessage = False
def handleMessageReceived(title, text):
    global messages, showingMessage
    if showingMessage:
        messages.append((title, text))
    else:
        messageBox = QMessageBox(QMessageBox.Information, title, text, QMessageBox.Ok, Client.mainWidget)
        def whenFinished():
            global messages, showingMessage
            showingMessage = False
            if len(messages) > 0:
                [title, text] = messages.pop(0)
                handleMessageReceived(title, text)
        messageBox.finished.connect(whenFinished)
        messageBox.show()


def disconnect(waitForDisconnected=False):
    try:
        Client.connector.errorOccurred.disconnect(handleError)
    except:
        pass
    Client.connector.disconnect(waitForDisconnected)


def handleUpdateReceived(finished, state):
    if finished:
        disconnect()
    applyState(state)
    Client.mainWidget.updateStatusBar()
    Client.mainWidget.update()


def handlePlayerLeft(name):
    gObj = Client.gameObject
    index = gObj.players.index(name)
    gObj.leftPlayers.add(index)
    gObjDict = getModuleAttrDict(gObj.module)
    if 'playerLeftGame' not in gObjDict:
        gObj.currentPlayerIndex = -1
        handleMessageReceived('Player Left', 'The game has been aborted because "{}" left the game '
                                             'but no playerLeft method has been implemented'.format(name))
        Client.connector.disconnect()
    else:
        nextInOrder = gObj.currentPlayerIndex
        if index == gObj.currentPlayerIndex:
            while nextInOrder in gObj.leftPlayers:
                nextInOrder += 1
                nextInOrder %= gObj.getPlayerCount()
        if nextInOrder == gObj.thisPlayerIndex:
            next = gObjDict['playerLeftGame'](index)
            if type(next) != int:
                raise Exception('"playerLeftGame" returned {} but it must return an integer'.format(next))
            if not (-1 <= next < gObj.getPlayerCount()):
                raise Exception('"playerLeftGame" returned {} which is neither -1 nor a valid player index!'.
                                format(next))
            if next in gObj.leftPlayers:
                raise Exception('"playerLeftGame" returned {} but this player has already left the game!'.format(next))
            gObj.currentPlayerIndex = next
            finished = (next == -1)
            Client.connector.sendUpdate(finished, getState())
            if finished:
                disconnect()
            Client.mainWidget.gameWidget.update()
    Client.mainWidget.updateStatusBar()


def handleError(error):
    QMessageBox.critical(Client.mainWidget, 'Error Occurred', 'The following error ocurred:\n\n' + error)


def runGame():
    Client.connector.updateReceived.connect(handleUpdateReceived)
    Client.connector.messageReceived.connect(handleMessageReceived)
    Client.connector.errorOccurred.connect(handleError)
    Client.connector.playerLeft.connect(handlePlayerLeft)
    gameWindow = openGameWindow()
    def handleMoveDone(res):
        finished = (res == -1)
        Client.connector.sendUpdate(finished, getState())
        if finished:
            disconnect()
    gameWindow.moveDone.connect(handleMoveDone)


def normalizePath(path):
    return QFileInfo(path).absoluteFilePath()


modules = None
thisDirName = normalizePath(os.path.dirname(__file__))


def getPathsAndModules():
    module = Client.gameObject.module
    moduleFile = normalizePath(getModuleFilePath(module))
    path = moduleFile[:(moduleFile.rfind('/') + 1)]
    pathLen = len(path)
    modules = [[moduleFile[pathLen:], module]]
    stack = [module]
    while len(stack) > 0:
        module = stack.pop()
        for var in getModuleAttrDict(module).values():
            if all(m[1] != var for m in modules) and var != GamePlayer and inspect.ismodule(var) and hasattr(var, '__file__'):
                moduleFile = normalizePath(var.__file__)
                if moduleFile.startswith(path) and os.path.dirname(moduleFile) != thisDirName:
                    modules.append([moduleFile[pathLen:], var])
                    stack.append(var)
    return modules


noSyncDict = dict()
def addToNoSyncList(*args):
    filename = inspect.stack()[2].filename
    names = noSyncDict.setdefault(filename, set())
    for arg in args:
        names.add(arg)


def getState():
    mstates = []
    for module in modules:
        ignore = noSyncDict.get(getModuleFilePath(module), set())
        vars = dict()
        for name, var in getModuleAttrDict(module).items():
            if name not in ignore and not name.startswith('__') and not name.endswith('__') and \
                    not inspect.ismodule(var) and not inspect.isfunction(var) and not inspect.isclass(var):
                vars[name] = var
        mstates.append(vars)
    return pickle.dumps([Client.gameObject.currentPlayerIndex, mstates])


def applyState(state):
    [currentPlayerIndex, mstates] = pickle.loads(state)
    Client.gameObject.currentPlayerIndex = currentPlayerIndex
    for module, vars in zip(modules, mstates):
        getModuleAttrDict(module).update(vars)


def runHosting():
    Client.connector.gameDataRequested.connect(handleGameDataRequested)
    Client.connector.startSession()


def handleGameDataRequested():
    global modules
    initGame()
    pathsAndModules = getPathsAndModules()
    modules = list(map(lambda x: x[1], pathsAndModules))
    # read modules
    for pathAndModule in pathsAndModules:
        pathAndModule[1] = open(getModuleFilePath(pathAndModule[1]), 'rb').read()
    gObj = Client.gameObject
    data = pickle.dumps([gObj.players, gObj.playerTitles, pathsAndModules])
    Client.connector.sendGameData(data, getState())
    gObj.thisPlayerIndex = gObj.players.index(Client.serverSettings.name)
    gObj.hostGame = True
    runGame()


def runClient(data, state):
    global tempDir, modules
    tempDir = TemporaryDirectory()
    tempPath = QFileInfo(tempDir.name).absoluteFilePath()+ '/'
    sys.path = [tempPath] + sys.path
    QApplication.instance().aboutToQuit.connect(tempDir.cleanup)
    [players, playerTitles, pathsAndModules] = pickle.loads(data)
    fullPaths = []
    paths = []
    for path, module in pathsAndModules:
        fullPath = tempPath + path
        os.makedirs(os.path.dirname(fullPath), exist_ok=True)
        open(fullPath, 'wb').write(module)
        fullPaths.append(fullPath)
        paths.append(path)
    Client.gameObject = GameObject(GameObject.LoadAsClient, moduleFile=fullPaths[0])
    Client.gameObject.execModule()
    # get locals dict of main frame
    for info in inspect.stack():
        frameLocals = info.frame.f_locals
        if frameLocals.get('__name__') == '__main__':
            mainLocals = frameLocals
            break
    # copy classes from game module to GamePlayer because on host __main__ might be the Game module
    # while on client __main__ module is the GamePlayer module
    gameModule = Client.gameObject.module
    for name, val in gameModule.__dict__.items():
        if inspect.isclass(val):
            if val.__module__ == gameModule.__name__:
                mainLocals[name] = val
    Client.gameObject.players = players
    Client.gameObject.playerTitles = playerTitles
    Client.gameObject.thisPlayerIndex = players.index(Client.serverSettings.name)
    Client.gameObject.hostGame = True

    modules = [None] * len(pathsAndModules)
    for path, module in getPathsAndModules():
        modules[paths.index(path)] = module

    GameOptions.options.clear()

    applyState(state)
    runGame()

