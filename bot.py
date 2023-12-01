# %%
from datetime import datetime, date
import json
import os
import shutil
from typing import Tuple, List, Dict, Optional
import discord
from copy import deepcopy

from openai import OpenAI

import discord
from discord.ext import commands
from discord.abc import Messageable
from dotenv import load_dotenv
from src.constants import VALID_YEAR, OUT_DIR, START_WEEK
from src.artists import add_frame
from src.msgs import (
    days_until_christmas,
    send_created_msg,
    send_eoe_msg,
    send_impish_msg,
    send_invalid_username,
    send_recovered_msg,
    send_admirable_msg,
    send_not_bayesbrew_msg,
    send_error,
    send_success_msg,
    send_rares_msg,
    send_odds_msg,
    send_welcome_msg,
    send_joke_msg,
)
from src.generators import (
    generate_dalle_description,
    generate_dalle_art,
    generate_erc721_metadata,
    generate_example_art,
)
from src.rarity import (
    sample_rarity_label,
    sample_attributes,
    sample_frame,
    sample_rarity_label_uniform,
    get_rarity_pmf,
    get_rarity_labels,
)
from threading import Lock
from PIL.Image import Image as ImgType

# %% Initialization
# ============================================ #
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SIM_FLAG = bool(int(os.getenv("SIM_FLAG")))

# Initialize the dalle API
openai_client = OpenAI()

# Initialize the discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
help_command = commands.DefaultHelpCommand(no_category="Commands")
bot_description = "To be added to the game, contact @bayesbrew.\n\n\
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
rarities_mutex = Lock()


# %% Utility Functions
# ============================================ #
async def verification(ctx, username: str):
    """Verify that the game is active and that the user has not claimed today."""
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
    year, week_num, day_num = date.today().isocalendar()
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
    shutil.copyfile("history.json", "tmp/history.json")
    try:
        with open("history.json", "w") as f:
            json.dump(history, f)
    except Exception as exc:
        shutil.copyfile("history.json", "tmp/history.json")
        history_mutex.release()
        raise exc

    # Release the mutex and return
    history_mutex.release()


def get_week_num():
    """Get the week number relative to the start of the game."""
    _, week_num, _ = date.today().isocalendar()
    return week_num - START_WEEK


def save_nft(nft_img: List[ImgType], filename: str):
    """Save the NFT gif.

    This function is slow and should run in a separate thread.
    """
    nft_img[0].save(
        filename,
        save_all=True,
        append_images=nft_img[1:],
        optimize=True,
        duration=10,
        loop=0,
    )
    return


def save_metadata(metadata: List[ImgType], filename: str):
    """Save the metadata json.

    This function should run in a separate thread.
    """
    with open(filename, "w") as f:
        json.dump(metadata, f)
    return


def increment_rarity(username: str, rarity_label: str):
    """Increment the rarity statistic for this user."""
    rarities_mutex.acquire()
    with open("rarities.json", "r") as f:
        rarities = json.load(f)

    rarities[username][rarity_label] += 1

    with open("rarities.json", "w") as f:
        json.dump(rarities, f)
    rarities_mutex.release()


def decrement_rarity(username: str, rarity_label: str):
    """Decrement the rarity statistic for this user."""
    rarities_mutex.acquire()
    with open("rarities.json", "r") as f:
        rarities = json.load(f)

    rarities[username][rarity_label] -= 1

    with open("rarities.json", "w") as f:
        json.dump(rarities, f)
    rarities_mutex.release()


async def _recover(ctx: Messageable, username: str, rarity_label: Optional[str]):
    """Recover a user's daily gift.

    If rarity_level is None, the rarity statistics will also be adjusted.
    """
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
    year, week_num, day_num = date.today().isocalendar()
    day_hash = hash((year, week_num, day_num))

    # Check to see if this user has claimed a loot box today
    if day_hash in history[username]:
        history[username].remove(day_hash)

        # Make a copy just in case
        shutil.copyfile("history.json", "tmp/history.json")
        try:
            with open("history.json", "w") as f:
                json.dump(history, f)
        except Exception as exc:
            shutil.copyfile("history.json", "tmp/history.json")
            history_mutex.release()
            raise exc

    history_mutex.release()

    # ========================== #
    # Rarity
    # ========================== #
    if rarity_label is not None:
        print(f"Decrementing rarity for {username}, {rarity_label}")
        decrement_rarity(username, rarity_label)

    await send_recovered_msg(ctx, username)


