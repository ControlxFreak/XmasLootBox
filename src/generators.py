from pydalle import Dalle
from PIL import Image
from PIL.Image import Image as ImgType
from typing import List, Tuple, Any, Dict

def generate_dalle_art(username: str, password: str, description: str) -> List[ImgType]:
    """Execute the Dalle-2 art generation API using the provided credentials and text prompt.
    """
    # TODO: Add this back before release
    # ============================================== #
    # DO NOT CALL THIS YET!! IT WILL COST MONEY!!!
    # ============================================== #
    # # Configure the Dalle Client
    # client = Dalle(username, password)

    # # Invoke the text2im API
    # text2im_task = client.text2im(description)

    # # Download the images and save them to disk
    # images = []
    # for image in text2im_task.download():
    #     images.append(image.to_pil())

    # ============================================== #
    # TEMPORARILY USE MY EXAMPLE IMAGES!!!
    # ============================================== #
    images = [
        Image.open("imgs/cat_santa_{i}.png") for i in range(4)
    ]

    # Return the list of images
    return images

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
    s += " with "

    has_beard = False
    if attributes["beard"] is not None:
        has_beard = True
        s += "a "
        s += attributes["beard"]
        s += " beard "

    has_eyes = False
    if attributes["eyes"] != "sunglasses":
        has_eyes = True
        # Add a conjunction if we also have a beard
        if has_beard:
            s += "and "

        s += attributes["eyes"]
        s += " eyes "

    # ======================================== #
    # Add the accessories
    s += "wearing a "

    has_hat = False
    if attributes["hat"] is not None:
        has_hat = True
        s += attributes["hat"]
        s += " "
    
    if not has_eyes:
        # This means we must be wearing sunglasses
        # so this should be considered an accessory rather than a feature
        if has_hat:
            s += ", "

        s += attributes["eyes"]
        s += " "

    if attributes["scarf"] is not None:
        if has_hat or not has_eyes:
            s += "and a "
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
