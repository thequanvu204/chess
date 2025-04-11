from bisect import bisect_right
import functools
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QTableWidget, QLabel, QHeaderView, QPushButton

from Internal.Util import makeTableWidgetItem


class GameTableWidget(QTableWidget):

    playLocally = pyqtSignal(str)
    hostGame = pyqtSignal(str)

    def __init__(self, games):
        super().__init__(len(games), 3)
        for row, game in enumerate(games):
            self.setItem(row, 0, makeTableWidgetItem(game))
            button = QPushButton('Play Locally')
            self.setCellWidget(row, 1, button)
            button.clicked.connect(functools.partial(self.playLocally.emit, game))
            button = QPushButton('Host Game')
            self.setCellWidget(row, 2, button)
            button.clicked.connect(functools.partial(self.hostGame.emit, game))
        self.verticalHeader().hide()
        header = self.horizontalHeader()
        header.hide()
        for col in range(self.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch if col == 0 else QHeaderView.ResizeToContents)


class SessionTableWidget(QTableWidget):
    def __init__(self):
        super().__init__(0, 3)
        self.sessions = []
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.setHorizontalHeaderLabels(['Game', 'Host', ''])
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.verticalHeader().hide()

    def resizeEvent(self, event):
        self.label.resize(event.size())
        super().resizeEvent(event)

    sessionJoined = pyqtSignal(int)

    def setConnecting(self):
        self.clearContents()
        self.setError('Connecting ...')

    def setConnected(self):
        self.setError('Currently no session on server.')

    def setError(self, error):
        if error is None or error == '':
            self.label.setText('')
            self.label.hide()
        else:
            self.label.setText(error)
            self.label.show()

    def removeSession(self, id):
        for row in range(self.rowCount()):
            if self.sessions[row].id == id:
                self.removeRow(row)
        if self.rowCount() == 0:
            self.setError('Currently no session on server.')

    def addSession(self, session):
        if self.rowCount() == 0:
            self.setError(None)
        row = bisect_right(self.sessions, session)
        self.sessions.insert(row, session)
        self.insertRow(row)
        self.setItem(row, 0, makeTableWidgetItem(session.game))
        self.setItem(row, 1, makeTableWidgetItem(session.host))
        button = QPushButton('Join')
        self.setCellWidget(row, 2, button)
        button.clicked.connect(lambda: self.sessionJoined.emit(session.id))
        if self.rowCount() == 1:
            self.resizeColumnToContents(2)

    def addSessions(self, sessions):
        for session in sessions:
            self.addSession(session)
