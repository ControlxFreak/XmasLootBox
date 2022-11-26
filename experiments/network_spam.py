from typing import Coroutine, Callable, Tuple, Optional
import dotenv
import os
import json
import asyncio
import functools

from web3 import Web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy

# Initialize the environment variables
dotenv.load_dotenv()
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
OWNER_ADDRESS = os.getenv("OWNER_ADDRESS")
OWNER_PRIVATE_KEY = os.getenv("OWNER_PRIVATE_KEY")

# HELPER TOKENS
ALCHEMY_TOKEN=os.getenv("ALCHEMY_TOKEN")            # Mine
# ALCHEMY_TOKEN=os.getenv("ALEX_ALCHEMY_TOKEN")     # Alex's
# ALCHEMY_TOKEN=os.getenv("CRYPTO_ALCHEMY_TOKEN")   # Crypto.trezza

# Instantiate the web3 client once since this is time-consuming
ALCHEMY_URL = f"https://eth-goerli.g.alchemy.com/v2/{ALCHEMY_TOKEN}"
w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
w3.eth.set_gas_price_strategy(rpc_gas_price_strategy)

# Create the account object
account = w3.eth.account.from_key(OWNER_PRIVATE_KEY)

# Load the ABI once into memory
with open("contracts/XmasLootBox_abi.json", "r") as f:
    CONTRACT_ABI=json.load(f)

# Instantiate the contract class
contract = w3.eth.contract(address=w3.toChecksumAddress(CONTRACT_ADDRESS), abi=CONTRACT_ABI)

def to_thread(func: Callable) -> Coroutine:
    """Helper to make these blocking functions cast to threads since they are really slow and cause Discord to freak out."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

@to_thread
def get_balance(addr: str) -> Tuple[float, int]:
    """Get the current ethereum balance in Eth."""
    # Get the the current nonce of the owner
    eth_balance = w3.fromWei(w3.eth.getBalance(addr),"ether")
    # Get the number of NFTs
    nft_balance = contract.functions.balanceOf(addr).call()
    return eth_balance, nft_balance

@to_thread
def get_owner(nft_id: str) -> Optional[str]:
    """Get the owner of this NFT."""
    try:
        return contract.functions.ownerOf(nft_id).call()
    except Exception as exc:
        print(exc)
        return None

# Spam the network using the Alchemy API Key
async def main():
    # Get the balances of everyone
    with open("accounts.json") as f:
        accounts = json.load(f)

    for acct, keys in accounts.items():
        bal, nfts = await get_balance(keys["address"])
        print(f"{acct} has {bal} ETH and {nfts} NFTs")

    # Get the owner of some NFTs
    inverse_accounts = {val["address"]: key for key, val in accounts.items()}
    for nft_id in range(100):
        res = await get_owner(nft_id)

        if res is None:
            print(f"NFT # {nft_id} is not owned by anyone")
        else:
            if res not in inverse_accounts.keys():
                print(f"Unknown owner for ID # {nft_id}")
            else:
                owner = inverse_accounts[res]
                print(f"{owner} owns NFT # {nft_id}")

asyncio.run(main())
