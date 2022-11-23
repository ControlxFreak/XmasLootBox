import datetime
from typing import Tuple

import discord
from table2ascii import table2ascii

from .rarity import get_rarity_color
from .artists import create_nft_preview
from .constants import VALID_YEAR, OPENSEA_URL


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
    return f"{days_until_christmas(year)} days until Christmas!!!!"

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
        Checkout this year's Advent Calendar Collection at: [OpenSea]({OPENSEA_URL})\n\
        ",
        color=0xff0000
    )
    # Attach the image
    santa_rocket_file = discord.File("assets/msgs/santa_rocket.gif", filename="santa_rocket.gif")
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
    impish_file = discord.File("assets/msgs/impish.jpg", filename="impish.jpg")
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
    shrug_file = discord.File("assets/msgs/shrug.jpg", filename="shrug.jpg")
    embedVar.set_image(url="attachment://shrug.jpg")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=shrug_file)

async def send_success_msg(ctx, addr, first_nft_id, preview, img_cid, nft_cid):
    """Send the success message."""
    # Configure the message
    embedVar = discord.Embed(
        title=f"Your Gift is available, {ctx.message.author.name}!",
        description=f"\
        You can check out your updated collection on [OpenSea](https://testnets.opensea.io/{addr}?tab=collected&search[sortBy]=CREATED_DATE&search[sortAscending]=false),\n\
        or download the [raw images](https://violet-legal-antelope-340.mypinata.cloud/ipfs/{img_cid}) and [NFTs](https://violet-legal-antelope-340.mypinata.cloud/ipfs/{nft_cid})\n\
        **Your NFT ID's are: {first_nft_id}, {first_nft_id+1}, {first_nft_id+2}, and {first_nft_id+3}.**\n\
        (It might take ~1 minute to register on OpenSea)\n\
        Here is a small preview:",
        color=0x00ff00
    )
    prev_file = discord.File(preview, filename=preview)
    embedVar.set_image(url=f"attachment://{preview}")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=prev_file)

async def send_not_aoth_msg(ctx):
    """Send the not aoth message for creating new users."""
    # Configure the message
    embedVar = discord.Embed(
        title=f"You Are Not Authorized To Create Accounts, {ctx.message.author.name}!",
        description=f"\
        I'm sure @aoth would be happy to help. :)\n\
        If you are interested in creating an ethereum address, @aoth can help you with that too!",
        color=0xff0000
    )
    stop_file = discord.File("assets/msgs/stop.jpg", filename="stop.jpg")
    embedVar.set_image(url="attachment://stop.jpg")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=stop_file)

async def send_created_msg(ctx, username, addr):
    # Configure the message
    embedVar = discord.Embed(
        title=f"Created an account for {username}!\nYour Ethereum address is:\n{addr}",
        description=f"\
        You should be able to collect a loot box right away, @{username}!\n\
        Use the `>help` command to get started.",
        color=0x00ff00
    )
    santa_file = discord.File("assets/msgs/santa_nft.png", filename="santa_nft.png")
    embedVar.set_image(url="attachment://santa_nft.png")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=santa_file)

async def send_addr_msg(ctx, addr):
    """Send the address message for when a user requests it."""
    # Configure the message
    embedVar = discord.Embed(
        title=f"{ctx.message.author.name}, your Ethereum address is:\n{addr}",
        description=f"\
        **You can find your collection on [OpenSea](https://testnets.opensea.io/{addr})**\n\
        If you are interested in understanding more about Ethereum addresses, ask @aoth!",
        color=0x00873E
    )
    eth_file = discord.File("assets/msgs/eth.jpg", filename="eth.jpg")
    embedVar.set_image(url="attachment://eth.jpg")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=eth_file)

async def send_user_has_account(ctx, username, addr):
    """Send the notification that this user already has an account."""
    # Configure the message
    embedVar = discord.Embed(
        title=f"{username} already has an account!\nYour Ethereum address is:\n{addr}",
        description=f"\
        If you are interested in understanding more about Ethereum addresses, ask @aoth!",
        color=0x00ff00
    )
    eth_file = discord.File("assets/msgs/eth.jpg", filename="eth.jpg")
    embedVar.set_image(url="attachment://eth.jpg")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=eth_file)

async def send_admirable_msg(ctx, username, rarity_label, description):
    """Send the notification informing the user their sampled rarity label and description."""
    # Configure the message
    embedVar = discord.Embed(
        title=f"Merry Christmas {username}!\nYour loot box contained a {rarity_label} NFT!",
        description=f"\
            ```diff\n+It Seems You Have Been Quite Admirable This Year!```\
            ```css\n[{generate_christmas_countdown_msg()}]\n```\n\
            **Please stand-by while my elves generate your daily gifts!**\n\
            **I hope its value goes to the moon!**🪙🚀\n\
            \n**Generating:**```\n{description}\n```",
        color=get_rarity_color(rarity_label)
    )
    lootbox_file = discord.File("assets/msgs/loot-box.gif", filename="loot_box.gif")
    embedVar.set_image(url="attachment://loot_box.gif")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=lootbox_file)

async def send_users_msg(ctx, users):
    """Send a message to show the usernames and addresses."""
    output = table2ascii(
        header=["Username", "Address", "Collection"],
        body=[
            [username, data["address"], f"https://testnets.opensea.io/{data['address']}"]
            for username, data in users.items()
        ],
    )

    # Send the message to the channel
    await ctx.send(f"```\n{output}\n```")
