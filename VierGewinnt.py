from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QPainter
import GamePlayer


board = None

def initGame():
    global board
    board = [ [ '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_'] ]


def paintGame(painter : QPainter):
    painter.fillRect(0, 0, 700, 600, Qt.white)

    pen = painter.pen()
    pen.setWidth(5)
    painter.setPen(pen)
    for i in range(0,701,100):
        painter.drawLine(i, 0, i, 600)
    for j in range(0,601,100):
        painter.drawLine(0, j, 700, j)

    font = painter.font()
    font.setPixelSize(80)
    painter.setFont(font)

    for i in range(7):
        for j in range(6):
            if board[i][j] != '_':
                painter.drawText(i*100, j*100, 100, 100, Qt.AlignCenter, board[i][j])


playerSymbols = ['X', 'O']


def makeMove(event : QEvent):
    currentPlayerIndex = GamePlayer.getCurrentPlayerIndex()
    if event.type() == QEvent.MouseButtonRelease:
        pos = event.pos()
        i = pos.x() // 100
        j = pos.y() // 100
        if i < 0 or i > 6 or j < 0 or j > 5:
            return None
        playerSymbol = playerSymbols[currentPlayerIndex]
        
        if board[i][j] == '_':
            for x in range(0,6,1):
                if board[i][x] != '_':
                    board[i][x-1] = playerSymbol
                    break
                if (x >= 5):
                    board[i][x] = playerSymbol
                    break   

            if hasWon(playerSymbol):
                GamePlayer.showMessageLaterForAll('Game Over', GamePlayer.getPlayerNames()[currentPlayerIndex] + ' has won the game.')
                return -1
            draw = True
            for i in range(7):
                for j in range(6):
                   if board[i][j] == '_':
                        draw = False
                        break
            if draw:
                GamePlayer.showMessageLaterForAll('Game Over', 'The game is a draw.')
                return -1
            else:
                return (currentPlayerIndex + 1) % GamePlayer.getPlayerCount()
            



def hasWon(playerSymbol : str):
    
    
    #y
    for i in range(7):
        for j in range(3):
            if board[i][j] == playerSymbol and board[i][j+1] == playerSymbol and board[i][j+2] == playerSymbol and board[i][j+3] == playerSymbol: 
                return True
    #x
    for i in range(4):
        for j in range(6):
            if board[i][j] == playerSymbol and board[i+1][j] == playerSymbol and board[i+2][j] == playerSymbol and board[i+3][j] == playerSymbol: 
                return True
    
    for i in range(4):
        for j in range(3):
            if board[i][j] == playerSymbol and board[i+1][j+1] == playerSymbol and board[i+2][j+2] == playerSymbol and board[i+3][j+3] == playerSymbol: 
                return True
    
    for i in range(4):
        for j in range(3,7):
            if board[i][j] == playerSymbol and board[i+1][j-1] == playerSymbol and board[i+2][j-2] == playerSymbol and board[i+3][j-3] == playerSymbol: 
                return True

GamePlayer.run(
    playerTitles=playerSymbols,
)
