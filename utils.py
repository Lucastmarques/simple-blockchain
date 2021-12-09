import json
import requests
from threading import Thread

def isValidTransactionData(data):
    validKeys = ['sender', 'recipient',
                 'amount', 'timestamp',
                 'privWifKey']
    if all(key in data.keys() for key in validKeys):
        return True, ""
    return False, "Wrong data"

def broadcastTransaction(nodes, data):
    data["broadcast"] = True
    for node in nodes:
        url = 'http://' + node + '/transactions/create'
        try:
            resp = requests.post(url, json=data)
            print(resp)
        except Exception as e:
            print(e)
            continue