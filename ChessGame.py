from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QPainter, QColor
import GamePlayer
import ChessGameClasses as C
import TupleOperations as T

clickedPos = None
selectedPiece = None               
phase = 1
board = [[]]
allPieces = []
blackPieces = []
whitePieces = []
selectedPossibles = []
rochade = []

passantHighlights = []

pawnStartW = None
pawnStartB = None
pawnW = None
pawnB = None
knight = None
bishop = None
rook = None
queen = None
king = None
whiteKing = None
blackKing = None
lRookB = None
rRookB = None
lRookW = None
rRookW = None
fiftymoverule = 0
checkBlack = None
checkWhite = None
pressed = False
offerdraw = False
playerSymbols = ["White", "Black"]

# Initialisiert das Board und setzt die Figuren
def initGame():
    global board
    global allPieces

    global pawnStartW
    global pawnStartB
    global pawnB
    global pawnW
    global knight
    global bishop
    global rook
    global queen
    global king
    global whiteKing
    global blackKing

    global lRookW
    global rRookW
    global lRookB
    global rRookB
    global pressed
    global offerdraw

    board = [ [ '_', '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_', '_'] ,
              [ '_', '_', '_', '_', '_', '_', '_', '_'] ]
    
    # Instanzieren der verschiedenen Figuren Typen
    pawnB = C.PieceType("\u2659","\u265F",[(1,0)],1,1)
    pawnStartB = C.PieceType("\u2659","\u265F",[(1,0)],2,1)
    pawnStartW = C.PieceType("\u2659","\u265F",[(-1,0)],2,1)
    pawnW = C.PieceType("\u2659","\u265F",[(-1,0)],1,1)
    knight = C.PieceType("\u2658","\u265E",[(-2,1),(-2,-1),(2,1),(2,-1),(-1,2),(-1,-2),(1,2),(1,-2)],1,3)
    bishop = C.PieceType("\u2657","\u265D",[(1,1),(1,-1),(-1,-1),(-1,1)],maxBoardSize(),3)
    rook = C.PieceType("\u2656","\u265C",[(-1,0),(1,0),(0,1),(0,-1)],maxBoardSize(),5)
    queen = C.PieceType("\u2655","\u265B",[(-1,0),(1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,-1),(-1,1)],maxBoardSize(),9)
    king = C.PieceType("\u2654","\u265A",[(-1,0),(1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,-1),(-1,1)],1,0)

    # Instanzieren der einzelnen Figuren
    for i in range(8):
        temp = C.ChessPiece(pawnStartB,C.Team.black,(1,i))
        temp.setPassant(False)
        blackPieces.append(temp)

    for i in range(8):
        temp = C.ChessPiece(pawnStartW,C.Team.white,(6,i))
        temp.setPassant(False)
        whitePieces.append(temp)

    lRookB = C.ChessPiece(rook,C.Team.black,(0,0))
    lRookB.setHasMoved(False)
    blackPieces.append(lRookB)
    rRookB = C.ChessPiece(rook,C.Team.black,(0,7))
    rRookB.setHasMoved(False)
    blackPieces.append(rRookB)

    blackPieces.append(C.ChessPiece(knight,C.Team.black,(0,1)))
    blackPieces.append(C.ChessPiece(knight,C.Team.black,(0,6)))
    blackPieces.append(C.ChessPiece(bishop,C.Team.black,(0,5)))
    blackPieces.append(C.ChessPiece(bishop,C.Team.black,(0,2)))
    blackPieces.append(C.ChessPiece(queen,C.Team.black,(0,3)))

    lRookW = C.ChessPiece(rook,C.Team.white,(7,0))
    lRookW.setHasMoved(False)
    whitePieces.append(lRookW)
    rRookW = C.ChessPiece(rook,C.Team.white,(7,7))
    rRookW.setHasMoved(False)
    whitePieces.append(rRookW)

    whitePieces.append(C.ChessPiece(knight,C.Team.white,(7,1)))
    whitePieces.append(C.ChessPiece(knight,C.Team.white,(7,6)))
    whitePieces.append(C.ChessPiece(bishop,C.Team.white,(7,5)))
    whitePieces.append(C.ChessPiece(bishop,C.Team.white,(7,2)))
    whitePieces.append(C.ChessPiece(queen,C.Team.white,(7,3)))
    
    blackKing = C.ChessPiece(king,C.Team.black,(0,4))
    blackKing.setHasMoved(False)
    blackPieces.append(blackKing)
    whiteKing = C.ChessPiece(king,C.Team.white,(7,4))
    whiteKing.setHasMoved(False)
    whitePieces.append(whiteKing)
    
    # Darstellung der Figuren auf dem Brett
    allPieces = whitePieces + blackPieces
    updateBoard()
    allPossibles()
    resetPassants()

