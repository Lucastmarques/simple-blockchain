from blockchain import Blockchain
from utils import *
from flask import request, jsonify
from flask import Flask
app = Flask(__name__)

blockchain = Blockchain()

@app.route('/transactions/create', methods=['POST'])
def create_transactions():
    data = request.get_json()
    valid_data, resp_data = isValidTransactionData(data)
    broadcast = False #Define se a transação vem de um broadcasting
    if 'broadcast' in [*data.keys()]:
        broadcast = data['broadcast']
    if valid_data:
        tx = blockchain.createTransaction(data['sender'], data['recipient'],
                                          data['amount'], data['timestamp'],
                                          data['privWifKey'])
        valid_tx, resp_tx = Blockchain.isValidTransaction(tx)
        if valid_tx:
            blockchain.addTransaction(tx)
            if not broadcast:
                broadcastTransaction(blockchain.nodes, data)
            return "", 200
        else:
            return resp_tx, 500
    else:
        return resp_data, 400
    
@app.route('/transactions/mempool', methods=['GET'])
def get_mempool():
    try:
        resp = jsonify(blockchain.memPool)
        return resp, 200
    except Exception as e:
        return e, 500

@app.route('/mine', methods=['GET'])
def mine():
    prevBlock = blockchain.createBlock(0, blockchain.prevBlock)
    blockchain.mineProofOfWork(prevBlock)

@app.route('/chain', methods=['GET'])
def get_chain():
    pass

@app.route('/nodes/register', methods=['POST'])
def register_node():
    data = request.get_json()
    nodes = data['nodes']
    blockchain.registerNodes(nodes)
    return "", 200

@app.route('/nodes/resolve', methods=['POST'])
def resolve_nodes():
    pass
    

if __name__ == "__main__":
    app.run(port=5001)