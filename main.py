#!/usr/bin/env python3
import datetime
import socket
import threading
import random
import time
from hashlib import sha256
import json
import string


HOST = socket.gethostbyname(socket.gethostname())
BROADCAST_PORT = 911
DATA_PORT = 912
nodes = []

run_threads = True

def recive_node():
    reciver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    reciver.bind(("0.0.0.0", BROADCAST_PORT))
    print("lintening on port: " + str(BROADCAST_PORT) + " for nodes")
    while run_threads:
        data, addr = reciver.recvfrom(5)
        if addr[0] not in nodes and addr[0] != socket.gethostbyname(socket.gethostname()) and data.decode('utf-8') == "!NODE":
            print("Recived: " + data.decode('utf-8') + " from: " + str(addr))
            nodes.append(addr[0])


def send_node():
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    print("sending broadcast on port: " + str(BROADCAST_PORT))
    while run_threads:
        time.sleep(3)
        msg = "!NODE"
        sender.sendto(msg.encode('utf-8'), ("255.255.255.255", BROADCAST_PORT))


def request_blockchain():
    for node in nodes:
        print("requesting blockchain from: " + node)
        threading.Thread(target=request_blockchain_thread(node)).start()


def request_blockchain_thread(node):
    try:
        # connect to node
        request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        request.connect((node, DATA_PORT))

        # send request
        msg = "!BLOCKCHAIN"
        request.send(msg.encode('utf-8'))

        # recive blockchain
        data = request.recv(1024)
        print(data.decode('utf-8'))
        request.close()
    except:
        print("can't connect to node: " + node)


def respond_blockchain():
    reciver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    reciver.bind(("0.0.0.0", DATA_PORT))

    reciver.listen()
    print("lintening on port: " + str(DATA_PORT) + " for blockchain request")

    while True:
        conn, addr = reciver.accept()
        print("recived request for blockchain from: " + str(addr))
        threading.Thread(target=respond_blockchain_thread(conn)).start()

def respond_blockchain_thread(conn):
    conn.send(blockchain.json().encode('utf-8'))
    conn.close()

class Transaction:
    def __init__(self, sender, reciver, car):
        self.sender = sender
        self.reciver = reciver
        self.car = car
    
    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

class Block:
    def __init__(self,index, date ,data, prev_hash):
        self.index = index
        self.date = date
        self.data = data
        self.prev_hash = prev_hash
        self.nonce = 0
        self.hash = self.calc_hash()
    
    def calc_hash(self):
        return sha256(f"{self.index}{self.date}{self.data.json()}{self.prev_hash}{self.nonce}".encode("utf-8")).hexdigest()
    
    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
    def mining_block(self,difficulty=2):
        self.hash = self.calc_hash()
        while self.hash[:difficulty] != "0"*difficulty:
            self.nonce += 1
            self.hash = self.calc_hash()
        print(f"Block {self.index} mined: " + self.hash)

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, str(datetime.datetime(1970,1,1)), Transaction("","",""), "0")
        genesis_block.hash = '0000029b68cd2a04e86102146801b28c0657762955c30356f36219174e0d022f'
        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        new_block.mining_block()
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            prev_block = self.chain[i-1]
            if current_block.hash != current_block.calc_hash():
                return False
            if current_block.prev_hash != prev_block.hash:
                return False
        return True

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
    def buy_new_car(self):
        transaction = Transaction("store", socket.gethostbyname(socket.gethostname()), ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6)))
        block = Block(self.get_last_block().index + 1 , str(datetime.datetime.now()), transaction, self.get_last_block().hash)
        block.mining_block(2)
        self.chain.append(block)
        return block.index
    
    def get_cars_from(self, ip):
        cars = []
        for block in self.chain:
            if block.data.reciver == ip:
                cars.append(block.data.car)
            elif block.data.sender == ip:
                cars.remove(block.data.car)
        return cars    

    def tranfes_car(self, reciver, car):
        transaction = Transaction(socket.gethostbyname(socket.gethostname()), reciver, car)
        block = Block(self.get_last_block().index + 1 , str(datetime.datetime.now()), transaction, self.get_last_block().hash)
        self.add_block(block)
        return block.index



time.sleep(random.randint(0,10))
print("Creating node: " + socket.gethostname() + " | IP: " + socket.gethostbyname(socket.gethostname()))

# starting find node threads
threading.Thread(target=recive_node).start()
threading.Thread(target=send_node).start()


# starting blockchain
blockchain = Blockchain()

for _ in range(0, random.randint(1,5)):
    blockchain.buy_new_car()




# time.sleep(10)
# print("blockchain is valid? " + str(blockchain.is_chain_valid()))
# print(blockchain.json())
# print(nodes)
# print(blockchain.get_cars_from(socket.gethostbyname(socket.gethostname())))


# blockchain.tranfes_car(nodes[0], blockchain.get_cars_from(socket.gethostbyname(socket.gethostname()))[0])
# print(blockchain.json())
# print(blockchain.get_cars_from(socket.gethostbyname(socket.gethostname())))
# print(nodes)
# run_threads = False


time.sleep(5)
threading.Thread(target=respond_blockchain).start()
time.sleep(10)
time.sleep(random.randint(0,15))
request_blockchain()


# can't stop execute
while True:
    time.sleep(10)