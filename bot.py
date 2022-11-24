import os
from copy import deepcopy
import warnings
from typing import List, Dict, Tuple, Any
import random
import json
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import shutil

import discord
from discord.ext import commands
from discord.abc import Messageable
from dotenv import load_dotenv
from dalle2 import Dalle2
from PIL import Image
from PIL.Image import Image as ImgType

from src.rarity import sample_rarity_label, sample_attributes, sample_frame, sample_rarity_label_uniform
from src.generators import generate_dalle_description, generate_dalle_art, generate_erc721_metadata, generate_example_art
from src.artists import add_frame, create_nft_preview
from src.msgs import *
from src.constants import *
from src.eth import pin_to_ipfs, mint_nfts, get_from_ipfs, create_acct, get_balance, get_owner, transfer_nft, send_daily_eth

warnings.filterwarnings("ignore")

# ============================================ #
# Initialize the environment variables
# ============================================ #
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
SIM_FLAG = bool(int(os.getenv("SIM_FLAG")))

# Initialize the dalle API
dalle = Dalle2(OPENAI_TOKEN)

# Initialize the discord bot
intents = discord.Intents.default()
intents.message_content = True
help_command = commands.DefaultHelpCommand(
    no_category = 'Commands'
)
bot_description = "\
Merry Christmas! Welcome to the 2022 Discord Christmas NFT Loot Box Advent Calendar!\n\n\
Every day in the month of December, users will be able to interact with @SantaBot to claim a special gift: a completely unique (and real) NFT that will be minted to the Ethereum Goerli testnet and be placed in your very own Ethereum wallet! \
Every gift's artwork will be procedurally generated and created by an AI program (Dalle-2) that translates natural language text into images. \
Each NFT will be randomly generated with different attributes and rarity levels. \
Attributes include a variety of subjects, hats, eyes, scarfs, and backgrounds. \
With over 1,249,248 possibilities, there is sure to be something for everyone!\n\n\n\
To claim your first gift, use the command: !claim"
bot = commands.Bot(
    command_prefix="!",
    description = bot_description,
    help_command=help_command,
    intents=intents,
    heartbeat_timeout=1000000000,
    case_insensitive=True,
)

# Initialize the mutex locks
accounts_mutex = Lock()
history_mutex = Lock()
owners_mutex = Lock()
next_nft_mutex = Lock()

# Initialize a threadpool executor
executor = ThreadPoolExecutor(max_workers=4)

# ============================================ #
# Utilities
# ============================================ #
async def user_check(ctx: Messageable, username: str, day_hash: int) -> Dict[str, Any]:
    """Verify that this user:
    1. Has an account
    2. Has not tried to claim today
    """
    # ========================== #
    # Accounts
    # ========================== #
    accounts_mutex.acquire()
    with open("accounts.json", 'r') as f:
        accounts = json.load(f)
    accounts_mutex.release()

    # Check if this username has registered to play and has setup an Ethereum wallet
    if username.lower() not in accounts.keys():
        await send_no_wallet_msg(ctx)
        raise RuntimeError("No Wallet.")

    # ========================== #
    # History
    # ========================== #
    history_mutex.acquire()
    with open("history.json", 'r') as f:
        history = json.load(f)

    # Check to see if this user has claimed a loot box today
    if (day_hash in history[username] and not SIM_FLAG):
        await send_impish_msg(ctx)
        history_mutex.release()
        raise RuntimeError("Multi-claim.")

    # Otherwise, they are admirable!
    # Update the dictionary notifying that they have claimed it today
    history[username].append(day_hash)

    # Make a copy just in case
    shutil.copyfile("history.json", "/tmp/history.json")
    try:
        with open("history.json", 'w') as f:
            json.dump(history, f)
    except Exception as exc:
        shutil.copyfile("history.json", "/tmp/history.json")
        raise exc

    # Release the mutex and return
    history_mutex.release()

    return accounts

