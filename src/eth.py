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

# Instantiate the web3 client once since this is time-consuming
ALCHEMY_URL = f"https://eth-goerli.g.alchemy.com/v2/{ALCHEMY_TOKEN}"
w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

# Load the ABI once into memory
with open("contracts/XmasLootBox_abi.json", "r") as f:
    CONTRACT_ABI=json.load(f)

# Instantiate the contract class
contract = w3.eth.contract(address=w3.toChecksumAddress(CONTRACT_ADDRESS), abi=CONTRACT_ABI)


def pin_to_ipfs(filenames: List[str]) -> str:
    """Pins all contents of a directory to IPFS and returns the CID hash.
    NOTE: All files must be in the same directory for this to work.
    """
    # Prepare the url, payload and header
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {
        'pinata_api_key': PINATA_API_KEY,
        'pinata_secret_api_key': PINATA_SECRET_KEY
    }

    # Prepare the files
    directory = os.path.dirname(filenames[0])
    files = [('pinataMetadata', (None, '{"name":"' + directory.split(os.sep)[-1] + '"}'))]

    for filename in filenames:
        files.append(('file', (os.sep.join(filename.split(os.sep)[-2:]), open(filename, 'rb'))))

    # Post the request
    request = Request(
        'POST',
        url,
        headers=headers,
        files=files,
    ).prepare()
    response = Session().send(request)

    if not response.ok:
        raise RuntimeError(f"Could not pin to IPFS.\n{response.text}")

    return response.json()["IpfsHash"]


# def mint_nfts():

    # # Construct the transaction
    # nonce = w3.eth.getTransactionCount(OWNER_ADDRESS)

    # tx = {
    #     'nonce': nonce,
    #     'to': account_2,
    #     'value': web3.toWei(1, 'ether'),
    #     'gas': 2000000,
    #     'gasPrice': web3.toWei('50', 'gwei'),
    # }