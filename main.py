#!/usr/bin/env python3
import socket
import threading
import random
import time


HOST = socket.gethostbyname(socket.gethostname())
PORT = 911
nodes = []

def recive_node():
    reciver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    reciver.bind(("0.0.0.0", PORT))
    print("lintening on port: " + str(PORT) + " for nodes")
    while True:
        data, addr = reciver.recvfrom(32)
        print("Recived: " + data.decode('utf-8') + " from: " + str(addr))
        if addr not in nodes and addr[0] != socket.gethostbyname(socket.gethostname()) and data.decode('utf-8') == "!NODE":
            nodes.append(addr)
        print(nodes)


def send_node():
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    print("sending broadcast on port: " + str(PORT))
    while True:
        time.sleep(10)
        msg = "!NODE"
        sender.sendto(msg.encode('utf-8'), ("255.255.255.255", PORT))






print("Creating node: " + socket.gethostname() + " | IP: " + socket.gethostbyname(socket.gethostname()))
threading.Thread(target=recive_node).start()
threading.Thread(target=send_node).start()
