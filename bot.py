import os
from copy import deepcopy
import warnings
from typing import List, Dict, Tuple, Optional
import random
import json
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import shutil
from datetime import datetime

import discord
from discord.ext import commands
from discord.abc import Messageable
from dotenv import load_dotenv
from dalle2 import Dalle2
from PIL.Image import Image as ImgType

from src.rarity import (
    sample_rarity_label,
    sample_attributes,
    sample_frame,
    sample_rarity_label_uniform,
    get_rarity_pmf,
    get_rarity_labels,
)
from src.generators import (
    generate_dalle_description,
    generate_dalle_art,
    generate_erc721_metadata,
    generate_example_art,
)
from src.artists import add_frame, create_nft_preview
from src.msgs import (
    get_date,
    send_addr_msg,
    send_admirable_msg,
    send_all_balances_msg,
    send_balance_msg,
    send_created_msg,
    send_eoe_msg,
    send_error,
    send_daily_eth_error,
    send_mint_error,
    send_bot_faq_msg,
    send_not_aoth_msg,
    send_web3_faq_msg,
    send_impish_msg,
    send_invalid_username,
    send_nft_dne_msg,
    send_nft_msg,
    send_no_nfts_msg,
    send_no_wallet_msg,
    send_nobody_nfts_msg,
    send_odds_msg,
    send_not_your_nft_msg,
    send_success_msg,
    send_transfer_conf_msg,
    send_transfer_error_msg,
    send_transfer_success_msg,
    send_user_has_account,
    send_joke_msg,
    send_users_msg,
    send_welcome_msg,
    send_rares_msg,
    send_recovered_msg,
    send_voted_msg,
    send_already_voted_msg,
    send_wrong_team_msg,
    send_votes_msg,
)
from src.constants import (
    VALID_YEAR,
    START_WEEK,
    OUT_DIR,
)
from src.eth import (
    pin_to_ipfs,
    mint_nfts,
    get_from_ipfs,
    create_acct,
    get_balance,
    get_owner,
    transfer_nft,
    send_daily_eth,
)

warnings.filterwarnings("ignore")

# ============================================ #
# Initialize the environment variables
# ============================================ #
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
SIM_FLAG = bool(int(os.getenv("SIM_FLAG")))

WINNING_TEAM = "argentina"

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
accounts_mutex = Lock()
history_mutex = Lock()
owners_mutex = Lock()
next_nft_mutex = Lock()
rarities_mutex = Lock()
voting_mutex = Lock()

# Initialize a threadpool executor
executor = ThreadPoolExecutor(max_workers=4)


# ============================================ #
# Utilities
# ============================================ #
async def verification(ctx, username: str) -> Tuple[str, str]:
    # Get the current date and create a date hash
    year, week_num, day_num = get_date()
    day_hash = hash((year, week_num, day_num))

    # Check that the date is valid
    if year != VALID_YEAR:
        # Unfortunately, the season has ended, but I haven't shutdown the bot yet...
        await send_eoe_msg(ctx)
        raise RuntimeError("End of Event.")

    user_addr = await user_check(ctx, username, day_hash)
    return user_addr, (week_num - START_WEEK)


async def user_check(ctx: Messageable, username: str, day_hash: int) -> str:
    """Verify that this user:
    1. Has an account
    2. Has not tried to claim today
    """
    username = username.lower()

    # ========================== #
    # Accounts
    # ========================== #
    accounts_mutex.acquire()
    with open("accounts.json", "r") as f:
        accounts = json.load(f)
    accounts_mutex.release()

    # Check if this username has registered to play and has setup an Ethereum wallet
    if username not in accounts.keys():
        await send_no_wallet_msg(ctx, username)
        raise RuntimeError("No Wallet.")

    # ========================== #
    # History
    # ========================== #
    history_mutex.acquire()
    with open("history.json", "r") as f:
        history = json.load(f)

    # Check to see if this user has claimed a loot box today
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

    return accounts[username]["address"]


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