# Gibt den Index des nächsten Spieler zurück (bei zwei Spielern 0 oder 1)
def getNextPlayerIndex():
    playersLeftSet = GamePlayer.getLeftPlayersSet()
    index = (GamePlayer.getCurrentPlayerIndex() + 1) % GamePlayer.getPlayerCount()
    while index in playersLeftSet:
        index = (index + 1) % GamePlayer.getPlayerCount()
    return index

# Errechnet die maximale Länge des Boardes, funktioniert nur mit quadratischen Boards
def maxBoardSize():
    global board

    if len(board) >= len(board[0]):
        size = len(board)
    else:
        size = len(board[0])

    return size

# Resetet das Board und die Position der Figursymbole auf dem Board
def updateBoard():
    global board
    for x in range(len(board)):
        for y in range(len(board[x])):
            board[x][y] = '_'

    for piece in allPieces:
        board[piece.getPosition()[0]][piece.getPosition()[1]] = piece.getType().getSymbol(piece.getTeam())    

# Entfernt eine Figur aus dem Spiel
def removePiece(piece):
    global allPieces
    global whitePieces
    global blackPieces

    allPieces.remove(piece)
    if (whitePieces.count(piece) > 0):
        whitePieces.remove(piece)
    if (blackPieces.count(piece) > 0):
        blackPieces.remove(piece)

# Wiederherstellung einer Figur, falls sie nur temporär entfernt werden sollte
def restorePiece(piece):
    global allPieces
    global whitePieces
    global blackPieces

    allPieces.append(piece)

    if (piece.getTeam() == C.Team.white):
        whitePieces.append(piece)

    if (piece.getTeam() == C.Team.black):
        blackPieces.append(piece)

# Überprüft ob das Spiel vorbei ist und was das Ergebnis ist
def checkGameOver():
    global allPieces
    allPossibles()

    movesLeft = False
    for piece in whitePieces:
    
        possibles = chessPossibles(piece,possibleMoves(piece))

        if (len(possibles) > 0):
            movesLeft = True

    if (checkChess('White') != None) and (movesLeft != True):
        return 'Black'
    elif (movesLeft != True):
        return 'Draw'
    
    movesLeft = False
    for piece in blackPieces:
            
        possibles = chessPossibles(piece,possibleMoves(piece))

        if (len(possibles) > 0):
            movesLeft = True
        
    if (checkChess('Black') != None) and (movesLeft != True):
        return 'White'
    elif (movesLeft != True):
        return 'Draw'
    
    return None

# Überprüft ob sich eine Spieler(playerSymbol) im Schach befindet und liefert die Figuren zurück, welche den König bedrohen
def checkChess(playerSymbol):
    global whiteKing
    global blackKing

    allPossibles()

    if playerSymbol == 'White':
        k = whiteKing
        pieces = blackPieces
    else:
        k = blackKing
        pieces = whitePieces

    L = []
    for piece in pieces:
        for p in piece.getPossibles():
            if p == k.getPosition():
                L.append(piece)
                break
    
    if len(L) > 0:          
        return L

    return None

