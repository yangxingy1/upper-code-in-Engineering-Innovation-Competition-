# coding=utf-8
import socket
def fromWiFiGetTaskInfo(communicationProtocol="udp", WiFiHost ="192.168.1.255", WiFiPort=4210):
    # tcp连接
    if communicationProtocol == "tcp":
        tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpSocket.connect(WiFiHost, WiFiPort)

        while True:
            taskNumberBytes = tcpSocket.recv(1024)
            taskNumberString = taskNumberBytes.decode()
            if len(taskNumberString) == 7:
                tcpSocket.close()

                return taskNumberString

    # udp连接
    elif communicationProtocol == "udp":
        udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udpSocket.bind((WiFiHost, WiFiPort))

        while True:
            taskNumberBytes = udpSocket.recvfrom(1024)[0]
            taskNumberString = taskNumberBytes.decode()
            if len(taskNumberString) == 7:
                udpSocket.close()

                return taskNumberString

if __name__ == "__main__":
    taskNumber = fromWiFiGetTaskInfo(communicationProtocol="udp", WiFiHost ="192.168.1.255", WiFiPort=4210)
    print(taskNumber)