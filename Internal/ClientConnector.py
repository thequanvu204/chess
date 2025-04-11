import os, glob, re, hashlib
from PyQt5.QtCore import QObject, QIODevice, pyqtSignal, QFileInfo
from PyQt5.QtNetwork import QSslSocket, QSslCertificate, QSslError
import Internal.Client as Client
from Internal.ClientSocket import ClientSocket
from Internal.Server import listenPort, sessionProtocolVersion, sessionClientSecret, certificate
from Internal.SendStream import SendStream
from Internal.GameObject import GameObject


registeredFiles = dict()
def registerFile(file):
    if Client.gameObject is None or not Client.gameObject.loadType == GameObject.LoadAsClient:
        fileInfo = QFileInfo(file)
        if not fileInfo.exists():
            raise Exception('The file "{}" was not found!'.format(file))
        absPath = fileInfo.absoluteFilePath()
        found = registeredFiles.get(absPath)
        if found:
            if found != file:
                raise Exception('You have already registered the file "{}" but as "{}" instead "{}". ' +
                                'Please only register once or use exactly the same path.'.
                                format(absPath, found, file))
        else:
            registeredFiles[absPath] = file
        return file
    else:
        try:
            return registeredFiles[file]
        except KeyError:
            raise Exception('The file "{}" has not been transmitted over network!')


class Session:
    def __init__(self, game, host, id):
        self.game = game
        self.host = host
        self.id   = id

    def __lt__(self, other):
        return (self.game.lower(), self.host.lower()) < (other.game.lower(), other.host.lower())


