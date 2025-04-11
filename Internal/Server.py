from datetime import datetime


sessionServer = 'agschoemer.zdv.uni-mainz.de'
listenPort = 55555

tcpServer = None

sessionProtocolVersion = 5

test               = set()
joiningClients     = set()
openSessions       = dict() # maps session id to session
activeSessions     = dict() # maps session id to session
unvalidatedSockets = set()
validatedSockets   = set()
controlHandlers    = set()
blockedAddresses   = dict() # maps address to remaining trial count
fileHashDict       = dict()

cacheFolder = 'GameSessionServerCache'

logFile = 'GameSessionServer.log'


# 9 bytes at maximum
sessionClientSecret = bytes.fromhex('d3 25 76 55 4b 4a 01 99 06')


# generate certificate and key by calling in Internal folder
#   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -subj /CN=* -nodes -days 10000
# and if you want to safe inline encode base64 by
#   cat ... | base64 -w100 | sed "s/.*/    '\0'\\\/"

certificate = open('Internal/cert.pem', 'rb').read()

privatekey = open('Internal/key.pem', 'rb').read()


def log(message):
    open(logFile, 'a').write(str(datetime.now()) + ' : ' + message + '\n')


class HandledError(Exception):
    def __init__(self):
        super().__init__()