def make_uniq_dirs() -> Tuple[int, str, str, str]:
    """Create the unique image, nft, and metadata directories.
    
    This function also returns the first available NFT id as a biproduct so we don't have to re-read that file.
    """
    # Get the next NFT ID
    next_nft_mutex.acquire()

    with open('next_id', 'r') as f:
        next_nft_id = int(f.readline())

    first_nft_id = next_nft_id

    # Write-back the next NFT ID so we can release this mutex lock as fast as possible
    shutil.copyfile("next_id", "/tmp/next_id")
    try:
        with open('next_id', 'w') as f:
            f.write(str(next_nft_id + 4))
    except Exception as exc:
        shutil.copyfile("/tmp/next_id", "next_id")
        raise exc

    next_nft_mutex.release()

    # Generate unique paths
    unq_img_dir = os.path.join(OUT_DIR, f"xlb-{next_nft_id}-img")
    unq_nft_dir = os.path.join(OUT_DIR, f"xlb-{next_nft_id}-nft")
    unq_dat_dir = os.path.join(OUT_DIR, f"xlb-{next_nft_id}-dat")
    unq_prv_dir = os.path.join(OUT_DIR, f"xlb-{next_nft_id}-prv")
    os.makedirs(unq_img_dir, exist_ok=True)
    os.makedirs(unq_nft_dir, exist_ok=True)
    os.makedirs(unq_dat_dir, exist_ok=True)
    os.makedirs(unq_prv_dir, exist_ok=True)

    return first_nft_id, unq_img_dir, unq_nft_dir, unq_dat_dir, unq_prv_dir

def save_nft(nft_img: List[ImgType], filename: str):
    """This is very slow so we will execute this in a seperate thread."""
    nft_img[0].save(filename,
            save_all = True, append_images = nft_img[1:],
            optimize = True, duration = 10, loop=0)
    return

def save_metadata(metadata: Dict[str, str], unq_dat_dir: str, nft_files: List[str], nft_base_uri: str) -> List[str]:
    """Saves the NFT metadata to disk.
    NOTE: This requires that all NFT images are saved to the same directory.
    """
    data_files = []
    for fullfile in nft_files:
        # Make a copy of the metadata dictionary
        metadata_cpy = deepcopy(metadata)

        # Get the nft_id (which is the basename of the file without the extension)
        nft_base = os.path.basename(fullfile)
        nft_id = os.path.splitext(nft_base)[0]

        # Update the name and description attributes
        metadata_cpy["name"] = metadata_cpy["name"].format(nft_id)

        # Add the image URI
        metadata_cpy["image"] = nft_base_uri + nft_base

        # Save the file
        data_file = os.path.join(unq_dat_dir, f"{nft_id}.json")

        with open(data_file, "w") as f:
            json.dump(metadata_cpy, f)

        data_files.append(data_file)

    return data_files