async def _recover(ctx: Messageable, username: str, rarity_label: str):
    # ========================== #
    # Accounts
    # ========================== #
    accounts_mutex.acquire()
    with open("accounts.json", "r") as f:
        accounts = json.load(f)
    accounts_mutex.release()

    # Check if this username has registered to play and has setup an Ethereum wallet
    if username not in accounts.keys():
        await send_no_wallet_msg(ctx, username)
        raise RuntimeError("No Wallet.")

    # ========================== #
    # History
    # ========================== #
    year, week_num, day_num = get_date()
    day_hash = hash((year, week_num, day_num))

    history_mutex.acquire()
    with open("history.json", "r") as f:
        history = json.load(f)

    # Check to see if this user has claimed a loot box today
    if day_hash in history[username]:
        history[username].remove(day_hash)

        # Make a copy just in case
        shutil.copyfile("history.json", "/tmp/history.json")
        try:
            with open("history.json", "w") as f:
                json.dump(history, f)
        except Exception as exc:
            shutil.copyfile("history.json", "/tmp/history.json")
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
    user_addr: str,
    rarity_label: str,
    description: str,
    metadata: Dict[str, str],
):
    start = datetime.now()

    # Send the admirable message
    await send_admirable_msg(ctx, username, rarity_label, description)

    try:
        # ============================================ #
        # Setup the unique directory structure
        # ============================================ #
        (
            first_nft_id,
            unq_img_dir,
            unq_nft_dir,
            unq_dat_dir,
            unq_prv_dir,
        ) = make_uniq_dirs()

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

            if images is None or img_files is None:
                _recover(ctx, username, rarity_label)
                await send_error(ctx, username)
                raise RuntimeError("Dalle Error")

        # Sample the frame
        frame_name = sample_frame(rarity_label)

        # ============================================ #
        # NFT Generation
        # ============================================ #
        num_imgs = len(images)  # This should always be 4 according to dalle...
        nft_files = [
            os.path.join(unq_nft_dir, f"{first_nft_id + idx}.gif")
            for idx in range(num_imgs)
        ]

        # Add the frame to each image and then save them
        # Spawn these in multiple threads since this can be done asynchronously and is slow
        print(f"Adding frames to the NFTs ({first_nft_id})...")
        nft_imgs = [
            res for res in executor.map(add_frame, images, num_imgs * [frame_name])
        ]

        print(f"Saving the NFTs ({first_nft_id})...")
        _ = [res for res in executor.map(save_nft, nft_imgs, nft_files)]

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
        with open("owners.json", "r") as f:
            owners = json.load(f)

        owners[username].append(
            {
                "img": img_cid,
                "nft": nft_cid,
                "data": data_cid,
                "ids": [first_nft_id + i for i in range(4)],
            }
        )

        shutil.copyfile("owners.json", "/tmp/owners.json")
        try:
            with open("owners.json", "w") as f:
                json.dump(owners, f)
        except Exception as exc:
            shutil.copyfile("/tmp/owners.json", "owners.json")
            raise exc

        owners_mutex.release()

        print("Minting NFTs...")
        if not SIM_FLAG:
            res = await mint_nfts(user_addr, data_uris)
            if not res:
                await send_mint_error(ctx)
                raise RuntimeError("Mint Error")

        # =============================== #
        # Send 0.010 eth to get started
        # =============================== #
        # print("Sending eth...")
        # if not SIM_FLAG:
        #     res = await send_daily_eth(user_addr)
        #     if not res:
        #         # If we ran out of eth or it didn't work for some reason... this function should still continue
        #         await send_daily_eth_error(ctx)

        # Create the preview image
        print("Creating Preview...")
        preview = create_nft_preview(nft_imgs, frame_name)
        preview_filename = os.path.join(unq_prv_dir, "preview.gif")
        preview[0].save(
            preview_filename,
            save_all=True,
            append_images=preview[1:],
            optimize=True,
            duration=10,
            loop=0,
        )

        # Send a message to the new owner with images of their new NFTs!
        print("Complete!")
        await send_success_msg(
            ctx, username, user_addr, first_nft_id, preview_filename, img_cid, nft_cid
        )

    finally:
        # Quickly cleanup the directories
        shutil.rmtree(unq_img_dir)
        shutil.rmtree(unq_nft_dir)
        shutil.rmtree(unq_dat_dir)
        shutil.rmtree(unq_prv_dir)

    stop = datetime.now()
    print("Elapsed Time: ", str(stop - start))


