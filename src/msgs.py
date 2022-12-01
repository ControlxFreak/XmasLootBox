import datetime
from typing import Tuple

import discord
from table2ascii import table2ascii

from .rarity import get_rarity_color
from .constants import VALID_YEAR, OPENSEA_URL


def get_date() -> Tuple[int, int, int]:
    """Find the current date in ISO format (Year, Week Number, Day Number)."""
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
    """Generate the End of Event message."""
    # Create the embedded message
    embedVar = discord.Embed(
        title=f"Sorry {ctx.message.author.name}, Santa is Broke!",
        description=f"\
        Santa cannot afford gifts at the moment...\n \
        ```yaml\nBut never fear children, I invested all of my savings for next year's gifts into Doge coin!\n```\n\
        Elon says it will moon by next Christmas, so I'll be a billionaire! \
        *...if not, Mrs. Claus will be PISSSSSSED...*\n\n\
        Keep being admirable and check back next year! Ho Ho Ho!\n\n\
        ```css\n[{generate_christmas_countdown_msg(VALID_YEAR + 1)}]\n```\n\
        Checkout this year's Advent Calendar Collection at: [OpenSea]({OPENSEA_URL})\n\
        ",
        color=0xFF0000,
    )
    # Attach the image
    santa_rocket_file = discord.File(
        "assets/msgs/santa_rocket.gif", filename="santa_rocket.gif"
    )
    embedVar.set_image(url="attachment://santa_rocket.gif")
    # Send the message
    await ctx.channel.send(embed=embedVar, file=santa_rocket_file)


async def send_no_wallet_msg(ctx, username):
    # Configure the message
    embedVar = discord.Embed(
        title=f"Sorry, {username} is on the Naughty List!",
        description="\
        ...Well more accurately, I don't see you on the Nice List.\n\
        If you would like to play and receive gifts this year, contact @aoth to be added!\n\
        Ho Ho Ho Ho!\
        ",
        color=0xFF0000,
    )
    # Send the message
    await ctx.channel.send(embed=embedVar)


async def send_impish_msg(ctx):
    """Sends the impish message!"""
    # Configure the message
    embedVar = discord.Embed(
        title=f"How Impish of you {ctx.message.author.name}!",
        description="\
            ```diff\n-You have already claimed a loot box today...```\n\
            Greed is very impish!\
            If you are admirable, you can check back tomorrow for a new loot box.",
        color=0xFF0000,
    )
    impish_file = discord.File("assets/msgs/impish.jpg", filename="impish.jpg")
    embedVar.set_image(url="attachment://impish.jpg")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=impish_file)


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
        color=0x00FF00,
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
        description="\
        I'm sure @aoth would be happy to help. :)\n\
        If you are interested in creating an ethereum address, @aoth can help you with that too!",
        color=0xFF0000,
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
        color=0x00FF00,
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
        color=0x00873E,
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
        description="\
        If you are interested in understanding more about Ethereum addresses, ask @aoth!",
        color=0x00FF00,
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
        color=get_rarity_color(rarity_label),
    )
    lootbox_file = discord.File("assets/msgs/loot-box.gif", filename="loot_box.gif")
    embedVar.set_image(url="attachment://loot_box.gif")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=lootbox_file)


async def send_users_msg(ctx, accounts):
    """Send a message to show the usernames and addresses."""
    output = table2ascii(
        header=["Username", "Address"],
        body=[
            [
                username,
                acct["address"],
            ]
            for username, acct in accounts.items()
        ],
    )

    # Send the message to the channel
    await ctx.send(f"```\n{output}\n```")


async def send_no_nfts_msg(ctx):
    # Configure the message
    embedVar = discord.Embed(
        title=f"You Don't have any NFTs, {ctx.message.author.name}!",
        description="Use the !claim command to get your first gift!",
        color=0xFF0000,
    )
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar)


async def send_nobody_nfts_msg(ctx):
    # Configure the message
    embedVar = discord.Embed(
        title="Nobody has any NFTs yet!",
        description="Use the !claim command to get your first gift!",
        color=0xFF0000,
    )
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar)