# ============================================ #
# Commands
# ============================================ #
@bot.command()
async def claim(ctx: Messageable):
    """Claim your daily gift!"""
    # ============================================ #
    # Verification
    # ============================================ #
    # Get the current date and create a date hash
    year, week_num, day_num = get_date()
    day_hash = hash((year, week_num, day_num))

    # Check that the date is valid
    if (
        (year != VALID_YEAR or
        week_num < START_WEEK or
        week_num > END_WEEK) and
        not SIM_FLAG
    ):
        # Unfortunately, the season has ended, but I haven't shutdown the bot yet...
        await send_eoe_msg(ctx)
        raise RuntimeError("End of Event.")

    # Check that the user has an account setup
    username = (ctx.message.author.name).lower()
    users = await user_check(ctx, username, day_hash)
    user_addr = users[username]["address"]

    # ============================================ #
    # Setup the unique directory structure
    # ============================================ #
    first_nft_id, unq_img_dir, unq_nft_dir, unq_dat_dir, unq_prv_dir = make_uniq_dirs()

    # ============================================ #
    # Sampling
    # ============================================ #
    print("Sampling the rarity and attributes...")
    # Sample the rarity level
    if SIM_FLAG:
        rarity_label = sample_rarity_label_uniform()
    else:
        rarity_label = sample_rarity_label(week_num)

    # Sample the metadata
    attributes = sample_attributes(rarity_label)

    # Structure the text string
    description = generate_dalle_description(attributes)

    # Send the admirable message
    await send_admirable_msg(ctx, username, rarity_label, description)

    # ============================================ #
    # Image Generation
    # ============================================ #
    # Generate the artwork
    print("Generating the artwork...")
    if SIM_FLAG:
        # Generate some example art so we don't have to query Dalle
        images, img_files = generate_example_art(unq_img_dir, first_nft_id)
    else:
        # Generate the art using Dalle
        images, img_files = generate_dalle_art(dalle, description, unq_img_dir)

    # Sample the frame
    # frame_name = sample_frame(rarity_label)
    frame_name = None

    # ============================================ #
    # NFT Generation
    # ============================================ #
    num_imgs = len(images) # This should always be 4 according to dalle...
    nft_files = [
        os.path.join(unq_nft_dir, f"{first_nft_id + idx}.gif")
        for idx in range(num_imgs)
    ]

    # Add the frame to each image and then save them
    # Spawn these in multiple threads since this can be done asynchronously and is slow
    print(f"Adding frames to the NFTs ({first_nft_id})...")
    nft_imgs = [res for res in executor.map(add_frame, images, num_imgs*[frame_name])]

    print(f"Saving the NFTs ({first_nft_id})...")
    _ = [res for res in executor.map(save_nft, nft_imgs, nft_files)]

    # ============================================ #
    # Metadata Generation
    # ============================================ #
    # Generate the ERC721-compliant metadata json
    metadata = generate_erc721_metadata(attributes, description)

    # ============================================ #
    # Web3
    # ============================================ #
    # Pin the images to IPFS
    img_cid = await pin_to_ipfs(img_files)
    print(f"IMG URI: {img_cid}")

    # Pin the nfts to IPFS
    nft_cid = await pin_to_ipfs(nft_files)
    nft_base_uri = f"ipfs://{nft_cid}/"
    print(f"NFT URI: {nft_base_uri}")

    # Create the metadata jsons
    metadata_files = save_metadata(metadata, unq_dat_dir, nft_files, nft_base_uri)

    # Pin the metadata to IPFS
    data_cid = await pin_to_ipfs(metadata_files)
    data_base_uri = f"ipfs://{data_cid}/"
    print(f"Data URI: {data_base_uri}")

    # Get the data uris
    data_uris = []
    for data_file in metadata_files:
        data_basename = os.path.basename(data_file)
        data_uris.append(data_base_uri + data_basename)

    # Update the owner's list
    print("Updating the owners list...")
    owners_mutex.acquire()
    with open("owners.json", 'r') as f:
        owners = json.load(f)

    owners[username].append(
        {"img": img_cid, "nft": nft_cid, "data": data_cid, "ids": [first_nft_id + i for i in range(4)]}
    )

    shutil.copyfile("owners.json", "/tmp/owners.json")
    try:
        with open("owners.json", 'w') as f:
            json.dump(owners, f)
    except Exception as exc:
        shutil.copyfile("/tmp/owners.json", "owners.json")
        raise exc

    owners_mutex.release()

    print("Minting NFTs...")
    # res = await mint_nfts(user_addr, data_uris)
    # TODO: Check if result worked or not

    # =============================== #
    # Send 0.010 eth to get started
    # =============================== #
    print("Sending eth...")
    # res = await send_daily_eth(user_addr)
    # TODO: Check if this worked or not

    # Create the preview image
    print("Creating Preview...")
    preview = create_nft_preview(nft_imgs, frame_name)
    preview_filename = os.path.join(unq_prv_dir, "preview.gif")
    preview[0].save(preview_filename,
            save_all = True, append_images = preview[1:],
            optimize = True, duration = 10, loop=0)

    # Send a message to the new owner with images of their new NFTs!
    print("Complete!")
    await send_success_msg(ctx, user_addr, first_nft_id, preview_filename, img_cid, nft_cid)

