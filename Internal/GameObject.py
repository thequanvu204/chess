import inspect, importlib.util, sys
from PyQt5.QtCore import QFileInfo
import GamePlayer
from Internal.Util import getInspectMember


class GameObject:

    StartFromModule = 0
    LoadSelected = 1
    LoadAsClient = 2

    def specAndModuleFromFile(self, filename):
        self.moduleSpec = importlib.util.spec_from_file_location(QFileInfo(filename).completeBaseName(), filename)
        self.module = importlib.util.module_from_spec(self.moduleSpec)
        # necessary for pickle
        sys.modules[self.module.__name__] = self.module

    def execModule(self):
        self.moduleSpec.loader.exec_module(self.module)

    def __init__(self, loadType, moduleFile=None, settings=None):
        self.currentPlayerIndex = 0
        self.thisPlayerIndex = 0
        self.loadType = loadType
        self.module = None
        self.moduleSpec = None
        self.leftPlayers = set()
        if loadType == self.StartFromModule: # retrieve module from stack
            gamePlayerFileName = getInspectMember(GamePlayer, '__file__')
            if gamePlayerFileName is None:
                raise ('Could not find Game module in stack!')
            gamePlayerFrameFound = False
            for info in inspect.stack():
                if info.filename == gamePlayerFileName:
                    gamePlayerFrameFound = True
                elif gamePlayerFrameFound:
                    self.specAndModuleFromFile(info.filename)
                    # transfer class definitions to module for unpickling
                    for name, val in info.frame.f_locals.items():
                        if inspect.isclass(val):
                            if val.__module__ == '__main__':
                                setattr(self.module, name, val)
                    # must use frame locals as module because they will be modified by game functions!
                    self.module = info.frame.f_locals
                    break
            if self.module is None:
                raise Exception('Game module could not be derived from stack!')
        else:
            if not moduleFile:
                raise Exception('Modulfile must be given for this load type')
            self.specAndModuleFromFile(moduleFile)
        if settings:
            self.addAndCheckSettings(settings)

    def addAndCheckSettings(self, settings):
        for key, value in settings.items():
            setattr(self, key, value)
        if type(self.minPlayerCount) is not int:
            raise Exception('Parameter minPlayerCount for GamePlayer.run must be an integer!')
        if type(self.maxPlayerCount) is not int:
            raise Exception('Parameter maxPlayerCount for GamePlayer.run must be an integer!')
        if type(self.autoStart) != bool:
            raise Exception('autoStart parameter for GamePlayer.run must be a bool!')
        if self.autoStart:
            self.hostGame = False
        if type(self.hostGame) == int:
            if not (self.minPlayerCount <= self.hostGame <= self.maxPlayerCount):
                raise Exception('hostGame must be in range [minPlayerCount, maxPlayerCount]!')
            if self.players is None:
                self.players = self.hostGame
            if type(self.players) == int:
                self.players = self.hostGame
            if type(self.players) == list:
                if len(self.players) < self.hostGame:
                    raise Exception('length of players parameter must be at the same as hostGame parameter!')
                self.players = self.players[:self.hostGame]
        else:
            self.hostGame = bool(self.hostGame)
        if self.players is None:
            self.players = self.minPlayerCount
        if type(self.players) == int:
            if self.players < self.minPlayerCount or self.players > self.maxPlayerCount:
                raise Exception('players parameter for GamePlayer.run is not in [minPlayerCount, maxPlayerCount]!')
            self.players = ['player ' + str(i + 1) for i in range(self.maxPlayerCount)]
        elif type(self.players) != list or any(map(lambda x: type(x) != str, self.players)):
            raise Exception(
                'players parameter for GamePlayer.run is neither None, nor an integer, nor a list of strings!')
        elif not (self.minPlayerCount <= len(self.players) <= self.maxPlayerCount):
            raise Exception(
                'len of players parameter for GamePlayer.run is not in [minPlayerCount, maxPlayerCount]!')
        if self.gameName is None:
            self.gameName = self.moduleSpec.name
        elif type(self.gameName) != str:
            raise Exception('gameName parameter for GamePlayer.run must be a string or None!')
        if self.playerTitles is not None:
            if type(self.playerTitles) != list or any(map(lambda x: type(x) != str, self.playerTitles)):
                raise Exception('playerTitles parameter for GamePlayer.run must be either None or a list of strings!')
            if len(self.playerTitles) != self.maxPlayerCount:
                raise Exception('length of playerTitles parameter list must be equal to maxPlayerCount')
        self.titlesAreChoosable = bool(self.titlesAreChoosable)
        self.mouseMoveEventsEnabled = bool(self.mouseMoveEventsEnabled)
        self.playerCanLeave = hasattr(self.module, 'playerLeftGame')

    def isMoving(self):
        return self.currentPlayerIndex == self.thisPlayerIndex

    def getPlayerCount(self):
        return len(self.players)
