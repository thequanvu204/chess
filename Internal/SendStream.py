from PyQt5.QtCore import QByteArray, QBuffer, QDataStream
from PyQt5.QtNetwork import QTcpSocket


def writeInt(socket : QTcpSocket, i : int):
    socket.write(i.to_bytes(4, 'big'))


def readInt(socket : QTcpSocket):
    return int.from_bytes(socket.read(4), 'big')


def writeData(socket : QTcpSocket, data : QByteArray):
    writeInt(socket, len(data))
    socket.write(data)


class SendStream:
    def __init__(self, data : bytes = b''):
        self.byteArray = QByteArray(data)
        self.buffer = QBuffer(self.byteArray)
        self.buffer.open(QBuffer.ReadOnly if data else QBuffer.WriteOnly)
        self.stream = QDataStream(self.buffer)

    def atEnd(self):
        return self.stream.atEnd()

    def data(self):
        return self.byteArray.data()

    def clear(self):
        self.buffer.reset()
        self.byteArray.resize(0)

    def send(self, tcpSocket : QTcpSocket):
        writeInt(tcpSocket, len(self.byteArray))
        tcpSocket.write(self.byteArray)

    def writeBytes(self, data: bytes):
        self.buffer.write(b'\xFE')
        self.stream.writeBytes(data)

    def readBytes(self):
        controlByte = self.buffer.read(1)
        if controlByte != b'\xFE':
            raise Exception('Failed to read bytes from stream')
        return self.stream.readBytes()

    def writeString(self, s: str):
        self.buffer.write(b'\xFD')
        self.stream.writeBytes(s.encode())

    def readString(self):
        controlByte = self.buffer.read(1)
        if controlByte != b'\xFD':
            raise Exception('Failed to read string from stream.')
        return self.stream.readBytes().decode()

    def writeInt(self, i: int):
        self.buffer.write(b'\xFC')
        self.stream.writeInt(i)

    def readInt(self):
        controlByte = self.buffer.read(1)
        if controlByte != b'\xFC':
            raise Exception('Failed to read int from stream.')
        return self.stream.readInt()

    def writeBool(self, b: bool):
        self.buffer.write(b'\xFB' if b else b'\xFA')

    def readBool(self):
        b = self.buffer.read(1)
        if b == b'\xFB':
            return True
        elif b == b'\xFA':
            return False
        else:
            raise Exception('Failed to read bool from stream')


class BoundSendStream(SendStream):
    def __init__(self, socket : QTcpSocket):
        super().__init__()
        self.socket = socket

    def send(self):
        super().send(self.socket)
        super().clear()