# Bekommt eine Figur übergeben und gibt alle möglichen Züge der Figur zurück (unabhängig von Schach oder nicht)
def possibleMoves(piece):
    global playerSymbols
    position = piece.getPosition()

    possibles = []
    movement = piece.getType().getMovement()

    for move in movement:
        i = 1
        while (i <= piece.getType().getLimit()):
            targetPos = T.sumTuple(position,(move[0]*i,move[1]*i))
            if ((T.compareTuple(targetPos,(len(board)-1,len(board[0])-1)) == -1) and (T.compareTuple(targetPos,(0,0)) == -2)) or targetPos == (0,0) or targetPos == (len(board)-1,len(board[0])-1):
                if (checkField(targetPos) == None):
                    possibles.append(targetPos)
                else:
                    if checkField(targetPos).getTeam() != piece.getTeam():
                        if (piece.getType() != pawnB and piece.getType() != pawnStartB) and (piece.getType() != pawnW and piece.getType() != pawnStartW):
                            possibles.append(targetPos)
                        break
                    else:
                        break
            i+=1
    # Für Pawns damit sie quer schlagen können
    if (piece.getType() == pawnB or piece.getType() == pawnStartB) or (piece.getType() == pawnW or piece.getType() == pawnStartW):
        temp = pawnKills(piece)
        if(len(temp) != 0):
            for t in temp:
                possibles.append(t)

    return possibles

# Checkt ob Schach und gibt nur moves zurück, welche das Schach verhindern
def chessPossibles(piece,possibleMoves):
    position = piece.getPosition()
    possibles = []

    if (piece.getTeam() == C.Team.white):
        index = 'White'
    if (piece.getTeam() == C.Team.black):
        index = 'Black'

    for move in possibleMoves:
        
        targetPiece = checkField(move)
        if (targetPiece != None):
            removePiece(targetPiece)

        piece.setPosition(move)

        allPossibles()

        if (checkChess(index) == None):
            possibles.append(move)

        if (targetPiece != None):
            restorePiece(targetPiece)
            
        piece.setPosition(position) 

        allPossibles()   

        if (checkChess(index) != None):
            for p in checkChess(index):
                if (move == p.getPosition()):

                    piece.setPosition(move)
                    removePiece(p)
                    allPossibles()

                    if (checkChess(index) == None):
                        possibles.append(move)

                    restorePiece(p)
                    piece.setPosition(position)
                    allPossibles()

    return possibles

# Checkt ob eine Rochade möglich ist und gibt ggf. die moves zurück, damit der König diese ausführen kann
def checkRochade(piece):
    possibles = []
    position = piece.getPosition()
    allPossibles()

    if (piece == whiteKing):
        king = whiteKing
        index = 'White'
        lRook = lRookW
        rRook = rRookW
        pieces = blackPieces

    if (piece == blackKing):
        king = blackKing
        index = 'Black'
        lRook = lRookB
        rRook = rRookB
        pieces = whitePieces

    # Team weiß
    if piece == king:
        if not(king.getHasMoved()):
            if (checkChess(index) == None):

                # Große Rochade
                if not(lRook.getHasMoved()):
                    help = False
                    for i in range(king.getPosition()[1]-1,lRook.getPosition()[1],-1):
                        for piece in pieces:
                            for p in piece.getPossibles():
                                if p == (king.getPosition()[0],i):
                                    help = True
                        if checkField((king.getPosition()[0],i)) != None:
                            help = True           
                    if not(help):
                        move = (T.sumTuple(king.getPosition(),(0,-2)))                 
                        possibles.append(move) 

                # Kleine Rochade
                if not(rRook.getHasMoved()):
                    help = False
                    for i in range(king.getPosition()[1]+1,rRook.getPosition()[1],+1):
                        for piece in pieces:
                            for p in piece.getPossibles():
                                if p == (king.getPosition()[0],i):
                                    help = True
                        if checkField((king.getPosition()[0],i)) != None:
                            help = True           
                    if not(help):
                        move = (T.sumTuple(king.getPosition(),(0,2)))                 
                        possibles.append(move) 
    
    return possibles

# Generiert für jede Figur die possibleMoves (unabhängig von Schach oder nicht Schach)
def allPossibles():
    for piece in allPieces:
        if piece.getType()==pawnB or piece.getType()==pawnW or piece.getType()==pawnStartW or piece.getType()==pawnStartB:
            possibles = []
            position = piece.getPosition()
            possibles.append(T.sumTuple(T.sumTuple(piece.getType().getMovement()[0],(0,1)),position))
            possibles.append(T.sumTuple(T.sumTuple(piece.getType().getMovement()[0],(0,-1)),position))
            piece.setPossibles(possibles)     
        else:    
            piece.setPossibles(possibleMoves(piece))
            
    return None

