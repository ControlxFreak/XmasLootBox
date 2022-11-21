import os
from copy import deepcopy
import warnings
from typing import List, Dict, Tuple, Any

import json
from threading import Lock

import discord
from discord.ext import commands
from discord.abc import Messageable
from dotenv import load_dotenv
from dalle2 import Dalle2
from PIL.Image import Image as ImgType

from src.rarity import sample_rarity_label, sample_attributes, sample_frame, sample_rarity_label_uniform
from src.generators import generate_dalle_description, generate_dalle_art, generate_erc721_metadata
from src.artists import add_frame
from src.msgs import get_date, send_eoe_msg, send_no_wallet_msg, send_admirable_msg, send_impish_msg, send_error_msg, send_success_msg, send_not_aoth_msg, send_addr_msg, send_created_msg, send_user_has_account
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
FRAME_DIR = os.path.join(BASE_DIR, "frames/")
NFT_DIR = os.path.join(BASE_DIR, "nfts/")

# Initialize the dalle API
dalle = Dalle2(OPENAI_TOKEN)

# Initialize the mutex locks
users_mutex = Lock()
next_nft_mutex = Lock()

# ============================================ #
# Utilities
# ============================================ #
def user_check(username: str, day_hash: int) -> Dict[str, Any]:
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


def save_nfts(nft_imgs: List[ImgType]) -> Tuple[int, List[str]]:
    """Saves the NFT files to disk."""
    # Get the next NFT ID
    next_nft_mutex.acquire()

    with open('next_id', 'r') as f:
        next_nft_id = int(f.readline())

    first_nft_id = next_nft_id

    # Write-back the next NFT ID so we can release this mutex lock as fast as possible
    with open('next_id', 'w') as f:
        f.write(str(next_nft_id + len(nft_imgs)))

    next_nft_mutex.release()

    # Generate a unique path to this NFT directory
    unq_nft_img_dir = os.path.join(NFT_DIR, f"{next_nft_id}-imgs")
    os.makedirs(unq_nft_img_dir, exist_ok=True)

    # Save the images and metadata to disk
    nft_files = []
    for nft_img in nft_imgs:
        print(f"Saving nft {next_nft_id}...")

        # First, save the gif
        filename = os.path.join(unq_nft_img_dir, f"{next_nft_id}.gif")
        nft_img[0].save(filename,
                    save_all = True, append_images = nft_img[1:],
                    duration = 10, loop=0)
        nft_files.append(filename)
        next_nft_id+=1

    return first_nft_id, nft_files


def save_metadata(metadata: Dict[str, str], first_nft_id: int, nft_files: List[str], nft_base_uri: str) -> List[str]:
    """Saves the NFT metadata to disk.
    NOTE: This assumes that all NFT images are saved to the same directory.
    """
    # Generate a unique path to this NFT directory
    unq_nft_data_dir = os.path.join(NFT_DIR, f"{first_nft_id}-data")
    os.makedirs(unq_nft_data_dir, exist_ok=True)

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
        data_file = os.path.join(unq_nft_data_dir, f"{nft_id}.json")
        with open(data_file, "w") as f:
            json.dump(metadata_cpy, f)
        data_files.append(data_file)

    return data_files


# ============================================ #
# Commands
# ============================================ #
def lootbox(username):
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
    users = user_check(username, day_hash)
    user_addr = users[username]["address"]

    # ============================================ #
    # Sampling
    # ============================================ #
    # Sample the rarity level
    rarity_level = sample_rarity_label(week_num, SIM_FLAG)

    # Sample the metadata
    attributes = sample_attributes(rarity_level)

    # ============================================ #
    # Image Generation
    # ============================================ #
    # Structure the text string
    description = generate_dalle_description(attributes)

    # Generate the artwork
    images = generate_dalle_art(dalle, description, SIM_FLAG)

    # Sample the frame
    frame_name = sample_frame(rarity_level)
    frame_path = os.path.join(FRAME_DIR, f"{frame_name}.gif")

    # ============================================ #
    # NFT Generation
    # ============================================ #
    # Add the frame to each image
    nft_imgs = [
        add_frame(image, frame_path) for image in images
    ]
    first_nft_id, nft_files = save_nfts(nft_imgs)

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
    metadata_files = save_metadata(metadata, first_nft_id, nft_files, nft_base_uri)

    # Pin the metadata to IPFS
    data_cid = pin_to_ipfs(metadata_files)
    data_base_uri = f"ipfs://{data_cid}/"
    print(f"Data URI: {data_base_uri}")

    # Mint the NFTs
    data_uris = []
    for data_file in metadata_files:
        data_basename = os.path.basename(data_file)
        data_uris.append(data_base_uri + data_basename)

    mint_nfts(user_addr, data_uris)


if __name__ == "__main__":
    lootbox("aoth")