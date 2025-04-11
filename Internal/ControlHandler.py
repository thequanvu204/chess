import re
import Internal.Server as Server
from Internal.Session import *
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtNetwork import QTcpSocket, QHostAddress


class ControlHandler:
    def __init__(self, socket : QTcpSocket):
        self.socket = socket
        socket.disconnected.connect(self.handleDisconnect)
        socket.readyRead.connect(self.handleReceive)
        self.handleReceive()

    def handleDisconnect(self):
        controlHandlers.discard(self)

    def help(self):
        self.socket.write(b'Supported commands:\n')
        maxLength = max([ len(x) for x in ControlHandler.commandMap.keys() ])
        for command, descr in sorted(ControlHandler.commandMap.items()):
            self.socket.write(b'  ' + command + b' ' * (maxLength-len(command)) + b'\t' + descr[1] + b'\n')

    def status(self):
        self.socket.write(str(Session.IdCounter).encode() + b' sessions created\n')
        for cont, name in [ (openSessions        , b'open sessions'), \
                            (activeSessions      , b'active sessions'), \
                            (unvalidatedSockets  , b'unvalidated sockets'), \
                            (fileHashDict        , b'cached files'), \
                            (joiningClients      , b'joining clients'), \
                            (blockedAddresses    , b'blocked addresses'), \
                            (controlHandlers     , b'active controller clients')]:
            self.socket.write(str(len(cont)).encode() + b' ' + name + b'\n')

    def listSessions(self, *args):
        for toList in args:
            if toList[0]:
                self.socket.write(str(len(toList[0])).encode() + b' ' + toList[1] + b' sessions:\n')
                self.socket.write(b'  ID\tHost\tGame\n')
                for session in toList[0].values():
                    self.socket.write('  {}\t{}\t{}\n'.format(session.id, session.hostName,
                                                              session.gameName).encode())
            else:
                self.socket.write(b'no ' + toList[1] + b' sessions\n')

    def listAllSessions(self):
        self.listSessions((openSessions, b'open'), (activeSessions, b'active'))

    def listActiveSessions(self):
        self.listSessions((activeSessions, b'active'))

    def listOpenSessions(self):
        self.listSessions((openSessions, b'open'))

    def quitControl(self):
        self.socket.disconnectFromHost()
        controlHandlers.discard(self)

    def killSession(self, id : int):
        for container in [ openSessions, activeSessions ]:
            session = container.get(id, None)
            if session:
                session.abortSession()
                self.socket.write('Session with ID {} has been killed.\n'.format(id).encode())
                return
        self.socket.write('{} is no valid session ID'.format(id).encode())

    def listControllers(self):
        self.socket.write(b'Controller clients:\n')
        for controller in controlHandlers:
            self.socket.write(b'  ' + controller.socket.peerAddress().toString().encode() + b'\n')

    def listBlocked(self):
        for address, count in blockedAddresses.items():
            self.socket.write(str(-count).encode() + b" blocked accesses for address '" + \
                              address.toString().encode() + b"'\n")

    def unblock(self, addressString : str):
        if not blockedAddresses:
            self.socket.write(b'There is no blocked address to unblock.\n')
            return
        address = QHostAddress(addressString)
        if address == QHostAddress():
            self.socket.write(b"'" + addressString.encode() + b"' is no valid host address.\n")
            return
        if blockedAddresses.pop(address, None) == None:
            self.socket.write(b"The address '" + addressString.encode() + b"' is not blocked.\n")
        else:
            self.socket.write(b"The address '" + addressString.encode() + b"' has been unblocked.\n")

    def shutdown(self):
        QCoreApplication.instance().exit(0)

    def restart(self):
        log('restarting server triggered by control access')
        Server.tcpServer.restart()

    commandMap = {
        b'quit'                      : [ quitControl       , b'close this control session'        ],
        b'exit'                      : [ quitControl       , b'close this control session'        ],
        b'help'                      : [ help              , b'list supported commands'           ],
        b'status'                    : [ status            , b'show current status'               ],
        b'list sessions'             : [ listAllSessions   , b'list all active and open sessions' ],
        b'list active sessions'      : [ listActiveSessions, b'list all active sessions'          ],
        b'list open sessions'        : [ listOpenSessions  , b'list all open sessions'            ],
        b'list controllers'          : [ listControllers   , b'list active control clients'       ],
        b'list blocked'              : [ listBlocked       , b'list blocked addresses'            ],
        b'kill session <session_id>' : [ killSession       , b'kill session by its ID'            ],
        b'restart'                   : [ restart           , b'restart this server'               ],
        b'shutdown'                  : [ shutdown          , b'shutdown this server'              ],
        b'unblock <address>'         : [ unblock           , b'unblock a blocked address'         ]
    }

    lookupMap = dict()
    for command, data in commandMap.items():
        parts = command.split()
        for i in range(len(parts)):
            if parts[i][0] == ord('<') and parts[i][-1] == ord('>'):
                parts[i] = int if parts[i].find(b'_id') != -1 else str
        lookupMap[tuple(parts)] = data[0]

    def handleReceive(self):
        for line in self.socket.readAll().data().split(b'\n'):
            if not line:
                continue
            parts = line.split()
            if not parts:
                continue
            args = []
            for i in range(len(parts)):
                if re.match(b'^[0-9]*$', parts[i]):
                    args.append(int(parts[i]))
                    parts[i] = int
            command = ControlHandler.lookupMap.get(tuple(parts), None)
            if command:
                command(self, *args)
                continue
            # check if last is string parameter
            args.append(parts[-1].decode())
            parts[-1] = str
            command = ControlHandler.lookupMap.get(tuple(parts), None)
            if command:
                command(self, *args)
            else:
                self.socket.write(b'Unknown command: ' + line + b'\nType help for listing supported commands.\n')
        if Server.tcpServer.isListening():
            self.socket.write(b'> ')