# Überprüft für einen Bauern ob er Einheiten schmeißen kann und liefert ggf. diese moves zurück
def pawnKills(piece):
    position = piece.getPosition()

    targetPos = []
    possibleKills = []

    if (piece.getType() == pawnB or piece.getType() == pawnStartB) or (piece.getType() != pawnW or piece.getType() != pawnStartW):
        targetPos.append(T.sumTuple(T.sumTuple(piece.getType().getMovement()[0],(0,1)),position))
        targetPos.append(T.sumTuple(T.sumTuple(piece.getType().getMovement()[0],(0,-1)),position))
    
        for target in targetPos:
            if (checkField(target) != None):
                if (checkField(target).getTeam() != piece.getTeam()):
                    possibleKills.append(target)

    return possibleKills

# Resetet die passant Variable für alle Bauern (auf False)
def resetPassants():
    global allPieces
    for piece in allPieces:
        if piece.getType() == pawnStartB or piece.getType() == pawnStartW or piece.getType() == pawnB or piece.getType() == pawnW:
            piece.setPassant(False)

# Überprüft ob sich eine Figur auf dem Feld(position) befindet, wenn ja wird die Figur zurückgeliefert
def checkField(position):
    for piece in allPieces:
        if piece.getPosition() == position:
            return piece
    return None

# Überprüft ob ein Bauer(piece) am Ende angekommen ist und ausgetauscht werden kann
def checkPawnSwap(piece):

    if piece.getTeam() == C.Team.white:
        i = 0
    if piece.getTeam() == C.Team.black:
        i = 7

    L = ['Queen','Rook','Bishop','Knight']

    for j in range(0,8,1):
        if piece.getPosition() == (i,j):
            temp = GamePlayer.addRadioButtonsOption(L,"Choose a piece to replace the pawn:")
            GamePlayer.showOptionsDialog('Choose a piece to replace the pawn')
            match temp.value:
                case 'Queen':
                    piece.setType(queen)
                case 'Rook':
                    piece.setType(rook)
                case 'Bishop':
                    piece.setType(bishop)
                case 'Knight':
                    piece.setType(knight)
                case _:
                    piece.setType(queen) 

            return None