async def send_nft_msg(ctx, username, nft_img, nft_id, addr):
    embedVar = discord.Embed(
        title=f"{username} owns this (NFT # {nft_id})!",
        description=f"\
        Checkout their collection on [OpenSea](https://testnets.opensea.io/{addr}?tab=collected&search[sortBy]=CREATED_DATE&search[sortAscending]=false)",
        color=0x00FF00,
    )
    img_file = discord.File(nft_img, filename=nft_img)
    embedVar.set_image(url=f"attachment://{nft_img}")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=img_file)


async def send_balance_msg(ctx, username, balance, num_nfts, addr):
    embedVar = discord.Embed(
        title=f"{username} has {balance:.3f} ETH and {num_nfts} NFTs!",
        description=f"\
        Checkout their collection on [OpenSea](https://testnets.opensea.io/{addr}?tab=collected&search[sortBy]=CREATED_DATE&search[sortAscending]=false)",
        color=0x00FF00,
    )
    money_file = discord.File("assets/msgs/money.png", filename="money.png")
    embedVar.set_image(url="attachment://money.png")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=money_file)


async def send_nft_dne_msg(ctx, nft_id, addr):
    embedVar = discord.Embed(
        title=f"{ctx.message.author.name}, NFT # {nft_id} Does Not Exist.",
        description=f"\
        Checkout your collection on [OpenSea](https://testnets.opensea.io/{addr}?tab=collected&search[sortBy]=CREATED_DATE&search[sortAscending]=false)",
        color=0xFF0000,
    )
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar)


async def send_not_your_nft_msg(ctx, nft_id, sender_addr, nft_owner):
    embedVar = discord.Embed(
        title=f"{ctx.message.author.name}, NFT # {nft_id} Is Not Yours.",
        description=f"\
        NFT # {nft_id} is owned by {nft_owner}.\n\
        Checkout your collection on [OpenSea](https://testnets.opensea.io/{sender_addr}?tab=collected&search[sortBy]=CREATED_DATE&search[sortAscending]=false)",
        color=0xFF0000,
    )
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar)


async def send_transfer_error_msg(ctx, sender, recipient, nft_id):
    embedVar = discord.Embed(
        title=f"The transfer of NFT # {nft_id} from {sender} to {recipient} failed.",
        description=f"\
        This most likely occurred due to a lack of funds in {sender}'s account.\n\
        Check your funds using the !balance command.",
        color=0xFF0000,
    )
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar)


async def send_transfer_success_msg(
    ctx, sender, recipient, nft_id, sender_addr, recipient_addr
):
    embedVar = discord.Embed(
        title=f"Successfully transferred NFT # {nft_id} from {sender} to {recipient}!",
        description=f"\
        Checkout your new collections:\n\
        [{sender}](https://testnets.opensea.io/{sender_addr}?tab=collected&search[sortBy]=CREATED_DATE&search[sortAscending]=false)\n\
        [{recipient}](https://testnets.opensea.io/{recipient_addr}?tab=collected&search[sortBy]=CREATED_DATE&search[sortAscending]=false)",
        color=0x00FF00,
    )
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar)


async def send_transfer_conf_msg(ctx, sender, recipient, nft_id):
    embedVar = discord.Embed(
        title=f"Sending NFT # {nft_id} as a gift from {sender} to {recipient}...",
        description="\
        My elves are flying the payload over now!\n\
        This might take 30s - 1min depending on network traffic.",
        color=0x00FF00,
    )
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar)


