import os
from PIL import Image
from PIL.Image import Image as ImgType
from typing import List

from .constants import FRAME_DIR

IMG_WIDTH, IMG_HEIGHT = 256, 256

def get_frame_offset(frame_name: str) -> int:
    """Get an offset padding based on the frame."""
    if frame_name in [None, "speedlines", "rain_of_gold"]:
        # NOTE: The speedlines and rain of gold frames look a lot better
        #       if you don't create a buffer border.
        offset = 0
    else:
        # NOTE: This offset creates a buffer border to prevent the frame from
        #       overlapping the image.
        offset = 140
    return offset


def add_frame(image: Image, frame_name: str) -> List[ImgType]:
    """Adds an animated GIF frame to an image."""
    output_images = []

    if frame_name is None:
        # There should not be a frame (common NFT)
        # Just make a fake gif with 2 frames
        output_images.extend([image.resize((IMG_WIDTH, IMG_HEIGHT)) for _ in range(2)])
    else:
        # Construct the path
        frame_path = os.path.join(FRAME_DIR, f"{frame_name}.gif")

        # Load the frame
        frame_gif = Image.open(frame_path)

        # Get the image's size
        image = image.resize((IMG_WIDTH, IMG_HEIGHT))

        # Get the frame
        offset = get_frame_offset(frame_name)

        # Create the base background image and paste the desired image ontop
        base_layer = Image.new(mode="RGB", size=(IMG_WIDTH + offset, IMG_HEIGHT + offset))
        base_layer.paste(image, (offset//2, offset//2))

        # Break apart the frame gif, paste it ontop of the base image, and reconstruct it in a list
        try:
            while 1:
                # Get the next frame, resize it, and add an alpha layer
                frame_gif.seek(frame_gif.tell()+1)
                frame_img = frame_gif.resize((IMG_WIDTH + offset, IMG_HEIGHT + offset))
                frame_img = frame_img.convert('RGBA')

                # Copy the base layer image
                temp_img = base_layer.copy()
                # Then the frame on top
                temp_img.paste(frame_img, (0, 0), frame_img)

                # Add this frame to the output list
                output_images.append(temp_img.copy())
        except EOFError:
            pass # end of sequence

    # Return the output gif images
    return output_images

def create_img_preview(nft_imgs: List[List[ImgType]], frame_name: str) -> List[ImgType]:
    """Creates a 4x4 preview of your NFTs using the first image frame of the gif.
    NOTE: This requires that exactly 4 NFT gifs are provided.
    """
    # Get the first frame from each gif
    prev_imgs = [img[0] for img in nft_imgs]

    offset = get_frame_offset(frame_name)

    # Construct a base image
    preview = Image.new(mode="RGB", size=(2 * (IMG_WIDTH + offset), 2 * (IMG_HEIGHT + offset)))

    # Paste each image onto the base layer
    preview.paste(prev_imgs[0], (0, 0))
    preview.paste(prev_imgs[1], (IMG_WIDTH+offset, 0))
    preview.paste(prev_imgs[2], (0, IMG_HEIGHT+offset))
    preview.paste(prev_imgs[3], (IMG_WIDTH+offset, IMG_HEIGHT+offset))

    return preview

def create_nft_preview(nft_imgs: List[List[ImgType]], frame_name: str) -> List[ImgType]:
    """Creates a 4x4 preview of your NFTs.
    NOTE: This requires that exactly 4 NFT gifs are provided and that they all share exactly the same number of frames.
    """
    # Construct a base image
    # We will make it half the size to fit in the discord message
    offset = get_frame_offset(frame_name)
    width = (IMG_WIDTH + offset) // 2
    height =  (IMG_HEIGHT + offset) // 2
    base_preview = Image.new(mode="RGB", size=(2 * width, 2 * height))

    # Get the number of frames
    num_frames = len(nft_imgs[0])

    # Paste over every layer
    preview = []
    for i in range(num_frames):
        # Paste each image onto the base layer
        temp_img = base_preview.copy()
        temp_img.paste(nft_imgs[0][i].resize((width, height)), (0, 0))
        temp_img.paste(nft_imgs[1][i].resize((width, height)), (width, 0))
        temp_img.paste(nft_imgs[2][i].resize((width, height)), (0, width))
        temp_img.paste(nft_imgs[3][i].resize((width, height)), (width, height))
        preview.append(temp_img)

    return preview
