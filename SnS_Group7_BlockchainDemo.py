
import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request


class Chain:
    def __init__(self):
        self.free_transactions = []
        self.chain = []
        self.nodes = set()
        self.add_block(previous_hash='1', nonce=100)

    def node_register(self, address):
        self.nodes.add(address)
        #print(self.nodes)

    def add_block(self, nonce, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.free_transactions,
            'nonce': nonce,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.free_transactions = []
        self.chain.append(block)
        return block

    def add_transaction(self, sender, receiver, value):
        self.free_transactions.append({
            'sender': sender,
            'receiver': receiver,
            'value': value,
        })
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_work(self, last_block):
        last_nonce = last_block['nonce']
        last_hash = self.hash(last_block)

        nonce = 0
        while self.valid_proof(last_nonce, nonce, last_hash) is False:
            nonce += 1

        return nonce

    @staticmethod
    def valid_proof(last_nonce, nonce, last_hash):
        guess = f'{last_nonce}{nonce}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
chain = Chain()


@app.route('/mine', methods=['GET'])
def mine():
    last_block = chain.last_block
    nonce = chain.proof_work(last_block)
    chain.add_transaction(
        sender="0",
        receiver=node_identifier,
        value=1,
    )
    previous_hash = chain.hash(last_block)
    block = chain.add_block(nonce, previous_hash)

    response = {
        'message': "New Block Mined",
        'index': block['index'],
        'transactions': block['transactions'],
        'nonce': block['nonce'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/add', methods=['POST'])
def add_transaction():
    values = request.get_json()
    required = ['sender', 'receiver', 'value']
    if not all(k in values for k in required):
        return 'Missing values', 400
    index = chain.add_transaction(values['sender'], values['receiver'], values['value'])
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain_info', methods=['GET'])
def full_chain():
    response = {
        'chain': chain.chain,
        'length': len(chain.chain),
    }
    return jsonify(response), 200


@app.route('/node/register', methods=['POST'])
def node_register():
    values = request.get_json()
    #print (values)
    node = values.get('node')
    if node is None:
        return "Error: Please supply a valid list of nodes", 400

    chain.node_register(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(chain.nodes),
    }
    return jsonify(response), 201

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)
 