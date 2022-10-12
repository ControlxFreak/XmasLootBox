from pydalle import Dalle
from PIL import Image
from PIL.Image import Image as ImgType
from typing import List, Tuple, Any

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

def generate_dalle_description(attributes: Tuple[int])->str:
    pass