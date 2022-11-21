from typing import List
from requests import Session, Request, Response
import dotenv
import os
import json

from web3 import Web3

# Initialize the environment variables
dotenv.load_dotenv()
ALCHEMY_TOKEN = os.getenv("ALCHEMY_TOKEN")
PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_SECRET_KEY = os.getenv("PINATA_SECRET_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
OWNER_ADDRESS = os.getenv("OWNER_ADDRESS")
OWNER_PRIVATE_KEY = os.getenv("OWNER_PRIVATE_KEY")

# Prepare the IPFS url, payload and header
ipfs_url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
ipfs_headers = {
    'pinata_api_key': PINATA_API_KEY,
    'pinata_secret_api_key': PINATA_SECRET_KEY
}

# Instantiate the web3 client once since this is time-consuming
ALCHEMY_URL = f"https://eth-goerli.g.alchemy.com/v2/{ALCHEMY_TOKEN}"
w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

# Create the account object
account = w3.eth.account.from_key(OWNER_PRIVATE_KEY)

# Load the ABI once into memory
with open("contracts/XmasLootBox_abi.json", "r") as f:
    CONTRACT_ABI=json.load(f)

# Instantiate the contract class
contract = w3.eth.contract(address=w3.toChecksumAddress(CONTRACT_ADDRESS), abi=CONTRACT_ABI)


def pin_to_ipfs(filenames: List[str]) -> str:
    """Pins all contents of a directory to IPFS and returns the CID hash.
    NOTE: All files must be in the same directory for this to work.
    """
    # Prepare the files
    directory = os.path.dirname(filenames[0])
    files = [('pinataMetadata', (None, '{"name":"' + directory.split(os.sep)[-1] + '"}'))]

    for filename in filenames:
        files.append(('file', (os.sep.join(filename.split(os.sep)[-2:]), open(filename, 'rb'))))

    # Post the request
    request = Request(
        'POST',
        ipfs_url,
        headers=ipfs_headers,
        files=files,
    ).prepare()
    response = Session().send(request)

    if not response.ok:
        raise RuntimeError(f"Could not pin to IPFS.\n{response.text}")

    return response.json()["IpfsHash"]


def mint_nfts(addr: str, ipfs_cids: List[str]):
    """Mint the NFT located at `ipfs_cid` to address `addr`"""

    # Get the the current nonce of the owner
    nonce = w3.eth.get_transaction_count(OWNER_ADDRESS)

    # Build the transaction
    txn = contract.functions.mint4NFTs(addr, ipfs_cids).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'maxPriorityFeePerGas': w3.toWei(100, 'gwei'),
        'maxFeePerGas': w3.toWei(125, 'gwei')
    })

    # Sign and send the transaction
    signed_txn = w3.eth.account.sign_transaction(txn, account.key)
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    w3.eth.waitForTransactionReceipt(txn_hash)