@bot.command()
async def add(ctx: Messageable, username: str):
    """Add a new user. This can only be run by @aoth."""
    # =============================== #
    # Verification
    # =============================== #
    # Make sure that the only user that is allowed to call this is me
    caller = (ctx.message.author.name).lower()

    if caller.lower() != "aoth":
        await send_not_aoth_msg(ctx)
        return

    # =============================== #
    # Accounts
    # =============================== #
    accounts_mutex.acquire()

    with open("accounts.json", 'r') as f:
        accounts = json.load(f)

    if username.lower() in accounts:
        await send_user_has_account(ctx, username, accounts[username]["address"])
        accounts_mutex.release()
        return

    # Generate a private / public key
    private_key, public_key = create_acct()

    accounts[username] = {
        "address": public_key,
        "private": private_key
    }

    # Save the accounts file (first make a copy just in case...)
    shutil.copyfile("accounts.json", "/tmp/accounts.json")
    try:
        with open("accounts.json", 'w') as f:
            json.dump(accounts, f)
    except Exception as exc:
        shutil.copyfile("/tmp/accounts.json", "accounts.json")
        raise exc

    # Release the mutex
    accounts_mutex.release()

    # =============================== #
    # History
    # =============================== #
    history_mutex.acquire()

    with open("history.json", "r") as f:
        history = json.load(f)
    
    history[username] = []

    # Save the accounts file (first make a copy just in case...)
    shutil.copyfile("history.json", "/tmp/history.json")
    try:
        with open("history.json", "w") as f:
            json.dump(history, f)
    except Exception as exc:
        shutil.copyfile("/tmp/history.json", "history.json")
        raise exc

    history_mutex.release()

    # =============================== #
    # Owners
    # =============================== #
    owners_mutex.acquire()

    with open("owners.json", "r") as f:
        owners = json.load(f)

    owners[username] = []

    shutil.copyfile("owners.json", "/tmp/owners.json")
    try:
        with open("owners.json", "w") as f:
            json.dump(owners, f)
    except:
        shutil.copyfile("/tmp/owners.json", "owners.json")

    owners_mutex.release()

    # =============================== #
    # Send the msg
    # =============================== #
    await send_created_msg(ctx, username, public_key)

@bot.command()
async def address(ctx: Messageable):
    """Display your Ethereum address."""
    # Get the caller's name
    username = (ctx.message.author.name).lower()

    # Get their address
    accounts_mutex.acquire()
    with open("accounts.json", 'r') as f:
        accounts = json.load(f)
    accounts_mutex.release()

    if username not in accounts:
        await send_no_wallet_msg(ctx)
        return

    user_addr = accounts[username]["address"]

    # Send them a message
    await send_addr_msg(ctx, user_addr)

@bot.command(name="users")
async def _users(ctx: Messageable):
    """Display the list of users and their Ethereum addresses.
    
    NOTE: This renders poorly on mobile and I can't get the hyperlinks to work.
    """
    # Get the accounts
    accounts_mutex.acquire()
    with open("accounts.json", 'r') as f:
        accounts = json.load(f)
    accounts_mutex.release()

    # Send them a message
    await send_users_msg(ctx, accounts)

@bot.command()
async def nft(ctx: Messageable):
    """Display one of your NFTs (chosen randomly)."""
    username = (ctx.message.author.name).lower()

    # Load the owners
    owners_mutex.acquire()
    with open("owners.json", 'r') as f:
        owners = json.load(f)
    owners_mutex.release()

    # Load the address
    accounts_mutex.acquire()
    with open("accounts.json", 'r') as f:
        accounts = json.load(f)
    accounts_mutex.release()

    # Check to see that this user exists
    if (username not in owners) or (username not in accounts):
        await send_no_wallet_msg(ctx)
        return

    # Get all of the CIDs that this owner has
    cids = owners[username]

    if len(cids) == 0:
        await send_no_nfts_msg(ctx)
        return

    # Randomly select one
    cid = random.choice(cids)
    nft_id = random.choice(cid["ids"])
    nft_filename = f"{nft_id}.gif"

    # Download it and save it to /tmp
    nft_img = await get_from_ipfs(cid["nft"], nft_filename)

    # Send it
    await send_nft_msg(ctx, username, nft_img, nft_id, accounts[username]["address"])

