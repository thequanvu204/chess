#!/usr/bin/env python3

import sys, signal, os, glob, re, subprocess, traceback, random
from datetime import datetime
from PyQt5.QtCore import QCoreApplication, QTimerEvent
from PyQt5.QtNetwork import QHostAddress, QTcpServer, QSsl, QSslSocket, QSslCertificate, QSslKey, QSslError
import Internal.Server as Server
from Internal.SendStream import *
from Internal.ClientSocket import ClientSocket
from Internal.Session import *
from Internal.ControlHandler import ControlHandler


signal.signal(signal.SIGINT, signal.SIG_DFL)


if os.path.exists(cacheFolder):
    for file in glob.glob(cacheFolder + '/[0-9a-f]*'):
        match = re.match('.*([0-9a-f]{40,40})$', file)
        if match:
            try:
                fileHashDict[match.group(1).encode()] = open(file, 'rb').read()
            except Exception as e:
                print("Could not read file '" + file + '": ' + str(e))
                sys.exit(1)
else:
    os.mkdir(cacheFolder)


app = QCoreApplication(sys.argv)


ctrlSecret = ''
argsSecrets = list(filter(lambda x: not x.startswith('--') and 4 <= len(x) <= 9, sys.argv[1:]))
if len(argsSecrets) > 0:
    ctrlSecret = argsSecrets[0]
else:
    a = ord('a')
    letters = [chr(i) for i in range(a, a + 26)]
    vocals = ['a', 'e', 'i', 'o', 'u', 'y']
    consonants = list(letters)
    for v in vocals:
        consonants.remove(v)
    for i in range(5):
        ctrlSecret += random.choice(vocals if (i & 1) else consonants)
    log('using random ctrl secret: ' + ctrlSecret)

ctrlSecret = ctrlSecret.encode()


def handleValidatedReceive(stream : SendStream, socket : ClientSocket):
    socket.unregister()
    protocolVersion = stream.readInt()
    if protocolVersion != sessionProtocolVersion:
        if protocolVersion < sessionProtocolVersion:
            text = 'Client uses outdated protocol version. Please update the client.'
        else:
            text = 'Client uses newer protocol version. Please inform the server provider that the server is outdated.'
        stream = socket.sendStream
        stream.writeBytes(b'error')
        stream.writeString(text)
        stream.send()
        socket.disconnectWhenWritten()
        raise HandledError()
    socket.name = stream.readString()
    socket.secret = stream.readString()
    Session.startHandling(stream, socket)


