import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import datetime

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

# Initialize the discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix=">")

def days_until_christmas() -> int:
    """Compute the number of days until Christmas."""
    xmas = datetime.date(VALID_YEAR, 12, 25)
    today = datetime.date.today()
    return (xmas - today).days


def get_week_number() -> int:
    """Find the current week number and ensure that the event is still active.

    The returned week number is relative to the start week.
    """
    # Grab the current week number
    today = datetime.date.today()
    year, week_num, _ = today.isocalendar()

    # Verify that the event is still valid
    if (
        year != VALID_YEAR or
        week_num < START_WEEK or
        week_num > END_WEEK
    ):
        print("The event has concluded.")
        print(f"Checkout {OPENSEA_CONTRACT_URL} to see the collection that was minted this year!")
        exit()

    # Return the week number as an offset from the start week
    return week_num - START_WEEK

# @bot.event
# async def on_message(message):
#     # Get the message author
#     author = message.author

#     # Ignore yourself mr. saltbot
#     if author == bot.user:
#         return

#     # Handle the get command
#     if '/pts' in message.content.lower():
#         await message.channel.send(f".")

#     return None

@bot.command()
async def lootbox(ctx):
    # Create an embedded image of the lootbox
    embedVar = discord.Embed(
        title=f"Generating NFTs for {ctx.message.author.name}!",
        description=f"\
            There are: {days_until_christmas()} days until Christmas!!!!\n\n\
            Please stand-by while I generate your gifts, this might take a moment!\n\n\
            I will let you know when your gift is ready!",
        color=0x00ff00
    )
    lootbox_file = discord.File("imgs/loot-box.gif", filename="loot_box.gif")
    embedVar.set_image(url="attachment://loot_box.gif")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=lootbox_file)

# Run the bot
bot.run(TOKEN)