def increment_rarity(username: str, rarity_label: str):
    rarities_mutex.acquire()
    with open("rarities.json", "r") as f:
        rarities = json.load(f)

    rarities[username][rarity_label] += 1

    with open("rarities.json", "w") as f:
        json.dump(rarities, f)
    rarities_mutex.release()


def decrement_rarity(username: str, rarity_label: str):
    rarities_mutex.acquire()
    with open("rarities.json", "r") as f:
        rarities = json.load(f)

    rarities[username][rarity_label] -= 1

    with open("rarities.json", "w") as f:
        json.dump(rarities, f)
    rarities_mutex.release()


async def _create_fifa_gift(ctx: Messageable, username: str, team: str):
    start = datetime.now()

    # Get the user's information
    accounts_mutex.acquire()
    with open("accounts.json", "r") as f:
        accounts = json.load(f)
    accounts_mutex.release()

    # Check if this username has registered to play and has setup an Ethereum wallet
    # This really should be impossible to hit... but just in case...
    if username not in accounts.keys():
        await send_no_wallet_msg(ctx, username)
        raise RuntimeError("No Wallet.")

    user_addr = accounts[username]["address"]

    # Cleanup the username a bit for DALLE
    clean_username = username.replace("shit", "sheet")
    clean_username = username.replace("bitch", "beach")

    # Construct the description and rarity  border
    if team == WINNING_TEAM:
        description = f"One-of-a-kind caricature of the {team} soccer team celebrating after winning the World Cup while it is snowing in an extremely high detailed digital art style made specifically as a gift for {clean_username}"
        frame_name = "worldcup"
        metadata = generate_erc721_metadata({"worldcup": "winner"}, description)
    else:
        description = f"One-of-a-kind caricature of the {team} soccer team cheering for {WINNING_TEAM} after they won the World Cup with a snowy background in an extremely high detailed digital art style made specifically as a gift for {clean_username}"
        frame_name = None
        metadata = generate_erc721_metadata({}, description)

    try:
        # ============================================ #
        # Setup the unique directory structure
        # ============================================ #
        (
            first_nft_id,
            unq_img_dir,
            unq_nft_dir,
            unq_dat_dir,
            unq_prv_dir,
        ) = make_uniq_dirs()

        # ============================================ #
        # Image Generation
        # ============================================ #
        # Generate the artwork
        print("Generating the artwork...")
        # Generate the art using Dalle
        images, img_files = generate_dalle_art(dalle, description, unq_img_dir)

        if images is None or img_files is None:
            await send_error(ctx, username)
            raise RuntimeError(f"{username} - Dalle Error")

        # ============================================ #
        # NFT Generation
        # ============================================ #
        num_imgs = len(images)  # This should always be 4 according to dalle...
        nft_files = [
            os.path.join(unq_nft_dir, f"{first_nft_id + idx}.gif")
            for idx in range(num_imgs)
        ]

        # Add the frame to each image and then save them
        # Spawn these in multiple threads since this can be done asynchronously and is slow
        print(f"Adding frames to the NFTs ({first_nft_id})...")
        nft_imgs = [
            res for res in executor.map(add_frame, images, num_imgs * [frame_name])
        ]

        print(f"Saving the NFTs ({first_nft_id})...")
        _ = [res for res in executor.map(save_nft, nft_imgs, nft_files)]

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
        with open("owners.json", "r") as f:
            owners = json.load(f)

        owners[username].append(
            {
                "img": img_cid,
                "nft": nft_cid,
                "data": data_cid,
                "ids": [first_nft_id + i for i in range(4)],
            }
        )

        shutil.copyfile("owners.json", "/tmp/owners.json")
        try:
            with open("owners.json", "w") as f:
                json.dump(owners, f)
        except Exception as exc:
            shutil.copyfile("/tmp/owners.json", "owners.json")
            raise exc

        owners_mutex.release()

        print("Minting NFTs...")
        if not SIM_FLAG:
            res = await mint_nfts(user_addr, data_uris)
            if not res:
                await send_mint_error(ctx)
                raise RuntimeError("Mint Error")

        # Create the preview image
        print("Creating Preview...")
        preview = create_nft_preview(nft_imgs, frame_name)
        preview_filename = os.path.join(unq_prv_dir, "preview.gif")
        preview[0].save(
            preview_filename,
            save_all=True,
            append_images=preview[1:],
            optimize=True,
            duration=10,
            loop=0,
        )

        # Send a message to the new owner with images of their new NFTs!
        print("Complete!")
        await send_success_msg(
            ctx, username, user_addr, first_nft_id, preview_filename, img_cid, nft_cid
        )

    finally:
        # Quickly cleanup the directories
        shutil.rmtree(unq_img_dir)
        shutil.rmtree(unq_nft_dir)
        shutil.rmtree(unq_dat_dir)
        shutil.rmtree(unq_prv_dir)

    stop = datetime.now()
    print("Elapsed Time: ", str(stop - start))