@bot.command(name="random")
async def _random(ctx: Messageable):
    """Display someone's NFT chosen completely at random."""
    # Load the owners
    owners_mutex.acquire()
    with open("owners.json", 'r') as f:
        owners = json.load(f)
    owners_mutex.release()

    # Load the address
    accounts_mutex.acquire()
    with open("accounts.json", 'r') as f:
        accounts = json.load(f)
    accounts_mutex.release()

    usernames = list(accounts.keys())
    while len(usernames) > 0:
        # Randomly select a user
        username = random.choice(usernames)

        # Check to see if they have an NFT
        if len(owners[username]) == 0:
            usernames.remove(username)
            continue

        # Randomly select an nft
        cid = random.choice(owners[username])
        nft_id = random.choice(cid["ids"])
        nft_filename = f"{nft_id}.gif"

        # Download it and save it to /tmp
        nft_img = await get_from_ipfs(cid["nft"], nft_filename)

        # Send it
        await send_nft_msg(ctx, username, nft_img, nft_id, accounts[username]["address"])
        return

    # We never found anyone
    await send_nobody_nfts_msg(ctx)

@bot.command()
async def balance(ctx: Messageable):
    """Display your current ethereum and NFTs balance."""
    username = (ctx.message.author.name).lower()

    # Get the accounts
    accounts_mutex.acquire()
    with open("accounts.json", 'r') as f:
        accounts = json.load(f)
    accounts_mutex.release()

    if username not in accounts:
        await send_no_wallet_msg(ctx)
        return

    user_addr = accounts[username]["address"]

    # Get the balances
    eth_balance, nft_balance = await get_balance(user_addr)

    # Format the message
    await send_balance_msg(ctx, username, eth_balance, nft_balance, user_addr)

@bot.command()
async def balanceOf(ctx: Messageable, username: str):
    """Display a user's current ethereum and NFTs balance."""

    # Get the accounts
    accounts_mutex.acquire()
    with open("accounts.json", 'r') as f:
        accounts = json.load(f)
    accounts_mutex.release()

    if username not in accounts:
        await send_no_wallet_msg(ctx)
        return

    user_addr = accounts[username]["address"]

    # Get the balances
    eth_balance, nft_balance = await get_balance(user_addr)

    # Format the message
    await send_balance_msg(ctx, username, eth_balance, nft_balance, user_addr)

@bot.command()
async def gift(ctx: Messageable, recipient: str, nft_id: int):
    """Randomly send one of your NFTs to a user!

    WARNING: This will use some of your ethereum to pay for the gas fees!

    Args:
        ctx (Messageable): Discord Context
        recipient (str): Recipient of the NFT. Use the official discord name, not their server nickname.
    """
    sender = (ctx.message.author.name).lower()

    # Get the accounts
    accounts_mutex.acquire()
    with open("accounts.json", 'r') as f:
        accounts = json.load(f)
    accounts_mutex.release()

    if sender not in accounts:
        await send_no_wallet_msg(ctx)
        return

    # Get the addresses
    sender_addr = accounts[sender]["address"]
    sender_priv = accounts[sender]["private"]

    # Check that the sender actually owns this NFT
    nft_owner = await get_owner(nft_id)

    if nft_owner is None:
        await send_nft_dne_msg(ctx, nft_id, sender_addr)
        return
    
    if nft_owner != sender_addr:
        with open("accounts.json", "r") as f:
            accounts = json.load(f)

        inverse_accounts = {val["address"]: key for key, val in accounts.items()}
        real_owner_name = inverse_accounts[nft_owner]
        await send_not_your_nft_msg(ctx, nft_id, sender_addr, real_owner_name)
        return

    if recipient not in accounts:
        await send_no_wallet_msg(ctx)
        return

    # Get the addresses
    recipient_addr = accounts[recipient]["address"]

    # Send a confirmation message
    await send_transfer_conf_msg(ctx, sender, recipient, nft_id)

    # Conduct the transaction
    res = await transfer_nft(sender_addr, sender_priv, recipient_addr, nft_id)

    if res is None:
        await send_transfer_error_msg(ctx, sender, recipient, nft_id)
        return

    await send_transfer_success_msg(ctx, sender, recipient, nft_id, sender_addr, recipient_addr)

@bot.command()
async def faq(ctx: Messageable):
    """Frequently Asked Questions."""
    await send_faq_msg(ctx)

# Run the bot
bot.run(DISCORD_TOKEN)
