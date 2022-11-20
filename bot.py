import os
from copy import deepcopy
import warnings
from typing import List, Dict, Tuple

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
from src.msgs import get_date, send_eoe_msg, send_no_wallet_msg, send_admirable_msg, send_impish_msg, send_error_msg, send_success_msg, send_not_aoth_msg, send_addr_msg, send_created_msg
from src.constants import START_WEEK, END_WEEK, VALID_YEAR
from src.eth import pin_to_ipfs#, mint_nfts

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

# Initialize the discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix=">")

# Initialize the mutex locks
participants_mutex = Lock()
next_nft_mutex = Lock()
addresses_mutex = Lock()

# ============================================ #
# Utilities
# ============================================ #
async def participant_check(ctx: Messageable, username: str, day_hash: int):
    """Verify that this participant:
    1. Has an account
    2. Has not tried to claim today
    """
    participants_mutex.acquire()

    # Open the participants json
    with open("participants.json", 'r') as f:
        participants = json.load(f)

    # Check if this username has registered to play and has setup an Ethereum wallet
    if username.lower() not in participants.keys():
        await send_no_wallet_msg(ctx)
        participants_mutex.release()
        raise RuntimeError("No Wallet.")

    # Check to see if this user has claimed a loot box today
    if (day_hash in participants[username] and not SIM_FLAG):
        await send_impish_msg(ctx)
        participants_mutex.release()
        raise RuntimeError("Multi-claim.")

    # Otherwise, they are admirable!
    # Update the dictionary notifying that they have claimed it today
    participants[username].append(day_hash)

    with open("participants.json", 'w') as f:
        json.dump(participants, f)

    # Release the mutex and return
    participants_mutex.release()


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
                    optimize = False, duration = 10, loop=0)
        nft_files.append(filename)
        next_nft_id+=1

    return first_nft_id, nft_files

def save_metadata(metadata: Dict[str, str], description: str, first_nft_id: int, nft_files: List[str], nft_base_uri: str) -> List[str]:
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
        metadata_cpy["image"] = nft_base_uri + "\\" + nft_base

        # Save the file
        data_file = os.path.join(unq_nft_data_dir, f"{nft_id}.json")
        with open(data_file, "w") as f:
            json.dump(metadata_cpy, f)
        data_files.append(data_file)

    return data_files


# ============================================ #
# Commands
# ============================================ #
@bot.command()
async def lootbox(ctx: Messageable):
    try:
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

        # Check that the participant has an account setup
        username = (ctx.message.author.name).lower()
        await participant_check(ctx, username, day_hash)

        # If they pass, they can play!
        # Send the admirable message
        await send_admirable_msg(ctx)

        # ============================================ #
        # Sampling
        # ============================================ #
        # Sample the rarity level
        # TODO: vv Use the real week number when it becomes time vv
        # rarity_level = sample_rarity_label(week_num, SIM_FLAG)
        rarity_level = sample_rarity_label_uniform()
        # TODO: ^^ Use the real week number when it becomes time ^^

        # Sample the metadata
        attributes = sample_attributes(rarity_level)

        # ============================================ #
        # Image Generation
        # ============================================ #
        # Structure the text string
        description = generate_dalle_description(attributes)
        await ctx.channel.send(f"Generating:\n{description}\nFor: {username}")

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
        data_base_uri = f"ipfs://{nft_cid}/"
        print(f"Data URI: {data_base_uri}")

        # Mint the NFTs

        # Send a message to the new owner with images of their new NFTs!
        await send_success_msg(ctx)

    finally:
        # Release the mutex, wether we hit an exception or not
        # NOTE: I know that this could cause an edge-case where this releases a lock that another thread is using...
        # However, I'm willing to take that risk since it is such an edge-case.
        # The one most at risk is the addresses_mutex, but honestly the odds of a conflict is extremely low, especially after the first day.
        if participants_mutex.locked():
            participants_mutex.release()

        if next_nft_mutex.locked():
            next_nft_mutex.release()

        if addresses_mutex.locked():
            addresses_mutex.release()


@bot.command()
async def create(ctx: Messageable, participant: str, participant_addr: str):
    # Make sure that the only user that is allowed to call this is me
    username = (ctx.message.author.name).lower()

    if username.lower() != "aoth":
        send_not_aoth_msg(ctx)
        return

    # Add the participant to the participants file
    participants_mutex.acquire()

    with open("participants.json", 'r') as f:
        participants = json.load(f)

    participants[participant] = []

    with open("participants.json", 'w') as f:
        json.dump(participants, f)

    # Release the mutex and return
    participants_mutex.release()

    # Add the ethereum address
    addresses_mutex.acquire()
    with open("addresses.json", 'r') as f:
        addresses = json.load(f)

    addresses[participant] = participant_addr

    with open("addresses.json", 'w') as f:
        json.dump(addresses, f)

    addresses_mutex.release()

    await send_created_msg(ctx, participant)


@bot.command()
async def address(ctx: Messageable):
    # Get the caller's name
    username = (ctx.message.author.name).lower()

    # Get their address
    addresses_mutex.acquire()
    with open("addresses.json", 'r') as f:
        addresses = json.load(f)
    addresses_mutex.release()

    if username not in addresses:
        await send_no_wallet_msg(ctx)
        return

    participant_addr = addresses[username]

    # Send them a message
    await send_addr_msg(ctx, participant_addr)

# Run the bot
bot.run(DISCORD_TOKEN)