# ============================================ #
# Commands
# ============================================ #
@bot.command()
async def claim(ctx: Messageable):
    """Claim your daily gift!"""
    # ============================================ #
    # Verification
    # ============================================ #
    username = (ctx.message.author.name).lower()
    user_addr, week_num = await verification(ctx, username)

    # ============================================ #
    # Sampling
    # ============================================ #
    print("Sampling the rarity and attributes...")
    # Sample the rarity level
    if SIM_FLAG:
        rarity_label = sample_rarity_label_uniform()
    else:
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
    await _gift_util(ctx, username, user_addr, rarity_label, description, metadata)


@bot.command()
async def topElfRecover(
    ctx: Messageable, username: str, rarity_label: Optional[str] = None
):
    """Only @aoth can use this function.

    Recover the credits if something broke when a user tried to claim their gift.
    """
    # Check if I called it...
    if (ctx.message.author.name).lower() != "aoth":
        await send_not_aoth_msg(ctx)
        return

    await _recover(ctx, username, rarity_label)


@bot.command()
async def topElfPower(
    ctx: Messageable, username: str, rarity_label: str, description: str
):
    """Only @aoth can use this function.

    Create an exact gift for someone.
    """
    # Check if I called it...
    if (ctx.message.author.name).lower() != "aoth":
        await send_not_aoth_msg(ctx)
        return

    # ============================================ #
    # Verification
    # ============================================ #
    user_addr, _ = await verification(ctx, username)

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
    await _gift_util(ctx, username, user_addr, rarity_label, description, metadata)


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
    user_addr, week_num = await verification(ctx, username)

    # ============================================ #
    # Sampling
    # ============================================ #
    print("Sampling the rarity and attributes...")
    # Sample the rarity level
    if SIM_FLAG:
        rarity_label = sample_rarity_label_uniform()
    else:
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
    await _gift_util(ctx, username, user_addr, rarity_label, description, metadata)


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
    # Accounts
    # =============================== #
    accounts_mutex.acquire()

    with open("accounts.json", "r") as f:
        accounts = json.load(f)

    if username in accounts:
        await send_user_has_account(ctx, username, accounts[username]["address"])
        accounts_mutex.release()
        return

    # Generate a private / public key
    private_key, public_key = create_acct()

    accounts[username] = {"address": public_key, "private": private_key}

    # Save the accounts file (first make a copy just in case...)
    shutil.copyfile("accounts.json", "/tmp/accounts.json")
    try:
        with open("accounts.json", "w") as f:
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
    except Exception as exc:
        print(exc)
        shutil.copyfile("/tmp/owners.json", "owners.json")

    owners_mutex.release()

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
    await send_created_msg(ctx, username, public_key)


