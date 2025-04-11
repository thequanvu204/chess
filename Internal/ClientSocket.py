import traceback
import Internal.Server as Server
from Internal.SendStream import *


class ClientSocket:
    def __init__(self, socket : QTcpSocket, name : str = ''):
        self.name = name
        self.secret = ''
        self.registerGroup = None
        self.socket = socket
        self.receiveHandler = None
        self.disconnectHandler = None
        self.remainingByteCount = 0
        self.receiveBuffer = QByteArray()
        self.sendStream = BoundSendStream(socket)
        socket.disconnected.connect(self.handleDisconnect)
        socket.readyRead.connect(self.handleReceive)

    def disconnectOnError(self):
        self.socket.disconnectFromHost()
        self.handleDisconnect()
        self.setDisconnectHandler(None)

    def handleDisconnect(self):
        if self.disconnectHandler:
            self.disconnectHandler(self)

    def handleReceive(self):
        if Server.tcpServer: # is server
            try:
                self.handleReceiveUnsafe()
            except Exception as e:
                Server.log('session error 1 : ' + str(e) + ' - ' + traceback.format_exc())
                self.disconnectOnError()
        else:
            self.handleReceiveUnsafe()

    def handleReceiveUnsafe(self):
        try:
            while self.socket.bytesAvailable():
                if self.remainingByteCount == 0:
                    if self.socket.bytesAvailable() < 4:
                        self.disconnectOnError()
                    self.remainingByteCount = readInt(self.socket)
                    if self.remainingByteCount < 0 or self.remainingByteCount > (100 << 20):
                        raise Exception('Read invalid receive byte count of ' + str(self.remainingByteCount))
                    self.receiveBuffer.reserve(self.remainingByteCount)
                read = self.socket.read(self.remainingByteCount)
                self.remainingByteCount -= len(read)
                self.receiveBuffer.append(read)
                if self.remainingByteCount == 0:
                    if not self.receiveHandler:
                        self.disconnectOnError()
                        return
                    stream = SendStream(self.receiveBuffer)
                    while not stream.atEnd():
                        self.receiveHandler(stream, self)
                    self.receiveBuffer.resize(0)
        except Server.HandledError:
            pass

    def unregister(self):
        if self.registerGroup:
            self.registerGroup.discard(self)
            self.registerGroup = None
        self.disconnectHandler = None

    def register(self, group):
        self.unregister()
        group.add(self)
        self.registerGroup = group
        def removeFromGroup(_):
            group.discard(self)
        self.disconnectHandler = removeFromGroup

    def setDisconnectHandler(self, disconnectHandler):
        self.unregister()
        self.disconnectHandler = disconnectHandler

    def setReceiveHandler(self, receiveHandler):
        self.receiveHandler = receiveHandler

    def send(self, sendStream : SendStream = None):
        if sendStream:
            sendStream.send(self.socket)
        else:
            self.sendStream.send()

    def disconnect(self):
        self.socket.disconnectFromHost()

    def disconnectWhenWritten(self):
        self.socket.bytesWritten.connect(self.disconnect)
