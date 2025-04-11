import traceback
from PyQt5.QtCore import QTimer
from Internal.SendStream import *
from Internal.ClientSocket import ClientSocket

from Internal.Server import *

class Session:
    StateOpen   = 1
    StateInit   = 2
    StateActive = 3
    StateDone   = 4

    IdCounter = 0

    class InitData:
        def __init__(self, clientCount : int):
            self.missingClientHashes = dict()
            self.missingClientCount = clientCount
            self.leftClients = []
            self.missingFileHashes = []
            self.gameData = None
            self.state = None

    def __init__(self, stream: SendStream, hostSocket: ClientSocket):
        self.gameName        = stream.readString()
        self.minPlayers      = stream.readInt()
        self.maxPlayers      = stream.readInt()
        self.playerCanLeave  = stream.readBool()
        returnId             = stream.readBool()
        self.hostSocket      = hostSocket
        self.hostName        = hostSocket.name
        self.secret          = hostSocket.secret
        self.clients         = { hostSocket.name : hostSocket } # map names to sockets
        self.state           = Session.StateOpen
        self.lastAnnounced   = None
        self.announcePending = False
        self.init            = None # holds during the init state some objects
        Session.IdCounter += 1
        self.id = Session.IdCounter

        if returnId:
            hostSocket.sendStream.writeBytes(b'id')
            hostSocket.sendStream.writeInt(self.id)
            hostSocket.send()

        hostSocket.setReceiveHandler(self.handleHostReceive)
        hostSocket.setDisconnectHandler(self.handleHostDisconnect)
        self.announce()

    def abortSession(self):
        for client in self.clients.values():
            client.setDisconnectHandler(None)
            client.disconnectOnError()
        if self.id in openSessions:
            del openSessions[self.id]
        if self.id in activeSessions:
            del activeSessions[self.id]

    def handleHostDisconnect(self, socket : ClientSocket):
        self.announceLater()
        del self.clients[self.hostName]
        if self.state == Session.StateOpen:
            stream = SendStream()
            stream.writeBytes(b'cancel')
            stream.writeString('The host has been disconnected.')
            for socket in self.clients.values():
                socket.send(stream)
                socket.register(joiningClients)
                socket.setReceiveHandler(self.handleJoiningReceive)
            self.state = Session.StateDone
            del openSessions[self.id]
        elif self.init:
            if self.init.missingFileHashes: # host disconnected before sending files
                self.handleErrorWhenOpen('Connection to host has been lost.')
            else:
                self.handleClientLeftDuringInit(socket)
        else:
            pass # this case should not occur

    def handleClientLeftDuringInit(self, socket):
        self.init.leftClients.append(socket)
        if len(self.clients) < self.minPlayers:
            self.handleErrorWhenOpen('The session has been aborted because players left so that the '
                                     'player count fell below the minimum of ' + str(self.minPlayers) + '.')

    def handleErrorWhenOpen(self, text):
        stream = SendStream()
        stream.writeBytes(b'error')
        stream.writeString(text)
        for socket in self.clients.values():
            socket.send(stream)
            socket.disconnectWhenWritten()
        if self.id in openSessions:
            del openSessions[self.id]

    def sendMissingClientData(self, clientSocket : ClientSocket, missingHashes):
        sendStream = clientSocket.sendStream
        sendStream.writeBytes(b'data')
        sendStream.writeInt(len(missingHashes))
        for hash in missingHashes:
            file = fileHashDict.get(hash, None)
            if not file:
                clientSocket.socket.disconnect()
                return
            sendStream.writeBytes(file)
        sendStream.writeBytes(self.init.gameData)
        sendStream.writeBytes(self.init.state)
        sendStream.send()
        self.init.missingClientCount -= 1
        if self.init.missingClientCount == 0:
            self.state = Session.StateActive
            leftClients = self.init.leftClients
            self.init = None
            for clientSocket in leftClients:
                self.handleClientDisconnect(clientSocket)

    def handleHostReceive(self, stream : SendStream, clientSocket : ClientSocket):
        try:
            command = stream.readBytes()
            if command == b'start':
                self.state = Session.StateInit
                # forward file list to clients
                data = stream.data()
                for socket in self.clients.values():
                    if socket != self.hostSocket:
                        writeData(socket.socket, data)
                self.init = Session.InitData(len(self.clients)-1)
                for i in range(stream.readInt()):
                    stream.readString() # filename
                    fileHash = stream.readBytes()
                    if fileHash not in fileHashDict:
                        self.init.missingFileHashes.append(fileHash)
                sendStream = clientSocket.sendStream
                sendStream.writeBytes(b'missing')
                sendStream.writeInt(len(self.init.missingFileHashes))
                for hash in self.init.missingFileHashes:
                    sendStream.writeBytes(hash)
                sendStream.send()
            elif command == b'data':
                count = stream.readInt()
                if count != len(self.init.missingFileHashes):
                    self.abortSession()
                    return
                for hash in self.init.missingFileHashes:
                    fileData = stream.readBytes()
                    fileHashDict[hash] = fileData
                    f = open(cacheFolder + '/' + hash.decode(), 'wb')
                    f.write(fileData)
                self.init.missingFileHashes = None
                self.init.gameData = stream.readBytes()
                self.init.state = stream.readBytes()
                for clientSocket, missingHashes in self.init.missingClientHashes.items():
                    self.sendMissingClientData(clientSocket, missingHashes)
                activeSessions[self.id] = self
                self.state = Session.StateActive
                del openSessions[self.id]
                self.hostSocket.setDisconnectHandler(self.handleClientDisconnect)
                self.hostSocket.setReceiveHandler(self.handleClientReceive)
        except Exception as e:
            self.abortSession()
            log('session error 2 : ' + str(e) + ' - ' + traceback.format_exc())
            raise e

    def handleClientDisconnect(self, socket : ClientSocket):
        del self.clients[socket.name]
        if self.state == Session.StateOpen:
            if len(self.clients) < self.maxPlayers:
                self.announceLater()
            stream = SendStream()
            stream.writeBytes(b'disjoin')
            stream.writeString(socket.name)
            stream.send(self.hostSocket.socket)
        elif self.state == Session.StateInit:
            if socket in self.init.missingClientHashes:
                self.init.missingClientCount -= 1
                del self.init.missingClientHashes[socket]
            self.handleClientLeftDuringInit(socket)
        else: # game phase
            sendStream = SendStream()
            sendStream.writeBytes(b'left')
            sendStream.writeString(socket.name)
            for socket in self.clients.values():
                socket.send(sendStream)
            if not self.clients and self.id in activeSessions:
                del activeSessions[self.id]

    def handleClientReceive(self, stream : SendStream, socket : ClientSocket):
        try:
            command = stream.readBytes()
            if command == b'update':
                finished = stream.readBool()
                stream.readBytes() # state
                data = stream.data()
                for othername, othersocket in self.clients.items():
                    if othername != socket.name:
                        writeData(othersocket.socket, data)
                        if finished:
                            othersocket.setDisconnectHandler(None)
                            othersocket.disconnectWhenWritten()
                if finished:
                    socket.setDisconnectHandler(None)
                    socket.disconnect()
                    del activeSessions[self.id]
            elif command == b'message':
                stream.readString() # title
                stream.readString() # text
                data = stream.data()
                for othername, othersocket in self.clients.items():
                    if othername != socket.name:
                        writeData(othersocket.socket, data)
            elif command == b'disjoin':
                if len(self.clients) == self.maxPlayers:
                    self.announceLater()
                self.handleClientDisconnect(socket)
                socket.register(joiningClients)
                socket.setReceiveHandler(self.handleJoiningReceive)
            elif command == b'data':
                count = stream.readInt()
                if not self.init:
                    socket.socket.disconnect()
                    return
                missingClientHashes = []
                for i in range(count):
                    missingClientHashes.append(stream.readBytes())
                if self.init.missingFileHashes is None:
                    self.sendMissingClientData(socket, missingClientHashes)
                else:
                    self.init.missingClientHashes[socket] = missingClientHashes
        except Exception as e:
            self.abortSession()
            log('session error 3 : ' + str(e) + ' - ' + traceback.format_exc())
            raise HandledError()

    def announce(self):
        self.announcePending = False
        stream = None
        if self.state == Session.StateOpen and len(self.clients) < self.maxPlayers and \
           self.hostSocket.socket.state() == QTcpSocket.ConnectedState:
            if not self.lastAnnounced:
                self.lastAnnounced = True
                stream = SendStream()
                stream.writeBytes(b'addsessions')
                stream.writeInt(1)
                stream.writeInt(self.id)
                stream.writeString(self.hostName)
                stream.writeString(self.gameName)
        else:
            if self.lastAnnounced:
                self.lastAnnounced = False
                stream = SendStream()
                stream.writeBytes(b'rmsession')
                stream.writeInt(self.id)
        if not stream:
            return
        for socket in joiningClients:
            if socket.secret == self.secret:
                socket.send(stream)
        for session in openSessions.values():
            if session != self:
                for socket in session.clients.values():
                    if socket.name != session.hostName and socket.secret == self.secret:
                        socket.send(stream)

    def announceLater(self):
        if not self.announcePending:
            self.announcePending = True
            QTimer.singleShot(0, self.announce)

    def addClient(self, socket : ClientSocket):
        if self.clients.get(socket.name, None): # client name already used
            return 'The client name ' + socket.name + ' is already used in this session.'
        if len(self.clients) + 1 > self.maxPlayers:
            return 'The maximum client count has been reached for this session.'
        if len(self.clients) + 1 == self.maxPlayers:
            self.announceLater()
        joiningClients.discard(socket)
        socket.setDisconnectHandler(self.handleClientDisconnect)
        socket.setReceiveHandler(self.handleClientReceive)
        self.clients[socket.name] = socket
        sendStream = self.hostSocket.sendStream
        sendStream.writeBytes(b'join')
        sendStream.writeString(socket.name)
        sendStream.send()
        return None

    @staticmethod
    def handleJoiningReceive(stream: SendStream, socket: ClientSocket):
        command = stream.readBytes()
        if command == b'host':
            socket.unregister()
            session = Session(stream, socket)
            openSessions[session.id] = session
        elif command == b'join':
            sessionId = stream.readInt()
            session = openSessions.get(sessionId, None)
            if session:
                error = session.addClient(socket)
                if not error:
                    return
            else:
                error = 'The session has been canceled.'
            sendStream = SendStream()
            sendStream.writeBytes(b'cancel')
            sendStream.writeString(error)
            sendStream.send(socket.socket)
        elif command == b'client':
            freeSessions = [x for x in openSessions.values() if len(x.clients) < x.maxPlayers and
                            socket.secret == x.secret]
            sendStream = socket.sendStream
            sendStream.writeBytes(b'addsessions')
            sendStream.writeInt(len(freeSessions))
            for session in freeSessions:
                sendStream.writeInt(session.id)
                sendStream.writeString(session.hostName)
                sendStream.writeString(session.gameName)
            sendStream.send()

    @classmethod
    def startHandling(cls, stream: SendStream, socket: ClientSocket):
        socket.register(joiningClients)
        socket.setReceiveHandler(cls.handleJoiningReceive)
        if not stream.atEnd():
            cls.handleJoiningReceive(stream, socket)
