from typing import List, Dict
from PIL import Image
from PIL.Image import Image as ImgType
from dalle2 import Dalle2

def generate_dalle_art(dalle : Dalle2, description: str, img_dir: str) -> List[ImgType]:
    """Execute the Dalle-2 art generation API using the provided credentials and text prompt.

    DO NOT CALL WITH `sim=True` UNTIL YOU ARE READY!! IT WILL COST MONEY!!!
    """
    # Generate and download new Dalle2 images
    img_files = dalle.generate_and_download(description,image_dir=img_dir)
    images = []
    for img_file in img_files:
        images.append(Image.open(img_file))

    # Return the list of images
    return images, img_files

def generate_dalle_description(attributes: Dict[str, str])->str:
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

    if not has_eyes:
        # This means we must be wearing sunglasses
        # so this should be considered an accessory rather than a feature
        if has_hat:
            s += ", "
        else:
            s += "wearing a "

        s += attributes["eyes"]
        s += " "

    if attributes["scarf"] is not None:
        if has_hat or not has_eyes:
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

def generate_erc721_metadata(attributes: Dict[str, str], description: str) -> Dict[str, str]:
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
