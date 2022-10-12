import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import datetime
from collections import defaultdict
from typing import Tuple
from src.rarity import sample_rarity_level, sample_attributes, sample_frame
from src.generators import generate_dalle_description, generate_dalle_art
from src.artists import add_frame

# Initialize the enviornment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL_ID = os.getenv("CHANNEL_ID")
OPENAI_USERNAME = os.getenv("OPENAI_USERNAME")
OPENAI_PASSWORD = os.getenv("OPENAI_PASSWORD")
OPENSEA_CONTRACT_URL = "TODO"

VALID_YEAR = 2022
START_WEEK = 49
END_WEEK = 53

# Initialize the daily present mapping and the participant list
# TODO: Store this in a database or file or something persistent in case the bot goes down
claimed_days = defaultdict(list)
participants = ["aoth"]

# Initialize the discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix=">")

def get_date() -> Tuple[int, int, int]:
    """Find the current date in ISO format (Year, Week Number, Day Number).
    """
    # Grab the current week number
    return datetime.date.today().isocalendar()

def days_until_christmas(year: int = VALID_YEAR) -> int:
    """Compute the number of days until Christmas."""
    xmas = datetime.date(year, 12, 25)
    today = datetime.date.today()
    return (xmas - today).days

def generate_christmas_countdown_msg(year: int = VALID_YEAR) -> str:
    """Generate a string that informs you of the number of days until Christmas!"""
    return f"There are: {days_until_christmas(year)} days until Christmas!!!!"

async def send_eoe_msg(ctx):
    """Generate the End of Event message.
    """
    # Create the embedded message
    embedVar = discord.Embed(
        title=f"Sorry {ctx.message.author.name}, Santa is Broke!",
        description=f"\
        Santa cannot afford loot boxes at the moment...\n \
        ```yaml\nBut never fear children, I invested all of my savings for next year's gifts into Dodge coin!\n```\
        Elon says it will moon by next Christmas, so I'll be a billionaire!\n\
        *...if not, Mrs. Claus will be PISSSSSSED...*\n\n\
        Keep being admirable and check back next year for more fat gains!\
        Ho Ho Ho!\n\n\
        ```css\n[{generate_christmas_countdown_msg(VALID_YEAR + 1)}]\n```\n\n\
        Checkout this year's Advent Calendar Collection at: {OPENSEA_CONTRACT_URL}\n\
        ",
        color=0xff0000
    )
    # Attach the image
    santa_rocket_file = discord.File("imgs/bot/santa_rocket.gif", filename="santa_rocket.gif")
    embedVar.set_image(url="attachment://santa_rocket.gif")
    # Send the message
    await ctx.channel.send(embed=embedVar, file=santa_rocket_file)

async def send_no_wallet_msg(ctx):
    """Generate the End of Event message.
    """
    # Configure the message
    embedVar = discord.Embed(
        title=f"Sorry {ctx.message.author.name}, You're on the Naughty List!",
        description="\
        ...Well more accurately, I don't see you on the Nice List.\n\
        If you would like to play and recieve gifts this year, contact @aoth to be added!\n\
        Ho Ho Ho Ho!\
        ",
        color=0xff0000
    )
    # Send the message
    await ctx.channel.send(embed=embedVar)

async def send_admirable_msg(ctx):
    """Sends the admirable message!"""
    # Configure the message
    embedVar = discord.Embed(
        title=f"Generating NFTs for {ctx.message.author.name}!",
        description=f"\
            ```diff\n+It Seems You Have Been Quite Admirable This Year!```\n\
            **Please stand-by while my elves generate your daily gifts!**\n\
            **I hope its value goes to the moon!**🪙🚀\n\n\
            This might take a moment, but I will let you know when your gift is ready!\n\n\
            ```css\n[{generate_christmas_countdown_msg()}]\n```",
        color=0x00ff00
    )
    lootbox_file = discord.File("imgs/bot/loot-box.gif", filename="loot_box.gif")
    embedVar.set_image(url="attachment://loot_box.gif")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=lootbox_file)

