import hashlib
import json
from time import time
import copy
import random
import requests
import bitcoinlib # pip install bitcoin

DIFFICULTY = 4 # Quantidade de zeros (em hex) iniciais no hash valido.

class Blockchain(object):

    def __init__(self):
        self.chain = []
        self.memPool = []
        self.nodes = set() # Conjunto para armazenar os nós registrados.
        self.createGenesisBlock()

    def createGenesisBlock(self):
        # Cria o bloco genêsis
        self.createBlock(previousHash='0'*64, nonce=0)
        self.mineProofOfWork(self.prevBlock) 

    def createBlock(self, nonce=0, previousHash=None):
        # Retorna um novo bloco criado e adicionado ao blockchain (ainda não minerado).
        if (previousHash == None):
            previousBlock = self.chain[-1]
            previousBlockCopy = copy.copy(previousBlock)
            previousBlockCopy.pop("transactions", None)

        block = {
            'index': len(self.chain) + 1,
            'timestamp': int(time()),
            'transactions': self.memPool,
            'merkleRoot': self.generateMerkleRoot(self.memPool),
            'nonce': nonce,
            'previousHash': previousHash or self.generateHash(previousBlockCopy),
        }

        self.memPool = []
        self.chain.append(block)
        return block

    def mineProofOfWork(self, prevBlock):
        # Retorna o nonce que satisfaz a dificuldade atual para o bloco passado como argumento.
        nonce = 0
        while self.isValidProof(prevBlock, nonce) is False:
            nonce += 1

        return nonce

    def createTransaction(self, sender, recipient, amount, timestamp, privWifKey):
        # Cria uma nova transação, assinada pela chave privada WIF do remetente.
        tx = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': timestamp
        }
 
        tx['signature'] = Blockchain.sign(privWifKey, json.dumps(tx, sort_keys=True))
        return tx
    
    def addTransaction(self, tx):
        if (not tx in self.memPool):
            self.memPool.append(tx)
    
    @staticmethod
    def isValidTransaction(tx):
        if not 'signature' in [*tx.keys()]:
            return False, "Missing Signature"
        signature = tx['signature']
        message = tx.copy()
        message.pop('signature')
        message = json.dumps(message)
        try:
            Blockchain.verifySignature(tx['sender'], signature, message)
            return True, ""
        except Exception as e:
            return False, e

    def isValidChain(self, chain):
        # Dado uma chain passada como parâmetro, faz toda a verificação se o blockchain é válido:
        for block in chain:
            # 1. PoW válido
            pow_result, pow_reason =  self.checkPow(block)
            if not pow_result:
                return False, pow_reason
            
            # 2. Transações assinadas e válidas
            tx_result, tx_reason = self.checkTransactions(block)
            if not tx_result:
                return False, tx_reason
            
            # 3. Verifica Merkle Root válido
            mr_result, mr_reason = self.checkMerkleRoot(block)
            if not mr_result:
                return False, mr_reason
        return True, ""
            
    def checkPow(self, block):
        guessHash = Blockchain.getBlockID(block)
        hash_result = guessHash[:DIFFICULTY] == '0' * DIFFICULTY
        if hash_result:
            return True, ""
        else:
            return False, "Invalid POW"
                
    def checkMerkleRoot(self, block):
        merkleRoot = Blockchain.generateMerkleRoot(block['transactions'])
        if block['merkleRoot'] != merkleRoot:
            return False, "Invalid merkleRoot"
        else:
            return True, ""
        
    def checkTransactions(self, block):
        for tx in block['transactions']:
            result, _ = self.isValidTransaction(tx)
            if not result:
                return False, "Invalid Transaction <{}>".format(tx)
        return True, ""
                

    def resolveConflicts(self):
        # Consulta todos os nós registrados, e verifica se algum outro nó tem um blockchain com mais PoW e válido. Em caso positivo,
        # substitui seu próprio chain.
        valid_chains = []
        for node in self.nodes:
            url = 'http://' + node + '/chain'
            chain = requests.get(url).json()
            print(chain)
            chain_result, _ = self.isValidChain(chain)
            if chain_result:
                valid_chains.append(chain)
                
        biggest = Blockchain.getBiggestChain(valid_chains)
        if len(biggest) > len(self.chain):
            self.chain = biggest
                
    @staticmethod  
    def getBiggestChain(chain_list):
        biggest = chain_list[0]
        for index in range(1, len(chain_list)):
            if len(chain_list[index]) > len(biggest):
                biggest = chain_list[index]
        return biggest

    @staticmethod
    def generateMerkleRoot(transactions):
        # Gera a Merkle Root de um bloco com as respectivas transações.
        if (len(transactions) == 0): # Para o bloco genesis
            return '0'*64

        txHashes = [] 
        for tx in transactions:
            txHashes.append(Blockchain.generateHash(tx))

        return Blockchain.hashTxHashes(txHashes)

    @staticmethod
    def hashTxHashes(txHashes):
        # Função auxiliar recursiva para cálculo do MerkleRoot
        if (len(txHashes) == 1): # Condição de parada.
            return txHashes[0]

        if (len(txHashes)%2 != 0): # Confere se a quantidade de hashes é par.
            txHashes.append(txHashes[-1]) # Se não for, duplica o último hash.

        newTxHashes = []
        for i in range(0,len(txHashes),2):        
            newTxHashes.append(Blockchain.generateHash(Blockchain.generateHash(txHashes[i]) + Blockchain.generateHash(txHashes[i+1])))
        
        return Blockchain.hashTxHashes(newTxHashes)

    @staticmethod
    def isValidProof(block, nonce):
        # Retorna True caso o nonce satisfaça a dificuldade atual para o bloco passado como argumento.
        block['nonce'] = nonce
        guessHash = Blockchain.getBlockID(block)
        return guessHash[:DIFFICULTY] == '0' * DIFFICULTY 

    @staticmethod
    def generateHash(data):
        # Retorna o SHA256 do argumento passado.
        blkSerial = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(blkSerial).hexdigest()

    @staticmethod
    def getBlockID(block):
        # Retorna o ID (hash do cabeçalho) do bloco passado como argumento.
        blockCopy = copy.copy(block)
        blockCopy.pop("transactions", None)
        return Blockchain.generateHash(blockCopy)

    def printChain(self):
        # Imprime no console um formato verboso do blockchain.
        # print(json.dumps(self.chain, indent=2, sort_keys=True))
        print(self.memPool)
        pass # Mantenha seu metodo de impressao do blockchain feito na pratica passada.

    @property
    def prevBlock(self):
        # Retorna o último bloco incluído no blockchain.
        return self.chain[-1]
    
    def registerNodes(self, nodes):
        for node in nodes:
            self.nodes.add(node)
        

    @staticmethod
    def getWifCompressedPrivateKey(private_key=None):
        # Retorna a chave privada no formato WIF-compressed da chave privada hex.
        if private_key is None:
            private_key = bitcoinlib.random_key()
        return bitcoinlib.encode_privkey(bitcoinlib.decode_privkey((private_key + '01'), 'hex'), 'wif')
        
    @staticmethod
    def getBitcoinAddressFromWifCompressed(wif_pkey):
        # Retorna o endereço Bitcoin da chave privada WIF-compressed.
        return bitcoinlib.pubtoaddr(bitcoinlib.privkey_to_pubkey(wif_pkey))

    @staticmethod
    def sign(wifCompressedPrivKey, message):
        # Retorna a assinatura digital da mensagem e a respectiva chave privada WIF-compressed.
        return bitcoinlib.ecdsa_sign(message, wifCompressedPrivKey)

    @staticmethod
    def verifySignature(address, signature, message):
        # Verifica se a assinatura é correspondente a mensagem e o endereço BTC.
        # Você pode verificar aqui também: https://tools.bitcoin.com/verify-message/
        return bitcoinlib.ecdsa_verify(message, signature, address)


# Implemente sua API com os end-points indicados no GitHub Classroom.
# Implemente um teste com ao menos 2 nós simultaneos.