from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QTableWidget, QVBoxLayout, QStyle, QComboBox, QHeaderView, QLabel
from Internal.Util import makeToolButton, makeTableWidgetItem


class PlayerTableWidget(QTableWidget):

    class MoveArrows(QWidget):
        # callback is called with self and True for up and False for down
        def __init__(self, callback, noUpper=False, noLower=False):
            super().__init__()
            self.setLayout(QVBoxLayout())
            self.layout().setContentsMargins(0, 0, 0, 0)
            self.layout().setSpacing(0)
            if not noUpper:
                self.upper = makeToolButton('▲')
                self.layout().addWidget(self.upper, 0, Qt.AlignCenter)
                self.upper.clicked.connect(lambda: callback(self, True))
            if not noLower:
                self.lower = makeToolButton('▼')
                self.layout().addWidget(self.lower, 0, Qt.AlignCenter)
                self.lower.clicked.connect(lambda: callback(self, False))

    def handleMoveButtonClick(self, moveArrows, up):
        for row in range(self.rowCount()):
            if self.cellWidget(row, self.moveArrowsCol) == moveArrows:
                break
        rows = (row, row-1 if up else row+1)
        items = [self.takeItem(row, self.playerCol) for row in rows]
        for row, item in zip(reversed(rows), items):
            self.setItem(row, self.playerCol, item)
        if self.titles and self.titlesAreChoosable:
            indexes = [self.cellWidget(row, self.titleCol).currentIndex() for row in rows]
            for row, index in zip(reversed(rows), indexes):
                self.cellWidget(row, self.titleCol).setCurrentIndex(index)

    def getNextTitle(self):
        usedTitles = self.getTitles()
        for title in self.titles:
            if title not in usedTitles:
                return title

    def handleTitleChanged(self, comboBox, title):
        rowCount = self.rowCount()
        for row in range(rowCount):
            if self.cellWidget(row, self.titleCol) == comboBox:
                break
        index = comboBox.currentIndex()
        for i in range(rowCount):
            if i != row:
                widget = self.cellWidget(i, self.titleCol)
                if widget.currentIndex() == index:
                    widget.setCurrentText(self.getNextTitle())

    playerRemoved = pyqtSignal(str)
    rowCountChanged = pyqtSignal(int)

    def handleRowCountChanged(self, rowCount):
        if self.playersAreMovable:
            self.setColumnHidden(self.moveArrowsCol, rowCount < 2)
        if self.playersAreRemovable:
            self.setColumnHidden(self.removeCol, rowCount <= self.minPlayerCount)

    def handlePlayerRemoved(self, button):
        for row in range(self.rowCount()):
            if self.cellWidget(row, self.removeCol) == button:
                break
        if self.playerRemoveCallback is not None and not \
            self.playerRemoveCallback(self.item(row, self.playerCol).text()):
            return
        self.removePlayerByRow(row)

    def removePlayer(self, player):
        for row in range(self.rowCount()):
            if self.item(row, self.playerCol).text() == player:
                self.removePlayerByRow(row)
                break

    def removePlayerByRow(self, row):
        rowCount = self.rowCount()
        if self.titles and not self.titlesAreChoosable:
            for i in range(rowCount-1, row, -1):
                self.item(i, self.titleCol).setText(self.item(i-1, self.titleCol).text())
        player = self.item(row, self.playerCol).text()
        self.removeRow(row)
        rowCount -= 1
        if rowCount > 0:
            if row == 0:
                self.cellWidget(0, self.moveArrowsCol).upper.hide()
            if row == rowCount:
                self.cellWidget(rowCount-1, self.moveArrowsCol).lower.hide()
        self.playerRemoved.emit(player)

    def appendPlayer(self, player):
        row = self.rowCount()
        if self.titles is None:
            title = None
        elif self.titlesAreChoosable:
            title = self.getNextTitle()
        else:
            title = self.titles[row]
        self.insertRow(row)
        if self.playersAreMovable:
            moveButtons = self.MoveArrows(self.handleMoveButtonClick)
            self.setCellWidget(row, self.moveArrowsCol, moveButtons)
            moveButtons.lower.hide()
            if row == 0:
                moveButtons.upper.hide()
            else:
                self.cellWidget(row-1, self.moveArrowsCol).lower.show()
        flags = Qt.ItemIsEnabled
        if self.playersAreEditable:
            flags |= Qt.ItemIsEditable
        self.setItem(row, self.playerCol, makeTableWidgetItem(player, flags))
        if self.titles is not None:
            if self.titlesAreChoosable:
                comboBox = QComboBox()
                comboBox.setStyleSheet('QComboBox{background: white;}')
                comboBox.setFrame(False)
                comboBox.addItems(self.titles)
                comboBox.setCurrentIndex(row)
                comboBox.currentTextChanged.connect(lambda text: self.handleTitleChanged(comboBox, text))
                self.setCellWidget(row, self.titleCol, comboBox)
            else:
                self.setItem(row, self.titleCol, makeTableWidgetItem(title))
        if self.playersAreRemovable:
            button = makeToolButton(QStyle.SP_TrashIcon)
            self.setCellWidget(row, self.removeCol, button)
            button.clicked.connect(lambda: self.handlePlayerRemoved(button))

    moveArrowsCol = 0
    playerCol = 1
    titleCol = 2
    removeCol = 3

    def __init__(self, players, titles, minPlayerCount=0, playersAreMovable=False, playersAreEditable=False, \
                 playersAreRemovable=False, titlesAreChoosable=False, playerRemoveCallback=None):
        super().__init__(0, 4)
        self.titles = titles
        self.minPlayerCount = minPlayerCount
        self.playersAreMovable = playersAreMovable
        self.playersAreEditable = playersAreEditable
        self.playersAreRemovable = playersAreRemovable
        self.titlesAreChoosable = titlesAreChoosable
        self.playerRemoveCallback = playerRemoveCallback
        for player in players:
            self.appendPlayer(player)
        self.setColumnHidden(self.titleCol, titles is None)
        header = self.horizontalHeader()
        header.hide()
        for col in range(self.columnCount()):
            stretch = (col in [self.playerCol, self.titleCol])
            header.setSectionResizeMode(col, QHeaderView.Stretch if stretch else QHeaderView.ResizeToContents)
        self.verticalHeader().hide()
        emitRowCount = lambda: self.rowCountChanged.emit(self.rowCount())
        self.model().rowsInserted.connect(emitRowCount)
        self.model().rowsRemoved.connect(emitRowCount)
        self.rowCountChanged.connect(self.handleRowCountChanged)
        self.handleRowCountChanged(self.rowCount())
        self.overlayLabel = QLabel(self)
        self.overlayLabel.setAlignment(Qt.AlignCenter)
        self.overlayLabel.hide()

    def resizeEvent(self, event):
        self.overlayLabel.resize(event.size())
        super().resizeEvent(event)

    def setOverlayLabel(self, text):
        if text is None or text == '':
            self.overlayLabel.setText('')
            self.overlayLabel.hide()
        else:
            self.overlayLabel.setText(text)
            self.overlayLabel.show()

    def getPlayers(self):
        return [ self.item(row, self.playerCol).text() for row in range(self.rowCount()) ]

    def getTitles(self):
        if self.titles is None:
            return None
        getTitle = lambda row: self.cellWidget(row, self.titleCol).currentText() if (self.titlesAreChoosable) \
                               else self.item(row, self.titleCol).text()
        return [ getTitle(row) for row in range(self.rowCount()) ]