async def send_bot_faq_msg(ctx):
    embedVar = discord.Embed(
        title="Frequently Asked Questions (bot)",
        description="\
        **Why is this bot so slow?**\n\
        For a couple of reasons...\n\n\
        1. My laptop is slow (~10 years old)\n\
        2. Dalle is slow (~30s-1min)\n\
        3. I am slow (*..well my program at least..*) (~30s)\n\
        4. Uploading to IPFS is slow (~10s)\n\
        5. Interacting with an Ethereum testnet is slow (~30s-1 min)\n\
        6. OpenSea is slow (~30s - 1 min)\n\n\
        sorry! I hope it is worth the wait. \
        Also, times can greatly vary based on how busy the Ethereum network is at the time. \
        If none of the above made sense, use the '!faq web3' command for more information.\n\n\
        **How do I participate?**\n\
        Every day you can claim a gift using ONE of the following commands:\n\n\
        !claim\n\
        !create ARTWORK DESCRIPTION\n\n\
        Both commands will send you a set of 4 NFTs. \
        The !create command allows you to provide your own art description to be sent to the AI art generator, [Dalle-2](https://openai.com/dall-e-2/). \
        The !claim command will randomly sample the attributes for your artwork. \
        Gifts from both commands will have an associated rarity level (read below), which determines the type of animated frame that your NFT will have.\n\n\
        **What is rarity?**\n\
        There are 7 possible rarity levels for your gifts:\n\n\
        1. Common\n\
        2. Uncommon\n\
        3. Rare\n\
        4. Legendary\n\
        5. Mythical\n\
        6. N-F-Tacular\n\
        7. Christmas Miracle\n\n\
        Each rarity level has its unique set of animated frames and set of attributes. \
        *My elves usually feel increasingly generous as it gets closer to Christmas!* As a result, every week it becomes more likely to receive higher-tier gifts! \
        [Here is a more detailed description, including the probabilities per week.](https://github.com/ControlxFreak/XmasLootBox/blob/main/DESIGN.md)\n\n\
        **How much ETH do I need to gift an NFT?**\n\
        This really depends on how busy the network is.\n\n\
        *Short answer:* I think ~0.004 ETH should be good on average.\n\n\
        *Long answer:* Every transaction on the Ethereum network requires gas to prevent malicious users from attacking the network. \
        The amount of gas required to do each operation on the network varies with network traffic. \
        Busy network => high gas prices, idle network => low gas prices. \
        On average, the price of gas is around ~50Gwei (50e-9 ETH... just think of Gwei as the 'nano-' equivalent in meters), but this fluctuates greatly. \
        Now, that price is *per computer operation*... transferring an NFT requires around 65,000 operations, meaning the cost is around (65000 * 50e-9) = 0.00325 ETH. \
        (There is also a tip that you need to pay the node operators to incentivize them to continue donating their computers to the Ethereum network... but that is cheap on a testnet so I rounded to 0.004 ETH.)\n\
        [Here is more information if you are interested](https://ethereum.org/en/developers/docs/gas/), or use the '!faq web3` for more answers to FAQs about web3.\n\n\
        **@aoth, why are you writing this instead of studying for your exam, spending time with your child or working on your thesis?**\n\
        Great question. 🤷‍♂️ I needed something to do when Katelyn was asleep and I missed coding.",
        color=0x4056AA,
    )
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar)


async def send_web3_faq_msg(ctx):
    embedVar = discord.Embed(
        title="Frequently Asked Questions (web3)",
        description="\
        **What is Ethereum?**\n\
        Ethereum is just a big-ol' decentralized computer.\n\
        It sounds fancy to tech people cause it uses a blockchain to maintain its state. \
        It sounds appealing to finance people cause it can be used in a secure and trustless manner for financial transactions (i.e., without the need for any 3rd parties trying to take a cut of the profits). \
        But it is really just a big virtual machine spread out across the world, run by millions of people, owned by no one, that people can use to run stupid code on... like this! \
        [Here is more information](https://ethereum.org/en/)\n\n\
        **What is the difference between ETH and Ethereum?**\n\
        ETH is just the $$ used in the Ethereum network to pay for things. \
        Since no single entity owns this massive lump of computers, no one can directly stop malicious users from trying to break it. \
        So, to prevent that, it costs ETH ([called gas](https://ethereum.org/en/developers/docs/gas/)) to execute software on the Ethereum network. \
        This is why you need ETH in your account to do things like send NFTs.\n\n\
        **What is an NFT?**\n\
        An NFT is really just a piece of code that says person X owns this unique digital asset. \
        That asset (in our case, the image) is represented by a token and is sent to the owner's address. \
        This becomes cryptographically secured in such a manner that *the proof of ownership* cannot be duplicated (of course the image can be duplicated, but no one else can prove they own it is the idea). \
        People are now using NFTs to sell houses and stuff, it doesn't have to be cat images. \
        [Here is more information](https://en.wikipedia.org/wiki/Non-fungible_token)\n\n\
        **What is IPFS?**\n\
        Just think of IPFS as a decentralized dropbox or google drive.\n\
        It allows you to store your data in a decentralized way (i.e., without the need for a 3rd party like Dropbox or Google). \
        There are millions of computers around the world that store a small encrypted fraction of your file and when you want to access your file, it gets reassembled and sent to you. \
        Crypto people like it because it isn't owned by anyone (so it is censorship resistant). \
        I like it because its free (typically). [Here is more information](https://en.wikipedia.org/wiki/InterPlanetary_File_System).\n\n\
        **What is a Testnet?**\n\
        An Ethereum Testnet is a version of Ethereum made for developers.\n\
        Nothing on it has any value in the real world. \
        You cannot sell your ETH from this network for USD or anything like that... In fact, websites will give you free ETH on a testnet to use for development. \
        However, there is no free lunch. Since it is just used for testing, it can be way more buggy than the real Ethereum network and (since it doesn't cost real $$) developers SPAM the network with transactions all the time and cause it to slow down... but it is free.\n\
        If you care, we are using the [Goerli testnet](https://goerli.net/). There are others, but this is the best IMO.\n\n",
        color=0x4056AA,
    )
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar)