@bot.command()
async def address(ctx: Messageable):
    """Display your Ethereum address."""
    # Get the caller's name
    username = (ctx.message.author.name).lower()

    # Get their address
    accounts_mutex.acquire()
    with open("accounts.json", "r") as f:
        accounts = json.load(f)
    accounts_mutex.release()

    if username not in accounts:
        await send_no_wallet_msg(ctx, username)
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
    with open("accounts.json", "r") as f:
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
    with open("owners.json", "r") as f:
        owners = json.load(f)
    owners_mutex.release()

    # Load the address
    accounts_mutex.acquire()
    with open("accounts.json", "r") as f:
        accounts = json.load(f)
    accounts_mutex.release()

    # Check to see that this user exists
    if (username not in owners) or (username not in accounts):
        await send_no_wallet_msg(ctx, username)
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
    with open("owners.json", "r") as f:
        owners = json.load(f)
    owners_mutex.release()

    # Load the address
    accounts_mutex.acquire()
    with open("accounts.json", "r") as f:
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
        await send_nft_msg(
            ctx, username, nft_img, nft_id, accounts[username]["address"]
        )
        return

    # We never found anyone
    await send_nobody_nfts_msg(ctx)


@bot.command()
async def balances(ctx: Messageable, username: Optional[str] = None):
    """Display ethereum and NFTs balances.

    Args:
        username (str): Name of the user whose balance you'd like to display. Use their official discord name (with no numbers), not their server nickname.
            If not included, then this will display everyone's balance.
    """

    # Get the accounts
    accounts_mutex.acquire()
    with open("accounts.json", "r") as f:
        accounts = json.load(f)
    accounts_mutex.release()

    # Check if the username input argument is none or not
    if username is None:
        bals = {}
        for username, keys in accounts.items():
            # Get the balances
            user_addr = keys["address"]
            eth_balance, nft_balance = await get_balance(user_addr)
            bals[username] = {"eth": eth_balance, "nft": nft_balance}

        # Format the message
        await send_all_balances_msg(ctx, bals)
    else:
        # If it is not None, check it exists and send just that balance
        if username not in accounts:
            await send_no_wallet_msg(ctx, username)
            return

        user_addr = accounts[username]["address"]

        # Get the balances
        eth_balance, nft_balance = await get_balance(user_addr)

        # Format the message
        await send_balance_msg(ctx, username, eth_balance, nft_balance, user_addr)


@bot.command()
async def rares(ctx: Messageable):
    """Display the number of rare NFTs everyone has!"""
    rarities_mutex.acquire()
    with open("rarities.json", "r") as f:
        rarities = json.load(f)
    rarities_mutex.release()
    await send_rares_msg(ctx, rarities)


@bot.command()
async def gift(ctx: Messageable, recipient: str, nft_id: int):
    """Randomly send one of your NFTs to a user!

    WARNING: This will use some of your ethereum to pay for the gas fees!

    Args:
        ctx (Messageable): Discord Context
        recipient (str): Recipient of the NFT. Use their official discord name (with no numbers), not their server nickname.
    """
    recipient = recipient.lower()
    sender = (ctx.message.author.name).lower()

    # Get the accounts
    accounts_mutex.acquire()
    with open("accounts.json", "r") as f:
        accounts = json.load(f)
    accounts_mutex.release()

    # Check the accounts exist
    if sender not in accounts:
        await send_no_wallet_msg(ctx, sender)
        return

    if recipient not in accounts:
        await send_no_wallet_msg(ctx, recipient)
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

    # Get the addresses
    recipient_addr = accounts[recipient]["address"]

    # Send a confirmation message
    await send_transfer_conf_msg(ctx, sender, recipient, nft_id)

    # Conduct the transaction
    res = await transfer_nft(sender_addr, sender_priv, recipient_addr, nft_id)

    if res is None:
        await send_transfer_error_msg(ctx, sender, recipient, nft_id)
        return

    await send_transfer_success_msg(
        ctx, sender, recipient, nft_id, sender_addr, recipient_addr
    )


