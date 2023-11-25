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
import pickle


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
            recive_block_from(client, adress)
        case default:
            client.close()
    
def recive_block_from(client, adress):
    recived = {
        "ip":adress[0],
        "blockchain":[]
    }
    while True:
        size = client.recv(BLOCKSIZE).decode("utf-8")
        if size == '':
            break
        data = client.recv(int(size))
        recived["chain"].append(pickle.loads(data))
    for past in recived_blockchain:
        if past["ip"] == adress[0]:
            recived_blockchain.remove(past)
            recived_blockchain.append(recived)
            return
    recived_blockchain.append(recived)

    client.close()

def validation_raw_blockchain(blockchain_validation):
    print(blockchain_validation)
    for block in blockchain_validation["chain"]:
        if(block["index"] == 0):
            continue
        new_block = Block(block["index"],block["date"],Transaction(block["data"]["sender"],block["data"]["reciver"],block["data"]["car"]),block["prev_hash"],block["nonce"])
        if(new_block.hash != block["hash"]):
            print("erro",new_block.hash, block["hash"])
    return True



def send_blockchain(node):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((node, DATA_PORT))
    command = "SENDINGBLOCKCHAIN"
    command = f'{len(command):<{COMMANDSIZE}}' + command
    conn.send(command.encode('utf-8'))
    for block in blockchain.chain:
        msg = pickle.dumps(block)
        msg = bytes(f'{len(msg):<{BLOCKSIZE}}', "utf-8") + msg
        conn.send(msg)
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
                cars.append(block.data.car)
            elif block.data.sender == ip:
                cars.remove(block.data.car)
        return cars    

    def tranfes_car(self, reciver, car):
        transaction = Transaction(socket.gethostbyname(socket.gethostname()), reciver, car)
        block = Block(self.get_last_block().index + 1 , str(datetime.datetime.now()), transaction, self.get_last_block().hash)
        self.add_block(block)
        return block.index
    
    def share_blockchain(self):
        for node in nodes:
            print("sending to -> ",node)
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

def edit_block():
    print("availables blocks:")
    for (i, item) in enumerate(blockchain.chain, start=0):
        print(i, item.json())
    index = int(input("block index ->"))
    blockchain.chain[index].data.car = input("new car ->")
    blockchain.chain[index].data.reciver = input("new reciver ->")
    blockchain.chain[index].data.sender = input("new sender ->")

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
    options = [
        "buy new car",
        "transfer car", 
        "see nodes",
        "see my cars", 
        "see my blockchain", 
        "share my blockchain",
        "edit block",
        "check local blockchain",
        "recived_blockchain"
    ]
    print("TranferCarBlockchain")
    for (i, item) in enumerate(options, start=1):
        print(i," - ", item)
    option = int(input())-1
    match options[option]:
        case "buy new car":
            blockchain.buy_new_car()
        case "see nodes":
            print(nodes)
        case "recived_blockchain":
            print(recived_blockchain)
        case "transfer car":
            transfer_car()
        case "see my cars":
            print(blockchain.get_cars_from(socket.gethostbyname(socket.gethostname())))
        case "see my blockchain":
            print(blockchain.json())
        case "share my blockchain":
            blockchain.share_blockchain()
        case "edit block":
            edit_block()
        case "check local blockchain":
            print(blockchain.is_chain_valid())
