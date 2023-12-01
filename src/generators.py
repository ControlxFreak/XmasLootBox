from typing import List, Dict, Tuple
import os
from PIL import Image
from PIL.Image import Image as ImgType
from base64 import b64decode
from .constants import ASSET_DIR
from io import BytesIO


def generate_dalle_art(
    openai_client, description: str, img_file: str
) -> Tuple[List[ImgType], List[str]]:
    """Execute the Dalle-3 art generation API using the provided credentials and text prompt."""
    # Query the image
    response = openai_client.images.generate(
        model="dall-e-3",
        prompt=description,
        size="1024x1024",
        quality="standard",
        response_format="b64_json",
        n=1,
    )

    imgbytes = b64decode(response.data[0].b64_json)
    with open(img_file, mode="wb") as png:
        png.write(imgbytes)

    # Return the list of images
    img = Image.open(BytesIO(imgbytes))
    revised_prompt = response.data[0].revised_prompt

    return img, revised_prompt


def generate_example_art(
    unq_img_dir: str, first_nft_id: int
) -> Tuple[List[ImgType], List[str]]:
    """Just generate some example artwork for testing."""
    # Load the example images
    images = [
        Image.open(os.path.join(ASSET_DIR, f"example/{i}.png")) for i in range(1, 5)
    ]
    # Copy them into the correct location so they can be uploaded
    img_files = [
        os.path.join(unq_img_dir, f"{first_nft_id + idx}.png") for idx in range(4)
    ]
    _ = [img.save(img_file) for img, img_file in zip(images, img_files)]

    return images, img_files


def generate_dalle_description(attributes: Dict[str, str]) -> str:
    """Generate the dalle description from the attributes."""
    # ======================================== #
    # Begin with the age
    s = ""
    if attributes["age"] is not None:
        s += "a "
        s += attributes["age"]
        s += " "

    # ======================================== #
    # Add the subject
    s += attributes["subject"].lower()

    # ======================================== #
    # Add the personal features
    has_eyes = False
    if attributes["eyes"] != "sunglasses":
        has_eyes = True
        s += " with "
        s += attributes["eyes"]
        s += " eyes "

    # ======================================== #
    # Add the accessories
    has_hat = False
    if attributes["hat"] is not None:
        has_hat = True
        s += "wearing a "
        s += attributes["hat"]
        s += " "

    has_sweater = False
    if attributes["sweater"] is not None:
        has_sweater = True
        if has_hat:
            s += ", "
        else:
            s += "wearing a "

        s += attributes["sweater"]
        s += " Christmas sweater "

    if not has_eyes:
        # This means we must be wearing sunglasses
        # so this should be considered an accessory rather than a feature
        if has_hat or has_sweater:
            s += ", "
        else:
            s += "wearing "

        s += attributes["eyes"]
        s += " "

    if attributes["scarf"] is not None:
        if has_hat or has_sweater or not has_eyes:
            s += "and a "
        else:
            s += "wearing a "

        s += attributes["scarf"]
        s += " scarf "

    # ======================================== #
    # Add the background
    s += "in a "
    s += attributes["background"]
    s += " background, "

    # ======================================== #
    # Add the style
    s += "drawn in a "
    s += attributes["style"]
    s += " style"

    return s


def generate_erc721_metadata(
    attributes: Dict[str, str], description: str
) -> Dict[str, str]:
    """Generate a dictionary that complies with the ERC721 metadata standard."""
    metadata = {
        "name": "Xmas Lootbox Reward # {0}",
        "description": description,
        "image": "<UPDATE WITH IPFS CID>",
    }

    # Reformat the attributes into ERC721 compliance
    fmt_attributes = [
        {
            "trait_type": key,
            "value": value,
        }
        for key, value in attributes.items()
        if value is not None
    ]

    # Append this to the metadata dictionary and return
    metadata["attributes"] = fmt_attributes

    return metadata
