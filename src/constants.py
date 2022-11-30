import os

# Define the valid time
VALID_YEAR = 2022
START_WEEK = 48

# Define the input/output directories
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "../assets/")
FRAME_DIR = os.path.join(BASE_DIR, ASSET_DIR, "frames/")
OUT_DIR = os.path.join(BASE_DIR, "../nfts/")

# Define the collection URL
OPENSEA_URL = "https://testnets.opensea.io/collection/testtoken2-0ovzz2rcee?search[sortAscending]=false&search[sortBy]=CREATED_DATE"
