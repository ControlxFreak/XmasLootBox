import os
from copy import deepcopy
import warnings
from typing import List, Dict, Tuple, Any
import asyncio

import json
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, wait

import discord
from discord.ext import commands
from discord.abc import Messageable
from dotenv import load_dotenv
from dalle2 import Dalle2
from PIL import Image
from PIL.Image import Image as ImgType

from src.rarity import sample_rarity_label, sample_attributes, sample_frame, sample_rarity_label_uniform
from src.generators import generate_dalle_description, generate_dalle_art, generate_erc721_metadata
from src.artists import add_frame
from src.msgs import get_date, send_eoe_msg, send_no_wallet_msg, send_admirable_msg, send_impish_msg, send_success_msg, send_not_aoth_msg, send_addr_msg, send_created_msg, send_user_has_account, send_users_msg
from src.constants import START_WEEK, END_WEEK, VALID_YEAR
from src.eth import pin_to_ipfs, mint_nfts

warnings.filterwarnings("ignore")

# ============================================ #
# Initialize the enviornment variables
# ============================================ #
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
SIM_FLAG = bool(int(os.getenv("SIM_FLAG")))

# Define the input/output directories
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets/")
FRAME_DIR = os.path.join(BASE_DIR, ASSET_DIR, "frames/")
OUT_DIR = os.path.join(BASE_DIR, "nfts/")

# Initialize the dalle API
dalle = Dalle2(OPENAI_TOKEN)

# Initialize the discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix="!", heartbeat_timeout=1000000000)

# Initialize the mutex locks
users_mutex = Lock()
next_nft_mutex = Lock()

# Initialize a threadpool executor
executor = ThreadPoolExecutor(max_workers=4)

# ============================================ #
# Utilities
# ============================================ #
async def user_check(username: str, day_hash: int) -> Dict[str, Any]:
    """Verify that this user:
    1. Has an account
    2. Has not tried to claim today
    """
    users_mutex.acquire()

    # Open the users json
    with open("users.json", 'r') as f:
        users = json.load(f)

    # Check if this username has registered to play and has setup an Ethereum wallet
    if username.lower() not in users.keys():
        users_mutex.release()
        raise RuntimeError("No Wallet.")

    # Check to see if this user has claimed a loot box today
    if (day_hash in users[username] and not SIM_FLAG):
        users_mutex.release()
        raise RuntimeError("Multi-claim.")

    # Otherwise, they are admirable!
    # Update the dictionary notifying that they have claimed it today
    users[username]["claimed"].append(day_hash)

    with open("users.json", 'w') as f:
        json.dump(users, f)

    # Release the mutex and return
    users_mutex.release()

    return users


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
    with open('next_id', 'w') as f:
        f.write(str(next_nft_id + 4))

    next_nft_mutex.release()

    # Generate unique paths
    unq_img_dir = os.path.join(OUT_DIR, f"xlb-{next_nft_id}-img")
    unq_nft_dir = os.path.join(OUT_DIR, f"xlb-{next_nft_id}-nft")
    unq_dat_dir = os.path.join(OUT_DIR, f"xlb-{next_nft_id}-dat")
    os.makedirs(unq_img_dir, exist_ok=True)
    os.makedirs(unq_nft_dir, exist_ok=True)
    os.makedirs(unq_dat_dir, exist_ok=True)

    return first_nft_id, unq_img_dir, unq_nft_dir, unq_dat_dir

def _save_nft_thread(nft_img: List[ImgType], filename: str):
    """This is very slow so we will execute this in a seperate thread."""
    nft_img[0].save(filename,
            save_all = True, append_images = nft_img[1:],
            optimize = True, duration = 10, loop=0)
    return


def save_nfts(nft_imgs: List[ImgType], unq_nft_dir: str, first_nft_id: int) -> List[str]:
    """Saves the NFT files to disk."""

    # Get the fullfilenames
    filenames = [
        os.path.join(unq_nft_dir, f"{first_nft_id + idx}.gif")
        for idx in range(len(nft_imgs))
    ]

    # Spawn the execution of each into a separate thread
    nft_futures = [
        executor.submit(_save_nft_thread, nft_img, filename)
        for nft_img, filename in zip(nft_imgs, filenames)
    ]

    # Wait for all threads to complete
    wait(nft_futures)

    # Return the filenames
    return filenames


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
async def claim():

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
        raise RuntimeError("End of Event.")

    # Check that the user has an account setup
    username = "aoth"
    users = await user_check(username, day_hash)
    user_addr = users[username]["address"]

    # ============================================ #
    # Setup the unique directory structure
    # ============================================ #
    first_nft_id, unq_img_dir, unq_nft_dir, unq_dat_dir = make_uniq_dirs()

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

    # ============================================ #
    # Image Generation
    # ============================================ #
    # Generate the artwork
    print("Generating the artwork...")
    if SIM_FLAG:
        # Load the example images
        images = [
            Image.open(os.path.join(ASSET_DIR, f"example/{i}.png")) for i in range(1,5)
        ]
        # Copy them into the correct location so they can be uploaded
        for idx, img in enumerate(images):
            img.save(os.path.join(unq_img_dir, f"{first_nft_id + idx}.png"))
    else:
        # Generate the art using Dalle
        images = generate_dalle_art(dalle, description, unq_img_dir)

    # Sample the frame
    frame_name = sample_frame(rarity_label)
    frame_path = os.path.join(FRAME_DIR, f"{frame_name}.gif")

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
    nft_imgs = [res for res in executor.map(add_frame, images, num_imgs*[frame_path])]

    print(f"Saving the NFTs ({first_nft_id})...")
    _ = [res for res in executor.map(_save_nft_thread, nft_imgs, nft_files)]

    # ============================================ #
    # Metadata Generation
    # ============================================ #
    # Generate the ERC721-compliant metadata json
    metadata = generate_erc721_metadata(attributes, description)

    # ============================================ #
    # Web3
    # ============================================ #
    # Pin the images to IPFS
    nft_cid = pin_to_ipfs(nft_files)
    nft_base_uri = f"ipfs://{nft_cid}/"
    print(f"NFT URI: {nft_base_uri}")

    # Create the metadata jsons
    metadata_files = save_metadata(metadata, unq_dat_dir, nft_files, nft_base_uri)

    # Pin the metadata to IPFS
    data_cid = pin_to_ipfs(metadata_files)
    data_base_uri = f"ipfs://{data_cid}/"
    print(f"Data URI: {data_base_uri}")

    # Mint the NFTs
    data_uris = []
    for data_file in metadata_files:
        data_basename = os.path.basename(data_file)
        data_uris.append(data_base_uri + data_basename)

    print("Minting NFTs...")
    mint_nfts(user_addr, data_uris)

    # Sleep for a few seconds before sending the confirmation message.
    # This (should) allow Opensea to sync
    print("Done Minting NFTs.\nRegistering on OpenSea...")
    await asyncio.sleep(10)

    # Send a message to the new owner with images of their new NFTs!
    print("Complete!")

# run
asyncio.run(claim())