@bot.command()
async def odds(ctx: Messageable):
    """Display this week's odds of getting various rarity level gifts!"""
    rarities_mutex.acquire()
    with open("rarities.json", "r") as f:
        rarities = json.load(f)
    rarities_mutex.release()

    _, week_num, _ = get_date()
    week_num = week_num - START_WEEK
    pmf = get_rarity_pmf(week_num)
    await send_odds_msg(ctx, week_num, pmf, rarities)


@bot.command()
async def faq(ctx: Messageable, topic: str = "bot"):
    """Frequently asked questions about the bot or web3.

    Args:
        topic (optional[str]): FAQ topic that you would like to display.
            Available options are: "bot", "web3", or "all".
            If not supplied, it will default to "bot".
    """
    if topic.lower() not in ["bot", "web3", "all"]:
        await ctx.send(
            f"{topic} is not a supported FAQ topic.\nSee to '!help faq' for more details."
        )

    if topic.lower() == "bot" or topic.lower() == "all":
        await send_bot_faq_msg(ctx)

    if topic.lower() == "web3" or topic.lower() == "all":
        await send_web3_faq_msg(ctx)


@bot.command()
async def vote(ctx: Messageable, team: str, force_str: str = ""):
    """Vote for the FIFA world cup champion."""
    username = (ctx.message.author.name).lower()

    # Read the voting file
    voting_mutex.acquire()
    with open("votes.json", "r") as f:
        votes = json.load(f)
    voting_mutex.release()

    # Do some checks unless they force the vote
    if force_str.lower() != "-f":
        # Check if they've already voted
        if username in votes:
            await send_already_voted_msg(ctx, username, votes[username])
            return

        # Check that the team is either Argentina or France
        if team.lower() not in ["argentina", "france"]:
            await send_wrong_team_msg(ctx, username, team)
            return

    # Otherwise, add their vote and return
    votes[username] = team.lower()

    shutil.copyfile("votes.json", "/tmp/votes.json")
    try:
        with open("votes.json", "w") as f:
            json.dump(votes, f)
    except Exception as exc:
        shutil.copyfile("/tmp/votes.json", "votes.json")
        raise exc

    await send_voted_msg(ctx, username, votes[username])


@bot.command()
async def votes(ctx: Messageable):
    """Display the votes for the FIFA world cup champion."""

    # Read the voting file
    voting_mutex.acquire()
    with open("votes.json", "r") as f:
        votes = json.load(f)
    voting_mutex.release()

    await send_votes_msg(ctx, votes)


@bot.command()
async def fifagifts(ctx: Messageable):
    """Only @aoth can use this function.

    Send the FIFA gifts to this server!
    """
    server_id = ctx.guild.id

    # Check if I called it...
    if (ctx.message.author.name).lower() != "aoth":
        await send_not_aoth_msg(ctx)
        return

    # Read the voting file
    voting_mutex.acquire()
    with open("votes.json", "r") as f:
        votes = json.load(f)
    voting_mutex.release()

    # Read the servers file
    with open("servers.json", "r") as f:
        servers = json.load(f)

    user_list = servers[str(server_id)]

    # Loop through the votes and create the gifts
    for user, team in votes.items():
        if user in user_list:
            print(f"Creating fifa gift for {user}")
            await _create_fifa_gift(ctx, user, team)


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