async def _gift_util(
    ctx: Messageable,
    username: str,
    rarity_label: str,
    description: str,
    metadata: Dict[str, str],
):
    start = datetime.now()

    # Send the admirable message
    await send_admirable_msg(ctx, username, rarity_label, description)

    # ============================================ #
    # Setup the unique directory structure
    # ============================================ #
    datestr = datetime.today().strftime("%Y-%m-%d")

    # Generate unique paths
    uniq_dir = os.path.join(OUT_DIR, username)
    os.makedirs(uniq_dir, exist_ok=True)

    img_file = os.path.join(uniq_dir, f"{datestr}.png")
    nft_file = os.path.join(uniq_dir, f"{datestr}.gif")
    data_file = os.path.join(uniq_dir, f"{datestr}.json")

    # ============================================ #
    # Image Generation
    # ============================================ #
    # Generate the artwork
    print("Generating the artwork...")
    if SIM_FLAG:
        # Generate some example art so we don't have to query Dalle
        image = generate_example_art(img_file)
        revised_prompt = description
    else:
        # Generate the art using Dalle
        image, revised_prompt = generate_dalle_art(openai_client, description, img_file)

        if image is None:
            _recover(ctx, username, rarity_label)
            await send_error(ctx, username)
            raise RuntimeError("Dalle Error")

    # Sample the frame
    frame_name = sample_frame(rarity_label)

    # ============================================ #
    # NFT Generation
    # ============================================ #
    # Add the frame to each image and then save them
    # Spawn these in multiple threads since this can be done asynchronously and is slow
    print("Adding frames to the NFTs...")
    nft_img = add_frame(image, frame_name)

    print("Saving the NFTs...")
    save_nft(nft_img, nft_file)

    # Save the metadata jsons
    print("Saving the NFTs...")
    save_metadata(metadata, data_file)

    # Send a message to the new owner with images of their new NFTs!
    print("Complete!")
    await send_success_msg(ctx, username, nft_file, revised_prompt)

    stop = datetime.now()
    print("Elapsed Time: ", str(stop - start))


# %%
# Commands
# ============================================ #
@bot.command()
async def claim(ctx: Messageable):
    """Claim your daily gift!"""
    # ============================================ #
    # Verification
    # ============================================ #
    username = (ctx.message.author.name).lower()
    await verification(ctx, username)

    # ============================================ #
    # Sampling
    # ============================================ #
    print("Sampling the rarity and attributes...")
    # Sample the rarity level
    if SIM_FLAG:
        rarity_label = sample_rarity_label_uniform()
    else:
        week_num = get_week_num()
        rarity_label = sample_rarity_label(week_num)

    # Increment their rarity counter
    increment_rarity(username, rarity_label)

    # Sample the metadata
    attributes = sample_attributes(rarity_label)

    # Structure the text string
    description = generate_dalle_description(attributes)

    # ============================================ #
    # Metadata Generation
    # ============================================ #
    # Generate the ERC721-compliant metadata json
    metadata = generate_erc721_metadata(attributes, description)

    # ============================================ #
    # Gift
    # ============================================ #
    # Use the gift util to construct the gifts and send the message
    await _gift_util(ctx, username, rarity_label, description, metadata)


@bot.command()
async def topElfRecover(
    ctx: Messageable, username: str, rarity_label: Optional[str] = None
):
    """Only @bayesbrew can use this function.

    Recover the credits if something broke when a user tried to claim their gift.
    """
    # Check if I called it...
    if (ctx.message.author.name).lower() != "bayesbrew":
        await send_not_bayesbrew_msg(ctx)
        return

    await _recover(ctx, username, rarity_label)


