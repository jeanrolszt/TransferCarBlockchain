#!/usr/bin/env python3
import datetime
import socket
import threading
import random
import time
from hashlib import sha256
import json


HOST = socket.gethostbyname(socket.gethostname())
PORT = 911
nodes = []

run_threads = True

def recive_node():
    reciver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    reciver.bind(("0.0.0.0", PORT))
    print("lintening on port: " + str(PORT) + " for nodes")
    while run_threads:
        data, addr = reciver.recvfrom(32)
        if addr not in nodes and addr[0] != socket.gethostbyname(socket.gethostname()) and data.decode('utf-8') == "!NODE":
            print("Recived: " + data.decode('utf-8') + " from: " + str(addr))
            nodes.append(addr)


def send_node():
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    print("sending broadcast on port: " + str(PORT))
    while run_threads:
        time.sleep(3)
        msg = "!NODE"
        sender.sendto(msg.encode('utf-8'), ("255.255.255.255", PORT))


class Transaction:
    def __init__(self, sender, reciver, car):
        self.sender = sender
        self.reciver = reciver
        self.car = car

class Block:
    def __init__(self,index, date ,data, prev_hash):
        self.index = index
        self.date = date
        self.data = data
        self.prev_hash = prev_hash
        self.nonce = 0
        self.hash = self.calc_hash()
    
    def calc_hash(self):
        return sha256((str(self.index) + str(self.date) + str(self.data) + str(self.prev_hash) + str(self.nonce)).encode("utf-8")).hexdigest()
    
    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
    def mining_block(self):
        difficulty = 5
        while self.hash[:difficulty] != "0"*difficulty:
            self.nonce += 1
            self.hash = self.calc_hash()
        print("Block mined: " + self.hash)

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, str(datetime.datetime(1970,1,1)), "Genesis Block", "0")
        genesis_block.mining_block()
        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        new_block.prev_hash = self.get_last_block().hash
        new_block.hash = new_block.calc_hash()
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
    

    # def add_transaction(self, transaction):
    #     self.transaction.append(transaction)
    #     return self.get_last_block().index + 1

    # def add_node(self, node):
    #     nodes.append(node)
    #     return nodes


print("Creating node: " + socket.gethostname() + " | IP: " + socket.gethostbyname(socket.gethostname()))

# starting find node threads
thread1 = threading.Thread(target=recive_node)
thread2 = threading.Thread(target=send_node)
thread1.start()
thread2.start()


# starting blockchain
blockchain = Blockchain()
block = Block(blockchain.get_last_block().index + 1 , str(datetime.datetime.now()), random.randint(0,1000), blockchain.get_last_block().hash)
block.mining_block()
blockchain.add_block(block)
block = Block(blockchain.get_last_block().index + 1 , str(datetime.datetime.now()), random.randint(0,1000), blockchain.get_last_block().hash)
block.mining_block()
blockchain.add_block(block)
print(blockchain.json())

run_threads = False

exit()