import requests
import argparse
import json
import os
import datatable as dt
from web3 import Web3
import datetime

# pip install etherscan-python
from etherscan import Etherscan



GRAPH_REQUEST_TIMEOUT = 10000
API_KEY = os.environ['ETHERSCAN_TOKEN']
infura_url = os.environ['PROVIDER']
ct = datetime.datetime.now()


def get_args():
    
    parser = argparse.ArgumentParser(description='create a CSV of accounts and their transactions')
    
    parser.add_argument('-n', '--num', help="(string): number of rows in resultant df", required=True)
    parser.add_argument('-s', '--start', help="(int): start block number", required=True)
    parser.add_argument('-e', '--end', help="(int): end block number", required=True)
    parser.add_argument('-o', '--out', help="(string): outpath", required=True)


    args = parser.parse_args()
    num = int(args.num)
    start = args.start
    end = args.end
    out = args.out

    return num, start, end, out


# query n transactions from the graph
def uniswap_transactions(count, skip=0):
    print("getting {} uniswap transactions".format(count))
    headers = {}
    query = """
    {
    transactions(first: %(count)s, skip: %(skip)s, orderBy:timestamp, orderDirection:desc) {
      id
      blockNumber
      timestamp
      mints {
        id
      }
      burns {
        id
      }
      swaps {
        id
      }
    }
    }
    """ % { 'count': count, 'skip': skip }
    
    request = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',
                           json={'query':query}, headers=headers, timeout=GRAPH_REQUEST_TIMEOUT)
    if request.status_code == 200:
        print("done")
        return request.json()
    
    
# get the addresses of those accounts
def getAddresses(txns, web3):
    print("getting addresses")
    # first need to get the txn ids
    try:
        ids = [x['id'] for x in txns['data']['transactions']]
    except:
        print(txns)
        if txns is None:
            return None
    # then get the wallet addresses in those txn ids
    addresses = [web3.eth.getTransaction(tx)['from'] for tx in ids]   # returns the receipt, parse the 'from' field
    print("done")
    return addresses

def main():
    
    num, startblock, endblock, outpath = get_args()
    
    ethscan = Etherscan(API_KEY)
    web3 = Web3(Web3.HTTPProvider(infura_url))
    
    features = ['address', 'num_txns', 'startblock', 'endblock']
    master = dt.Frame(names=features)
    skip = 0    # can't exceed 5000, max pages i guess
    count = 1000   #max in a query is 1k
    
    # while number of rows in dataset is < num
    #   go through a batch of transactions, get weekly txns per account, rbind to master, run unique
    while master.nrows < num:
    
        txns = uniswap_transactions(count, skip)
        addresses = getAddresses(txns, web3)
        if addresses is None:
            skip = skip + count
            if skip > 5000:
                skip = 0
            continue
        
        
        skip = skip + count
        if skip > 5000:
            skip = 0

        for addr in addresses:
            #print("getting transactions by address")
            try:
                print(addr)
                num_txns = len(ethscan.get_normal_txs_by_address(addr, startblock, endblock, 'desc'))    # block difference approximately a week
            except:
                continue
            #print("done, appending to master")
            row = [[addr], [num_txns], [startblock], [endblock]]    # needs to be a list of lists for a row in dt
            temp = dt.Frame(row, names=features)
            master.rbind(temp)
            #print("done")
    
        print("Number of rows: {}".format(master.nrows))
        master.to_csv(outpath, append=True)

    
    
    
if __name__ == '__main__':
    main()