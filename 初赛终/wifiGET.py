import socket

def fromWiFiGetTaskInfo(communicationProtocol="", WiFiHost="", WiFiPort=0):
    if communicationProtocol == "tcp":
        tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpSocket.connect((WiFiHost, WiFiPort))

        while True:
            taskNumberBytes = tcpSocket.recv(1024)
            taskNumberString = taskNumberBytes.decode()
            if len(taskNumberString) == 7:
                tcpSocket.close()
                # print(taskNumberString)
                return taskNumberString

    elif communicationProtocol == "udp":
        udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udpSocket.bind((WiFiHost, WiFiPort))
        print("begin")
        while True:
            taskNumberBytes = udpSocket.recvfrom(1024)[0]
            taskNumberString = taskNumberBytes.decode()
            if len(taskNumberString) == 7:
                udpSocket.close()
                # print(taskNumberString)
                return taskNumberString
                
a = fromWiFiGetTaskInfo("udp", "192.168.43.255", 4210)
print(a)