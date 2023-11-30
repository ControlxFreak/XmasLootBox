# %%
import json
import os
import shutil
from typing import Tuple
import discord

import discord
from discord.ext import commands
from discord.abc import Messageable
from dotenv import load_dotenv
from dalle2 import Dalle2
from src.constants import START_WEEK, VALID_YEAR
from src.msgs import days_until_christmas, get_date, send_eoe_msg, send_impish_msg
from threading import Lock
from PIL.Image import Image as ImgType

# %% Initialization
# ============================================ #
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
SIM_FLAG = bool(int(os.getenv("SIM_FLAG")))

# Initialize the dalle API
dalle = Dalle2(OPENAI_TOKEN)

# Initialize the discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
help_command = commands.DefaultHelpCommand(no_category="Commands")
bot_description = "To be added to the game, contact @aoth.\n\n\
                   To claim a gift, use the command: !claim"
bot = commands.Bot(
    command_prefix="!",
    description=bot_description,
    help_command=help_command,
    intents=intents,
    heartbeat_timeout=1000000000,
    case_insensitive=True,
)

# Initialize the mutex locks
history_mutex = Lock()

# %% Utility Functions
# ============================================ #
async def verification(ctx, username: str) -> Tuple[str, str]:
    # Check that the user has not claimed a gift today
    username = username.lower()

    # Check that the game is still active
    countdown = days_until_christmas(VALID_YEAR)
    if countdown < 0:
        await send_eoe_msg(ctx)
        raise RuntimeError("End of Event.")

    history_mutex.acquire()
    with open("history.json", "r") as f:
        history = json.load(f)

    # Check to see if this user has claimed a loot box today
    year, week_num, day_num = get_date()
    day_hash = hash((year, week_num, day_num))

    if day_hash in history[username]:
        await send_impish_msg(ctx)
        history_mutex.release()
        raise RuntimeError("Multi-claim.")

    # Otherwise, they are admirable!
    # Update the dictionary notifying that they have claimed it today
    if not SIM_FLAG:
        history[username].append(day_hash)

    # Make a copy just in case
    shutil.copyfile("history.json", "/tmp/history.json")
    try:
        with open("history.json", "w") as f:
            json.dump(history, f)
    except Exception as exc:
        shutil.copyfile("history.json", "/tmp/history.json")
        history_mutex.release()
        raise exc

    # Release the mutex and return
    history_mutex.release()

    return (week_num - START_WEEK)

def make_uniq_dirs() -> Tuple[int, str, str, str]:
    """Create the unique image, nft, and metadata directories.

    This function also returns the first available NFT id as a biproduct so we don't have to re-read that file.
    """
    # Get the next NFT ID
    next_nft_mutex.acquire()

    with open("next_id", "r") as f:
        next_nft_id = int(f.readline())

    first_nft_id = next_nft_id

    # Write-back the next NFT ID so we can release this mutex lock as fast as possible
    shutil.copyfile("next_id", "/tmp/next_id")
    try:
        with open("next_id", "w") as f:
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
    nft_img[0].save(
        filename,
        save_all=True,
        append_images=nft_img[1:],
        optimize=True,
        duration=10,
        loop=0,
    )
    return

def save_metadata(
    metadata: Dict[str, str], unq_dat_dir: str, nft_files: List[str], nft_base_uri: str
) -> List[str]:
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