@bot.command()
async def topElfPower(
    ctx: Messageable, username: str, rarity_label: str, description: str
):
    """Only @bayesbrew can use this function.

    Create an exact gift for someone.
    """
    # Check if I called it...
    if (ctx.message.author.name).lower() != "bayesbrew":
        await send_not_bayesbrew_msg(ctx)
        return

    # ============================================ #
    # Verification
    # ============================================ #
    await verification(ctx, username)

    # ============================================ #
    # Increment their rarity counter
    # ============================================ #
    increment_rarity(username, rarity_label)

    # ============================================ #
    # Metadata Generation
    # ============================================ #
    # Generate the ERC721-compliant metadata json
    metadata = generate_erc721_metadata({}, description)

    # ============================================ #
    # Gift
    # ============================================ #
    # Use the gift util to construct the gifts and send the message
    await _gift_util(ctx, username, rarity_label, description, metadata)


@bot.command()
async def create(ctx: Messageable, *, description: str):
    """Create your own daily gift!

    Aide my elves and provide a prompt to create your daily gift!
    Note that no attributes will be listed on OpenSea if you decide to use your own description.

    Args:
        description (str): Description of your artwork.
    """
    # ============================================ #
    # Verification
    # ============================================ #
    username = (ctx.message.author.name).lower()
    await verification(ctx, username)

    # ============================================ #
    # Sampling
    # ============================================ #
    print("Sampling the rarity and attributes...")
    # Sample the rarity level
    if SIM_FLAG:
        rarity_label = sample_rarity_label_uniform()
    else:
        week_num = get_week_num()
        rarity_label = sample_rarity_label(week_num)

    # Increment their rarity counter
    increment_rarity(username, rarity_label)

    # ============================================ #
    # Metadata Generation
    # ============================================ #
    # Generate the ERC721-compliant metadata json
    metadata = generate_erc721_metadata({}, description)

    # ============================================ #
    # Gift
    # ============================================ #
    # Use the gift util to construct the gifts and send the message
    await _gift_util(ctx, username, rarity_label, description, metadata)


@bot.command()
async def join(ctx: Messageable):
    """Create an account and join the game!"""
    username = (ctx.message.author.name).lower()

    # =============================== #
    # Verification
    # =============================== #
    all_members = [mem.name.lower() for mem in bot.get_all_members()]

    if username not in all_members:
        await send_invalid_username(ctx, username)
        return

    # =============================== #
    # History
    # =============================== #
    history_mutex.acquire()

    with open("history.json", "r") as f:
        history = json.load(f)

    if username in history.keys():
        history_mutex.release()
        await send_created_msg(ctx, username)
        return

    history[username] = []

    # Save the accounts file (first make a copy just in case...)
    shutil.copyfile("history.json", "tmp/history.json")
    try:
        with open("history.json", "w") as f:
            json.dump(history, f)
    except Exception as exc:
        shutil.copyfile("tmp/history.json", "history.json")
        raise exc

    history_mutex.release()

    # =============================== #
    # Rarities
    # =============================== #
    rarities_mutex.acquire()

    with open("rarities.json", "r") as f:
        rarities = json.load(f)

    rarity_labels = get_rarity_labels()
    rarities[username] = {r: 0 for r in rarity_labels}

    shutil.copyfile("rarities.json", "/tmp/rarities.json")
    try:
        with open("rarities.json", "w") as f:
            json.dump(rarities, f)
    except Exception as exc:
        print(exc)
        shutil.copyfile("/tmp/rarities.json", "rarities.json")

    rarities_mutex.release()

    # =============================== #
    # Send the msg
    # =============================== #
    await send_created_msg(ctx, username)


@bot.command()
async def rares(ctx: Messageable):
    """Display the number of rare NFTs everyone has!"""
    rarities_mutex.acquire()
    with open("rarities.json", "r") as f:
        rarities = json.load(f)
    rarities_mutex.release()
    await send_rares_msg(ctx, rarities)


@bot.command()
async def odds(ctx: Messageable):
    """Display this week's odds of getting various rarity level gifts!"""
    rarities_mutex.acquire()
    with open("rarities.json", "r") as f:
        rarities = json.load(f)
    rarities_mutex.release()

    week_num = get_week_num()
    pmf = get_rarity_pmf(week_num)
    await send_odds_msg(ctx, week_num, pmf, rarities)


@bot.command()
async def welcome(ctx: Messageable):
    """Send the welcome message."""
    await send_welcome_msg(ctx)


@bot.command()
async def joke(ctx: Messageable):
    """Tell a random Christmas joke!"""
    await send_joke_msg(ctx)


# Run the bot
bot.run(DISCORD_TOKEN)
