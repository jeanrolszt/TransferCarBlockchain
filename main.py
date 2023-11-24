#!/usr/bin/env python3
import datetime
import socket
import sys
import threading
import random
import time
from hashlib import sha256
import json
import string


HOST = socket.gethostbyname(socket.gethostname())
BROADCAST_PORT = 911
DATA_PORT = 912
COMMANDSIZE = 50
BLOCKSIZE = 100

nodes = []
recived_blockchain = []
valides_recived_blockchain = []

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

def recive_data():
    reciver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    reciver.bind((socket.gethostbyname(socket.gethostname()), DATA_PORT))
    reciver.listen()
    while run_threads:
        client, adress = reciver.accept()
        threading.Thread(target=handler_data(client, adress)).start()


def handler_data(client, adress ):
    size = client.recv(COMMANDSIZE).decode("utf-8")
    command = client.recv(int(size)).decode("utf-8")
    print(f'from {adress[0]} -> {command}')
    match command:
        case "SENDINGBLOCKCHAIN":
            recived = {
            "ip":adress[0],
            "chain":[]
            }
            while True:
                size = client.recv(BLOCKSIZE).decode("utf-8")
                if size == '':
                    break
                data = client.recv(int(size)).decode("utf-8")
                recived["chain"].append(json.loads(data))
            recived_blockchain.append(recived)

def validation_raw_blockchain(blockchain_validation):
    print(blockchain_validation)
    for block in blockchain_validation["chain"]:
        if(block["index"] == 0):
            continue
        new_block = Block(block["index"],block["date"],Transaction(block["data"]["sender"],block["data"]["reciver"],block["data"]["car"]),block["prev_hash"],block["nonce"])
        if(new_block.hash != block["hash"]):
            print("erro",new_block.hash, block["hash"])
    return True


def request_blockchain():
    for node in nodes:
        threading.Thread(target=request_blockchain_thread(node)).start()
    for blockchain in recived_blockchain:
        print(validation_raw_blockchain(blockchain))


def request_blockchain_thread(node):
    try:
        print("requesting blockchain from: " + node)
        recived = {
            "ip":node,
            "chain":[]
        }
        # connect to node
        request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        request.connect((node, DATA_PORT))

        # send request
        msg = "!BLOCKCHAIN"
        request.send(msg.encode('utf-8'))
        # recive blockchain
        while True:
            data = request.recv(512)
            if(data.decode('utf-8') == "BLOCKCHAIN!"):
                break
            else:
                recived["chain"].append(json.loads(data.decode('utf-8')))
        recived_blockchain.append(recived)
    except Exception as error:
        print("An exception occurred:", type(error).__name__, error)


def respond_blockchain():
    reciver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    reciver.bind(("0.0.0.0", DATA_PORT))

    reciver.listen(10)
    print("lintening on port: " + str(DATA_PORT) + " for blockchain request")

    while run_threads:
        conn, addr = reciver.accept()
        print("recived request for blockchain from: " + str(addr))
        threading.Thread(target=respond_blockchain_thread(conn)).start()

def respond_blockchain_thread(conn):
    for block in blockchain.chain:
        conn.send(block.json().encode('utf-8'))
        time.sleep(0.01)
    conn.send("BLOCKCHAIN!".encode('utf-8'))
    conn.close()

def send_blockchain(node):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((node, DATA_PORT))
    command = "SENDINGBLOCKCHAIN"
    command = f'{len(command):<{COMMANDSIZE}}' + command
    conn.send(command.encode('utf-8'))
    for block in blockchain.chain:
        msg = block.json()
        msg = f'{len(msg):<{BLOCKSIZE}}' + msg
        conn.send((msg).encode("utf-8"))
    conn.close()

class Transaction:
    def __init__(self, sender, reciver, car):
        self.sender = sender
        self.reciver = reciver
        self.car = car
    
    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

class Block:
    def __init__(self,index, date ,data, prev_hash,nonce=0,hash = ""):
        self.index = index
        self.date = date
        self.data = data
        self.prev_hash = prev_hash
        self.nonce = nonce
        self.hash = hash
    
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
                print("add")
                cars.append(block.data.car)
            elif block.data.sender == ip:
                print("remove")
                cars.remove(block.data.car)
        return cars    

    def tranfes_car(self, reciver, car):
        transaction = Transaction(socket.gethostbyname(socket.gethostname()), reciver, car)
        block = Block(self.get_last_block().index + 1 , str(datetime.datetime.now()), transaction, self.get_last_block().hash)
        self.add_block(block)
        return block.index
    
    def share_blockchain(self):
        for node in nodes:
            threading.Thread(target=send_blockchain(node)).start()

    




print("Creating node: " + socket.gethostname() + " | IP: " + socket.gethostbyname(socket.gethostname()))

# starting find node threads
threading.Thread(target=recive_node).start()
threading.Thread(target=send_node).start()


# starting blockchain
blockchain = Blockchain()
# threading.Thread(target=respond_blockchain).start()
threading.Thread(target=recive_data).start()



def transfer_car():
    reciver = "1"
    while not reciver in nodes:
        print("availables nodes:")
        for (i, item) in enumerate(nodes, start=0):
            print(i, item)
        index = input("reciver index ->")
        reciver = nodes[int(index)]
        if not reciver in nodes:
            print("incorrect")
    
    cars = blockchain.get_cars_from(socket.gethostbyname(socket.gethostname()))
    car = ""
    while not car in cars:
        print("availables cars:")
        for (i, item) in enumerate(cars, start=0):
                print(i, item)
        index = input("car index ->")
        car = cars[int(index)]
        if not car in cars:
            print("incorrect")

    blockchain.tranfes_car(reciver,car)


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




# can't stop execute
while True:
    print("TranferCarBlockchain")
    print("1 - buy new car")
    print("2 - request_blockchain")
    print("3 - see nodes")
    print("4 - recived_blockchain")
    print("5 - transfer car")
    print("6 - see my cars")
    print("7 - my blockchain")
    print("8 - share my blockchain")
    option = input()
    match option:
        case "1":
            blockchain.buy_new_car()
        case "2":
            request_blockchain()
        case "3":
            print(nodes)
        case "4":
            print(recived_blockchain)
        case "5":
            transfer_car()
        case "6":
            print(blockchain.get_cars_from(socket.gethostbyname(socket.gethostname())))
        case "7":
            print(blockchain.json())
        case "8":
            blockchain.share_blockchain()
