import os
import discord
from dotenv import load_dotenv
import datetime

# Initialize the enviornment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL_ID = os.getenv("CHANNEL_ID")
OPENAI_USERNAME = os.getenv("OPENAI_USERNAME")
OPENAI_PASSWORD = os.getenv("OPENAI_PASSWORD")

VALID_YEAR = 2022
START_WEEK = 49
END_WEEK = 53

OPENSEA_CONTRACT_URL = "TODO"

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
