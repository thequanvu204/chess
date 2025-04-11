from enum import Enum

class Team(Enum):
    white = 0
    black = 1

class ChessPiece:
    def __init__(self,type,team,position):
        self.__type = type
        self.__team = team
        self.__position = position
        self.__possibles = None
    
    def getType(self):
        return self.__type
    
    def getTeam(self):
        return self.__team
    
    def getPosition(self):
        return self.__position
    
    def getHasMoved(self):
        return self.__hasMoved

    def setHasMoved(self, hasMoved):
        self.__hasMoved = hasMoved
    
    def setPosition(self, position):
        self.__position = position

    def setType(self, type):
        self.__type = type
    
    def setPossibles(self,possibles):
        self.__possibles = possibles

    def setPassant(self,passant):
        self.__passant = passant
    
    def getPossibles(self):
        return self.__possibles
    
    def getPassant(self):
        return self.__passant

class PieceType:
    def __init__(self,whiteSymbol,blackSymbol,movement : list,limit,value):
        self.__whiteSymbol = whiteSymbol
        self.__blackSymbol = blackSymbol
        self.__movement = movement
        self.__limit = limit
        self.__value = value

    def getValue(self):
        return self.__value

    def getSymbol(self,team):
        if (team == Team.white):
            return self.__whiteSymbol
        if (team == Team.black):
            return self.__blackSymbol
    
    def getMovement(self) -> list:
        return self.__movement
    
    def getLimit(self):
        return self.__limit
    
    def setLimit(self, limit):
        self.__limit = limit

    def setMovement(self, movement):
        self.__movement = movement