class ClientConnector(QObject):

    cacheFolder = 'GamePlayerCache'

    def __init__(self):
        super().__init__()
        self.clientSocket = ClientSocket(QSslSocket())
        self.socket = self.clientSocket.socket
        self.sendStream = self.clientSocket.sendStream
        self.clientSocket.setReceiveHandler(self.handleConnectorReceive)
        self.socket.setCaCertificates([QSslCertificate(certificate)])
        self.socket.encrypted.connect(self.handleConnected)
        self.socket.error.connect(self.handleError)
        def sslErrors(errors):
            if [e.error() for e in errors] == [QSslError.HostNameMismatch]:
                self.socket.ignoreSslErrors()
        self.socket.sslErrors.connect(sslErrors)
        self.socket.connectToHostEncrypted(Client.serverSettings.address, listenPort, QIODevice.ReadWrite,
                                           QSslSocket.IPv4Protocol)


    def disconnect(self, waitForDisconnected=False):
        self.socket.disconnectFromHost()
        if waitForDisconnected:
            self.socket.waitForDisconnected()

    def handleConnected(self):
        self.socket.write(str(len(sessionClientSecret)).encode() + sessionClientSecret)
        self.sendStream.writeInt(sessionProtocolVersion)
        self.sendStream.writeString(Client.serverSettings.name)
        self.sendStream.writeString(Client.serverSettings.secret)
        self.sendStream.send()
        self.connected.emit()

    def host(self, returnId=False):
        self.sendStream.writeBytes(b'host')
        self.sendStream.writeString(Client.gameObject.gameName)
        self.sendStream.writeInt(Client.gameObject.minPlayerCount)
        self.sendStream.writeInt(Client.gameObject.maxPlayerCount)
        self.sendStream.writeBool(Client.gameObject.playerCanLeave)
        self.sendStream.writeBool(returnId)
        self.sendStream.send()

    def getSessions(self):
        self.sendStream.writeBytes(b'client')
        self.sendStream.send()

    def join(self, sessionId):
        self.sendStream.writeBytes(b'join')
        self.sendStream.writeInt(sessionId)
        self.sendStream.send()

    def disjoin(self):
        self.sendStream.writeBytes(b'disjoin')
        self.sendStream.send()

    def startSession(self):
        self.sendStream.writeBytes(b'start')
        self.sendStream.writeInt(len(registeredFiles))
        self.fileLoadMap = dict()
        for name in registeredFiles.values():
            fileData = open(name, 'rb').read()
            hash = hashlib.sha1(fileData).hexdigest().encode()
            self.sendStream.writeString(name)
            self.sendStream.writeBytes(hash)
            self.fileLoadMap[hash] = fileData
        self.sendStream.send()

    def sendGameData(self, data, state):
        self.sendStream.writeBytes(b'data')
        self.sendStream.writeInt(len(self.filesToSend))
        for file in self.filesToSend:
            self.sendStream.writeBytes(file)
        self.sendStream.writeBytes(data)
        self.sendStream.writeBytes(state)
        self.sendStream.send()

    def sendUpdate(self, finished, state):
        self.sendStream.writeBytes(b'update')
        self.sendStream.writeBool(finished)
        self.sendStream.writeBytes(state)
        self.sendStream.send()

    def sendMessage(self, title, text):
        self.sendStream.writeBytes(b'message')
        self.sendStream.writeString(title)
        self.sendStream.writeString(text)
        self.sendStream.send()


    connected = pyqtSignal()
    sessionIdReceived = pyqtSignal(int)
    sessionsAdded = pyqtSignal(list)
    sessionRemoved = pyqtSignal(int)
    sessionCanceled = pyqtSignal(str)
    playerJoined = pyqtSignal(str)
    playerDisjoined = pyqtSignal(str)
    playerLeft = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    gameDataRequested = pyqtSignal()
    gameDataReceived = pyqtSignal(bytes, bytes)
    updateReceived = pyqtSignal(bool, bytes)
    messageReceived = pyqtSignal(str, str)

    def handleError(self, error):
        self.socket.disconnectFromHost()
        if type(error) != str:
            if error == QSslSocket.SocketTimeoutError:
                error = 'A timeout error occurred.'
            elif error == QSslSocket.ConnectionRefusedError:
                error = 'The connection has been refused.'
            else:
                error = 'Socket error {} occurred.'.format(int(error))
        self.errorOccurred.emit(error)


    def initCache(self):
        self.cacheMap = dict()
        if os.path.exists(self.cacheFolder):
            for file in glob.glob(self.cacheFolder + '/[0-9a-f]*'):
                match = re.match('.*([0-9a-f]{40,40}).*', file)
                self.cacheMap[match.group(1).encode()] = file
        else:
            os.mkdir(self.cacheFolder)


    def handleConnectorReceive(self, stream: SendStream, socket: ClientSocket):
        global registeredFiles
        command = stream.readBytes()
        if command == b'id':
            self.sessionIdReceived.emit(stream.readInt())
        elif command == b'error':
            self.handleError(stream.readString())
        elif command == b'join':
            self.playerJoined.emit(stream.readString())
        elif command == b'disjoin':
            self.playerDisjoined.emit(stream.readString())
        elif command == b'left':
            self.playerLeft.emit(stream.readString())
        elif command == b'cancel':
            self.sessionCanceled.emit(stream.readString())
        elif command == b'rmsession':
            self.sessionRemoved.emit(stream.readInt())
        elif command == b'addsessions':
            sessions = []
            for i in range(stream.readInt()):
                id = stream.readInt()
                host = stream.readString()
                game = stream.readString()
                sessions.append(Session(game, host, id))
            self.sessionsAdded.emit(sessions)
        elif command == b'start':
            self.initCache()
            self.missing = []
            for i in range(stream.readInt()):
                fileName = stream.readString()
                fileHash = stream.readBytes()
                if fileHash in self.cacheMap:
                    registeredFiles[fileName] = self.cacheMap[fileHash]
                else:
                    self.missing.append((fileName, fileHash))
            self.sendStream.writeBytes(b'data')
            self.sendStream.writeInt(len(self.missing))
            for _, hash in self.missing:
                self.sendStream.writeBytes(hash)
            self.sendStream.send()
        elif command == b'missing':
            self.filesToSend = []
            for i in range(stream.readInt()):
                hash = stream.readBytes()
                self.filesToSend.append(self.fileLoadMap[hash])
            self.gameDataRequested.emit()
        elif command == b'data':
            count = stream.readInt()
            if count != len(self.missing):
                raise Exception('{} files are missing but server sent {}.'.format(len(self.missing), count))
            for name, hash in self.missing:
                nameInCache = self.cacheFolder + '/' + hash.decode() + '.' + QFileInfo(name).suffix()
                open(nameInCache, 'wb').write(stream.readBytes())
                registeredFiles[name] = nameInCache
            data = stream.readBytes()
            state = stream.readBytes()
            self.gameDataReceived.emit(data, state)
        elif command == b'update':
            finished = stream.readBool()
            state = stream.readBytes()
            self.updateReceived.emit(finished, state)
        elif command == b'message':
            title = stream.readString()
            text = stream.readString()
            self.messageReceived.emit(title, text)