async def send_welcome_msg(ctx):
    embedVar = discord.Embed(
        title="HO HO HO HO! MERRY CHRISTMAS! Welcome to the 2022 Discord Advent Calendar!",
        description=f"\
        Every day in the month of December, my elves will make you a special gift:\n\n*4 completely unique NFTs and 0.01 ETH!*\n\n\
        My new AI elves have been working hard all year to perfectly generate unique gifts, spanning a variety of rarity levels and an assortment of subjects, hats, eyes, scarfs and backgrounds.\
        With over 14 million possible combinations, there is sure to be something for everyone! ...and if not, you can send your NFTs as gifts to other users if you are feeling the Christmas spirit!\n\n\
        *Use the '!join' command to be added to the game!*\n\n\
        *Once you have been added, use the '!claim' or '!create' command to claim your daily gift!*\n\n\
        Use the '!help' or '!faq' commands for more information or answers to frequently asked questions respectively.\
        Throughout the month, we can see our collection grow on [OpenSea]({OPENSEA_URL})!\n\n",
        color=0xC54245,
    )
    preview_file = discord.File("assets/example/preview.gif", filename="preview.gif")
    embedVar.set_image(url="attachment://preview.gif")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=preview_file)


async def send_invalid_username(ctx, username):
    embedVar = discord.Embed(
        title=f"Cannot create account for: {username}.",
        description="This user is neither on my naughty nor nice list!\n\n\
        Double check the spelling and be sure to use their *actual* name (not the server nickname and do not include the numbers).",
        color=0xFF0000,
    )
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar)


async def send_error(ctx):
    embedVar = discord.Embed(
        title="Oh No! My Elves are Broken...",
        description="It looks like my AI elves have broken their hands during the hot coco races, meaning they cannot draw any gifts!\n\n\
        Contact @aoth and tell him to fix this immediately.",
        color=0xFF0000,
    )
    elf_file = discord.File("assets/msgs/broken_elf.png", filename="broken_elf.png")
    embedVar.set_image(url="attachment://broken_elf.png")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=elf_file)


async def send_mint_error(ctx):
    embedVar = discord.Embed(
        title="Oh No! My Reindeer are Broken...",
        description="It looks like my reindeer are sick, meaning they cannot deliver your gift!\n\n\
        Contact @aoth and tell him to fix this immediately.",
        color=0xFF0000,
    )
    elf_file = discord.File(
        "assets/msgs/sick_reindeer.png", filename="sick_reindeer.png"
    )
    embedVar.set_image(url="attachment://sick_reindeer.png")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=elf_file)


async def send_daily_eth_error(ctx):
    embedVar = discord.Embed(
        title="Santa's been hacked!",
        description="I never should have trusted that shady elf on ChristmasFans...\n\n\
        Now I have no more ETH to give to the admirable...\n\n\
        Contact @aoth and tell him to fix this immediately.",
        color=0xFF0000,
    )
    elf_file = discord.File("assets/msgs/santa_hacker.png", filename="santa_hacker.png")
    embedVar.set_image(url="attachment://santa_hacker.png")
    # Send the message to the channel
    await ctx.channel.send(embed=embedVar, file=elf_file)


async def send_all_balances_msg(ctx, bals):
    output = table2ascii(
        header=["Username", "ETH", "NFTs"],
        body=[
            [
                username,
                f"{bal['eth']:.3f}",
                bal["nft"],
            ]
            for username, bal in bals.items()
        ],
    )

    # Send the message to the channel
    await ctx.send(f"```\n{output}\n```")