class MyServer(QTcpServer):
    def __init__(self):
        super().__init__()
        self.timerDict = dict()
        self.lastLogMinute = datetime.now().minute // 10
        self.watchDogTimer = self.startTimer(30000)
        self.restartTimer = None
        self.testSocket = QSslSocket()
        self.testSocket.setCaCertificates([QSslCertificate(certificate)])
        def onTestSuccess():
            if self.restartTimer:
                self.killTimer(self.restartTimer)
                self.restartTimer = None
            minute = datetime.now().minute // 10
            if minute != self.lastLogMinute:
                log('server ok, tot: ' + str(Session.IdCounter) + ' open: ' + str(len(openSessions)) +
                    ' active: ' + str(len(activeSessions)) + ' unv: ' + str(len(unvalidatedSockets)) +
                    ' cached: ' + str(len(fileHashDict)) + ' join: ' + str(len(joiningClients)) +
                    ' blockd: ' + str(len(blockedAddresses)) + ' ctrl: ' + str(len(controlHandlers)))
                self.lastLogMinute = minute
            self.testSocket.disconnectFromHost()
        self.testSocket.errorOccurred.connect(lambda e: log(f'test socket connection error: {e}'))
        self.testSocket.sslErrors.connect(self.handleTestSocketSslErrors)
        self.testSocket.encrypted.connect(onTestSuccess)
        self.newConnection.connect(self.handleNewConnection)
        self.destroyed.connect(self.logClose)

    def handleTestSocketSslErrors(self, errors):
        if all(e.error() == QSslError.HostNameMismatch for e in errors):
            self.testSocket.ignoreSslErrors()
        else:
            log(f'test socket ssl errors: {", ".join(e.errorString() for e in errors)}')

    def logClose(self):
        log('Server deleted - ' + traceback.format_exc())

    def restart(self):
        self.close()
        subprocess.Popen(sys.argv, close_fds=True)
        app.exit(0)

    def timerEvent(self, event : QTimerEvent):
        id = event.timerId()
        if id == self.restartTimer:
            log('restarting server because test socket cannot connect')
            self.restart()
        elif id == self.watchDogTimer:
            if self.testSocket.state() == QSslSocket.UnconnectedState and not self.restartTimer:
                self.restartTimer = self.startTimer(30000)
                self.testSocket.connectToHostEncrypted('localhost', listenPort, QSslSocket.ReadWrite, QSslSocket.IPv4Protocol)
        else:
            self.killTimer(id)
            socket = self.timerDict[id]
            socket.close()
            socket.deleteLater()
            del self.timerDict[id]
            if socket in unvalidatedSockets:
                unvalidatedSockets.discard(socket)

    def incomingConnection(self, handle):
        socket = QSslSocket()
        if socket.setSocketDescriptor(handle):
            if blockedAddresses.get(socket.peerAddress(), 1) <= 0:
                socket.close()
                return
            def handleSslErrors(errors, socket = socket):
                address = socket.peerAddress().toString()
                log('SSL errors for peer ' + address + ' : ' + ', '.join([x.errorString() for x in errors]))
            socket.sslErrors.connect(handleSslErrors)
            socket.setLocalCertificate(QSslCertificate(certificate))
            socket.setPrivateKey(QSslKey(privatekey, QSsl.Rsa))
            socket.startServerEncryption()
            self.addPendingConnection(socket)

    def handleNewConnection(self):
        while True:
            socket = self.nextPendingConnection()
            if not socket:
                return
            timerId = self.startTimer(30000)
            self.timerDict[timerId] = socket
            def handleNewEncryptedConnection(socket = socket, timerId = timerId):
                unvalidatedSockets.add(socket)
                def handleDisconnect(socket = socket):
                    unvalidatedSockets.discard(socket)
                socket.disconnected.connect(handleDisconnect)
                def handleReceive(socket = socket, timerId = timerId):
                    if timerId:
                        self.killTimer(timerId)
                    unvalidatedSockets.discard(socket)
                    socket.disconnected.disconnect(handleDisconnect)
                    def blockAddress():
                        address = socket.peerAddress()
                        remaining = blockedAddresses.setdefault(address, 3)
                        blockedAddresses[address] -= 1
                        if remaining == 1:  # was last trial
                            socket.write(b"your address '" + address.toString().encode() + b"' has been blocked\n")
                            log("block address '" + address.toString() + "'")
                        socket.disconnectFromHost()
                    try:
                        secretLen = int(socket.read(1))
                    except:
                        blockAddress()
                        return
                    secret = socket.read(secretLen)
                    if secret == ctrlSecret:
                        blockedAddresses.pop(socket.peerAddress(), None)
                        controlHandlers.add(ControlHandler(socket))
                        socket.readyRead.disconnect(handleReceive)
                    elif secret == sessionClientSecret:
                        blockedAddresses.pop(socket.peerAddress(), None)
                        clientSocket = ClientSocket(socket)
                        clientSocket.register(validatedSockets)
                        clientSocket.setReceiveHandler(handleValidatedReceive)
                        socket.readyRead.disconnect(handleReceive)
                        clientSocket.handleReceive()
                    else:
                        address = socket.peerAddress()
                        remaining = blockedAddresses.setdefault(address, 3)
                        blockedAddresses[address] -= 1
                        if remaining == 1: # was last trial
                            socket.write(b"your address '" + address.toString().encode() + b"' has been blocked\n")
                            log("block address '" + address.toString() + "'")
                        socket.disconnectFromHost()
                        return
                socket.readyRead.connect(handleReceive)

            if socket.isEncrypted():
                handleNewEncryptedConnection()
            else:
                socket.encrypted.connect(handleNewEncryptedConnection)

Server.tcpServer = MyServer()

hostAddress = QHostAddress.AnyIPv4 if ('-a' in sys.argv or '--all-interfaces' in sys.argv) else QHostAddress.LocalHost

if not Server.tcpServer.listen(hostAddress, listenPort):
    log('could not bind to port - exiting')
    print('Could not listen.')
    sys.exit(1)
else:
    log('server started')
    try:
        sys.exit(app.exec())
    except Exception as e:
        log('crash - ' + str(e) + ' - ' + traceback.format_exc())
        sys.exit(1)