async def send_impish_msg(ctx):
    """Sends the impish message!"""
    # Configure the message
    embedVar = discord.Embed(
        title=f"How Impish of you {ctx.message.author.name}!",
        description=f"\
            ```diff\n-You have already claimed a loot box today...```\n\
            Greed is very impish!\
            If you are admirable, you can check back tomorrow for a new loot box.",
        color=0xff0000
    )
    impish_file = discord.File("imgs/bot/impish.jpg", filename="impish.jpg")
    embedVar.set_image(url="attachment://impish.jpg")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=impish_file)

async def send_error_msg(ctx):
    """Sends the erorr message to the user"""
    # Configure the message
    embedVar = discord.Embed(
        title=f"Well this is embarrassing...",
        description=f"\
            ```diff\n-An Error Occured Minting the NFTs for {ctx.message.author.name}...```\n\
            Contact @aoth and he will try to fix it or mint it manually for you.",
        color=0xff0000
    )
    shrug_file = discord.File("imgs/bot/shrug.jpg", filename="shrug.jpg")
    embedVar.set_image(url="attachment://shrug.jpg")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=shrug_file)

@bot.command()
async def lootbox(ctx):
    # Check if this username has registered to play and has setup an Ethereum wallet
    username = ctx.message.author.name
    if username.lower() not in participants:
        await send_no_wallet_msg(ctx)
        return

    # Get the current date
    year, week_num, day_num = get_date()
    day_hash = hash((year, week_num, day_num))

    # TODO: Add this back before release
    # Verify that the event is still valid
    # if (
    #     year != VALID_YEAR or
    #     week_num < START_WEEK or
    #     week_num > END_WEEK
    # ):
    #     # Unfortunately, the season has ended, but I haven't shutdown the bot yet...
    #     await send_eoe_msg(ctx)
    #     return

    # Check to see if this user has claimed a loot box today
    # if day_hash in claimed_days[username]:
    #     await send_impish_msg(ctx)
    #     return

    # Otherwise, they are admirable!
    # Update the dictionary notifying that they have claimed it today
    claimed_days[username].append(day_hash)

    # Send the admirable message
    await send_admirable_msg(ctx)

    # Sample the rarity level
    # TODO: Use the real week number when it becomes time
    rarity_level = sample_rarity_level(4)
    # TODO: Remove this debug message
    await ctx.channel.send(f"Rarity Level: {rarity_level}")

    # TODO: Remove
    rarity_level = "christmas miracle" # Just overwrite it for debugging

    # Sample the atributes
    attributes = sample_attributes(rarity_level)

    # # Sample the frame
    frame = sample_frame(rarity_level)

    # Structure the text string
    description = generate_dalle_description(attributes)
    print(description)

    # # Generate the artwork
    # images = generate_dalle_art(OPENAI_USERNAME, OPENAI_PASSWORD, description)

    # Save the artwork to disc
    # TODO: Fix this
    # image_names = [f"cat_santa_{i}" for i in range(1, 5)]

    # # Add the frame to each image
    # nfts = [
    #     add_frame(image_name, "speedlines") for image_name in image_names
    # ]

    # Save the NFT images to disk

    # Create the metadata JSON files

    # Save the metadata files to disk

    # Call our NodeJS tool to:
    #   * Push the NFTs to IPFS
    #   * Update the metadata JSON files with each NFT's corresponding CID location
    #   * Push the metadata to IPFS
    #   * Mint the NFTs
    # if os.system(f"node scripts/xmaslootbox.js {username} {nft_dir} {data_dir}"):
    #     await send_error_msg(ctx)
    #     return

    # Send a message to the new owner with images of their new NFTs!
    # await send_success_msg(ctx)


# Run the bot
bot.run(TOKEN)