# Optische Darstellung
def paintGame(painter : QPainter):
    global selectedPossibles

    y = len(board)*100
    x = len(board[0])*100
    painter.fillRect(-55, -55, x+110, y+110, Qt.white)
    painter.fillRect(0, 0, x, y, QColor(191, 179, 174))

    #paint checkerboard pattern
    for i in range(0,y,100):
        for j in range(0,x,200):
            z = j
            if (i//100) % 2 == 0:
                z = j+100
                if z > x:
                    break
            painter.fillRect(z, i, 100, 100, QColor(115, 85, 72))  

    pen = painter.pen()
    pen.setWidth(5)
    painter.setPen(pen)

    for i in range(0,x+1,100):
        painter.drawLine(i, 0, i, y)
    for j in range(0,y+1,100):
        painter.drawLine(0, j, x, j)
      
    #Draw options
    painter.fillRect(300,-52,200,38, QColor(255,255,255))
    pen13 = painter.pen()
    pen13.setWidth(3)
    painter.setPen(pen13)
    painter.drawLine(300,-52,500,-52)
    painter.drawLine(300,-15,500,-15)
    painter.drawLine(300,-52,300,-15)
    painter.drawLine(500,-52,500,-15)
    
    font2 = painter.font()
    font2.setBold(True)
    font2.setItalic(True)
    font2.setPixelSize(18)
    painter.setFont(font2)
    painter.drawText(300,-52,200,38, Qt.AlignCenter, "Choose draw options")
    
    font2.setItalic(False)
    font2.setBold(False)
    painter.setFont(font2)
    painter.setPen(pen)
    
    font = painter.font()
    font.setPixelSize(80)
    painter.setFont(font)
    y = len(board)
    x = len(board[0])
    
    #paint pieces
    playerid = GamePlayer.getThisPlayerIndex()
    for i in range(len(board)):
        for j in range(len(board[0])):
            if board[i][j] != '_':
                if playerid == 0:
                    painter.drawText(j*100, i*100, 100, 100, Qt.AlignCenter, board[i][j])
                else:
                    painter.drawText((x-(j+1))*100, (y-(i+1))*100, 100, 100, Qt.AlignCenter, board[i][j])

    #paint board layout
    font3 = painter.font()
    font3.setPixelSize(40)
    painter.setFont(font3)
    N = ['8','7','6','5','4','3','2','1']
    B = ['a','b','c','d','e','f','g','h']
    for i in range(len(board)):
        if playerid == 0:
            painter.drawText(len(board[i]), i*100, -75, 100, Qt.AlignCenter, N[i])
        else:
            painter.drawText(len(board[i]), (y-(i+1))*100, -75, 100, Qt.AlignCenter, N[i])
    for j in range(len(board[i])):
        if playerid == 0:
            painter.drawText(j*100, len(board), 100, 1640, Qt.AlignCenter, B[j]) 
        else:
            painter.drawText((x-(j+1))*100, len(board), 100, 1640, Qt.AlignCenter, B[j])   
    painter.setFont(font)        

    #paint check
    pen4 = painter.pen()
    pen4.setColor(QColor(77, 9, 10))
    painter.setPen(pen4)

    if checkBlack != None:
        for c in checkBlack:
            if playerid == 0:
                j,i = blackKing.getPosition()
                painter.drawRect(i*100+5,j*100+5,90,90)
                j,i = c.getPosition()
                painter.drawRect(i*100+5,j*100+5,90,90)
            else:
                j,i = blackKing.getPosition()
                painter.drawRect((y-(i+1))*100+5,(x-(j+1))*100+5,90,90)
                j,i = c.getPosition()
                painter.drawRect((y-(i+1))*100+5,(x-(j+1))*100+5,90,90)

    if checkWhite != None:
        for c in checkWhite:
            if playerid == 0:
                j,i = whiteKing.getPosition()
                painter.drawRect(i*100+5,j*100+5,90,90)
                j,i = c.getPosition()
                painter.drawRect(i*100+5,j*100+5,90,90)
            else:
                j,i = whiteKing.getPosition()
                painter.drawRect((y-(i+1))*100+5,(x-(j+1))*100+5,90,90)
                j,i = c.getPosition()
                painter.drawRect((y-(i+1))*100+5,(x-(j+1))*100+5,90,90)

    #paint all posiible moves for the selected piece
    for p in selectedPossibles:
        pen3 = painter.pen()
        pen3.setColor(QColor(0, 255, 0))
        if board[p[0]][p[1]] != '_' or p in passantHighlights:
            pen3.setColor(Qt.red)
        painter.setPen(pen3)
        if playerid == 0:
            painter.drawRect(p[1]*100+5,p[0]*100+5,90,90)
        else:
            painter.drawRect((x-(p[1]+1))*100+5,(y-(p[0]+1))*100+5,90,90)

    #highlights the selected piece
    if clickedPos != None:
        i,j = clickedPos
        pen2 = painter.pen()
        pen2.setColor(QColor(0, 0, 255))
        painter.setPen(pen2)
        if playerid == 0:
            painter.drawRect(j*100+5,i*100+5,90,90)
        else:
            painter.drawRect(((x-(j+1))*100)+5,((y-(i+1))*100)+5,90,90)
    painter.setPen(pen)

# Errechnet das geklickte Feld aus der Mausposition und prüft ob es eine valide Eingabe ist
def mouseClick(event : QEvent):
    global pressed
    if event.type() == QEvent.MouseButtonPress:
        y = len(board)-1
        x = len(board[0])-1
        pos = event.pos()
        j = pos.x() // 100
        i = pos.y() // 100
        if not (pos.x() <= 300 or pos.x() >= 500 or pos.y() <= -52 or pos.y() >= -15):
            pressed = True
        if (i < 0 or i > y or j < 0 or j > x):
            return None
        else:
            if playerSymbols[GamePlayer.getCurrentPlayerIndex()] == 'White':
                return (i,j)
            else: 
                return (y-i,x-j)

# Führt die Bewegungen, Auswahl von Figuren usw. aus
def makeMove(event : QEvent):
    global selectedPiece # Aktuell ausgewählte Figur
    global selectedPossibles # Mögliche Züge der aktuell ausgewählten Figur
    global phase # Phase das aktuellen Zugs (1 = Figur auswählen, 2 = Ausgewählte Figur ziehen)
    global clickedPos 
    global checkBlack 
    global checkWhite
    global rochade
    global passantHighlights
    global fiftymoverule
    global pressed
    global offerdraw

    N = ['No','Yes']
    if offerdraw:
        offerdraw = False
        temp2 = GamePlayer.addRadioButtonsOption(N,'Accept draw?')
        GamePlayer.showOptionsDialog('Draw offer')
        print(temp2.value)
        match temp2.value:
            case 'Yes':
                GamePlayer.showMessageLaterForAll("Game Over","Draw! Nobody has won.")
                return -1
            case 'No':
                GamePlayer.showMessageLaterForAll('Information','Draw not accepted')
                return getNextPlayerIndex()
            case _:
                GamePlayer.showMessageLaterForAll('Information','Draw not accepted')
                return getNextPlayerIndex()
            
    a = mouseClick(event)
    if a != None:
        clickedPos = a

    currentPlayerIndex = GamePlayer.getCurrentPlayerIndex()
    playerSymbol = playerSymbols[currentPlayerIndex]

    if fiftymoverule >= 100:
        M = ['Draw','Fiftymovedraw']
    else:
        M = ['Draw']
    if pressed:
        pressed = False
        opt = GamePlayer.addRadioButtonsOption(M,'Choose draw options')
        GamePlayer.showOptionsDialog('Draw options')
        match opt.value:
            case 'Draw':
                offerdraw = True
                return getNextPlayerIndex()
            case 'Fiftymovedraw':
                GamePlayer.showMessageLaterForAll("Game Over","Draw! Nobody has won.")
                return -1   
    #move phase               
    if phase == 2:
        phase = 1
        for p in selectedPossibles:
            if (p == clickedPos):

                # Schlagen
                targetPiece = checkField(p)
                if targetPiece != None:
                    fiftymoverule = 0
                    removePiece(targetPiece)

                # Bewegen 
                oldPosition = selectedPiece.getPosition()
                selectedPiece.setPosition(clickedPos)

                # Prüfen ob eine Rochade ausgeführt wird und ggf. Turm bewegen
                if (selectedPiece.getType() == king):
                    for r in rochade:
                        if selectedPiece.getPosition() == r:
                            if selectedPiece.getTeam() == C.Team.white:
                                if (T.compareTuple(selectedPiece.getPosition(),oldPosition) == -2):
                                    rRookW.setPosition( T.sumTuple(selectedPiece.getPosition(),(0,-1)) )
                                elif (T.compareTuple(selectedPiece.getPosition(),oldPosition) == -1):
                                    lRookW.setPosition( T.sumTuple(selectedPiece.getPosition(),(0,1)) )
                            if selectedPiece.getTeam() == C.Team.black:
                                if (T.compareTuple(selectedPiece.getPosition(),oldPosition) == -2):
                                    rRookB.setPosition( T.sumTuple(selectedPiece.getPosition(),(0,-1)) )
                                elif (T.compareTuple(selectedPiece.getPosition(),oldPosition) == -1):
                                    lRookB.setPosition( T.sumTuple(selectedPiece.getPosition(),(0,1)) )


                resetPassants()                 
                fiftymoverule = fiftymoverule + 1

                # Wenn Bauer zum ersten mal bewegt, Typ ändern und en passant zeug
                if selectedPiece.getType() == pawnStartB:
                    selectedPiece.setType(pawnB)
                    if oldPosition[0]-selectedPiece.getPosition()[0] == -2:
                        selectedPiece.setPassant(True)
                if selectedPiece.getType() == pawnStartW:
                    selectedPiece.setType(pawnW)
                    if oldPosition[0]-selectedPiece.getPosition()[0] == 2:
                        selectedPiece.setPassant(True)
                
                # Wenn König oder Türme bewegt werden hasMoved auf true setzten
                if (selectedPiece.getType() == king) or (selectedPiece.getType() == rook):
                    selectedPiece.setHasMoved(True)

                # Pawn Swap und kill bei en passant
                if selectedPiece.getType()==pawnB or selectedPiece.getType()== pawnW:
                    checkPawnSwap(selectedPiece)
                    if selectedPiece.getPosition() in passantHighlights:
                        if selectedPiece.getTeam() == C.Team.white:
                            pos = T.sumTuple(selectedPiece.getPosition(),(1,0))
                            target = checkField(pos)
                            if target != None:
                                removePiece(target)
                        if selectedPiece.getTeam() == C.Team.black:
                            pos = T.sumTuple(selectedPiece.getPosition(),(-1,0))
                            target = checkField(pos)
                            if target != None:
                                removePiece(target)

                #check if pawn was moved and reset fiftymoverule
                if selectedPiece.getType() == pawnB or selectedPiece.getType() == pawnW or selectedPiece.getType() == pawnStartB or selectedPiece.getType() == pawnStartW:
                    fiftymoverule = 0
                
                #reset all global variables
                selectedPossibles.clear()
                rochade.clear()
                selectedPiece = None
                passantHighlights.clear()
                updateBoard()
                allPossibles()
                
                # Check for Game Over
                result = checkGameOver()
                if fiftymoverule >= 150:
                    result = 'Draw'
                if (result != None):
                    match result:
                        case 'White':
                            GamePlayer.showMessageLaterForAll("Game Over","White has won the game!")
                        case 'Black':
                            GamePlayer.showMessageLaterForAll("Game Over","Black has won the game!")
                        case 'Draw':
                            GamePlayer.showMessageLaterForAll("Game Over","Draw! Nobody has won.")
                    return -1            
                    
                # Prüfen ob Schach
                checkWhite = checkChess('White')
                checkBlack = checkChess('Black')

                return getNextPlayerIndex()

        selectedPossibles.clear()
        selectedPiece = None

    #piece selection phase
    if phase == 1:
        if (checkField(clickedPos) != None):
            # Prüfen ob angeklickte Figur im Team vom ziehenden Spieler ist
            if ((checkField(clickedPos).getTeam()==C.Team.white and playerSymbol == "White") or (checkField(clickedPos).getTeam()==C.Team.black and playerSymbol == "Black")):
                # Figur wird ausgewählt
                selectedPiece = checkField(clickedPos)
                # Mögliche Züge für ausgewählte Figur berechnen
                selectedPossibles = chessPossibles(selectedPiece,possibleMoves(selectedPiece))

                # Rochade checken
                if (selectedPiece.getType() == king):
                    temp = checkRochade(selectedPiece)
                    if temp != None:
                        for x in temp:
                            rochade.append(x)
                            selectedPossibles.append(x)

                # En passant checken
                if (selectedPiece.getType() == pawnB) or (selectedPiece.getType() == pawnW):
                    temp = []
                    temp.append(T.sumTuple(selectedPiece.getPosition(),(0,1)))
                    temp.append(T.sumTuple(selectedPiece.getPosition(),(0,-1)))
                    for t in temp:
                        piece = checkField(t)
                        if (piece != None) and (piece.getType() == pawnB or piece.getType() == pawnW):
                            if piece.getPassant():
                                if (piece.getType() == pawnB or piece.getType() == pawnW):
                                    if (selectedPiece.getTeam() != piece.getTeam()):
                                        if selectedPiece.getTeam() == C.Team.white:
                                            selectedPossibles.append(T.sumTuple(t,(-1,0)))
                                            passantHighlights.append(T.sumTuple(t,(-1,0)))
                                        if selectedPiece.getTeam() == C.Team.black:
                                            selectedPossibles.append(T.sumTuple(t,(1,0)))
                                            passantHighlights.append(T.sumTuple(t,(1,0)))


                phase = 2
                return None
            else:
                clickedPos = None
                return None
        else:
            clickedPos = None
            return None



GamePlayer.run(
    playerTitles=playerSymbols,
)
