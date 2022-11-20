# %%
from copy import deepcopy
import json
import os
from dotenv import load_dotenv
from src.generators import generate_dalle_description, generate_erc721_metadata, generate_dalle_art
from src.rarity import sample_rarity_label_uniform, sample_attributes, sample_frame
from src.artists import add_frame
from dalle2 import Dalle2
from PIL import Image

print("DO NOT RUN THIS.")
print("THIS IS JUST A TEST SCRIPT FOR DRAINING MY ACCOUNT OF UNUSED VALUES")
exit()

load_dotenv()
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
FRAME_DIR = "frames/"
OUT_DIR = "out/"

# Define the number of NFTs that you want to generate
N = 3

# Construct the dalle-2 object
dalle = Dalle2(OPENAI_TOKEN)

# Get the next NFT ID
with open('next_id', 'r', encoding="utf8") as f:
    next_nft_id = int(f.readline())

# Generate some NFTs
for _ in range(N):
    print("==========================================")
    print("------------------------------------------")
    print("------------------------------------------")
    print("==========================================")

    # Sample a rarity level
    rarity_label = sample_rarity_label_uniform()
    print(f"Sampled Rarity Level: {rarity_label}")

    # Sample the atributes
    attributes = sample_attributes(rarity_label)

    # Generate the description string and query Dalle-2
    description = generate_dalle_description(attributes)
    print(f"Description: {description}")

    # Generate the dalle images
    images = generate_dalle_art(dalle, description)

    # Sample the frame
    frame_name = sample_frame(rarity_label)
    print(f"Frame Name: {frame_name}")

    if frame_name is None:
        nft_imgs = [image for image in images]
    else:
        # Add the frame to each image
        frame_path = os.path.join(FRAME_DIR, f"{frame_name}.gif")
        nft_imgs = [
            add_frame(image, frame_path) for image in images
        ]

    # Generate the ERC721-compliant metadata json
    metadata = generate_erc721_metadata(attributes)

    # Save the images and metadata to disk
    for img, nft_img in zip(images, nft_imgs):
        print(f"Saving NFT: {next_nft_id}...")

        # First, save the image
        img.save(os.path.join(OUT_DIR, f"{next_nft_id}_img.png"))

        # Second, save the nft
        if frame_name is None:
            nft_img.save(os.path.join(OUT_DIR, f"{next_nft_id}.png"))
        else:
            nft_img[0].save(os.path.join(OUT_DIR, f"{next_nft_id}.gif"),
                save_all = True, append_images = nft_img[1:],
                optimize = False, duration = 10, loop=0)

        # Lastly, save the metadata
        metadata_cpy = deepcopy(metadata)
        metadata_cpy["name"] = metadata_cpy["name"].format(next_nft_id)
        metadata_cpy["description"] = description

        with open(os.path.join(OUT_DIR, f"{next_nft_id}.json"), "w", encoding="utf8") as outfile:
            json.dump(metadata_cpy, outfile)

        next_nft_id+=1

    # Update the ID
    with open('next_id', 'w', encoding="utf8") as f:
        f.write(f"{next_nft_id}")

# %%
